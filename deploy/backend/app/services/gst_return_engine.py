import pandas as pd
import json
import re
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from app.services.file_parser import SmartFileParser

logger = logging.getLogger(__name__)
DB_PATH = Path("/data/payments.db")


class GSTReturnEngine:
    def __init__(self):
        self.parser = SmartFileParser()
        self._init_db()
        logger.info("✅ GST Return engine loaded")

    def _init_db(self):
        os.makedirs("/data", exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS gst_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gstin TEXT UNIQUE NOT NULL,
            trade_name TEXT,
            state_code TEXT,
            email TEXT,
            phone TEXT,
            filing_frequency TEXT DEFAULT 'monthly',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS gst_filings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_gstin TEXT NOT NULL,
            return_type TEXT NOT NULL,
            period TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            data_json TEXT,
            filed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS gst_audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_gstin TEXT,
            action TEXT NOT NULL,
            details TEXT,
            user_email TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
        conn.close()

    # =====================================================
    # GSTR-1 PREPARATION
    # =====================================================

    def prepare_gstr1(self, sales_file: str, period: str, client_gstin: str = "") -> dict:
        logger.info(f"🔄 Preparing GSTR-1 for {period}")
        df = self.parser.parse(sales_file)
        if df.empty:
            return {"error": "Could not parse sales file"}

        invoices = self._extract_invoices(df)
        logger.info(f"📊 Found {len(invoices)} invoices")

        b2b, b2cl, b2cs, exports, credit_notes, debit_notes = {}, [], [], [], [], []

        for inv in invoices:
            inv_type = self._classify(inv)
            if inv_type == "b2b":
                if inv["gstin"] not in b2b:
                    b2b[inv["gstin"]] = {"ctin": inv["gstin"], "inv": []}
                b2b[inv["gstin"]]["inv"].append(self._to_gstr1_inv(inv))
            elif inv_type == "b2cl":
                b2cl.append({"pos": inv["pos"], "inv": [self._to_gstr1_inv(inv)]})
            elif inv_type == "b2cs":
                b2cs.append({"sply_ty": "INTRA", "typ": "OE", "txval": round(inv["taxable"], 2),
                             "iamt": round(inv["igst"], 2), "camt": round(inv["cgst"], 2),
                             "samt": round(inv["sgst"], 2), "csamt": round(inv["cess"], 2)})
            elif inv_type == "export":
                exports.append({"exp_typ": "WPAY", "inv": [self._to_gstr1_inv(inv)]})
            elif inv_type == "credit":
                credit_notes.append(self._to_note(inv, "C"))
            elif inv_type == "debit":
                debit_notes.append(self._to_note(inv, "D"))

        gstr1 = {
            "gstin": client_gstin, "fp": period,
            "gt": round(sum(i["inv_value"] for i in invoices), 2),
            "cur_gt": round(sum(i["inv_value"] for i in invoices), 2),
            "b2b": list(b2b.values()), "b2cl": b2cl, "b2cs": b2cs,
            "exp": exports, "cdnr": credit_notes, "cdnur": debit_notes,
        }

        summary = {
            "total_invoices": len(invoices),
            "b2b": sum(len(v["inv"]) for v in b2b.values()),
            "b2cl": len(b2cl), "b2cs": len(b2cs),
            "exports": len(exports), "credit_notes": len(credit_notes),
            "debit_notes": len(debit_notes),
            "total_taxable": round(sum(i["taxable"] for i in invoices), 2),
            "total_tax": round(sum(i["igst"] + i["cgst"] + i["sgst"] for i in invoices), 2),
            "total_value": round(sum(i["inv_value"] for i in invoices), 2),
        }

        self._log_audit(client_gstin, "GSTR1_PREPARED", json.dumps(summary))
        return {"gstr1": gstr1, "summary": summary}

    # =====================================================
    # GSTR-2B RECONCILIATION
    # =====================================================

    def reconcile_gstr2b(self, books_file: str, gstr2b_file: str, client_gstin: str = "") -> dict:
        logger.info("🔄 GSTR-2B reconciliation")
        books_df = self.parser.parse(books_file)
        portal_df = self.parser.parse(gstr2b_file)
        if books_df.empty or portal_df.empty:
            return {"error": "Could not parse files"}

        books = self._extract_invoices(books_df)
        portal = self._extract_invoices(portal_df)

        matched, mismatched, missing_2b, missing_books = [], [], [], []
        matched_idx = set()
        itc_eligible, itc_blocked = 0, 0

        for book in books:
            best, best_score, best_i = None, 0, -1
            for pi, p in enumerate(portal):
                if pi in matched_idx:
                    continue
                score = self._inv_match(book, p)
                if score > best_score:
                    best_score, best, best_i = score, p, pi

            if best and best_score >= 50:
                matched_idx.add(best_i)
                diffs = self._get_diffs(book, best)
                itc = best["igst"] + best["cgst"] + best["sgst"]
                if diffs:
                    mismatched.append({
                        "invoice_number": book["inv_num"], "gstin": book["gstin"],
                        "vendor_name": book["name"], "book_taxable": book["taxable"],
                        "portal_taxable": best["taxable"], "status": "Amount Mismatch" if "gstin" not in ";".join(diffs) else "GSTIN Mismatch",
                        "confidence": round(best_score, 2), "differences": "; ".join(diffs),
                    })
                else:
                    itc_eligible += itc
                    matched.append({
                        "invoice_number": book["inv_num"], "gstin": book["gstin"],
                        "vendor_name": book["name"], "book_taxable": book["taxable"],
                        "portal_taxable": best["taxable"], "itc_amount": round(itc, 2),
                        "status": "Matched", "confidence": round(best_score, 2),
                    })
            else:
                itc_blocked += book["igst"] + book["cgst"] + book["sgst"]
                missing_2b.append({
                    "invoice_number": book["inv_num"], "gstin": book["gstin"],
                    "vendor_name": book["name"], "taxable_value": book["taxable"],
                    "status": "Missing in GSTR-2B",
                    "reason": "Invoice in books but not in GSTR-2B. ITC cannot be claimed.",
                })

        for pi, p in enumerate(portal):
            if pi not in matched_idx:
                missing_books.append({
                    "invoice_number": p["inv_num"], "gstin": p["gstin"],
                    "vendor_name": p["name"], "taxable_value": p["taxable"],
                    "status": "Missing in Books",
                    "reason": "Invoice in GSTR-2B but not in books.",
                })

        summary = {
            "total_book": len(books), "total_2b": len(portal),
            "matched": len(matched), "mismatched": len(mismatched),
            "missing_in_2b": len(missing_2b), "missing_in_books": len(missing_books),
            "itc_eligible": round(itc_eligible, 2), "itc_blocked": round(itc_blocked, 2),
            "match_rate": round(len(matched) / max(len(matched) + len(mismatched) + len(missing_2b), 1) * 100, 2),
        }

        self._log_audit(client_gstin, "GSTR2B_RECONCILED", json.dumps(summary))
        return {"summary": summary, "matched": matched, "mismatched": mismatched,
                "missing_in_2b": missing_2b, "missing_in_books": missing_books}

    # =====================================================
    # GSTR-3B PREPARATION
    # =====================================================

    def prepare_gstr3b(self, gstr1_data: dict, gstr2b_data: dict, period: str, client_gstin: str = "") -> dict:
        logger.info(f"🔄 Preparing GSTR-3B for {period}")
        gstr1_sum = gstr1_data.get("summary", {})
        gstr2b_sum = gstr2b_data.get("summary", {})

        outward_taxable = gstr1_sum.get("total_taxable", 0)
        outward_igst = gstr1_sum.get("total_tax", 0) * 0.33
        outward_cgst = gstr1_sum.get("total_tax", 0) * 0.33
        outward_sgst = gstr1_sum.get("total_tax", 0) * 0.34

        itc_eligible = gstr2b_sum.get("itc_eligible", 0)
        itc_igst = itc_eligible * 0.33
        itc_cgst = itc_eligible * 0.33
        itc_sgst = itc_eligible * 0.34

        tax_igst = max(0, round(outward_igst - itc_igst, 2))
        tax_cgst = max(0, round(outward_cgst - itc_cgst, 2))
        tax_sgst = max(0, round(outward_sgst - itc_sgst, 2))

        gstr3b = {
            "gstin": client_gstin, "ret_period": period,
            "table_3_1": {
                "outward_taxable": round(outward_taxable, 2),
                "outward_igst": round(outward_igst, 2),
                "outward_cgst": round(outward_cgst, 2),
                "outward_sgst": round(outward_sgst, 2),
            },
            "table_4": {
                "itc_igst": round(itc_igst, 2), "itc_cgst": round(itc_cgst, 2),
                "itc_sgst": round(itc_sgst, 2),
                "itc_ineligible": round(gstr2b_sum.get("itc_blocked", 0), 2),
            },
            "tax_payable": {
                "igst": tax_igst, "cgst": tax_cgst, "sgst": tax_sgst,
                "total": round(tax_igst + tax_cgst + tax_sgst, 2),
            },
        }

        self._log_audit(client_gstin, "GSTR3B_PREPARED",
                        json.dumps({"period": period, "tax": gstr3b["tax_payable"]}))
        return {"gstr3b": gstr3b}

    # =====================================================
    # CLIENT MANAGEMENT
    # =====================================================

    def add_client(self, gstin: str, trade_name: str = "", email: str = "", phone: str = "") -> dict:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        try:
            c.execute("INSERT OR REPLACE INTO gst_clients (gstin, trade_name, state_code, email, phone) VALUES (?,?,?,?,?)",
                      (gstin.upper(), trade_name, gstin[:2] if len(gstin) >= 2 else "", email, phone))
            conn.commit()
            self._log_audit(gstin.upper(), "CLIENT_ADDED", trade_name)
            return {"success": True, "gstin": gstin.upper()}
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def list_clients(self) -> list:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("SELECT * FROM gst_clients ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "gstin": r[1], "trade_name": r[2],
                 "state_code": r[3], "email": r[4], "phone": r[5],
                 "filing_frequency": r[6], "created_at": r[7]} for r in rows]

    def get_client_filings(self, gstin: str) -> list:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("SELECT * FROM gst_filings WHERE client_gstin=? ORDER BY created_at DESC", (gstin,))
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "return_type": r[2], "period": r[3],
                 "status": r[4], "filed_at": r[6], "created_at": r[7]} for r in rows]

    # =====================================================
    # DASHBOARD & AUDIT
    # =====================================================

    def get_dashboard(self, client_gstin: str = None) -> dict:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM gst_clients")
        total_clients = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM gst_filings WHERE status='filed'")
        filed = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM gst_filings WHERE status='draft'")
        draft = c.fetchone()[0]
        if client_gstin:
            c.execute("SELECT return_type, period, status FROM gst_filings WHERE client_gstin=? ORDER BY created_at DESC", (client_gstin,))
        else:
            c.execute("SELECT client_gstin, return_type, period, status FROM gst_filings ORDER BY created_at DESC LIMIT 20")
        recent = c.fetchall()
        conn.close()
        return {
            "total_clients": total_clients, "filed_returns": filed,
            "draft_returns": draft,
            "recent_filings": [{"gstin": f[0], "type": f[1], "period": f[2], "status": f[3]} for f in recent],
        }

    def get_audit_trail(self, client_gstin: str = None, limit: int = 100) -> list:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        if client_gstin:
            c.execute("SELECT * FROM gst_audit_trail WHERE client_gstin=? ORDER BY timestamp DESC LIMIT ?", (client_gstin, limit))
        else:
            c.execute("SELECT * FROM gst_audit_trail ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "gstin": r[1], "action": r[2],
                 "details": r[3], "user_email": r[4], "timestamp": r[5]} for r in rows]

    def _log_audit(self, gstin: str, action: str, details: str = ""):
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("INSERT INTO gst_audit_trail (client_gstin, action, details) VALUES (?,?,?)",
                         (gstin, action, details))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Audit error: {e}")

    # =====================================================
    # HELPERS
    # =====================================================

    def _extract_invoices(self, df: pd.DataFrame) -> list:
        cols = {str(c).strip().lower(): c for c in df.columns}
        inv_col = self._fc(cols, ["invoice number", "invoice no", "inv no", "bill number", "vch no"])
        date_col = self._fc(cols, ["invoice date", "date", "bill date"])
        gstin_col = self._fc(cols, ["gstin", "gst number", "supplier gstin", "vendor gstin"])
        name_col = self._fc(cols, ["trade name", "vendor name", "supplier name", "name", "party name"])
        value_col = self._fc(cols, ["invoice value", "total amount", "total value", "gross amount"])
        taxable_col = self._fc(cols, ["taxable value", "taxable amount", "assessable value", "base amount", "net amount"])
        igst_col = self._fc(cols, ["igst", "integrated tax"])
        cgst_col = self._fc(cols, ["cgst", "central tax"])
        sgst_col = self._fc(cols, ["sgst", "state tax", "utgst"])
        cess_col = self._fc(cols, ["cess", "cess amount"])
        pos_col = self._fc(cols, ["place of supply", "pos"])
        hsn_col = self._fc(cols, ["hsn", "hsn code", "hsn/sac"])

        invoices = []
        for _, row in df.iterrows():
            inv_num = str(row.get(inv_col, "")).strip() if inv_col else ""
            gstin = str(row.get(gstin_col, "")).strip().upper() if gstin_col else ""
            if not inv_num and not gstin:
                continue
            taxable = self._sf(row.get(taxable_col)) if taxable_col else 0
            igst = self._sf(row.get(igst_col)) if igst_col else 0
            cgst = self._sf(row.get(cgst_col)) if cgst_col else 0
            sgst = self._sf(row.get(sgst_col)) if sgst_col else 0
            cess = self._sf(row.get(cess_col)) if cess_col else 0
            inv_val = self._sf(row.get(value_col)) if value_col else (taxable + igst + cgst + sgst)
            invoices.append({
                "inv_num": inv_num, "date": str(row.get(date_col, "")) if date_col else "",
                "gstin": gstin, "name": str(row.get(name_col, "")).strip() if name_col else "",
                "inv_value": inv_val, "taxable": taxable,
                "igst": igst, "cgst": cgst, "sgst": sgst, "cess": cess,
                "pos": str(row.get(pos_col, "")).strip() if pos_col else "",
                "hsn": str(row.get(hsn_col, "")).strip() if hsn_col else "",
            })
        return invoices

    def _fc(self, cols_lower, keywords):
        for kw in keywords:
            for cl, co in cols_lower.items():
                if cl == kw:
                    return co
        for kw in keywords:
            for cl, co in cols_lower.items():
                if kw in cl or cl in kw:
                    return co
        return None

    def _sf(self, value) -> float:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0.0
        s = str(value).strip().replace(',', '').replace('₹', '').replace('Rs', '').replace('INR', '')
        s = re.sub(r'[^\d.\-]', '', s)
        try:
            return abs(float(s)) if s else 0.0
        except ValueError:
            return 0.0

    def _classify(self, inv: dict) -> str:
        desc = (inv["inv_num"] + " " + inv["name"]).upper()
        if "CREDIT NOTE" in desc or inv["inv_value"] < 0:
            return "credit"
        if "DEBIT NOTE" in desc:
            return "debit"
        if "EXPORT" in desc:
            return "export"
        if not inv["gstin"] or len(inv["gstin"]) < 15:
            return "b2cl" if inv["inv_value"] > 250000 else "b2cs"
        return "b2b"

    def _to_gstr1_inv(self, inv: dict) -> dict:
        return {"inum": inv["inv_num"], "idt": inv["date"], "val": round(inv["inv_value"], 2),
                "pos": inv["pos"][:2] if inv["pos"] else "", "rchrg": "N",
                "inv": [{"num": 1, "rt": 18, "txval": round(inv["taxable"], 2),
                         "iamt": round(inv["igst"], 2), "camt": round(inv["cgst"], 2),
                         "samt": round(inv["sgst"], 2), "csamt": round(inv["cess"], 2)}]}

    def _to_note(self, inv: dict, ntype: str) -> dict:
        return {"ntty": ntype, "nt_num": inv["inv_num"], "nt_dt": inv["date"],
                "val": abs(round(inv["inv_value"], 2)),
                "nt": [{"num": 1, "rt": 18, "txval": round(abs(inv["taxable"]), 2),
                         "iamt": round(abs(inv["igst"]), 2), "camt": round(abs(inv["cgst"]), 2),
                         "samt": round(abs(inv["sgst"]), 2)}]}

    def _inv_match(self, a: dict, b: dict) -> float:
        score = 0
        if a["inv_num"] and b["inv_num"]:
            ac = re.sub(r'[^A-Z0-9]', '', a["inv_num"].upper())
            bc = re.sub(r'[^A-Z0-9]', '', b["inv_num"].upper())
            score += 40 if ac == bc else (25 if ac in bc or bc in ac else 0)
        if a["gstin"] and b["gstin"] and a["gstin"][:10] == b["gstin"][:10]:
            score += 30
        if a["taxable"] > 0 and b["taxable"] > 0:
            diff = abs(a["taxable"] - b["taxable"]) / max(a["taxable"], 1)
            score += 25 if diff < 0.01 else (15 if diff < 0.05 else (5 if diff < 0.10 else 0))
        return score

    def _get_diffs(self, a: dict, b: dict) -> list:
        diffs = []
        if abs(a["taxable"] - b["taxable"]) > 1:
            diffs.append(f"Taxable: ₹{a['taxable']:,.2f} vs ₹{b['taxable']:,.2f}")
        if abs(a["igst"] - b["igst"]) > 1:
            diffs.append(f"IGST: ₹{a['igst']:,.2f} vs ₹{b['igst']:,.2f}")
        if abs(a["cgst"] - b["cgst"]) > 1:
            diffs.append(f"CGST: ₹{a['cgst']:,.2f} vs ₹{b['cgst']:,.2f}")
        if abs(a["sgst"] - b["sgst"]) > 1:
            diffs.append(f"SGST: ₹{a['sgst']:,.2f} vs ₹{b['sgst']:,.2f}")
        if a["gstin"] and b["gstin"] and a["gstin"][:10] != b["gstin"][:10]:
            diffs.append(f"GSTIN mismatch")
        return diffs

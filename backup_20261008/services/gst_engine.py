import joblib
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from difflib import SequenceMatcher
import logging
import re

from app.services.file_parser import SmartFileParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent.parent / "models"


@dataclass
class GSTMatchResult:
    invoice_number: str
    gstin: str
    vendor_name: str
    book_taxable: float
    book_igst: float
    book_cgst: float
    book_sgst: float
    book_total: float
    portal_taxable: float
    portal_igst: float
    portal_cgst: float
    portal_sgst: float
    portal_total: float
    status: str
    confidence: float
    category: str
    reason: str


class GSTReconciliationEngine:
    def __init__(self):
        self.classifier = joblib.load(MODEL_DIR / "gst_classifier_day11.pkl")
        self.vectorizer = joblib.load(MODEL_DIR / "gst_vectorizer_day11.pkl")
        self.parser = SmartFileParser()
        logger.info("✅ GST engine loaded (classifier + reconciler)")

    def classify_invoice(self, text: str) -> dict:
        vector = self.vectorizer.transform([text])
        prediction = self.classifier.predict(vector)[0]
        prob = self.classifier.predict_proba(vector)[0]
        confidence = round(max(prob) * 100, 2)
        return {"category": prediction, "confidence": confidence}

    def reconcile(self, books_path: str, gstr2b_path: str) -> dict:
        logger.info("🔄 Starting GST reconciliation...")

        books_df = self.parser.parse(books_path)
        portal_df = self.parser.parse(gstr2b_path)

        if books_df.empty or portal_df.empty:
            return {
                "total_book_invoices": 0,
                "total_2b_invoices": 0,
                "matched": 0,
                "mismatched": 0,
                "missing_in_2b": 0,
                "missing_in_books": 0,
                "itc_blocked": 0,
                "results": [],
                "error": "Could not parse files",
            }

        logger.info(f"📊 Books: {len(books_df)}, GSTR-2B: {len(portal_df)}")
        logger.info(f"📋 Books columns: {list(books_df.columns)}")
        logger.info(f"📋 2B columns: {list(portal_df.columns)}")

        books_entries = self._build_entries(books_df, "books")
        portal_entries = self._build_entries(portal_df, "portal")

        logger.info(f"🔧 Book entries: {len(books_entries)}")
        logger.info(f"🔧 Portal entries: {len(portal_entries)}")

        matched_portal_indices = set()
        all_results = []

        for book in books_entries:
            best_match = None
            best_score = 0
            best_idx = -1

            for pidx, portal in enumerate(portal_entries):
                if pidx in matched_portal_indices:
                    continue

                score = 0

                inv_match = self._match_invoice_number(
                    book["invoice_number"], portal["invoice_number"]
                )
                if inv_match:
                    score += 40

                gstin_match = self._match_gstin(
                    book["gstin"], portal["gstin"]
                )
                if gstin_match:
                    score += 30

                amt_match = self._match_amount(
                    book["taxable"], portal["taxable"]
                )
                if amt_match:
                    score += 20

                name_sim = self._text_similarity(
                    book["vendor_name"], portal["vendor_name"]
                )
                score += int(name_sim * 10)

                if score > best_score:
                    best_score = score
                    best_match = portal
                    best_idx = pidx

            cat_result = self.classify_invoice(book["description"])

            if best_match and best_score >= 50:
                matched_portal_indices.add(best_idx)

                tax_diff = abs(book["taxable"] - best_match["taxable"])
                total_diff = abs(book["total"] - best_match["total"])

                if tax_diff <= 1 and total_diff <= 1:
                    status = "Matched"
                elif tax_diff > 1:
                    status = "Invoice Mismatch"
                else:
                    status = "Amount Mismatch"

                if not gstin_match and best_score >= 50:
                    status = "GSTIN Mismatch"

                all_results.append(GSTMatchResult(
                    invoice_number=book["invoice_number"],
                    gstin=book["gstin"],
                    vendor_name=book["vendor_name"],
                    book_taxable=book["taxable"],
                    book_igst=book["igst"],
                    book_cgst=book["cgst"],
                    book_sgst=book["sgst"],
                    book_total=book["total"],
                    portal_taxable=best_match["taxable"],
                    portal_igst=best_match["igst"],
                    portal_cgst=best_match["cgst"],
                    portal_sgst=best_match["sgst"],
                    portal_total=best_match["total"],
                    status=status,
                    confidence=round(best_score, 2),
                    category=cat_result["category"],
                    reason=self._explain_diff(book, best_match),
                ))
            else:
                all_results.append(GSTMatchResult(
                    invoice_number=book["invoice_number"],
                    gstin=book["gstin"],
                    vendor_name=book["vendor_name"],
                    book_taxable=book["taxable"],
                    book_igst=book["igst"],
                    book_cgst=book["cgst"],
                    book_sgst=book["sgst"],
                    book_total=book["total"],
                    portal_taxable=0,
                    portal_igst=0,
                    portal_cgst=0,
                    portal_sgst=0,
                    portal_total=0,
                    status="Missing in GSTR-2B",
                    confidence=0,
                    category=cat_result["category"],
                    reason="No matching entry found in GSTR-2B",
                ))

        for pidx, portal in enumerate(portal_entries):
            if pidx not in matched_portal_indices:
                all_results.append(GSTMatchResult(
                    invoice_number=portal["invoice_number"],
                    gstin=portal["gstin"],
                    vendor_name=portal["vendor_name"],
                    book_taxable=0,
                    book_igst=0,
                    book_cgst=0,
                    book_sgst=0,
                    book_total=0,
                    portal_taxable=portal["taxable"],
                    portal_igst=portal["igst"],
                    portal_cgst=portal["cgst"],
                    portal_sgst=portal["sgst"],
                    portal_total=portal["total"],
                    status="Missing in Books",
                    confidence=0,
                    category="Unknown",
                    reason="Entry found in GSTR-2B but not in books",
                ))

        matched = [r for r in all_results if r.status == "Matched"]
        mismatched = [r for r in all_results if r.status in ["Invoice Mismatch", "Amount Mismatch", "GSTIN Mismatch"]]
        missing_2b = [r for r in all_results if r.status == "Missing in GSTR-2B"]
        missing_books = [r for r in all_results if r.status == "Missing in Books"]
        itc_blocked = [r for r in all_results if r.status in ["Missing in GSTR-2B", "GSTIN Mismatch"]]

        logger.info(
            f"✅ GST Done!\n"
            f"   Matched: {len(matched)}\n"
            f"   Mismatched: {len(mismatched)}\n"
            f"   Missing in 2B: {len(missing_2b)}\n"
            f"   Missing in Books: {len(missing_books)}\n"
            f"   ITC Blocked: {len(itc_blocked)}"
        )

        return {
            "total_book_invoices": len(books_entries),
            "total_2b_invoices": len(portal_entries),
            "matched": len(matched),
            "mismatched": len(mismatched),
            "missing_in_2b": len(missing_2b),
            "missing_in_books": len(missing_books),
            "itc_blocked": len(itc_blocked),
            "match_rate": round(
                len(matched) / max(len(matched) + len(mismatched) + len(missing_2b), 1) * 100, 2
            ),
            "results": [self._to_dict(r) for r in all_results],
        }

    def _build_entries(self, df: pd.DataFrame, source: str) -> list:
        entries = []
        cols = list(df.columns)
        cols_lower = {str(c).strip().lower(): c for c in cols}

        inv_col = self._find_col(cols_lower, [
            "invoice number", "invoice no", "inv no", "bill number",
            "bill no", "vch no", "voucher number"
        ])
        gstin_col = self._find_col(cols_lower, [
            "gstin", "gst number", "gst no", "tin",
            "supplier gstin", "vendor gstin"
        ])
        name_col = self._find_col(cols_lower, [
            "name", "vendor name", "supplier name", "party name",
            "trade name", "recipient name"
        ])
        taxable_col = self._find_col(cols_lower, [
            "taxable value", "taxable amount", "assessable value",
            "base amount", "net amount", "invoice value"
        ])
        igst_col = self._find_col(cols_lower, [
            "igst", "integrated tax", "igst amount"
        ])
        cgst_col = self._find_col(cols_lower, [
            "cgst", "central tax", "cgst amount"
        ])
        sgst_col = self._find_col(cols_lower, [
            "sgst", "state tax", "sgst amount", "utgst"
        ])
        total_col = self._find_col(cols_lower, [
            "total", "total amount", "total value",
            "invoice value", "gross amount"
        ])

        for _, row in df.iterrows():
            inv = str(row.get(inv_col, "")).strip() if inv_col else ""
            gstin = str(row.get(gstin_col, "")).strip() if gstin_col else ""
            name = str(row.get(name_col, "")).strip() if name_col else ""

            if not inv and not gstin:
                continue

            taxable = self._safe_float(row.get(taxable_col)) if taxable_col else 0
            igst = self._safe_float(row.get(igst_col)) if igst_col else 0
            cgst = self._safe_float(row.get(cgst_col)) if cgst_col else 0
            sgst = self._safe_float(row.get(sgst_col)) if sgst_col else 0
            total = self._safe_float(row.get(total_col)) if total_col else (taxable + igst + cgst + sgst)

            desc_parts = [inv, gstin, name, str(taxable), str(total)]

            entries.append({
                "invoice_number": inv.upper(),
                "gstin": gstin.upper().replace(" ", ""),
                "vendor_name": name,
                "taxable": taxable,
                "igst": igst,
                "cgst": cgst,
                "sgst": sgst,
                "total": total,
                "description": " ".join(desc_parts),
            })

        return entries

    def _find_col(self, cols_lower, keywords):
        for kw in keywords:
            for cl, co in cols_lower.items():
                if cl == kw:
                    return co
        for kw in keywords:
            for cl, co in cols_lower.items():
                if kw in cl or cl in kw:
                    return co
        return None

    def _match_invoice_number(self, a, b):
        if not a or not b:
            return False
        a_clean = re.sub(r'[^A-Z0-9]', '', a.upper())
        b_clean = re.sub(r'[^A-Z0-9]', '', b.upper())
        return a_clean == b_clean or a_clean in b_clean or b_clean in a_clean

    def _match_gstin(self, a, b):
        if not a or not b:
            return False
        a_clean = re.sub(r'[^A-Z0-9]', '', a.upper())
        b_clean = re.sub(r'[^A-Z0-9]', '', b.upper())
        if len(a_clean) >= 10 and len(b_clean) >= 10:
            return a_clean[:10] == b_clean[:10]
        return a_clean == b_clean

    def _match_amount(self, a, b, tolerance=0.05):
        if a == 0 and b == 0:
            return True
        if a == 0 or b == 0:
            return False
        return abs(a - b) / max(abs(a), abs(b)) <= tolerance

    def _text_similarity(self, a, b):
        if not a or not b:
            return 0.0
        a_n = re.sub(r'[^A-Z0-9\s]', '', a.upper()).strip()
        b_n = re.sub(r'[^A-Z0-9\s]', '', b.upper()).strip()
        if a_n == b_n:
            return 1.0
        return SequenceMatcher(None, a_n, b_n).ratio()

    def _explain_diff(self, book, portal):
        reasons = []
        if abs(book["taxable"] - portal["taxable"]) > 1:
            reasons.append(f"Taxable: ₹{book['taxable']:,.2f} vs ₹{portal['taxable']:,.2f}")
        if abs(book["igst"] - portal["igst"]) > 1:
            reasons.append(f"IGST: ₹{book['igst']:,.2f} vs ₹{portal['igst']:,.2f}")
        if abs(book["cgst"] - portal["cgst"]) > 1:
            reasons.append(f"CGST: ₹{book['cgst']:,.2f} vs ₹{portal['cgst']:,.2f}")
        if abs(book["sgst"] - portal["sgst"]) > 1:
            reasons.append(f"SGST: ₹{book['sgst']:,.2f} vs ₹{portal['sgst']:,.2f}")
        return "; ".join(reasons) if reasons else "Match"

    def _to_dict(self, r: GSTMatchResult) -> dict:
        return {
            "invoice_number": r.invoice_number,
            "gstin": r.gstin,
            "vendor_name": r.vendor_name,
            "book_taxable": r.book_taxable,
            "book_igst": r.book_igst,
            "book_cgst": r.book_cgst,
            "book_sgst": r.book_sgst,
            "book_total": r.book_total,
            "portal_taxable": r.portal_taxable,
            "portal_igst": r.portal_igst,
            "portal_cgst": r.portal_cgst,
            "portal_sgst": r.portal_sgst,
            "portal_total": r.portal_total,
            "status": r.status,
            "confidence": r.confidence,
            "category": r.category,
            "reason": r.reason,
        }

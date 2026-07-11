# backend/app/services/ml_engine.py
import joblib
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from difflib import SequenceMatcher
import logging
import re
import csv
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent.parent / "models"


@dataclass
class Transaction:
    book_description: str
    bank_description: str
    book_amount: float
    bank_amount: float
    book_reference: str
    bank_reference: str


@dataclass
class MatchResult:
    book_description: str
    bank_description: str
    book_amount: float
    bank_amount: float
    status: str
    confidence: float
    reason: str


# =========================================================
# HELPERS
# =========================================================

def safe_float(value) -> float:
    if value is None:
        return 0.0
    s = str(value).strip()
    if s in ["", "nan", "None", "NA", "N/A", "-", "--"]:
        return 0.0
    try:
        cleaned = s.replace(",", "")
        cleaned = re.sub(r"[^\d.\-]", "", cleaned)
        return float(cleaned) if cleaned else 0.0
    except (ValueError, TypeError):
        return 0.0


def safe_str(value) -> str:
    if value is None or str(value).strip().lower() in [
        "nan", "none", ""
    ]:
        return ""
    return str(value).strip()


HEADER_KEYWORDS = [
    "date", "description", "narration", "particulars",
    "remarks", "details", "amount", "debit", "credit",
    "reference", "ref", "cheque", "chq", "utr",
    "transaction", "txn", "withdrawal", "deposit",
    "balance", "vch", "type", "branch",
]


def is_header_line(line: str) -> bool:
    line_stripped = line.strip()
    line_lower = line_stripped.lower()
    first_field = line_stripped.split(",")[0].strip().lower()
    if ":" in first_field:
        return False
    fields = line_stripped.split(",")
    non_empty = sum(1 for f in fields if f.strip())
    if non_empty <= 3:
        return False
    keyword_count = sum(
        1 for kw in HEADER_KEYWORDS if kw in line_lower
    )
    return keyword_count >= 3 and len(fields) >= 3


def normalize_description(desc: str) -> str:
    """Normalize text for better matching."""
    if not desc:
        return ""
    d = desc.strip().upper()

    prefixes = [
        "TO TRANSFER-INB", "TO TRANSFER-CMPNEFT",
        "TO TRANSFER-CMPIFTP", "TO TRANSFER-CMPCHRG",
        "TO TRANSFER-COMM", "TO TRANSFER-",
        "BY TRANSFER-", "DEBIT- IOI PAYMENT CHARGES",
        "CHEQUE WDL-", "TO DEBIT THROUGH CHEQUE-",
        "CHQ TRANSFER-", "BY CASH",
    ]
    for pfx in prefixes:
        if d.startswith(pfx):
            d = d[len(pfx):].strip()
            if d.startswith("--"):
                d = d[2:].strip()
            break

    noise = [
        "--", "INB", "NEFT", "RTGS", "UTR", "NO:",
        "TRANSFER", "FROM", "TO", "OWN ACCT",
        "ACCT TFR", "CHEQUE", "SBI",
    ]
    for n in noise:
        d = d.replace(n, " ")

    d = re.sub(r"\b\d{5,}\b", "", d)
    d = re.sub(r"[^A-Z0-9\s]", " ", d)
    d = re.sub(r"\s+", " ", d).strip()

    return d


def text_similarity(a: str, b: str) -> float:
    """Enhanced text similarity using multiple methods."""
    if not a or not b:
        return 0.0

    a_norm = normalize_description(a)
    b_norm = normalize_description(b)

    if not a_norm or not b_norm:
        return 0.0

    if a_norm == b_norm:
        return 1.0

    seq_ratio = SequenceMatcher(None, a_norm, b_norm).ratio()

    words_a = set(a_norm.split())
    words_b = set(b_norm.split())
    if words_a and words_b:
        intersection = words_a & words_b
        union = words_a | words_b
        jaccard = len(intersection) / len(union) if union else 0
    else:
        jaccard = 0

    containment = 0.0
    if a_norm in b_norm or b_norm in a_norm:
        containment = 0.8

    return max(seq_ratio, jaccard, containment)


# =========================================================
# ENGINE
# =========================================================

class ReconciliationEngine:
    def __init__(self):
        self.model = joblib.load(
            MODEL_DIR / "reconciliation_v2_model.pkl"
        )
        self.vectorizer = joblib.load(
            MODEL_DIR / "reconciliation_v2_vectorizer.pkl"
        )
        logger.info("✅ Reconciliation engine loaded")

    def _build_features(self, txn: Transaction) -> str:
        return (
            f"{txn.book_description} "
            f"{txn.bank_description} "
            f"{txn.book_amount} "
            f"{txn.bank_amount} "
            f"{txn.book_reference} "
            f"{txn.bank_reference}"
        )

    def match_one(self, txn: Transaction) -> MatchResult:
        features = self._build_features(txn)
        vector = self.vectorizer.transform([features])
        prediction = self.model.predict(vector)[0]
        prob = self.model.predict_proba(vector)[0]
        confidence = round(max(prob) * 100, 2)
        return MatchResult(
            book_description=txn.book_description,
            bank_description=txn.bank_description,
            book_amount=txn.book_amount,
            bank_amount=txn.bank_amount,
            status=prediction,
            confidence=confidence,
            reason=self._explain(txn),
        )

    def match_batch(
        self, transactions: List[Transaction]
    ) -> List[MatchResult]:
        if not transactions:
            return []
        features = [
            self._build_features(txn) for txn in transactions
        ]
        vectors = self.vectorizer.transform(features)
        predictions = self.model.predict(vectors)
        probs = self.model.predict_proba(vectors)
        results = []
        for txn, pred, prob in zip(
            transactions, predictions, probs
        ):
            confidence = round(max(prob) * 100, 2)
            results.append(
                MatchResult(
                    book_description=txn.book_description,
                    bank_description=txn.bank_description,
                    book_amount=txn.book_amount,
                    bank_amount=txn.bank_amount,
                    status=pred,
                    confidence=confidence,
                    reason=self._explain(txn),
                )
            )
        return results

    # =========================================================
    # CSV LOADER
    # =========================================================

    def _load_csv_robust(self, filepath: str) -> pd.DataFrame:
        logger.info(f"📂 Loading: {filepath}")

        with open(
            filepath, "r", encoding="utf-8", errors="ignore"
        ) as f:
            raw_lines = f.readlines()

        logger.info(f"📋 Total raw lines: {len(raw_lines)}")

        header_idx = -1
        for i, line in enumerate(raw_lines[:50]):
            if is_header_line(line):
                header_idx = i
                break

        if header_idx < 0:
            logger.warning("⚠️ No header found, using first line")
            header_idx = 0

        header_line = raw_lines[header_idx].strip()
        reader = csv.reader(io.StringIO(header_line))
        headers = next(reader)
        headers = [h.strip() for h in headers]
        num_cols = len(headers)

        logger.info(f"📋 Header at line {header_idx}: {headers}")

        data_rows = []
        skipped = 0
        for line in raw_lines[header_idx + 1:]:
            line = line.strip()
            if not line:
                continue
            try:
                row_reader = csv.reader(io.StringIO(line))
                row = next(row_reader)
            except Exception:
                skipped += 1
                continue
            if all(r.strip() in ["", "nan"] for r in row):
                continue
            row_lower = [r.strip().lower() for r in row]
            header_match = sum(
                1 for r in row_lower if r in HEADER_KEYWORDS
            )
            if header_match >= 2:
                skipped += 1
                continue
            while len(row) < num_cols:
                row.append("")
            row = row[:num_cols]
            data_rows.append(row)

        logger.info(
            f"📋 Parsed {len(data_rows)} rows, skipped {skipped}"
        )

        df = pd.DataFrame(data_rows, columns=headers)
        df = df.dropna(how="all").reset_index(drop=True)

        logger.info(f"📋 Final columns: {list(df.columns)}")
        logger.info(f"📋 Clean rows: {len(df)}")

        return df

    # =========================================================
    # COLUMN DETECTION
    # =========================================================

    def _detect_columns(
        self, df: pd.DataFrame, label: str
    ) -> dict:
        cols_lower = {
            str(c).strip().lower(): c for c in df.columns
        }

        logger.info(f"📋 {label} columns: {list(df.columns)}")

        desc_col = None
        for kw in [
            "particulars", "narration", "description",
            "remarks", "details", "name",
        ]:
            for cl, co in cols_lower.items():
                if cl == kw:
                    desc_col = co
                    break
            if desc_col:
                break

        amt_col = None
        for kw in [
            "debit amount", "debit", "amount",
            "withdrawal", "amt",
        ]:
            for cl, co in cols_lower.items():
                if cl == kw:
                    amt_col = co
                    break
            if amt_col:
                break

        ref_col = None
        for kw in [
            "ref no./cheque no.", "vch no.", "vch no",
            "ref", "cheque", "utr", "instrument",
        ]:
            for cl, co in cols_lower.items():
                if cl == kw:
                    ref_col = co
                    break
            if ref_col:
                break

        col_list = list(df.columns)
        if not desc_col:
            desc_col = col_list[1] if len(col_list) > 1 else col_list[0]
        if not amt_col:
            amt_col = col_list[4] if len(col_list) > 4 else col_list[-1]
        if not ref_col:
            ref_col = col_list[3] if len(col_list) > 3 else col_list[0]

        result = {
            "description": desc_col,
            "amount": amt_col,
            "reference": ref_col,
        }

        credit_col = None
        for kw in ["credit amount", "credit"]:
            for cl, co in cols_lower.items():
                if cl == kw:
                    credit_col = co
                    break
            if credit_col:
                break
        result["credit"] = credit_col

        # If description column is mostly empty, try alternatives
        if len(df) > 10:
            non_empty_count = df[desc_col].apply(
                lambda x: len(safe_str(x)) > 2
            ).sum()
            fill_rate = non_empty_count / len(df)
            if fill_rate < 0.3:
                logger.warning(
                    f"⚠️ {label} desc column '{desc_col}' is "
                    f"{fill_rate:.0%} full — trying alternatives"
                )
                for alt_kw in [
                    "particulars", "narration", "remarks",
                    "details", "description",
                ]:
                    for cl, co in cols_lower.items():
                        if cl == alt_kw and co != desc_col:
                            alt_count = df[co].apply(
                                lambda x: len(safe_str(x)) > 2
                            ).sum()
                            alt_rate = alt_count / len(df)
                            if alt_rate > fill_rate:
                                logger.info(
                                    f"📋 Switching {label} desc "
                                    f"'{desc_col}' → '{co}' "
                                    f"({alt_rate:.0%} full)"
                                )
                                result["description"] = co
                                desc_col = co
                                fill_rate = alt_rate

        if len(df) > 0:
            s = df.iloc[0]
            final_desc = result["description"]
            logger.info(
                f"📋 {label} mapped: {result}\n"
                f"   Sample — desc: [{safe_str(s.get(final_desc, ''))[:50]}], "
                f"amt: [{safe_str(s.get(amt_col, ''))}], "
                f"credit: [{safe_str(s.get(credit_col, '')) if credit_col else 'N/A'}], "
                f"ref: [{safe_str(s.get(ref_col, ''))[:20]}]"
            )

        return result

    # =========================================================
    # SMART AMOUNT EXTRACTION
    # =========================================================

    def _get_amount(
        self, row: dict, debit_col: str, credit_col: Optional[str] = None
    ) -> float:
        """Get amount from either debit or credit column."""
        debit = safe_float(row.get(debit_col))
        if debit > 0:
            return debit
        if credit_col:
            credit = safe_float(row.get(credit_col))
            if credit > 0:
                return credit
        return 0.0

    # =========================================================
    # AMOUNT MATCHING HELPERS
    # =========================================================

    def _amount_close(
        self, a: float, b: float, tolerance: float = 0.15
    ) -> bool:
        if a == 0 and b == 0:
            return True
        if a == 0 or b == 0:
            return False
        return abs(a - b) / max(abs(a), abs(b)) <= tolerance

    def _is_internal_transfer(self, desc: str) -> bool:
        d = desc.strip().upper()
        internal_keywords = [
            "SBI OD A/C", "SBI BANK-", "SBI 1144",
            "COL SUNIL DALAL", "CASH", "HDFC BANK",
            "PROFIT & LOSS", "OPENING BALANCE",
            "DEPRECIATION", "FDR INTEREST",
            "FDR", "SUSPENSE",
        ]
        for kw in internal_keywords:
            if kw in d:
                return True
        return False

    # =========================================================
    # MAIN RECONCILIATION
    # =========================================================

    def reconcile_csv(
        self, book_csv_path: str, bank_csv_path: str
    ) -> dict:
        logger.info("🔄 Starting reconciliation...")

        book_df = self._load_csv_robust(book_csv_path)
        bank_df = self._load_csv_robust(bank_csv_path)

        if book_df.empty or bank_df.empty:
            return {
                "total_transactions": 0,
                "matched_count": 0,
                "unmatched_count": 0,
                "match_rate": 0,
                "matched": [],
                "unmatched": [],
                "error": "Could not parse files",
            }

        logger.info(
            f"📊 Book: {len(book_df)}, Bank: {len(bank_df)}"
        )

        book_cols = self._detect_columns(book_df, "Book")
        bank_cols = self._detect_columns(bank_df, "Bank")

        b_desc_col = book_cols["description"]
        b_amt_col = book_cols["amount"]
        b_ref_col = book_cols["reference"]
        b_credit_col = book_cols.get("credit")

        k_desc_col = bank_cols["description"]
        k_amt_col = bank_cols["amount"]
        k_ref_col = bank_cols["reference"]
        k_credit_col = bank_cols.get("credit")

        if k_credit_col:
            logger.info(
                f"🔧 Bank credit column detected: '{k_credit_col}'"
            )

        # Build bank entries with BOTH debit & credit
        logger.info("🔧 Building bank entries...")
        bank_entries = []
        bank_credit_count = 0
        bank_debit_count = 0

        for idx, row in bank_df.iterrows():
            row_dict = row.to_dict()
            debit = safe_float(row_dict.get(k_amt_col))
            credit = safe_float(row_dict.get(k_credit_col)) if k_credit_col else 0
            amt = debit if debit > 0 else credit

            if amt <= 0:
                continue

            bank_entries.append({
                "idx": idx,
                "row": row,
                "amount": amt,
                "description": safe_str(row_dict.get(k_desc_col)),
                "reference": safe_str(row_dict.get(k_ref_col)),
            })

            if debit > 0:
                bank_debit_count += 1
            else:
                bank_credit_count += 1

        logger.info(
            f"🔧 Bank entries: {len(bank_entries)} total "
            f"({bank_debit_count} debits, {bank_credit_count} credits)"
        )

        matched_bank_indices = set()
        all_results = []
        total = len(book_df)
        skipped_internal = 0

        logger.info(
            f"⏳ Matching {total} book entries against "
            f"{len(bank_entries)} bank entries..."
        )

        for i, (_, brow) in enumerate(book_df.iterrows()):
            if i % 200 == 0:
                logger.info(f"⏳ {i}/{total}...")

            brow_dict = brow.to_dict()
            bdesc = safe_str(brow_dict.get(b_desc_col))
            bamt = self._get_amount(brow_dict, b_amt_col, b_credit_col)
            bref = safe_str(brow_dict.get(b_ref_col))

            # Skip truly empty rows
            if not bdesc and bamt == 0:
                continue

            # Skip internal transfers
            if self._is_internal_transfer(bdesc):
                skipped_internal += 1
                continue

            # Skip zero-amount entries
            if bamt == 0:
                all_results.append({
                    "book_description": bdesc,
                    "bank_description": "",
                    "book_amount": 0,
                    "bank_amount": 0,
                    "status": "Skipped",
                    "confidence": 0,
                    "reason": "Zero amount entry",
                })
                continue

            # Find candidates by amount tolerance
            candidates = []
            for be in bank_entries:
                if be["idx"] in matched_bank_indices:
                    continue
                if self._amount_close(bamt, be["amount"]):
                    candidates.append(be)

            best_result: Optional[MatchResult] = None
            best_score: float = 0.0
            best_bank_ref: str = ""

            if candidates:
                # Build Transaction objects for ML batch predict
                txns = []
                for be in candidates:
                    txns.append(
                        Transaction(
                            book_description=bdesc,
                            bank_description=be["description"],
                            book_amount=bamt,
                            bank_amount=be["amount"],
                            book_reference=bref,
                            bank_reference=be["reference"],
                        )
                    )

                ml_results = self.match_batch(txns)

                for be, ml_res in zip(candidates, ml_results):
                    text_sim = text_similarity(
                        bdesc, be["description"]
                    )
                    amount_diff_pct = abs(
                        bamt - be["amount"]
                    ) / max(bamt, 1) * 100

                    amount_bonus = (
                        30 if amount_diff_pct < 0.01 else 0
                    )

                    ref_bonus = 0
                    if bref and be["reference"]:
                        if (bref.upper() in be["reference"].upper() or
                                be["reference"].upper() in bref.upper()):
                            ref_bonus = 20

                    combined_score = (
                        ml_res.confidence * 0.3
                        + text_sim * 40
                        + amount_bonus
                        + ref_bonus
                        + (30 if amount_diff_pct < 5 else 0)
                    )

                    if combined_score > best_score:
                        best_score = combined_score
                        best_result = ml_res
                        best_bank_ref = be["reference"]

            if best_result and best_score > 35:
                # Find the matching bank entry index
                matched_idx = -1
                for be in candidates:
                    if be["reference"] == best_bank_ref:
                        matched_idx = be["idx"]
                        break
                if matched_idx >= 0:
                    matched_bank_indices.add(matched_idx)

                explain_txn = Transaction(
                    book_description=bdesc,
                    bank_description=best_result.bank_description,
                    book_amount=bamt,
                    bank_amount=best_result.bank_amount,
                    book_reference=bref,
                    bank_reference=best_bank_ref,
                )

                all_results.append({
                    "book_description": bdesc,
                    "bank_description": best_result.bank_description,
                    "book_amount": bamt,
                    "bank_amount": best_result.bank_amount,
                    "status": "Matched",
                    "confidence": round(best_score, 2),
                    "reason": self._explain(explain_txn),
                })
            else:
                all_results.append({
                    "book_description": bdesc,
                    "bank_description": "",
                    "book_amount": bamt,
                    "bank_amount": 0,
                    "status": "Unmatched",
                    "confidence": 0,
                    "reason": "No matching bank entry found"
                              + (f" ({len(candidates)} candidates "
                                 f"scored below threshold)"
                                 if candidates else ""),
                })

        # Unmatched bank entries
        for be in bank_entries:
            if be["idx"] not in matched_bank_indices:
                all_results.append({
                    "book_description": "",
                    "bank_description": be["description"],
                    "book_amount": 0,
                    "bank_amount": be["amount"],
                    "status": "Unmatched Bank",
                    "confidence": 0,
                    "reason": "No matching book entry",
                })

        matched = [
            r for r in all_results
            if r["status"] == "Matched"
        ]
        unmatched = [
            r for r in all_results
            if r["status"] not in ["Matched", "Skipped"]
        ]
        skipped = [
            r for r in all_results
            if r["status"] == "Skipped"
        ]

        logger.info(
            f"✅ Done!\n"
            f"   Matched: {len(matched)}\n"
            f"   Unmatched: {len(unmatched)}\n"
            f"   Skipped (internal/zero): {len(skipped)}\n"
            f"   Internal transfers filtered: {skipped_internal}\n"
            f"   Bank entries (debit): {bank_debit_count}\n"
            f"   Bank entries (credit): {bank_credit_count}\n"
            f"   Total: {len(all_results)}"
        )

        return {
            "total_transactions": len(all_results),
            "matched_count": len(matched),
            "unmatched_count": len(unmatched),
            "skipped_count": len(skipped),
            "internal_filtered": skipped_internal,
            "match_rate": round(
                len(matched)
                / max(len(matched) + len(unmatched), 1)
                * 100,
                2,
            ),
            "matched": matched,
            "unmatched": unmatched,
        }

    def _explain(self, txn: Transaction) -> str:
        reasons = []
        if txn.book_amount != txn.bank_amount:
            diff = abs(txn.book_amount - txn.bank_amount)
            reasons.append(
                f"Amount: ₹{txn.book_amount:,.2f} vs "
                f"₹{txn.bank_amount:,.2f} "
                f"(diff ₹{diff:,.2f})"
            )
        return "; ".join(reasons) if reasons else "Match"

    def _to_dict(self, r: MatchResult) -> dict:
        return {
            "book_description": r.book_description,
            "bank_description": r.bank_description,
            "book_amount": r.book_amount,
            "bank_amount": r.bank_amount,
            "status": r.status,
            "confidence": r.confidence,
            "reason": r.reason,
        }

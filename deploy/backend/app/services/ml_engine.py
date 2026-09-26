# backend/app/services/ml_engine.py
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
    if value is None or str(value).strip().lower() in ["nan", "none", ""]:
        return ""
    return str(value).strip()


def normalize_description(desc: str) -> str:
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
        self.model = joblib.load(MODEL_DIR / "reconciliation_v2_model.pkl")
        self.vectorizer = joblib.load(MODEL_DIR / "reconciliation_v2_vectorizer.pkl")
        self.parser = SmartFileParser()
        logger.info("✅ Reconciliation engine loaded (SmartFileParser)")

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

    def match_batch(self, transactions: List[Transaction]) -> List[MatchResult]:
        if not transactions:
            return []
        features = [self._build_features(txn) for txn in transactions]
        vectors = self.vectorizer.transform(features)
        predictions = self.model.predict(vectors)
        probs = self.model.predict_proba(vectors)
        results = []
        for txn, pred, prob in zip(transactions, predictions, probs):
            confidence = round(max(prob) * 100, 2)
            results.append(MatchResult(
                book_description=txn.book_description,
                bank_description=txn.bank_description,
                book_amount=txn.book_amount,
                bank_amount=txn.bank_amount,
                status=pred,
                confidence=confidence,
                reason=self._explain(txn),
            ))
        return results

    # =========================================================
    # AMOUNT HELPERS
    # =========================================================

    def _amount_close(self, a: float, b: float, tolerance: float = 0.15) -> bool:
        if a == 0 and b == 0:
            return True
        if a == 0 or b == 0:
            return False
        return abs(a - b) / max(abs(a), abs(b)) <= tolerance

    def _is_internal_transfer(self, desc: str) -> bool:
        d = desc.strip().upper()
        for kw in [
            "SBI OD A/C", "SBI BANK-", "SBI 1144",
            "COL SUNIL DALAL", "CASH", "HDFC BANK",
            "PROFIT & LOSS", "OPENING BALANCE",
            "DEPRECIATION", "FDR INTEREST",
            "FDR", "SUSPENSE",
        ]:
            if kw in d:
                return True
        return False

    # =========================================================
    # MAIN RECONCILIATION (uses SmartFileParser)
    # =========================================================

    def reconcile_csv(self, book_csv_path: str, bank_csv_path: str) -> dict:
        logger.info("🔄 Starting reconciliation (SmartFileParser)...")

        # SmartFileParser handles encoding, delimiters, headers,
        # column detection, and returns normalized columns:
        # description, amount, reference, date
        book_df = self.parser.parse(book_csv_path)
        bank_df = self.parser.parse(bank_csv_path)

        if book_df.empty or bank_df.empty:
            return {
                "total_transactions": 0,
                "matched_count": 0,
                "unmatched_count": 0,
                "match_rate": 0,
                "matched": [],
                "unmatched": [],
                "error": "Could not parse files. Check format and try again.",
            }

        logger.info(f"📊 Book: {len(book_df)} rows, Bank: {len(bank_df)} rows")
        logger.info(f"📋 Book columns: {list(book_df.columns)}")
        logger.info(f"📋 Bank columns: {list(bank_df.columns)}")

        # Build bank entries from normalized columns
        logger.info("🔧 Building bank entries...")
        bank_entries = []

        for idx, row in bank_df.iterrows():
            amt = float(row.get('amount', 0))
            if amt <= 0:
                continue
            bank_entries.append({
                "idx": idx,
                "amount": amt,
                "description": safe_str(row.get('description', '')),
                "reference": safe_str(row.get('reference', '')),
            })

        logger.info(f"🔧 Bank entries: {len(bank_entries)}")

        if not bank_entries:
            logger.warning("⚠️ No bank entries with amount > 0 found")
            return {
                "total_transactions": len(book_df),
                "matched_count": 0,
                "unmatched_count": len(book_df),
                "match_rate": 0,
                "matched": [],
                "unmatched": [
                    {
                        "book_description": safe_str(row.get('description', '')),
                        "bank_description": "",
                        "book_amount": float(row.get('amount', 0)),
                        "bank_amount": 0,
                        "status": "Unmatched",
                        "confidence": 0,
                        "reason": "No bank entries found with valid amounts",
                    }
                    for _, row in book_df.iterrows()
                    if safe_str(row.get('description', '')) or float(row.get('amount', 0)) > 0
                ],
            }

        matched_bank_indices = set()
        all_results = []
        skipped_internal = 0
        total = len(book_df)

        logger.info(f"⏳ Matching {total} book entries against {len(bank_entries)} bank entries...")

        for i, (_, brow) in enumerate(book_df.iterrows()):
            if i % 200 == 0:
                logger.info(f"⏳ {i}/{total}...")

            # SmartFileParser gives us normalized columns
            bdesc = safe_str(brow.get('description', ''))
            bamt = float(brow.get('amount', 0))
            bref = safe_str(brow.get('reference', ''))

            # Skip empty rows
            if not bdesc and bamt == 0:
                continue

            # Skip internal transfers
            if self._is_internal_transfer(bdesc):
                skipped_internal += 1
                continue

            # Skip zero-amount
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

            best_result = None
            best_score = 0.0
            best_bank_ref = ""

            if candidates:
                # Build Transaction objects for ML batch predict
                txns = [
                    Transaction(
                        book_description=bdesc,
                        bank_description=be["description"],
                        book_amount=bamt,
                        bank_amount=be["amount"],
                        book_reference=bref,
                        bank_reference=be["reference"],
                    )
                    for be in candidates
                ]

                ml_results = self.match_batch(txns)

                for be, ml_res in zip(candidates, ml_results):
                    text_sim = text_similarity(bdesc, be["description"])
                    amount_diff_pct = abs(bamt - be["amount"]) / max(bamt, 1) * 100

                    amount_bonus = 30 if amount_diff_pct < 0.01 else 0

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
                # Find matching bank entry index
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
                              + (f" ({len(candidates)} candidates scored below threshold)"
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

        matched = [r for r in all_results if r["status"] == "Matched"]
        unmatched = [r for r in all_results if r["status"] not in ["Matched", "Skipped"]]
        skipped = [r for r in all_results if r["status"] == "Skipped"]

        logger.info(
            f"✅ Done!\n"
            f"   Matched: {len(matched)}\n"
            f"   Unmatched: {len(unmatched)}\n"
            f"   Skipped: {len(skipped)}\n"
            f"   Internal filtered: {skipped_internal}\n"
            f"   Total: {len(all_results)}"
        )

        return {
            "total_transactions": len(all_results),
            "matched_count": len(matched),
            "unmatched_count": len(unmatched),
            "skipped_count": len(skipped),
            "internal_filtered": skipped_internal,
            "match_rate": round(
                len(matched) / max(len(matched) + len(unmatched), 1) * 100, 2
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

# backend/app/services/upi_engine.py
import joblib
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from difflib import SequenceMatcher
import logging
import re

from app.services.file_parser import SmartFileParser

logger = logging.getLogger(__name__)
MODEL_DIR = Path(__file__).parent.parent / "models"

# UPI-specific noise words for normalization
UPI_NOISE = [
    "UPI/DR/", "UPI/CR/", "IMPS/", "NEFT/", "RTGS/",
    "P2P", "P2M", "UPI P2P", "UPI P2M",
    "VIA", "REF:", "PAYMENT TO", "RECEIVED FROM",
    "BILL PAYMENT", "SUBSCRIPTION", "EMI PAYMENT",
    "RECHARGE", "INSURANCE PREMIUM",
    "GPay", "PhonePe", "Paytm", "BHIM", "AmazonPay", "Cred", "Mobikwik",
]

UPI_MERCHANTS = [
    "AMAZON", "FLIPKART", "SWIGGY", "ZOMATO", "BIGBASKET",
    "RELIANCE", "DMART", "CROMA", "NETFLIX", "SPOTIFY",
    "HOTSTAR", "AIRTEL", "JIO", "VODAFONE", "BSNL",
    "HDFC", "ICICI", "SBI", "AXIS", "KOTAK",
]


def upi_safe_float(value) -> float:
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


def upi_safe_str(value) -> str:
    if value is None or str(value).strip().lower() in ["nan", "none", ""]:
        return ""
    return str(value).strip()


def extract_upi_utr(text: str) -> str:
    """Extract UPI UTR number from narration."""
    if not text:
        return ""
    match = re.search(r'\b(\d{12})\b', text)
    return match.group(1) if match else ""


def extract_upi_id(text: str) -> str:
    """Extract UPI ID from narration."""
    if not text:
        return ""
    match = re.search(r'[\w.]+@[\w]+', text)
    return match.group(1) if match else ""


def normalize_upi_narration(desc: str) -> str:
    """Normalize UPI narration for matching."""
    if not desc:
        return ""
    d = desc.strip().upper()
    for noise in UPI_NOISE:
        d = d.replace(noise.upper(), " ")
    d = re.sub(r'\b\d{10,}\b', '', d)  # Remove long numbers (UTR)
    d = re.sub(r'[\w.]+@[\w]+', '', d)  # Remove UPI IDs
    d = re.sub(r'[^A-Z0-9\s]', ' ', d)
    d = re.sub(r'\s+', ' ', d).strip()
    return d


def upi_text_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    a_norm = normalize_upi_narration(a)
    b_norm = normalize_upi_narration(b)
    if not a_norm or not b_norm:
        return 0.0
    if a_norm == b_norm:
        return 1.0
    seq_ratio = SequenceMatcher(None, a_norm, b_norm).ratio()
    words_a = set(a_norm.split())
    words_b = set(b_norm.split())
    jaccard = len(words_a & words_b) / len(words_a | words_b) if words_a and words_b else 0
    containment = 0.8 if a_norm in b_norm or b_norm in a_norm else 0
    return max(seq_ratio, jaccard, containment)


def detect_upi_app(text: str) -> str:
    """Detect which UPI app was used."""
    if not text:
        return "Unknown"
    d = text.upper()
    apps = {
        "GPAY": "GPay", "GOOGLE": "GPay",
        "PHONEPE": "PhonePe", "PHONE PE": "PhonePe",
        "PAYTM": "Paytm", "PPBL": "Paytm",
        "BHIM": "BHIM", "AMAZONPAY": "AmazonPay", "AMAZON PAY": "AmazonPay",
        "CRED": "Cred", "MOBIKWIK": "Mobikwik",
    }
    for key, val in apps.items():
        if key in d:
            return val
    return "Unknown"


def is_upi_failed(desc: str) -> bool:
    """Check if UPI transaction failed."""
    d = desc.upper()
    return any(kw in d for kw in ["FAILED", "FAILURE", "DECLINED", "ERROR"])


def is_upi_reversed(desc: str) -> bool:
    """Check if UPI transaction was reversed."""
    d = desc.upper()
    return any(kw in d for kw in ["REVERSAL", "REVERSED", "REVERSAL ENTRY", "REFUND"])


class UPIReconciliationEngine:
    """UPI-specific reconciliation engine."""

    def __init__(self):
        try:
            self.model = joblib.load(MODEL_DIR / "upi_reconciliation_v3_model.pkl")
            self.vectorizer = joblib.load(MODEL_DIR / "upi_reconciliation_v3_vectorizer.pkl")
        except FileNotFoundError:
            logger.warning("UPI v3 model not found, falling back to v2")
            self.model = joblib.load(MODEL_DIR / "reconciliation_v2_model.pkl")
            self.vectorizer = joblib.load(MODEL_DIR / "reconciliation_v2_vectorizer.pkl")
        self.parser = SmartFileParser()
        logger.info("✅ UPI Reconciliation engine loaded")

    def _build_features(self, book_desc, bank_desc, book_amt, bank_amt,
                        book_ref, bank_ref, upi_id="", upi_type="", upi_app="") -> str:
        return (
            f"{book_desc} {bank_desc} {book_amt} {bank_amt} "
            f"{book_ref} {bank_ref} {upi_id} {upi_type} {upi_app}"
        )

    def _predict(self, features_list: List[str]) -> List[tuple]:
        vectors = self.vectorizer.transform(features_list)
        predictions = self.model.predict(vectors)
        probs = self.model.predict_proba(vectors)
        results = []
        for pred, prob in zip(predictions, probs):
            confidence = round(max(prob) * 100, 2)
            results.append((pred, confidence))
        return results

    def reconcile_upi_files(self, book_path: str, bank_path: str) -> dict:
        """Main UPI reconciliation method."""
        logger.info("🔄 Starting UPI reconciliation...")

        book_df = self.parser.parse(book_path)
        bank_df = self.parser.parse(bank_path)

        if book_df.empty or bank_df.empty:
            return {
                "total_transactions": 0,
                "matched_count": 0,
                "unmatched_count": 0,
                "match_rate": 0,
                "matched": [],
                "unmatched": [],
                "error": "Could not parse files. Check format.",
                "type": "upi",
            }

        logger.info(f"📊 Book: {len(book_df)} rows, Bank: {len(bank_df)} rows")

        # Build bank entries
        bank_entries = []
        for idx, row in bank_df.iterrows():
            amt = upi_safe_float(row.get('amount', 0))
            desc = upi_safe_str(row.get('description', ''))
            ref = upi_safe_str(row.get('reference', ''))
            if amt == 0 and not desc:
                continue
            bank_entries.append({
                "idx": idx,
                "amount": amt,
                "description": desc,
                "reference": ref,
                "upi_utr": extract_upi_utr(desc),
                "upi_id": extract_upi_id(desc),
                "upi_app": detect_upi_app(desc),
            })

        logger.info(f"🔧 Bank entries: {len(bank_entries)}")

        matched_bank_indices = set()
        all_results = []

        for i, (_, brow) in enumerate(book_df.iterrows()):
            bdesc = upi_safe_str(brow.get('description', ''))
            bamt = upi_safe_float(brow.get('amount', 0))
            bref = upi_safe_str(brow.get('reference', ''))

            if not bdesc and bamt == 0:
                continue

            # Check UPI status first
            if is_upi_failed(bdesc):
                all_results.append({
                    "book_description": bdesc,
                    "bank_description": "",
                    "book_amount": bamt,
                    "bank_amount": 0,
                    "status": "UPI Failed",
                    "confidence": 100.0,
                    "reason": "UPI transaction failed",
                    "upi_utr": extract_upi_utr(bdesc),
                    "upi_app": detect_upi_app(bdesc),
                })
                continue

            if is_upi_reversed(bdesc):
                all_results.append({
                    "book_description": bdesc,
                    "bank_description": "",
                    "book_amount": bamt,
                    "bank_amount": -bamt,
                    "status": "UPI Reversed",
                    "confidence": 100.0,
                    "reason": "UPI transaction reversed/refunded",
                    "upi_utr": extract_upi_utr(bdesc),
                    "upi_app": detect_upi_app(bdesc),
                })
                continue

            # Find candidates
            b_utr = extract_upi_utr(bdesc)
            candidates = []
            for be in bank_entries:
                if be["idx"] in matched_bank_indices:
                    continue
                # Exact UTR match = strong candidate
                if b_utr and be["upi_utr"] and b_utr == be["upi_utr"]:
                    candidates.append((be, 1.0))
                    continue
                # Amount match
                if bamt != 0 and abs(bamt - be["amount"]) / max(abs(bamt), 1) <= 0.15:
                    candidates.append((be, 0.5))

            best_result = None
            best_score = 0.0
            best_bank_entry = None

            if candidates:
                features = []
                for be, _ in candidates:
                    upi_id = extract_upi_id(be["description"])
                    upi_app = detect_upi_app(be["description"])
                    features.append(self._build_features(
                        bdesc, be["description"], bamt, be["amount"],
                        bref, be["reference"], upi_id, "", upi_app
                    ))

                ml_results = self._predict(features)

                for (be, candidate_bonus), (ml_pred, ml_conf) in zip(candidates, ml_results):
                    text_sim = upi_text_similarity(bdesc, be["description"])
                    amt_diff = abs(bamt - be["amount"]) / max(abs(bamt), 1) * 100

                    score = ml_conf * 0.25 + text_sim * 35 + candidate_bonus * 20

                    if amt_diff < 0.01:
                        score += 30
                    elif amt_diff < 5:
                        score += 15

                    if b_utr and be["upi_utr"] and b_utr == be["upi_utr"]:
                        score += 25

                    if bref and be["reference"]:
                        if bref.upper() in be["reference"].upper() or be["reference"].upper() in bref.upper():
                            score += 15

                    if score > best_score:
                        best_score = score
                        best_result = (ml_pred, ml_conf)
                        best_bank_entry = be

            if best_result and best_score > 30 and best_bank_entry:
                matched_bank_indices.add(best_bank_entry["idx"])

                # Determine final status
                if best_score > 75:
                    status = "Matched"
                elif best_score > 50:
                    status = "Partial Match"
                else:
                    status = "Pending Settlement"

                all_results.append({
                    "book_description": bdesc,
                    "bank_description": best_bank_entry["description"],
                    "book_amount": bamt,
                    "bank_amount": best_bank_entry["amount"],
                    "status": status,
                    "confidence": round(best_score, 2),
                    "reason": self._explain_upi(bdesc, best_bank_entry["description"],
                                                 bamt, best_bank_entry["amount"],
                                                 b_utr, best_bank_entry["upi_utr"]),
                    "upi_utr": b_utr or best_bank_entry["upi_utr"],
                    "upi_app": detect_upi_app(best_bank_entry["description"]),
                })
            else:
                all_results.append({
                    "book_description": bdesc,
                    "bank_description": "",
                    "book_amount": bamt,
                    "bank_amount": 0,
                    "status": "Unmatched",
                    "confidence": 0,
                    "reason": f"No matching UPI transaction found ({len(candidates)} candidates)" if candidates else "No candidates",
                    "upi_utr": b_utr,
                    "upi_app": detect_upi_app(bdesc),
                })

        # Unmatched bank entries
        for be in bank_entries:
            if be["idx"] not in matched_bank_indices:
                all_results.append({
                    "book_description": "",
                    "bank_description": be["description"],
                    "book_amount": 0,
                    "bank_amount": be["amount"],
                    "status": "Unmatched",
                    "confidence": 0,
                    "reason": "No matching book entry",
                    "upi_utr": be["upi_utr"],
                    "upi_app": be["upi_app"],
                })

        matched = [r for r in all_results if r["status"] in ["Matched", "Partial Match"]]
        unmatched = [r for r in all_results if r["status"] not in ["Matched", "Partial Match"]]

        logger.info(f"✅ UPI Reconciliation done: {len(matched)} matched, {len(unmatched)} unmatched")

        return {
            "total_transactions": len(all_results),
            "matched_count": len(matched),
            "unmatched_count": len(unmatched),
            "match_rate": round(len(matched) / max(len(matched) + len(unmatched), 1) * 100, 2),
            "matched": matched,
            "unmatched": unmatched,
            "type": "upi",
        }

    def _explain_upi(self, book_desc, bank_desc, book_amt, bank_amt, book_utr, bank_utr) -> str:
        reasons = []
        if book_utr and bank_utr:
            if book_utr == bank_utr:
                reasons.append(f"UTR match: {book_utr}")
            else:
                reasons.append(f"UTR: {book_utr} vs {bank_utr}")
        if abs(book_amt - bank_amt) > 0.01:
            diff = abs(book_amt - bank_amt)
            reasons.append(f"Amount diff: ₹{diff:,.2f}")
        app = detect_upi_app(bank_desc or book_desc)
        if app != "Unknown":
            reasons.append(f"App: {app}")
        return "; ".join(reasons) if reasons else "Exact match"

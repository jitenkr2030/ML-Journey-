# backend/app/services/file_parser.py
import pandas as pd
import chardet
import csv
import io
import re
import logging
from typing import Optional, Tuple, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class SmartFileParser:
    """Parses ANY bank statement or ledger file — CSV or Excel.
    Auto-detects encoding, header position, column mapping,
    amount format, and date format.
    """

    # =========================================================
    # MASTER COLUMN VOCABULARY
    # =========================================================

    DESCRIPTION_KEYWORDS = [
        # Tier 1 — exact matches (highest priority)
        "narration", "particulars", "description",
        "remarks", "details", "memo", "narrative",
        # Tier 2 — common variations
        "transaction details", "transaction description",
        "transaction remarks", "transaction narration",
        "payment details", "transfer remarks",
        "cheque description", "particular",
        # Tier 3 — software-specific
        "name", "ledger name", "party name",
        "beneficiary", "sender", "receiver",
        "transaction", "txn description",
    ]

    DEBIT_KEYWORDS = [
        "debit amount", "debit", "withdrawal",
        "debit(dr)", "debit (dr)", "dr amount",
        "dr.", "debit amt", "withdrawal amount",
        "paid", "payment", "money out",
    ]

    CREDIT_KEYWORDS = [
        "credit amount", "credit", "deposit",
        "credit(cr)", "credit (cr)", "cr amount",
        "cr.", "credit amt", "deposit amount",
        "received", "receipt", "money in",
    ]

    AMOUNT_KEYWORDS = [
        "amount", "transaction amount", "txn amount",
        "value", "sum", "total", "amt",
        "net amount", "running balance amount",
    ]

    REFERENCE_KEYWORDS = [
        "ref no./cheque no.", "ref no.", "reference",
        "cheque no.", "cheque", "chq no",
        "utr no", "utr", "utr number",
        "neft/rtgs/imps ref", "transaction ref",
        "instrument no", "instrument number",
        "vch no.", "vch no", "voucher no",
        "ref number", "reference number",
        "transaction id", "txn id", "txn ref",
    ]

    DATE_KEYWORDS = [
        "date", "transaction date", "txn date",
        "value date", "posting date", "statement date",
        "trans date", "dt", "vale date",
    ]

    BALANCE_KEYWORDS = [
        "balance", "closing balance", "running balance",
        "available balance", "balance amount",
    ]

    # =========================================================
    # MAIN ENTRY POINT
    # =========================================================

    def parse(self, filepath: str) -> pd.DataFrame:
        """Parse any file and return a clean DataFrame."""
        logger.info(f"📂 Parsing: {filepath}")

        ext = Path(filepath).suffix.lower()

        if ext in ['.xlsx', '.xls']:
            df = self._parse_excel(filepath)
        else:
            df = self._parse_csv(filepath)

        if df is None or df.empty:
            logger.warning(f"⚠️ Empty result from {filepath}")
            return pd.DataFrame()

        # Detect and clean the header
        df = self._detect_and_fix_header(df)

        # Map columns
        mapping = self._map_columns(df)
        logger.info(f"📋 Column mapping: {mapping}")

        # Normalize the DataFrame
        df = self._normalize(df, mapping)

        logger.info(f"✅ Parsed {len(df)} rows from {filepath}")
        return df

    # =========================================================
    # EXCEL PARSER
    # =========================================================

    def _parse_excel(self, filepath: str) -> Optional[pd.DataFrame]:
        """Try parsing Excel with multiple strategies."""
        try:
            # Strategy 1: Read normally
            df = pd.read_excel(filepath, header=None)
            if self._looks_like_data(df):
                return df

            # Strategy 2: Try different header rows
            for header_row in range(0, 15):
                try:
                    df = pd.read_excel(filepath, header=header_row)
                    if self._looks_like_data(df):
                        return df
                except Exception:
                    continue

            # Strategy 3: Read all sheets, return the largest
            xls = pd.ExcelFile(filepath)
            best_df = pd.DataFrame()
            for sheet in xls.sheet_names:
                try:
                    df = pd.read_excel(filepath, sheet_name=sheet, header=None)
                    if len(df) > len(best_df):
                        best_df = df
                except Exception:
                    continue

            return best_df if not best_df.empty else None

        except Exception as e:
            logger.error(f"❌ Excel parse error: {e}")
            return None

    # =========================================================
    # CSV PARSER
    # =========================================================

    def _parse_csv(self, filepath: str) -> Optional[pd.DataFrame]:
        """Try parsing CSV with multiple encodings and delimiters."""
        # Read raw bytes for encoding detection
        with open(filepath, 'rb') as f:
            raw = f.read()

        # Detect encoding
        encoding = self._detect_encoding(raw)
        logger.info(f"📋 Detected encoding: {encoding}")

        text = raw.decode(encoding, errors='ignore')
        lines = text.splitlines()

        if not lines:
            return None

        # Detect delimiter
        delimiter = self._detect_delimiter(lines[:20])
        logger.info(f"📋 Detected delimiter: '{delimiter}'")

        # Parse with detected delimiter
        try:
            reader = csv.reader(io.StringIO(text), delimiter=delimiter)
            rows = []
            for row in reader:
                cleaned = [cell.strip() for cell in row]
                if any(cleaned):
                    rows.append(cleaned)

            if not rows:
                return None

            # Find header row
            header_idx = self._find_header_row(rows)

            if header_idx >= 0:
                headers = rows[header_idx]
                data_rows = rows[header_idx + 1:]
            else:
                # No header found — use first row
                headers = rows[0]
                data_rows = rows[1:]

            # Normalize column count
            num_cols = len(headers)
            normalized_rows = []
            for row in data_rows:
                while len(row) < num_cols:
                    row.append("")
                normalized_rows.append(row[:num_cols])

            df = pd.DataFrame(normalized_rows, columns=headers)
            return df

        except Exception as e:
            logger.error(f"❌ CSV parse error: {e}")
            # Fallback: pandas
            try:
                return pd.read_csv(
                    filepath, encoding=encoding,
                    header=None, on_bad_lines='skip'
                )
            except Exception:
                return None

    # =========================================================
    # DETECTION HELPERS
    # =========================================================

    def _detect_encoding(self, raw: bytes) -> str:
        """Detect file encoding."""
        # Try chardet
        try:
            import chardet
            result = chardet.detect(raw[:10000])
            if result['confidence'] > 0.7:
                return result['encoding']
        except ImportError:
            pass

        # Try common encodings
        for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                raw[:1000].decode(enc)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue

        return 'utf-8'

    def _detect_delimiter(self, lines: List[str]) -> str:
        """Detect CSV delimiter by testing common options."""
        test_text = '\n'.join(lines)
        delimiters = [',', '\t', ';', '|']

        best_delimiter = ','
        best_score = 0

        for d in delimiters:
            reader = csv.reader(io.StringIO(test_text), delimiter=d)
            rows = list(reader)
            if len(rows) < 2:
                continue

            # Score: consistent column count + reasonable column count
            col_counts = [len(r) for r in rows]
            if not col_counts:
                continue

            mode_cols = max(set(col_counts), key=col_counts.count)
            consistency = col_counts.count(mode_cols) / len(col_counts)
            reasonableness = min(mode_cols, 10) / 10

            score = consistency * reasonableness * mode_cols

            if score > best_score:
                best_score = score
                best_delimiter = d

        return best_delimiter

    def _find_header_row(self, rows: List[List[str]]) -> int:
        """Find the header row by scoring each row for keyword matches."""
        all_keywords = (
            self.DESCRIPTION_KEYWORDS + self.DEBIT_KEYWORDS +
            self.CREDIT_KEYWORDS + self.AMOUNT_KEYWORDS +
            self.REFERENCE_KEYWORDS + self.DATE_KEYWORDS +
            self.BALANCE_KEYWORDS
        )

        best_idx = -1
        best_score = 0

        for i, row in enumerate(rows[:20]):  # Check first 20 rows
            score = 0
            non_empty = sum(1 for cell in row if cell.strip())

            if non_empty < 3:
                continue

            for cell in row:
                cell_lower = cell.strip().lower()
                for kw in all_keywords:
                    if cell_lower == kw or cell_lower in kw or kw in cell_lower:
                        score += 1
                        break

            if score > best_score:
                best_score = score
                best_idx = i

        return best_idx if best_score >= 2 else -1

    def _looks_like_data(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame looks like transaction data."""
        if df.empty or len(df.columns) < 3:
            return False

        # Check if any column name matches our keywords
        for col in df.columns:
            col_lower = str(col).strip().lower()
            for kw in self.DESCRIPTION_KEYWORDS + self.DEBIT_KEYWORDS + self.CREDIT_KEYWORDS + self.AMOUNT_KEYWORDS:
                if kw in col_lower or col_lower in kw:
                    return True

        return False

    # =========================================================
    # HEADER DETECTION AND FIXING
    # =========================================================

    def _detect_and_fix_header(self, df: pd.DataFrame) -> pd.DataFrame:
        """If first row looks like data (not header), try to find real header."""
        # Check if current columns look like headers
        col_score = self._score_headers(list(df.columns))

        if col_score >= 2:
            # Current columns are good headers
            return df

        # Search for header in first 15 rows
        for i in range(min(15, len(df))):
            row_values = list(df.iloc[i].values)
            row_score = self._score_headers(row_values)

            if row_score >= 2:
                # Found header — slice the DataFrame
                new_headers = [str(v).strip() for v in row_values]
                data_df = df.iloc[i + 1:].reset_index(drop=True)
                data_df.columns = new_headers
                return data_df

        # No good header found — return as-is
        return df

    def _score_headers(self, values: list) -> int:
        """Score a list of values for how likely they are to be headers."""
        score = 0
        all_keywords = (
            self.DESCRIPTION_KEYWORDS + self.DEBIT_KEYWORDS +
            self.CREDIT_KEYWORDS + self.AMOUNT_KEYWORDS +
            self.REFERENCE_KEYWORDS + self.DATE_KEYWORDS +
            self.BALANCE_KEYWORDS
        )

        for val in values:
            val_lower = str(val).strip().lower()
            if not val_lower or val_lower in ['nan', 'none', '']:
                continue
            for kw in all_keywords:
                if val_lower == kw or kw in val_lower:
                    score += 1
                    break

        return score

    # =========================================================
    # COLUMN MAPPING
    # =========================================================

    def _map_columns(self, df: pd.DataFrame) -> dict:
        """Map DataFrame columns to standard names."""
        cols = list(df.columns)
        cols_lower = {str(c).strip().lower(): c for c in cols}

        mapping = {
            'description': None,
            'amount': None,
            'debit': None,
            'credit': None,
            'reference': None,
            'date': None,
            'balance': None,
        }

        # Map description
        mapping['description'] = self._find_best_column(
            cols_lower, self.DESCRIPTION_KEYWORDS
        )

        # Map debit
        mapping['debit'] = self._find_best_column(
            cols_lower, self.DEBIT_KEYWORDS
        )

        # Map credit
        mapping['credit'] = self._find_best_column(
            cols_lower, self.CREDIT_KEYWORDS
        )

        # Map amount (single amount column — if no debit/credit found)
        if not mapping['debit'] and not mapping['credit']:
            mapping['amount'] = self._find_best_column(
                cols_lower, self.AMOUNT_KEYWORDS
            )

        # Map reference
        mapping['reference'] = self._find_best_column(
            cols_lower, self.REFERENCE_KEYWORDS
        )

        # Map date
        mapping['date'] = self._find_best_column(
            cols_lower, self.DATE_KEYWORDS
        )

        # Map balance
        mapping['balance'] = self._find_best_column(
            cols_lower, self.BALANCE_KEYWORDS
        )

        # Fallback: if description not found, pick column with most text
        if not mapping['description']:
            mapping['description'] = self._find_text_column(df)

        # Fallback: if no amount found at all, pick column with most numbers
        if not mapping['debit'] and not mapping['credit'] and not mapping['amount']:
            mapping['amount'] = self._find_numeric_column(df)

        return mapping

    def _find_best_column(
        self, cols_lower: dict, keywords: list
    ) -> Optional[str]:
        """Find the best matching column for a list of keywords."""
        # Tier 1: Exact match
        for kw in keywords:
            for cl, co in cols_lower.items():
                if cl == kw:
                    return co

        # Tier 2: Contains match
        for kw in keywords:
            for cl, co in cols_lower.items():
                if kw in cl or cl in kw:
                    return co

        return None

    def _find_text_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find column with the most text content."""
        best_col = None
        best_score = 0

        for col in df.columns:
            text_count = df[col].apply(
                lambda x: len(str(x).strip()) > 5
            ).sum()
            if text_count > best_score:
                best_score = text_count
                best_col = col

        return best_col

    def _find_numeric_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find column with the most numeric values."""
        best_col = None
        best_score = 0

        for col in df.columns:
            numeric_count = df[col].apply(
                lambda x: self._is_numeric(str(x))
            ).sum()
            if numeric_count > best_score:
                best_score = numeric_count
                best_col = col

        return best_col

    def _is_numeric(self, s: str) -> bool:
        """Check if a string looks like a number."""
        s = s.strip().replace(',', '').replace('₹', '')
        try:
            float(s)
            return True
        except ValueError:
            return False

    # =========================================================
    # NORMALIZE
    # =========================================================

    def _normalize(self, df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
        """Create a normalized DataFrame with standard columns."""
        result = pd.DataFrame()

        # Description
        if mapping['description']:
            result['description'] = df[mapping['description']].apply(
                lambda x: str(x).strip() if pd.notna(x) else ''
            )
        else:
            result['description'] = ''

        # Amount — combine debit/credit or use single amount
        if mapping['debit'] and mapping['credit']:
            result['amount'] = df.apply(
                lambda row: self._get_amount_from_debit_credit(
                    row.get(mapping['debit']),
                    row.get(mapping['credit'])
                ), axis=1
            )
        elif mapping['amount']:
            result['amount'] = df[mapping['amount']].apply(
                lambda x: self._safe_float(x)
            )
        elif mapping['debit']:
            result['amount'] = df[mapping['debit']].apply(
                lambda x: self._safe_float(x)
            )
        else:
            result['amount'] = 0.0

        # Reference
        if mapping['reference']:
            result['reference'] = df[mapping['reference']].apply(
                lambda x: str(x).strip() if pd.notna(x) else ''
            )
        else:
            result['reference'] = ''

        # Date
        if mapping['date']:
            result['date'] = df[mapping['date']].apply(
                lambda x: str(x).strip() if pd.notna(x) else ''
            )
        else:
            result['date'] = ''

        # Balance
        if mapping['balance']:
            result['balance'] = df[mapping['balance']].apply(
                lambda x: self._safe_float(x)
            )

        # Drop rows where both description and amount are empty
        result = result[
            (result['description'] != '') | (result['amount'] != 0)
        ].reset_index(drop=True)

        return result

    def _get_amount_from_debit_credit(
        self, debit_val, credit_val
    ) -> float:
        """Extract amount from separate debit/credit columns."""
        debit = self._safe_float(debit_val)
        credit = self._safe_float(credit_val)

        if debit > 0:
            return debit
        elif credit > 0:
            return credit
        return 0.0

    def _safe_float(self, value) -> float:
        """Safely convert any value to float."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0.0

        s = str(value).strip()
        if s in ['', 'nan', 'None', 'NA', 'N/A', '-', '--', 'Dr', 'Cr']:
            return 0.0

        # Remove currency symbols, commas, spaces
        s = s.replace('₹', '').replace(',', '').replace(' ', '')
        s = s.replace('Rs.', '').replace('Rs', '').replace('INR', '')

        # Handle Dr/Cr suffixes (common in Indian accounting)
        is_credit = False
        if s.upper().endswith('CR'):
            is_credit = True
            s = s[:-2]
        elif s.upper().endswith('DR'):
            s = s[:-2]

        # Remove any non-numeric chars except . and -
        s = re.sub(r'[^\d.\-]', '', s)

        try:
            val = float(s) if s else 0.0
            return abs(val)  # Always return positive
        except ValueError:
            return 0.0

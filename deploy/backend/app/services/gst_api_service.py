import requests
import json
import base64
import logging
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load credentials
CREDS_PATH = Path(__file__).parent.parent.parent / "gst-api" / "credentials.env"
if CREDS_PATH.exists():
    load_dotenv(CREDS_PATH)


class GSTAPIService:
    """Service to interact with GSTN via ClearTax API"""

    def __init__(self, use_sandbox: bool = False):
        self.use_sandbox = use_sandbox
        self.access_token = os.getenv("CLEARTAX_ACCESS_TOKEN", "")
        self.client_secret = os.getenv("CLEARTAX_CLIENT_SECRET", "")
        self.workspace_id = os.getenv("CLEARTAX_WORKSPACE_ID", "")
        self.my_gstin = os.getenv("MY_GSTIN", "")

        if use_sandbox:
            self.base_url = "https://api.sandbox.cleartax.in"
        else:
            self.base_url = os.getenv("CLEARTAX_API_BASE", "https://api.cleartax.in")

        self.session_tokens = {}
        self.session_expiry = {}

        mode = "Sandbox" if use_sandbox else "Production"
        logger.info(f"✅ GST API Service initialized ({mode})")

    def _get_headers(self, gstin: str = "") -> dict:
        """Get common headers for ClearTax API"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        if gstin:
            headers["gstin"] = gstin
        if self.workspace_id:
            headers["workspace-id"] = self.workspace_id
        return headers

    def is_authenticated(self, gstin: str) -> bool:
        """Check if we have valid credentials"""
        return bool(self.access_token)

    def get_session_info(self, gstin: str) -> Dict[str, Any]:
        """Get authentication status"""
        if not self.access_token:
            return {
                "authenticated": False,
                "gstin": gstin,
                "message": "No API credentials configured"
            }
        return {
            "authenticated": True,
            "gstin": gstin,
            "provider": "ClearTax",
            "mode": "Production" if not self.use_sandbox else "Sandbox",
            "message": "Session active"
        }

    # =====================================================
    # GSTR-1 FILING
    # =====================================================

    def file_gstr1(self, gstin: str, period: str, gstr1_data: Dict) -> Dict[str, Any]:
        """File GSTR-1 via ClearTax API"""
        try:
            if not self.is_authenticated(gstin):
                return {"status": "ERROR", "message": "Not authenticated"}

            # Step 1: Save GSTR-1
            save_result = self._save_gstr1(gstin, period, gstr1_data)
            if save_result.get("status") == "ERROR":
                return save_result

            # Step 2: Submit GSTR-1
            submit_result = self._submit_gstr1(gstin, period)

            return submit_result

        except Exception as e:
            logger.error(f"❌ GSTR-1 filing failed: {e}")
            return {"status": "ERROR", "message": str(e)}

    def _save_gstr1(self, gstin: str, period: str, data: Dict) -> Dict:
        """Save GSTR-1 on GSTN via ClearTax"""
        try:
            url = f"{self.base_url}/gst/returns/gstr1/save"
            payload = {
                "gstin": gstin,
                "return_period": period,
                "gstr1_data": data
            }

            headers = self._get_headers(gstin)

            if self.use_sandbox:
                # Sandbox: simulate save
                return {
                    "status": "SUCCESS",
                    "message": "GSTR-1 saved (sandbox)",
                    "reference_id": f"save_{gstin}_{period}_{int(time.time())}"
                }

            response = requests.post(url, json=payload, headers=headers, timeout=60)
            result = response.json()

            if response.status_code in [200, 201]:
                logger.info(f"✅ GSTR-1 saved for {gstin}")
                return {"status": "SUCCESS", "data": result}
            else:
                logger.error(f"❌ GSTR-1 save failed: {result}")
                return {"status": "ERROR", "message": result.get("message", "Save failed")}

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ GSTR-1 save request failed: {e}")
            return {"status": "ERROR", "message": str(e)}

    def _submit_gstr1(self, gstin: str, period: str) -> Dict:
        """Submit/File GSTR-1 on GSTN via ClearTax"""
        try:
            url = f"{self.base_url}/gst/returns/gstr1/submit"
            payload = {
                "gstin": gstin,
                "return_period": period
            }

            headers = self._get_headers(gstin)

            if self.use_sandbox:
                return {
                    "status": "SUCCESS",
                    "message": "GSTR-1 filed successfully (sandbox)",
                    "arn": f"ARN{gstin}{period}{int(time.time())}",
                    "timestamp": datetime.now().isoformat(),
                    "acknowledgement": {
                        "arn": f"ARN{gstin}{period}{int(time.time())}",
                        "date": datetime.now().strftime("%d/%m/%Y"),
                        "time": datetime.now().strftime("%H:%M:%S")
                    }
                }

            response = requests.post(url, json=payload, headers=headers, timeout=120)
            result = response.json()

            if response.status_code in [200, 201]:
                logger.info(f"✅ GSTR-1 filed for {gstin}")
                return {
                    "status": "SUCCESS",
                    "message": "GSTR-1 filed successfully",
                    "arn": result.get("arn", ""),
                    "timestamp": datetime.now().isoformat(),
                    "acknowledgement": result.get("acknowledgement", {}),
                    "data": result
                }
            else:
                return {"status": "ERROR", "message": result.get("message", "Filing failed")}

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ GSTR-1 submit failed: {e}")
            return {"status": "ERROR", "message": str(e)}

    # =====================================================
    # GSTR-3B FILING
    # =====================================================

    def file_gstr3b(self, gstin: str, period: str, gstr3b_data: Dict) -> Dict[str, Any]:
        """File GSTR-3B via ClearTax API"""
        try:
            if not self.is_authenticated(gstin):
                return {"status": "ERROR", "message": "Not authenticated"}

            # Step 1: Save GSTR-3B
            save_result = self._save_gstr3b(gstin, period, gstr3b_data)
            if save_result.get("status") == "ERROR":
                return save_result

            # Step 2: Submit GSTR-3B
            submit_result = self._submit_gstr3b(gstin, period)

            return submit_result

        except Exception as e:
            logger.error(f"❌ GSTR-3B filing failed: {e}")
            return {"status": "ERROR", "message": str(e)}

    def _save_gstr3b(self, gstin: str, period: str, data: Dict) -> Dict:
        """Save GSTR-3B on GSTN via ClearTax"""
        try:
            url = f"{self.base_url}/gst/returns/gstr3b/save"
            payload = {
                "gstin": gstin,
                "return_period": period,
                "gstr3b_data": data
            }

            headers = self._get_headers(gstin)

            if self.use_sandbox:
                return {
                    "status": "SUCCESS",
                    "message": "GSTR-3B saved (sandbox)",
                    "reference_id": f"save_{gstin}_{period}_{int(time.time())}"
                }

            response = requests.post(url, json=payload, headers=headers, timeout=60)
            result = response.json()

            if response.status_code in [200, 201]:
                return {"status": "SUCCESS", "data": result}
            else:
                return {"status": "ERROR", "message": result.get("message", "Save failed")}

        except requests.exceptions.RequestException as e:
            return {"status": "ERROR", "message": str(e)}

    def _submit_gstr3b(self, gstin: str, period: str) -> Dict:
        """Submit/File GSTR-3B on GSTN via ClearTax"""
        try:
            url = f"{self.base_url}/gst/returns/gstr3b/submit"
            payload = {
                "gstin": gstin,
                "return_period": period
            }

            headers = self._get_headers(gstin)

            if self.use_sandbox:
                return {
                    "status": "SUCCESS",
                    "message": "GSTR-3B filed successfully (sandbox)",
                    "arn": f"ARN{gstin}{period}{int(time.time())}",
                    "timestamp": datetime.now().isoformat(),
                    "tax_payable": gstr3b_data.get("tax_payable", {}),
                    "acknowledgement": {
                        "arn": f"ARN{gstin}{period}{int(time.time())}",
                        "date": datetime.now().strftime("%d/%m/%Y"),
                        "time": datetime.now().strftime("%H:%M:%S")
                    }
                }

            response = requests.post(url, json=payload, headers=headers, timeout=120)
            result = response.json()

            if response.status_code in [200, 201]:
                logger.info(f"✅ GSTR-3B filed for {gstin}")
                return {
                    "status": "SUCCESS",
                    "message": "GSTR-3B filed successfully",
                    "arn": result.get("arn", ""),
                    "timestamp": datetime.now().isoformat(),
                    "tax_payable": gstr3b_data.get("tax_payable", {}),
                    "acknowledgement": result.get("acknowledgement", {}),
                    "data": result
                }
            else:
                return {"status": "ERROR", "message": result.get("message", "Filing failed")}

        except requests.exceptions.RequestException as e:
            return {"status": "ERROR", "message": str(e)}

    # =====================================================
    # DOWNLOAD GSTR-2A/2B
    # =====================================================

    def download_gstr2a(self, gstin: str, period: str) -> Dict[str, Any]:
        """Download GSTR-2A from GSTN via ClearTax"""
        try:
            url = f"{self.base_url}/gst/returns/gstr2a"
            params = {"gstin": gstin, "return_period": period}
            headers = self._get_headers(gstin)

            if self.use_sandbox:
                return {
                    "status": "SUCCESS",
                    "gstin": gstin,
                    "fp": period,
                    "b2b": [],
                    "message": "GSTR-2A data (sandbox)"
                }

            response = requests.get(url, params=params, headers=headers, timeout=60)

            if response.status_code == 200:
                return {"status": "SUCCESS", "data": response.json()}
            else:
                return {"status": "ERROR", "message": "Download failed"}

        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def download_gstr2b(self, gstin: str, period: str) -> Dict[str, Any]:
        """Download GSTR-2B from GSTN via ClearTax"""
        try:
            url = f"{self.base_url}/gst/returns/gstr2b"
            params = {"gstin": gstin, "return_period": period}
            headers = self._get_headers(gstin)

            if self.use_sandbox:
                return {
                    "status": "SUCCESS",
                    "gstin": gstin,
                    "fp": period,
                    "data": [],
                    "message": "GSTR-2B data (sandbox)"
                }

            response = requests.get(url, params=params, headers=headers, timeout=60)

            if response.status_code == 200:
                return {"status": "SUCCESS", "data": response.json()}
            else:
                return {"status": "ERROR", "message": "Download failed"}

        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    # =====================================================
    # FILING STATUS
    # =====================================================

    def check_filing_status(self, gstin: str, arn: str) -> Dict[str, Any]:
        """Check filing status using ARN via ClearTax"""
        try:
            url = f"{self.base_url}/gst/returns/status"
            params = {"gstin": gstin, "arn": arn}
            headers = self._get_headers(gstin)

            if self.use_sandbox:
                return {
                    "status": "SUCCESS",
                    "arn": arn,
                    "gstin": gstin,
                    "filing_status": "FILED",
                    "filing_date": datetime.now().strftime("%d/%m/%Y"),
                    "message": "Return filed successfully"
                }

            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code == 200:
                return {"status": "SUCCESS", "data": response.json()}
            else:
                return {"status": "ERROR", "message": "Status check failed"}

        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    # =====================================================
    # SESSION MANAGEMENT (Not needed for ClearTax)
    # =====================================================

    def initiate_session(self, gstin: str, username: str) -> Dict[str, Any]:
        """ClearTax uses access token, not OTP sessions"""
        if self.access_token:
            return {
                "status": "SUCCESS",
                "status_cd": "1",
                "message": "Already authenticated via ClearTax API",
                "txn_id": f"cleartax_{int(time.time())}"
            }
        return {
            "status": "ERROR",
            "message": "No ClearTax access token configured"
        }

    def verify_otp(self, gstin: str, txn_id: str, otp: str) -> Dict[str, Any]:
        """ClearTax uses access token, OTP verification not needed"""
        if self.access_token:
            return {
                "status": "SUCCESS",
                "status_cd": "1",
                "auth_token": self.access_token[:20] + "...",
                "message": "Authenticated via ClearTax (no OTP needed)"
            }
        return {"status": "ERROR", "message": "No credentials"}

    def revoke_session(self, gstin: str) -> Dict[str, Any]:
        """Not applicable for ClearTax"""
        return {
            "status": "SUCCESS",
            "message": "ClearTax tokens are managed by ClearTax. Revoke from dashboard."
        }

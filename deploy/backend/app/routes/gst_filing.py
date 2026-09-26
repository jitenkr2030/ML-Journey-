from fastapi import APIRouter, Form, HTTPException
from typing import Optional
import logging

from app.services.gst_api_service import GSTAPIService
from app.services.gst_return_engine import GSTReturnEngine

logger = logging.getLogger(__name__)

router = APIRouter()
gst_api = GSTAPIService(use_sandbox=False)  # Start with sandbox
gst_engine = GSTReturnEngine()


@router.post("/api/gst/auth/init")
async def initiate_auth(
    gstin: str = Form(...),
    username: str = Form(...)
):
    """Initialize GST API session (sends OTP)"""
    try:
        result = gst_api.initiate_session(gstin, username)
        return result
    except Exception as e:
        logger.error(f"Auth initiation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/gst/auth/verify")
async def verify_auth(
    gstin: str = Form(...),
    txn_id: str = Form(...),
    otp: str = Form(...)
):
    """Verify OTP and get session token"""
    try:
        result = gst_api.verify_otp(gstin, txn_id, otp)
        return result
    except Exception as e:
        logger.error(f"Auth verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/gst/auth/status/{gstin}")
async def check_auth_status(gstin: str):
    """Check authentication status for GSTIN"""
    try:
        return gst_api.get_session_info(gstin)
    except Exception as e:
        logger.error(f"Auth status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/gst/file/gstr1")
async def file_gstr1(
    gstin: str = Form(...),
    period: str = Form(...),
    gstr1_data: str = Form(...)  # JSON string of GSTR-1 data
):
    """File GSTR-1 return via GSTN API"""
    try:
        import json

        # Check authentication
        if not gst_api.is_authenticated(gstin):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Please verify OTP first."
            )

        # Parse GSTR-1 data
        try:
            gstr1_json = json.loads(gstr1_data)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid GSTR-1 JSON data: {str(e)}"
            )

        # Prepare data for GSTN
        gstn_data = {
            "gstin": gstin,
            "fp": period,
            "gt": gstr1_json.get("gt", 0),
            "cur_gt": gstr1_json.get("cur_gt", 0),
            "b2b": gstr1_json.get("b2b", []),
            "b2cl": gstr1_json.get("b2cl", []),
            "b2cs": gstr1_json.get("b2cs", []),
            "exp": gstr1_json.get("exp", []),
            "cdnr": gstr1_json.get("cdnr", []),
            "cdnur": gstr1_json.get("cdnur", [])
        }

        # File GSTR-1
        result = gst_api.file_gstr1(gstin, period, gstn_data)

        # Log to audit trail
        gst_engine._log_audit(
            gstin,
            "GSTR1_FILED",
            json.dumps({"period": period, "result": result.get("status")})
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GSTR-1 filing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/gst/file/gstr3b")
async def file_gstr3b(
    gstin: str = Form(...),
    period: str = Form(...),
    gstr3b_data: str = Form(...)  # JSON string of GSTR-3B data
):
    """File GSTR-3B return via GSTN API"""
    try:
        import json

        # Check authentication
        if not gst_api.is_authenticated(gstin):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Please verify OTP first."
            )

        # Parse GSTR-3B data
        try:
            gstr3b_json = json.loads(gstr3b_data)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid GSTR-3B JSON data: {str(e)}"
            )

        # Prepare data for GSTN
        gstn_data = {
            "table_3_1": gstr3b_json.get("table_3_1", {}),
            "table_4": gstr3b_json.get("table_4", {}),
            "table_5": gstr3b_json.get("table_5", {}),
            "table_6_1": gstr3b_json.get("table_6_1", {}),
            "tax_payable": gstr3b_json.get("tax_payable", {})
        }

        # File GSTR-3B
        result = gst_api.file_gstr3b(gstin, period, gstn_data)

        # Log to audit trail
        gst_engine._log_audit(
            gstin,
            "GSTR3B_FILED",
            json.dumps({
                "period": period,
                "tax_payable": gstr3b_json.get("tax_payable", {}),
                "result": result.get("status")
            })
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GSTR-3B filing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/gst/filing/status/{gstin}/{arn}")
async def check_filing_status(gstin: str, arn: str):
    """Check filing status using ARN"""
    try:
        # Check authentication
        if not gst_api.is_authenticated(gstin):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated."
            )

        return gst_api.check_filing_status(gstin, arn)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/gst/download/2a/{gstin}/{period}")
async def download_gstr2a(gstin: str, period: str):
    """Download GSTR-2A data from GSTN"""
    try:
        # Check authentication
        if not gst_api.is_authenticated(gstin):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated."
            )

        return gst_api.download_gstr2a(gstin, period)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GSTR-2A download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/gst/download/2b/{gstin}/{period}")
async def download_gstr2b(gstin: str, period: str):
    """Download GSTR-2B data from GSTN"""
    try:
        # Check authentication
        if not gst_api.is_authenticated(gstin):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated."
            )

        return gst_api.download_gstr2b(gstin, period)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GSTR-2B download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/gst/revoke/{gstin}")
async def revoke_session(gstin: str):
    """Revoke API session for GSTIN"""
    try:
        return gst_api.revoke_session(gstin)
    except Exception as e:
        logger.error(f"Session revocation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

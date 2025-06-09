# routes/file_bugs.py

from fastapi import APIRouter, HTTPException, Query
from db.models import file_analysis_collection

router = APIRouter()

@router.get("/file-bugs")
async def get_file_bugs(file: str = Query(..., description="Full file path to query")):
    doc = file_analysis_collection.find_one({ "file": file })

    if not doc:
        raise HTTPException(status_code=404, detail="File not found in analysis results.")

    return {
        "file": doc["file"],
        "bugs_original": doc.get("bugs_original", []),
        "bugs_sanity_checked": doc.get("bugs_sanity_checked", []),
        "optimizations_original": doc.get("optimizations_original", []),
        "optimizations_sanity_checked": doc.get("optimizations_sanity_checked", [])
    }

# routes/file_bugs.py

from fastapi import APIRouter, HTTPException, Query
from db.models import file_analysis_collection

router = APIRouter()

@router.get("/file-bugs")
async def get_file_bugs(upload_id: str = Query(...), file: str = Query(...)):
    file = file.strip()  # optional → clean up just in case

    doc = file_analysis_collection.find_one({ "upload_id": upload_id, "file": file })

    if not doc:
        print(f"[GET /file-bugs] upload_id={upload_id} file={file} → NOT FOUND")
        raise HTTPException(status_code=404, detail="File not found in analysis results.")

    print(f"[GET /file-bugs] upload_id={upload_id} file={file} → FOUND ✅")

    return {
        "file": doc["file"],
        "bugs_original": doc.get("bugs_original", []),
        "bugs_sanity_checked": doc.get("bugs_sanity_checked", []),
        "optimizations_original": doc.get("optimizations_original", []),
        "optimizations_sanity_checked": doc.get("optimizations_sanity_checked", []),
    }

# routes/file_bugs.py
import os
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



@router.get("/file_bugs/{upload_id}")
async def get_all_file_bugs(upload_id: str):
    docs = file_analysis_collection.find({ "upload_id": upload_id })

    results = []

    for doc in docs:
        original_name = doc.get("original_filename", "(unknown)")
        file_path = doc.get("file", "")
        zip_name = doc.get("zip_name", "")  # ✅ Add this line
        bugs = doc.get("bugs_sanity_checked", [])

        results.append({
            "file_path": file_path,
            "file_name": original_name,
            "zip_name": zip_name,              # ✅ Include in response
            "bugs": bugs
        })  

        print(f"[DEBUG] {file_path} from {original_name} → {len(bugs)} bug(s)")

    if not results:
        print(f"[GET /file_bugs/{upload_id}] → No files found ❌")
    else:
        print(f"[GET /file_bugs/{upload_id}] → {len(results)} file(s) ✅")

    return results



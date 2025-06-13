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
        # Extract original filename — show this in UI
        original_name = doc.get("original_filename", "(unknown)")
        
        # If you want to also show path, you can split `file`, but here it's optional
        full_file_path = doc.get("file", "")
        file_path, _ = os.path.split(full_file_path)

        print(f"[DEBUG] Processing file: {original_name} (stored path: {full_file_path})")

        for bug in doc.get("bugs_sanity_checked", []):
            results.append({
                "file_path": file_path,  # optional — can leave "" if not needed
                "file_name": original_name,  # show real uploaded filename
                "line": bug.get("line"),
                "description": bug.get("description"),
                "priority": bug.get("priority", "Unknown"),
            })

    if not results:
        print(f"[GET /file_bugs/{upload_id}] → No bugs found")
    else:
        print(f"[GET /file_bugs/{upload_id}] → {len(results)} bugs found ✅")

    return { "bugs": results }




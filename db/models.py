# db/models.py

from .mongo_client import client

db = client["bug_triage_db"]
file_analysis_collection = db["file_analysis"]

def save_to_mongo(file_path, parsed_data, author="Uploaded by user"):
    doc = {
        "file": file_path,
        "bugs_original": parsed_data["bugs_original"],
        "bugs_sanity_checked": parsed_data["bugs_sanity_checked"],
        "optimizations_original": parsed_data["optimizations_original"],
        "optimizations_sanity_checked": parsed_data["optimizations_sanity_checked"],
        "analysis_output": parsed_data["analysis_output"],
        "sanity_checked_output": parsed_data["sanity_checked_output"],
        "author": author
    }
    file_analysis_collection.insert_one(doc)
    print(f"[MongoDB] Saved analysis for file: {file_path}")

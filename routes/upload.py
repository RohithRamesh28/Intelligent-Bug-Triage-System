from fastapi import APIRouter, UploadFile, File, HTTPException
from utils.file_extractor import extract_zip, is_code_file, is_valid_code_file
from utils.constants import JUNK_FOLDERS
import os
import uuid
import shutil
from services.project_summary import get_project_summary, parse_project_summary
from services.gpt_analysis import call_gpt_analyze_chunk, run_sanity_check_on_bugs
import asyncio
from dotenv import load_dotenv
from services.parser import parse_outputs
from db.models import save_to_mongo
from routes.progress_ws import connected_websockets

load_dotenv()

router = APIRouter()

TEMP_FOLDER = "temp_uploads"

# Helper function to send progress to all connected WebSocket clients
async def send_progress(message: str, progress: int = None):
    for ws in connected_websockets:
        try:
            payload = { "status": message }
            if progress is not None:
                payload["progress"] = progress
            await ws.send_json(payload)
        except:
            pass  # Ignore if client disconnected

@router.post("/")
async def upload_project(files: list[UploadFile] = File(...)):
    try:
        os.makedirs(TEMP_FOLDER, exist_ok=True)

        all_code_files = []
        zip_extract_paths = []

        file_previews = []  # NEW → for Project Summary

        # Process uploads
        for uploaded_file in files:
            file_id = str(uuid.uuid4())

            if uploaded_file.filename.endswith(".zip"):
                zip_temp_path = os.path.join(TEMP_FOLDER, f"{file_id}_{uploaded_file.filename}")
                with open(zip_temp_path, "wb") as f:
                    content = await uploaded_file.read()
                    f.write(content)

                extract_path = os.path.join(TEMP_FOLDER, file_id)
                extract_zip(zip_temp_path, extract_path)

                for root, dirs, files_in_zip in os.walk(extract_path):
                    dirs[:] = [d for d in dirs if d not in JUNK_FOLDERS]

                    for file_in_zip in files_in_zip:
                        file_full_path = os.path.join(root, file_in_zip)
                        if is_code_file(file_full_path) and is_valid_code_file(file_full_path):
                            all_code_files.append(file_full_path)

                            # Build preview
                            with open(file_full_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read(500)
                            file_previews.append({
                                "filename": file_full_path,
                                "preview": content
                            })

                zip_extract_paths.append(extract_path)
                os.remove(zip_temp_path)

            else:
                # Normal file → read in memory → no disk save
                content_bytes = await uploaded_file.read()
                content_text = content_bytes.decode("utf-8", errors="ignore")
                file_lines = content_text.splitlines()

                if is_code_file(uploaded_file.filename):
                    all_code_files.append((uploaded_file.filename, file_lines))

                    # Build preview
                    preview_text = content_text[:500]
                    file_previews.append({
                        "filename": uploaded_file.filename,
                        "preview": preview_text
                    })

        # Progress → Upload complete
        await send_progress("Upload complete ✅", progress=5)

        # ✅ Project Summary → now pass file_previews
        await send_progress("Running Project Summary...", progress=10)

        summary_text = await get_project_summary(file_previews)  # CHANGE HERE → passing previews!
        dependencies, connected_groups = parse_project_summary(summary_text)

        if not connected_groups:
            connected_groups = [[file] for file in all_code_files]

        await send_progress(f"Connected Groups ready — {len(connected_groups)} groups", progress=15)

        # Analyze Groups
        tasks = []

        for group in connected_groups:
            file_chunks = []

            for file_entry in group:
                if isinstance(file_entry, tuple):
                    file_name, file_lines = file_entry
                else:
                    file_name = file_entry
                    with open(file_name, "r", encoding="utf-8") as f:
                        file_lines = f.readlines()

                MAX_LINES_PER_CHUNK = 500
                num_chunks = (len(file_lines) + MAX_LINES_PER_CHUNK - 1) // MAX_LINES_PER_CHUNK

                for chunk_index in range(num_chunks):
                    start_line = chunk_index * MAX_LINES_PER_CHUNK
                    end_line = min(start_line + MAX_LINES_PER_CHUNK, len(file_lines))
                    chunk_lines = file_lines[start_line:end_line]

                    file_chunks.append((file_name, chunk_lines))

            task = call_gpt_analyze_chunk(file_chunks)
            tasks.append(task)

        # Run all analyze tasks
        gpt_results_raw = await asyncio.gather(*tasks)

        gpt_results = []

        total_groups = len(connected_groups)

        for i, group in enumerate(connected_groups):
            group_progress = 15 + int((i / total_groups) * 70)
            await send_progress(f"Analyzing Group {i+1}/{total_groups}...", progress=group_progress)

            analysis_output = gpt_results_raw[i]

            # Sanity check step
            bug_lines = []
            for line in analysis_output.splitlines():
                line = line.strip()
                if line.startswith("- BUG "):
                    bug_lines.append(line)

            bug_list_text = "\n".join(bug_lines)

            await send_progress(f"Running Sanity Check on Group {i+1}/{total_groups}...", progress=group_progress + 5)

            sanity_checked_output = await run_sanity_check_on_bugs(group[0], bug_list_text)

            gpt_results.append({
                "files": group,
                "analysis_output": analysis_output,
                "sanity_checked_output": sanity_checked_output
            })

            # Save to Mongo
            await send_progress(f"Saving Group {i+1} to MongoDB...", progress=group_progress + 10)

            for file_in_group in group:
                if isinstance(file_in_group, tuple):
                    file_name = file_in_group[0]
                else:
                    file_name = file_in_group

                parsed_data = parse_outputs(analysis_output, sanity_checked_output)
                save_to_mongo(file_name, parsed_data)

        # Cleanup
        for extract_path in zip_extract_paths:
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path)

        await send_progress("DONE 🚀", progress=100)

        return {
            "message": "Analysis complete!",
            "files_analyzed": len(gpt_results),
            "results": gpt_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
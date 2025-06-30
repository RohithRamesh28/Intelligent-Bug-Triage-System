import traceback
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from utils.file_extractor import extract_zip, is_code_file, is_valid_code_file
from utils.constants import JUNK_FOLDERS
import os
import json
import uuid
import shutil
from services.project_summary import get_project_summary, parse_project_summary
from services.gpt_analysis import call_gpt_analyze_chunk, run_sanity_check_on_bugs
import asyncio
from dotenv import load_dotenv
from services.parser import parse_outputs
from db.models import save_to_mongo
from routes.progress_ws import connected_websockets
from fastapi import Request
from utils.auth_utils import get_current_user_data
load_dotenv()
router = APIRouter()
TEMP_FOLDER = "temp_uploads"

from routes.progress_ws import connected_websockets

async def send_progress(upload_id: str, message: str, progress: int = None):
    if upload_id not in connected_websockets:
        print(f"[WebSocket] No active clients for upload_id={upload_id}")
        return
    
    disconnected_clients = []
    for ws in connected_websockets[upload_id]:
        try:
            payload = {"status": message}
            if progress is not None:
                payload["progress"] = progress
            await ws.send_json(payload)
        except:
            disconnected_clients.append(ws)
    

    for ws in disconnected_clients:
        connected_websockets[upload_id].remove(ws)
    

    if len(connected_websockets[upload_id]) == 0:
        del connected_websockets[upload_id]


@router.post("/")
async def upload_project(
    request: Request,
    upload_description: str = Form(""),  
    files: list[UploadFile] = File(...),
    user_data: dict = Depends(get_current_user_data)
):
    try:
       
        user_id = user_data["user_id"]
        project_id = user_data["project_id"]
        username = user_data["username"] 
        #Main logic
        os.makedirs(TEMP_FOLDER, exist_ok=True)
        upload_id = str(uuid.uuid4())
        all_code_files = []
        zip_extract_paths = []
        normal_file_paths = []
        file_previews = []

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
                            with open(file_full_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read(500)
                            relative_name = os.path.relpath(file_full_path, start=TEMP_FOLDER).replace("\\", "/")
                            file_previews.append({
                                "filename": file_full_path,
                                "display_name": relative_name,
                                "original_name": file_in_zip,
                                "preview": content
                            })

                zip_extract_paths.append(extract_path)
                os.remove(zip_temp_path)

            else:
                normal_file_path = os.path.join(TEMP_FOLDER, f"{file_id}_{uploaded_file.filename}")
                with open(normal_file_path, "wb") as f:
                    content_bytes = await uploaded_file.read()
                    f.write(content_bytes)

                normal_file_paths.append(normal_file_path)

                with open(normal_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content_text = f.read()
                    file_lines = content_text.splitlines()

                if is_code_file(normal_file_path):
                    all_code_files.append(normal_file_path)
                    relative_name = os.path.relpath(normal_file_path, start=TEMP_FOLDER).replace("\\", "/")
                    preview_text = content_text[:500]
                    file_previews.append({
                        "filename": normal_file_path,
                        "display_name": relative_name,
                        "original_name": uploaded_file.filename,
                        "preview": preview_text
                    })

        await send_progress(upload_id, "Upload complete ", progress=5)
        await send_progress(upload_id, "Running Project Summary...", progress=10)

        summary_text = await get_project_summary(file_previews)
        dependencies, connected_groups = parse_project_summary(summary_text)

        display_name_to_full_path = {
            file_obj["display_name"]: file_obj["filename"]
            for file_obj in file_previews
        }

        connected_groups_full_paths = []
        for group in connected_groups:
            group_full_paths = []
            for display_name in group:
                full_path = display_name_to_full_path.get(display_name)
                if full_path:
                    group_full_paths.append(full_path)
                else:
                    print(f"[WARNING] No matching full path for: {display_name}")
            connected_groups_full_paths.append(group_full_paths)
        await send_progress(upload_id, f"Connected Groups ready — {len(connected_groups_full_paths)} groups", progress=15)


        asyncio.create_task(run_analysis_task(
            upload_id,
            connected_groups_full_paths,
            zip_extract_paths + normal_file_paths,
            file_previews,
            user_id,
            username,
            project_id,
            upload_description
        ))

        return {
            "message": "Upload started",
            "upload_id": upload_id,
            "groups": len(connected_groups_full_paths),
            "files": [f for group in connected_groups for f in group]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_analysis_task(upload_id, connected_groups, extract_paths, file_previews, user_id, username, project_id, upload_description):
    try:
        gpt_results = []
        tasks = []

      
        full_path_to_original_name = {
            file_obj["filename"]: file_obj.get("original_name", "")
            for file_obj in file_previews
        }

        for i, group in enumerate(connected_groups):
            tasks.append(
                analyze_one_group(
                    upload_id,
                    group,
                    i,
                    len(connected_groups),
                    gpt_results,
                    full_path_to_original_name,
                    user_id,
                    username,
                    project_id,
                    upload_description
                )
            )

        await asyncio.gather(*tasks)

        
        for path in extract_paths:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)

        if os.path.exists(TEMP_FOLDER) and not os.listdir(TEMP_FOLDER):
            shutil.rmtree(TEMP_FOLDER)

        await send_progress(upload_id, "DONE 🚀", progress=100)

    except Exception as e:
        traceback.print_exc()

async def analyze_one_group(upload_id, group, group_index, total_groups, gpt_results, full_path_to_original_name, user_id, username, project_id, upload_description):
    try:
        group_progress = 15 + int((group_index / total_groups) * 70)
        await send_progress(upload_id, f"Analyzing Group {group_index + 1}/{total_groups}...", progress=group_progress)

        file_chunks = []
        for file_entry in group:
            if isinstance(file_entry, tuple):
                file_name, file_lines = file_entry
            else:
                file_name = file_entry
                with open(file_name, "r", encoding="utf-8") as f:
                    file_lines = f.readlines()

            total_lines = len(file_lines)

            if total_lines <= 300:
                MAX_LINES_PER_CHUNK = total_lines
            elif total_lines <= 2000:
                MAX_LINES_PER_CHUNK = 400
            else:
                MAX_LINES_PER_CHUNK = 400

            num_chunks = (total_lines + MAX_LINES_PER_CHUNK - 1) // MAX_LINES_PER_CHUNK

            for chunk_index in range(num_chunks):
                start_line = chunk_index * MAX_LINES_PER_CHUNK
                end_line = min(start_line + MAX_LINES_PER_CHUNK, total_lines)
                chunk_lines = file_lines[start_line:end_line]
                file_chunks.append((file_name, chunk_lines))

        # Call GPT on the combined chunks of the group
        analysis_output = await call_gpt_analyze_chunk(file_chunks)

        try:
            if analysis_output.strip().startswith("```json"):
                analysis_output = analysis_output.strip().split("```json")[1].split("```")[0].strip()
            elif analysis_output.strip().startswith("```"):
                analysis_output = analysis_output.strip().split("```")[1].split("```")[0].strip()

            analysis_data = json.loads(analysis_output)
        except Exception as e:
            print(f"[Parse Error] Could not parse GPT analysis output JSON: {e}")
            analysis_data = []

        await send_progress(upload_id, f"Running Sanity Check on Group {group_index + 1}/{total_groups}...", progress=group_progress + 5)

        # Iterate through each file's results in the group
        for file_result in analysis_data:
            file_path = file_result["file"]
            bugs = file_result.get("bugs", [])
            optimizations = file_result.get("optimizations", [])

            # Run sanity check on this file's bugs
            sanity_checked = await run_sanity_check_on_bugs(file_path, json.dumps(bugs, indent=2))

            try:
                if sanity_checked.strip().startswith("```json"):
                    sanity_checked = sanity_checked.strip().split("```json")[1].split("```")[0].strip()
                elif sanity_checked.strip().startswith("```"):
                    sanity_checked = sanity_checked.strip().split("```")[1].split("```")[0].strip()

                sanity_checked_data = json.loads(sanity_checked)
            except Exception as e:
                print(f"[Parse Error] Could not parse Sanity Check output JSON: {e}")
                sanity_checked_data = { "bugs": [] }

            parsed_data = parse_outputs(
                {"bugs": bugs, "optimizations": optimizations},
                sanity_checked_data
            )

            relative_file_name = os.path.relpath(file_path, start=TEMP_FOLDER).replace("\\", "/")
            original_name = full_path_to_original_name.get(file_path, "")

            save_to_mongo(
                upload_id,
                relative_file_name,
                parsed_data,
                user_id,
                username,
                project_id,
                original_name,
                upload_description
            )

        await send_progress(upload_id, f"Saved Group {group_index + 1} to MongoDB", progress=group_progress + 10)
        await asyncio.sleep(0.2)

    except Exception as e:
        traceback.print_exc()

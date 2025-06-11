# services/project_summary.py

import openai
import os
import asyncio
import json
from dotenv import load_dotenv
load_dotenv()

# Create OpenAI client (new API style)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_project_summary(file_previews):
    # Build project file list with previews as text → USE display_name
    project_file_list = ""
    for file_obj in file_previews:
        project_file_list += f"\nFilename: {file_obj['display_name']}\nPreview:\n{file_obj['preview']}\n{'-'*40}\n"

    print(f"[DEBUG] Project Summary prompt length: {len(project_file_list)} chars")

    messages = [
        {"role": "system", "content": "You are an expert software architect."},
        {"role": "user", "content": f"""
You are given a list of files in a software project.
For each file, you are provided:
- the filename (relative path)
- a preview of the file content (first 500 characters).

Your goal is to analyze this information and group the files logically into connected groups.

⚠️ VERY IMPORTANT:
- You must return the output as a VALID JSON list of groups, in this format:

[
    ["src/services/auth_service.py", "src/services/user_service.py"],
    ["src/routes/auth_routes.py", "src/routes/user_routes.py"]
]

- Do NOT output explanations or any extra text. Only return the pure JSON.

Here is the list of project files with previews:

{project_file_list}

Please generate the Connected Groups in the format described above.
"""}
    ]

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="gpt-4o",
        messages=messages,
        max_tokens=4096,
        temperature=0
    )

    content = response.choices[0].message.content

    print("\n===== GPT Project Summary Output =====")
    print(content)
    print("======================================\n")

    return content

def parse_project_summary(summary_text):
    try:
        # Clean GPT response → remove ```json if present
        clean_text = summary_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:].strip()
        if clean_text.startswith("```"):
            clean_text = clean_text[3:].strip()
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3].strip()

        connected_groups = json.loads(clean_text)

    except Exception as e:
        print(f"[Parse Error] Could not parse Project Summary JSON: {e}")
        connected_groups = []

    dependencies = {}  # Not used anymore

    return dependencies, connected_groups

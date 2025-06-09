import openai
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()


# Create OpenAI client (new API style)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_project_summary(file_previews):
    # Build project file list with previews as text
    project_file_list = ""
    for file_obj in file_previews:
        project_file_list += f"\nFilename: {file_obj['filename']}\nPreview:\n{file_obj['preview']}\n{'-'*40}\n"

    messages = [
        {"role": "system", "content": "You are an expert software architect."},
        {"role": "user", "content": f"""
You are given a list of files in a software project.
For each file, you are provided:
- the full filename (including path)
- a preview of the file content (first 500 characters), which may include imports, top-level functions, and classes.

Your goal is to analyze this information and group the files logically into connected groups.
A connected group represents files that work together as part of the same component or feature.

Files can belong to:
- Services
- API Routes
- Utilities
- Core logic
- Configuration
- Tests
- Other relevant categories

Use the filename path and preview content to make informed groupings.

Important guidelines:
- Do NOT attempt to fully analyze code → only use preview to help understand relationships.
- Prioritize grouping files that import each other or work together.
- Do not leave any file ungrouped unless it is completely standalone.

Your output format must be a JSON list of groups:

[
    ["src/services/auth_service.py", "src/services/user_service.py"],
    ["src/routes/auth_routes.py", "src/routes/user_routes.py"],
    ["src/utils/data_utils.py", "src/utils/email_utils.py"],
    ["src/main.py"]
]

Do not include the preview in your output — only the list of filenames grouped logically.

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

    return content

def parse_project_summary(summary_text):
    dependencies = {}
    connected_groups = []

    lines = summary_text.splitlines()
    current_section = None

    for line in lines:
        line = line.strip()

        if line.startswith("Dependencies:"):
            current_section = "dependencies"
            continue
        if line.startswith("Connected Groups:"):
            current_section = "groups"
            continue

        if current_section == "dependencies" and "→" in line:
            file, deps = line.split("→")
            file = file.strip()
            deps = deps.strip().strip("[]").replace(",", "").split()
            dependencies[file] = deps

        if current_section == "groups" and line.startswith("-"):
            group_files = line[1:].strip().strip("[]").replace(",", "").split()
            connected_groups.append(group_files)

    return dependencies, connected_groups

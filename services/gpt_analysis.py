import openai
import os
import asyncio
from dotenv import load_dotenv
import json
load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def call_gpt_analyze_chunk(file_chunks):
    chunk_message_parts = []

    for file_name, chunk_lines in file_chunks:
        chunk_text = "".join(chunk_lines)
        part = f"---\nFilename: {file_name}\nChunk:\n```\n{chunk_text}\n```\n---\n"
        chunk_message_parts.append(part)

    chunk_message = "".join(chunk_message_parts).replace("{", "{{").replace("}", "}}")

    messages = [
        {
            "role": "system",
            "content": "You are a professional software engineer and expert code reviewer."
        },
        {
            "role": "user",
            "content": f"""
You are analyzing the following files from a software project.
Each file is divided into clearly labeled chunks.

For each BUG:
- Line number (approximate is fine)
- Priority: High / Medium / Low
- Confidence: High / Medium / Low
- Description

For each OPTIMIZATION:
- Line number (or 0 / -1 if not applicable)
- Description

⚠️ Return ONLY valid JSON:
{{
  "bugs": [{{"line": ..., "priority": "...", "confidence": "...", "description": "..."}}],
  "optimizations": [{{"line": ..., "description": "..."}}]
}}

If no bugs/optimizations:
{{"bugs": [], "optimizations": []}}

Now here are the files:

{chunk_message}
"""
        }
    ]

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="gpt-4o",
        messages=messages,
        max_tokens=4096,
        temperature=0
    )

    content = response.choices[0].message.content
    print("\n===== GPT Analyze Chunk Output =====")
    print(content)
    print("====================================\n")

    return content



async def run_sanity_check_on_bugs(file_name, bug_list_text_json):
    messages = [
        {
            "role": "system",
            "content": """
You are a professional code reviewer.

You will receive a list of BUGS in JSON format.

Your task:
- REMOVE false positives.
- ADD missing critical bugs if any.
- FIX incorrect line numbers if needed.
- DO NOT include cosmetic or style-only issues.
- DO NOT erase valid bugs unless clearly wrong.

You MUST return a clean JSON object in the following format:

{
  "bugs": [
    { "line": ..., "priority": "...", "confidence": "...", "description": "..." }
  ]
}

If no bugs remain:

{
  "bugs": []
}

Do NOT return any explanation or extra text. Only return the clean JSON.
"""
        },
        {
            "role": "user",
            "content": f"""
You are reviewing file: {file_name}

Here is the detected bug list (JSON format):

{bug_list_text_json}

Please return the corrected list, as valid JSON only.
"""
        }
    ]

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="gpt-4o",
        messages=messages,
        max_tokens=2048,
        temperature=0
    )

    content = response.choices[0].message.content


    if content.strip().startswith("```json"):
        content = content.strip().split("```json")[1].split("```")[0].strip()
    elif content.strip().startswith("```"):
        content = content.strip().split("```")[1].split("```")[0].strip()

    print("\n===== GPT Sanity Check Output =====")
    print(content)
    print("==================================\n")

    return content




async def call_gpt_async(code_chunk, file_path):
    code_chunk_safe = code_chunk.replace("{", "{{").replace("}", "}}")

    messages = [
        {
            "role": "system",
            "content": "You are a professional software engineer and expert code reviewer."
        },
        {
            "role": "user",
            "content": f"""
You are analyzing the following code from a single file: {file_path}

Return ONLY valid JSON:
{{
  "bugs": [{{"line": ..., "priority": "...", "confidence": "...", "description": "..."}}],
  "optimizations": [{{"line": ..., "description": "..."}}]
}}

If no bugs/optimizations:
{{"bugs": [], "optimizations": []}}

Here is the file content:

{code_chunk_safe}
"""
        }
    ]

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="gpt-4o",
        messages=messages,
        max_tokens=4096,
        temperature=0
    )

    content = response.choices[0].message.content
    print("\n===== GPT Single File Analyze Output =====")
    print(content)
    print("=========================================")

    return content


async def analyze_file_async(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

    
        analysis_content = await call_gpt_async(code, file_path)

        return {
            "file_path": file_path,
            "analysis_results": [{
                "chunk": code[:100] + "..." if len(code) > 100 else code,
                "analysis": analysis_content
            }]
        }

    except Exception as e:
        return {
            "file_path": file_path,
            "error": str(e)
        }
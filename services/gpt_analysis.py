import openai
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()


# Create OpenAI client (new API style)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 1️⃣ GPT call wrapper for single chunk (single file or multi-file chunk)
async def call_gpt_analyze_chunk(file_chunks):
    # Build message content
    chunk_message = ""

    for file_name, chunk_lines in file_chunks:
        chunk_text = "".join(chunk_lines)

        # Count chunks → if your chunking supports it (for now assume 1 chunk per file here)
        chunk_message += f"---\nFilename: {file_name}\nChunk:\n```\n{chunk_text}\n```\n---\n"

    # Build messages
    messages = [
        {
            "role": "system",
            "content": "You are a professional software engineer and expert code reviewer."
        },
        {
            "role": "user",
            "content": f"""
You are analyzing the following files from a software project.
You will be given the full content of each file, divided into chunks.

Your goal is to perform a deep analysis of this code.
For each file, carefully analyze the logic, structure, and style.
Then generate the following output:

1️⃣ BUGS
- Identify real bugs in the code.
- Include logic errors, missing edge cases, incorrect usage of APIs, security vulnerabilities, etc.
- Do not report trivial style issues unless they cause bugs.

2️⃣ OPTIMIZATIONS
- Suggest meaningful optimizations.
- Include performance improvements, code clarity improvements, reducing duplication, better patterns, etc.

Important Guidelines:
- You are analyzing full content — think deeply.
- Avoid shallow comments (do not say "remove unused import").
- For each BUG, give:
    - Line number (approximate is fine)
    - Short description (1-2 lines)
    - Priority: High / Medium / Low
    - Confidence: High / Medium / Low

- For each OPTIMIZATION, give:
    - Line number (if applicable, else "N/A")
    - Short description (1-2 lines)

Output Format (strict):

- BUG line X → Priority: High → Confidence: Medium → Description: ...
- BUG line Y → Priority: Low → Confidence: High → Description: ...
...
- OPTIMIZATION line X → Description: ...
- OPTIMIZATION line N/A → Description: ...

Do not output explanations. Only output the list in the format above.

Now here are the files:

{chunk_message}
"""
        }
    ]

    # Call GPT → in thread so your main async loop is not blocked
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="gpt-4o",
        messages=messages,
        max_tokens=4096,
        temperature=0
    )

    content = response.choices[0].message.content

    return content
# 2️⃣ Sanity Check step → review bug list and correct
async def run_sanity_check_on_bugs(file_name, bug_list_text):
    messages = [
        {"role": "system", "content": """
You are a professional code reviewer.

You will now review a list of bugs previously detected.

Your task is:

- Identify and REMOVE false positives — bugs that are not valid.
- Identify and ADD any clearly MISSING critical bugs.
- Correct line numbers if needed.
- DO NOT add cosmetic or style suggestions — focus only on real bugs.
- Return the corrected bug list in this format:

FILE: <file name>
- BUG [Priority: ...] [Confidence: ...] at line ...: Description
"""},

        {"role": "user", "content": f"""
Here is the list of bugs detected for file {file_name}:

{bug_list_text}

Do you see any false positives or missing critical bugs?
Please CORRECT and return the bug list in correct format.
Do NOT repeat optimizations here — just BUGS.
"""}
    ]

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="gpt-4o",
        messages=messages,
        max_tokens=2048,
        temperature=0
    )

    content = response.choices[0].message.content

    return content

# 3️⃣ GPT call wrapper for single file chunk (for existing analyze_file_async)
async def call_gpt_async(code_chunk, file_path):
    messages = [
        {"role": "system", "content": "You are a professional code reviewer. Analyze code, find bugs, and suggest optimizations."},
        {"role": "user", "content": f"Analyze the following code from {file_path}:\n\n{code_chunk}"}
    ]

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="gpt-4o",
        messages=messages,
        max_tokens=2048,
        temperature=0
    )

    content = response.choices[0].message.content

    return content

# 4️⃣ Analyze single file async (compatible with your existing code)
async def analyze_file_async(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        # TODO: Later → chunk large files → for now, one chunk per file
        chunks = [code]

        results = []
        for chunk in chunks:
            analysis_content = await call_gpt_async(chunk, file_path)
            results.append({
                "chunk": chunk[:100] + "..." if len(chunk) > 100 else chunk,  # show preview in result
                "analysis": analysis_content
            })

        return {
            "file_path": file_path,
            "analysis_results": results
        }

    except Exception as e:
        return {
            "file_path": file_path,
            "error": str(e)
        }

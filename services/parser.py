import json

def parse_outputs(analysis_output, sanity_checked_output=None):
    def clean_gpt_output(text):
        """Removes markdown wrappers like ```json from GPT output if present."""
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:].strip()
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:].strip()
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3].strip()
        return clean_text

    
    try:
        if isinstance(analysis_output, dict):
            parsed_json = analysis_output
        else:
            clean_analysis = clean_gpt_output(analysis_output)
            parsed_json = json.loads(clean_analysis)
    except Exception as e:
        print(f"[Parse Error] Could not parse GPT analysis output JSON: {e}")
        parsed_json = { "bugs": [], "optimizations": [] }

    
    sanity_json = { "bugs": [] }
    if sanity_checked_output:
        try:
            if isinstance(sanity_checked_output, dict):
                sanity_json = sanity_checked_output
            else:
                clean_sanity = clean_gpt_output(sanity_checked_output)
                sanity_json = json.loads(clean_sanity)
        except Exception as e:
            print(f"[Parse Error] Could not parse Sanity Check output JSON: {e}")
            sanity_json = { "bugs": [] }

    return {
        "bugs_original": parsed_json.get("bugs", []),
        "bugs_sanity_checked": sanity_json.get("bugs", []),
        "optimizations_original": parsed_json.get("optimizations", []),
        "optimizations_sanity_checked": sanity_json.get("optimizations", []),
        "analysis_output": analysis_output,
        "sanity_checked_output": sanity_checked_output if isinstance(sanity_checked_output, str) else json.dumps(sanity_checked_output)
    }

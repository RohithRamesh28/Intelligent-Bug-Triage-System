# services/parser.py

import re

def parse_bugs(output_text):
    bug_pattern = re.compile(
        r'line\s*(\d+)[^\n]*bug[^\n]*?:\s*(.*?)\s*priority\s*:\s*(\w+)\s*confidence\s*:\s*(\d+)%?', 
        re.IGNORECASE | re.DOTALL
    )
    bugs = []
    for match in bug_pattern.finditer(output_text):
        line = int(match.group(1))
        description = match.group(2).strip()
        priority = match.group(3).capitalize()
        confidence = int(match.group(4))
        bugs.append({
            "line": line,
            "description": description,
            "priority": priority,
            "confidence": confidence
        })
    return bugs

def parse_optimizations(output_text):
    opt_pattern = re.compile(
        r'line\s*(\d+)[^\n]*optimization[^\n]*?:\s*(.*?)($|\n)', 
        re.IGNORECASE | re.DOTALL
    )
    optimizations = []
    for match in opt_pattern.finditer(output_text):
        line = int(match.group(1))
        description = match.group(2).strip()
        optimizations.append({
            "line": line,
            "description": description
        })
    return optimizations

def parse_outputs(analysis_output, sanity_checked_output):
    return {
        "bugs_original": parse_bugs(analysis_output),
        "bugs_sanity_checked": parse_bugs(sanity_checked_output),
        "optimizations_original": parse_optimizations(analysis_output),
        "optimizations_sanity_checked": parse_optimizations(sanity_checked_output),
        "analysis_output": analysis_output,
        "sanity_checked_output": sanity_checked_output
    }

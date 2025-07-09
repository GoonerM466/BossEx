import re

def process_name_field(selected_text, full_text, start_idx, end_idx, name_patterns, possible_separators):
    """
    Process the name field based on highlighted text.
    Returns: (regex_pattern, extracted_text)
    """
    # Modified regex to capture text after the number if present - using \d+ for multiple digits
    match = re.match(r"^([A-Za-z\s\+\-\(\)]+?)\s*(\d+)(?:\s*([A-Za-z\s\+\-\(\)]+?))?$", selected_text.strip(), re.IGNORECASE)
    if match:
        name_content = match.group(1).strip()
        number = match.group(2)
        after_text = match.group(3).strip() if match.group(3) else ""
        
        # Escape special characters in the text portions
        escaped_name = re.escape(name_content)
        
        # Create the pattern based on what was captured - using \d+ for multiple digits
        if after_text:
            escaped_after = re.escape(after_text)
            pattern = fr"^({escaped_name}\s*\d+\s*{escaped_after})"
            extracted = f"{name_content} {number} {after_text}"
        else:
            pattern = fr"^({escaped_name}\s*\d+)"
            extracted = f"{name_content} {number}"
        
        # Try to find the pattern in the full text
        full_match = re.search(pattern, full_text, re.IGNORECASE)
        if full_match:
            extracted = full_match.group(0).strip()
        
        return pattern, extracted
    
    # Fallback to existing pattern matching logic
    escaped_separators = "".join(re.escape(sep) for sep in possible_separators)
    best_pattern = None
    best_match = None
    for name_pattern in name_patterns:
        pattern_str = name_pattern["pattern"].replace("<symbols>", escaped_separators)
        try:
            match = re.search(pattern_str, full_text, re.IGNORECASE)
            if match and match.start() <= start_idx and match.end() >= end_idx:
                if not best_match or (match.start() == 0 and match.end() - match.start() <= best_match.end() - best_match.start()):
                    best_pattern = pattern_str
                    best_match = match
        except re.error:
            continue
    
    if best_match:
        extracted = best_match.group(0).strip()
        return best_pattern, extracted
    
    pattern = fr"^(.+?)"
    extracted = selected_text.strip()
    return pattern, extracted
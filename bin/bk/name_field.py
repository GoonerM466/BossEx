import re

def process_name_field(selected_text, full_text, start_idx, end_idx, name_patterns, possible_separators):
    """
    Process the name field based on highlighted text.
    Returns: (regex_pattern, extracted_text)
    """
    match = re.match(r"^([A-Za-z\s-]+)\s*(\d{1,3})$", selected_text.strip(), re.IGNORECASE)
    if match:
        name_content = match.group(1).strip()
        number = match.group(2)
        escaped_name = re.escape(name_content)
        pattern = fr"^{escaped_name}\s*(\d{{1,3}})"
        extracted = f"{name_content} {number}"
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            extracted = match.group(0).strip()
        return pattern, extracted

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
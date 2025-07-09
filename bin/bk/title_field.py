import re

def process_title_field(selected_text, full_text, start_idx, end_idx, possible_separators, detect_separator):
    """
    Process the title field based on highlighted text.
    Returns: (regex_pattern, extracted_text)
    """
    # Find the opening separator (before the selection)
    latest_pos = -1
    opening_sep = None
    for sep in possible_separators:
        pattern = fr"(?:(?<=[\S])\s*{re.escape(sep)}\s*|^\s*{re.escape(sep)}\s*|\s*{re.escape(sep)}\s*(?=[\S])|\s*{re.escape(sep)}\s*$)"
        matches = [m for m in re.finditer(pattern, full_text[:start_idx])]
        if matches:
            pos = matches[-1].start()
            if pos > latest_pos:
                latest_pos = pos
                opening_sep = sep
    if not opening_sep:
        opening_sep = detect_separator(full_text[:start_idx]) or ":"

    # Find the closing separator (after the selection)
    earliest_pos = len(full_text)
    closing_sep = None
    for sep in possible_separators:
        pattern = fr"(?:(?<=[\S])\s*{re.escape(sep)}\s*|^\s*{re.escape(sep)}\s*|\s*{re.escape(sep)}\s*(?=[\S])|\s*{re.escape(sep)}\s*$)"
        matches = [m for m in re.finditer(pattern, full_text[end_idx:])]
        if matches:
            pos = matches[0].start() + end_idx
            if pos < earliest_pos:
                earliest_pos = pos
                closing_sep = sep
    if not closing_sep:
        closing_sep = detect_separator(full_text[end_idx:]) or "//"

    # Build regex: {opening_sep} ([^/]*?)(?=\s*{closing_sep})
    escaped_open = re.escape(opening_sep)
    escaped_close = re.escape(closing_sep)
    pattern = fr"{escaped_open}\s*([^/]*?)(?=\s*{escaped_close})"
    match = re.search(pattern, full_text, re.IGNORECASE)
    extracted = match.group(1).strip() if match else selected_text
    return pattern, extracted
import re

def process_title_field(selected_text, full_text, start_idx, end_idx, possible_separators, detect_separator):
    """
    Process the title field based on highlighted text.
    Returns: (regex_pattern, extracted_text)
    """
    # Placeholder for future term exclusion
    ignore_terms = []  # Empty list for potential future use to ignore specific terms in capture groups
    
    # Optionally filter out timezone-related separators
    # Filter ON
    #timezone_separators = {'UK', 'EST', 'ET'}
    # Fliter OFF
    timezone_separators = {}
    valid_separators = [sep for sep in possible_separators if sep not in timezone_separators]
    
    # Find the opening separator (before the selection)
    latest_pos = -1
    opening_sep = None
    opening_sep_count = 0
    
    for sep in valid_separators:
        pattern = fr"(?:(?<=[\S])\s*{re.escape(sep)}\s*|^\s*{re.escape(sep)}\s*|\s*{re.escape(sep)}\s*(?=[\S])|\s*{re.escape(sep)}\s*$)"
        matches = [m for m in re.finditer(pattern, full_text[:start_idx], re.IGNORECASE)]
        if matches:
            pos = matches[-1].start()
            if pos > latest_pos:
                latest_pos = pos
                opening_sep = sep
                opening_sep_count = len(matches)
    
    if not opening_sep:
        opening_sep = detect_separator(full_text[:start_idx]) or ":"
        # Assume first occurrence if using fallback
        opening_sep_count = 1
        matches = [m for m in re.finditer(fr"\s*{re.escape(opening_sep)}\s*", full_text[:start_idx], re.IGNORECASE)]
        if matches:
            opening_sep_count = len(matches)
    
    # Find the closing separator (after the selection)
    earliest_pos = len(full_text)
    closing_sep = None
    
    for sep in valid_separators:
        pattern = fr"(?:(?<=[\S])\s*{re.escape(sep)}\s*|^\s*{re.escape(sep)}\s*|\s*{re.escape(sep)}\s*(?=[\S])|\s*{re.escape(sep)}\s*$)"
        matches = [m for m in re.finditer(pattern, full_text[end_idx:], re.IGNORECASE)]
        if matches:
            pos = matches[0].start() + end_idx
            if pos < earliest_pos:
                earliest_pos = pos
                closing_sep = sep
    
    if not closing_sep:
        closing_sep = detect_separator(full_text[end_idx:]) or "//"
    
    # Build regex: skip to n-th opening_sep, capture group, match closing_sep
    escaped_open = re.escape(opening_sep)
    escaped_close = re.escape(closing_sep)
    
    # Modified pattern to capture up to the last occurrence of closing separator
    if closing_sep == "|":
        # Special handling for pipe - capture everything up to last pipe
        pattern = fr"(?:.*?\s*{escaped_open}\s*){{{opening_sep_count}}}(.*?)\s*{escaped_close}\s*[^{escaped_close}]*$"
    else:
        # Original pattern for other separators
        pattern = fr"(?:.*?\s*{escaped_open}\s*){{{opening_sep_count}}}(.*?)(?=\s*{escaped_close}\s*)"
    
    match = re.search(pattern, full_text, re.IGNORECASE)
    extracted = match.group(1).strip() if match else selected_text.strip()
    
    return pattern, extracted
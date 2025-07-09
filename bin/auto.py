import re
from bin.name_field import process_name_field
from bin.title_field import process_title_field
from bin.time_field import process_time_field
from bin.date_field import process_date_field, identify_components, build_base_pattern

def auto_process(full_text, config, timezone, detect_separator, count_separators_before):
    """
    Auto-match name, title, time, and date fields from Sample 1.
    Args:
        full_text: Sample text.
        config: Configuration dictionary.
        timezone: Selected timezone friendly name.
        detect_separator: Function to detect default separator.
        count_separators_before: Function to count separators before index.
    Returns:
        Dictionary with patterns, extracted values, and formats for each field.
    """
    # Get valid separators for name/title (exclude timezones)
    timezone_matches = set()
    for tz in config["timezones"]:
        timezone_matches.update(tz["match"])
    possible_separators = [item["symbol"] for item in config["separators"] if item["symbol"] not in timezone_matches]
    selected_tz = next(tz for tz in config["timezones"] if tz["friendly_name"] == timezone)
    tz_matches = selected_tz["match"]
    results = {
        "name": {"pattern": "", "extracted": "", "format": "", "start_idx": None, "end_idx": None},
        "title": {"pattern": "", "extracted": "", "format": "", "start_idx": None, "end_idx": None},
        "time": {"pattern": "", "extracted": "", "format": "", "start_idx": None, "end_idx": None},
        "date": {"pattern": "", "extracted": "", "format": "", "start_idx": None, "end_idx": None}
    }

    # Name: Try number-based first, then fallback to word-based
    number_match = re.search(r"\b\d{1,3}\b", full_text)
    if number_match:
        number_end = number_match.end()
        sep, sep_pos = None, float('inf')
        for s in possible_separators:
            match = re.search(fr"(?:(?<=[\S])\s*{re.escape(s)}\s*|\s*{re.escape(s)}\s*(?=[\S])|\s*{re.escape(s)}\s*$)", full_text[number_end:])
            if match and (number_end + match.start()) < sep_pos:
                sep = s
                sep_pos = number_end + match.start()
        if sep:
            name_text = full_text[:sep_pos].strip()
            start_idx = full_text.index(name_text)
            pattern, extracted = process_name_field(name_text, full_text, start_idx, start_idx + len(name_text), config.get("name_patterns", []), possible_separators)
            results["name"] = {"pattern": pattern, "extracted": extracted, "format": "", "start_idx": start_idx, "end_idx": start_idx + len(name_text)}
            name_end = sep_pos
        else:
            name_end = number_end
    else:
        # Fallback: Extract before first separator after a word
        word_match = re.search(r"[a-zA-Z]+", full_text)
        if word_match:
            word_start = word_match.start()
            sep, sep_pos = None, float('inf')
            for s in possible_separators:
                match = re.search(fr"(?:(?<=[\S])\s*{re.escape(s)}\s*|\s*{re.escape(s)}\s*(?=[\S])|\s*{re.escape(s)}\s*$)", full_text[word_start:])
                if match and (word_start + match.start()) < sep_pos:
                    sep = s
                    sep_pos = word_start + match.start()
            if sep:
                name_text = full_text[:sep_pos].strip()
                start_idx = full_text.index(name_text)
                pattern = fr"^(.*?)(?=\s*{re.escape(sep)})"
                extracted = name_text
                results["name"] = {"pattern": pattern, "extracted": extracted, "format": "", "start_idx": start_idx, "end_idx": start_idx + len(name_text)}
                name_end = sep_pos
            else:
                name_end = word_start
        else:
            name_end = 0

    # Title: After name separator to most common of valid separators
    common_seps = [s for s in ["|", "/", "-"] if s in possible_separators]
    sep_counts = {s: len(list(re.finditer(fr"(?:(?<=[\S])\s*{re.escape(s)}\s*|\s*{re.escape(s)}\s*(?=[\S])|\s*{re.escape(s)}\s*$)", full_text))) for s in common_seps}
    most_common_sep = max(sep_counts, key=sep_counts.get, default="|") if sep_counts else possible_separators[0]
    title_match = re.search(fr"(?:(?<=[\S])\s*{re.escape(most_common_sep)}\s*|\s*{re.escape(most_common_sep)}\s*(?=[\S])|\s*{re.escape(most_common_sep)}\s*$)", full_text[name_end:])
    if title_match:
        title_end = name_end + title_match.start()
        title_text = full_text[name_end:title_end].strip()
        if title_text:
            start_idx = full_text.index(title_text, name_end)
            pattern, extracted = process_title_field(title_text, full_text, start_idx, start_idx + len(title_text), possible_separators, detect_separator)
            results["title"] = {"pattern": pattern, "extracted": extracted, "format": "", "start_idx": start_idx, "end_idx": start_idx + len(title_text)}
        else:
            title_end = name_end
    else:
        title_end = len(full_text)

    # Time: Prefer AM/PM, prioritize timezone
    time_matches = []
    for pattern in config["time_formats"]:
        for match in re.finditer(pattern, full_text, re.IGNORECASE):
            time_text = match.group(0)
            start_idx = match.start()
            is_am_pm = bool(re.search(r'[AaPp][Mm]$', time_text, re.IGNORECASE))
            # Boost tz_score for closer timezone matches
            tz_score = 0
            for m in tz_matches:
                tz_pos = full_text[max(0, start_idx-20):start_idx].upper().rfind(m)
                if tz_pos != -1:
                    tz_score = max(tz_score, 20 - tz_pos)  # Higher score for closer matches
            time_matches.append((start_idx, start_idx + len(time_text), time_text, pattern, is_am_pm, tz_score))
    if time_matches:
        time_matches.sort(key=lambda x: (-x[5], not x[4], x[0]))  # Prefer timezone score, then AM/PM, then position
        start_idx, end_idx, time_text, matched_pattern, _, _ = time_matches[0]
        pattern, extracted, format_str = process_time_field(
            time_text, full_text, start_idx, end_idx, [matched_pattern], [item["symbol"] for item in config["separators"]],
            config["days"], config["months"], True, detect_separator, count_separators_before, tz_matches
        )
        results["time"] = {"pattern": pattern, "extracted": extracted, "format": format_str, "start_idx": start_idx, "end_idx": end_idx}

    # Date: Prioritize timezone
    date_matches = []
    components = identify_components(full_text, config["days"], config["months"])
    if components:
        base_pattern = build_base_pattern(components, config["days"], config["months"])
    else:
        base_pattern = r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:\s+\d{2,4})?"
    for match in re.finditer(base_pattern, full_text, re.IGNORECASE):
        date_text = match.group(0)
        start_idx = match.start()
        tz_score = 0
        for m in tz_matches:
            tz_pos = full_text[max(0, start_idx-20):start_idx].upper().rfind(m)
            if tz_pos != -1:
                tz_score = max(tz_score, 20 - tz_pos)
        date_matches.append((start_idx, start_idx + len(date_text), date_text, tz_score))
    if date_matches:
        date_matches.sort(key=lambda x: (-x[3], x[0]))  # Prefer timezone score, then position
        start_idx, end_idx, date_text, _ = date_matches[0]
        pattern, extracted, format_str = process_date_field(
            date_text, full_text, start_idx, end_idx, config.get("date_formats", []), [item["symbol"] for item in config["separators"]],
            config["days"], config["months"], True, detect_separator, count_separators_before, tz_matches
        )
        results["date"] = {"pattern": pattern, "extracted": extracted, "format": format_str, "start_idx": start_idx, "end_idx": end_idx}

    return results
import re

def process_time_field(selected_text, full_text, start_idx, end_idx, time_formats, possible_separators, days, months, anchor_enabled, detect_separator, count_separators_before):
    pattern, extracted = get_time_pattern(selected_text, full_text, start_idx, time_formats, possible_separators, anchor_enabled, detect_separator, count_separators_before)
    format_str = get_time_format(extracted, time_formats)
    return pattern, extracted, format_str

def refresh_time_field(selected_text, full_text, start_idx, end_idx, time_formats, possible_separators, days, months, anchor_enabled, detect_separator, count_separators_before):
    matches = []
    for pattern in time_formats:
        matches.extend([(m.start(), m.end(), m.group(0), pattern) for m in re.finditer(pattern, full_text, re.IGNORECASE)])
    matches.sort(key=lambda x: x[0])

    if not matches:
        return "No pattern detected", selected_text, "No format detected"

    current_idx = min(range(len(matches)), key=lambda i: abs(matches[i][0] - start_idx))
    next_idx = (current_idx + 1) % len(matches)
    new_start_idx, new_end_idx, new_selected_text, matched_pattern = matches[next_idx]

    pattern, extracted = get_time_pattern(new_selected_text, full_text, new_start_idx, [matched_pattern], possible_separators, anchor_enabled, detect_separator, count_separators_before)
    format_str = get_time_format(extracted, time_formats)
    return pattern, extracted, format_str

def get_time_pattern(selected_text, full_text, start_idx, time_formats, possible_separators, anchor_enabled, detect_separator, count_separators_before):
    base_pattern = None
    for pattern in time_formats:
        if re.match(pattern, selected_text, re.IGNORECASE):
            base_pattern = pattern
            break
    if not base_pattern:
        base_pattern = time_formats[0]

    matches = list(re.finditer(base_pattern, full_text, re.IGNORECASE))
    if not anchor_enabled or len(matches) <= 1:
        pattern = fr"({base_pattern})"
    else:
        separator, sep_count, _ = get_closest_separator(full_text, start_idx, possible_separators)
        if not separator:
            separator = detect_separator(full_text) or "|"
            sep_count = count_separators_before(full_text, start_idx, separator)
        escaped_sep = re.escape(separator)
        sep_pattern = fr"\s*{escaped_sep}\s*"
        prior_pattern = fr"(?:{sep_pattern}.*?){{{sep_count}}}"
        pattern = fr"{prior_pattern}\s*({base_pattern})"

    match = re.search(pattern, full_text, re.IGNORECASE)
    extracted = match.group(1).strip() if match and match.groups() else selected_text
    return pattern, extracted

def get_closest_separator(full_text, start_idx, possible_separators):
    closest_sep = None
    min_distance = float('inf')
    sep_count = 0
    sep_pos = None

    for sep in possible_separators:
        escaped_sep = re.escape(sep)
        matches = list(re.finditer(fr"(?:(?<=[\S])\s*{escaped_sep}\s*|^\s*{escaped_sep}\s*|\s*{escaped_sep}\s*(?=[\S])|\s*{escaped_sep}\s*$)", full_text[:start_idx], re.IGNORECASE))
        if matches:
            last_match = matches[-1]
            distance = start_idx - last_match.end()
            if distance < min_distance:
                min_distance = distance
                closest_sep = sep
                sep_count = len(matches)
                sep_pos = last_match.start()

    return closest_sep, sep_count, sep_pos

def get_time_format(time_str, time_formats):
    time_str_lower = time_str.lower()
    has_am_pm = bool(re.search(r'[ap]m$', time_str_lower))
    hours = int(re.search(r"\d{1,2}", time_str_lower).group(0)) if re.search(r"\d{1,2}", time_str_lower) else 0
    formats = []

    for pattern in time_formats:
        if re.match(pattern, time_str, re.IGNORECASE):
            if re.search(r':\d{2}', time_str_lower):
                separator = ":"
            elif re.search(r'-\d{2}', time_str_lower):
                separator = "-"
            elif re.search(r'\.\d{2}', time_str_lower):
                separator = "."
            else:
                separator = ""

            space_option = " " if " " in time_str and re.search(r'\s+[ap]m$', time_str_lower) else ""

            if pattern == r"\d{1,2}(?::\d{2})?[AaPp][Mm]":
                if hours <= 12 and f"h{space_option}a" not in formats:
                    formats.append(f"h{space_option}a")
                if hours <= 24 and f"hh{space_option}a" not in formats:
                    formats.append(f"hh{space_option}a")
            elif has_am_pm:
                if hours <= 12 and f"h{separator}mm{space_option}a" not in formats:
                    formats.append(f"h{separator}mm{space_option}a")
                if hours <= 24 and f"hh{separator}mm{space_option}a" not in formats:
                    formats.append(f"hh{separator}mm{space_option}a")
            else:
                if hours <= 24 and f"H{separator}mm" not in formats:
                    formats.append(f"H{separator}mm")
                if hours <= 24 and f"HH{separator}mm" not in formats:
                    formats.append(f"HH{separator}mm")

    return ";".join(formats) if formats else "No format detected"
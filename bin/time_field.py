import re

def process_time_field(selected_text, full_text, start_idx, end_idx, time_formats, possible_separators, days, months, anchor_enabled, detect_separator, count_separators_before, tz_matches=None):
    pattern, extracted = get_time_pattern(selected_text, full_text, start_idx, time_formats, possible_separators, anchor_enabled, detect_separator, count_separators_before, tz_matches)
    format_str = get_time_format(extracted)
    return pattern, extracted, format_str

def refresh_time_field(full_text, time_formats, possible_separators, days, months, anchor_enabled, detect_separator, count_separators_before, tz_matches=None, current_time=None):
    matches = []
    for pattern in time_formats:
        for match in re.finditer(pattern, full_text, re.IGNORECASE):
            time_text = match.group(0)
            start_idx = match.start()
            is_am_pm = bool(re.search(r'[AaPp][Mm]', time_text.strip()))
            tz_score = 0
            if tz_matches:
                for m in tz_matches:
                    tz_pos = full_text[max(0, start_idx-20):start_idx].upper().rfind(m)
                    if tz_pos != -1:
                        tz_score = max(tz_score, 20 - tz_pos)
            matches.append((start_idx, start_idx + len(time_text), time_text, pattern, is_am_pm, tz_score))

    if not matches:
        return "No pattern detected", "", "No format detected"

    matches.sort(key=lambda x: (-x[5], not x[4], x[0]))
    if current_time:
        current_idx = next((i for i, m in enumerate(matches) if m[2] == current_time), 0)
        next_idx = (current_idx + 1) % len(matches)
    else:
        next_idx = 0

    start_idx, end_idx, time_text, matched_pattern, _, _ = matches[next_idx]
    pattern, extracted = get_time_pattern(time_text, full_text, start_idx, [matched_pattern], possible_separators, anchor_enabled, detect_separator, count_separators_before, tz_matches)
    format_str = get_time_format(extracted)
    return pattern, extracted, format_str

def get_time_pattern(selected_text, full_text, start_idx, time_formats, possible_separators, anchor_enabled, detect_separator, count_separators_before, tz_matches=None):
    selected_text = selected_text.strip()
    base_pattern = None
    for pattern in time_formats:
        if re.fullmatch(pattern, selected_text, re.IGNORECASE):
            base_pattern = pattern
            break

    if not base_pattern:
        base_pattern = time_formats[0]

    matches = list(re.finditer(base_pattern, full_text, re.IGNORECASE))
    if not matches:
        return "No pattern detected", selected_text

    best_match = matches[0]
    if tz_matches and anchor_enabled:
        max_tz_score = -1
        for match in matches:
            match_start = match.start()
            tz_score = 0
            for m in tz_matches:
                tz_pos = full_text[max(0, match_start-20):match_start].upper().rfind(m)
                if tz_pos != -1:
                    tz_score = max(tz_score, 20 - tz_pos)
            if tz_score > max_tz_score:
                max_tz_score = tz_score
                best_match = match

    extracted = best_match.group(0).strip()
    if not anchor_enabled or len(matches) <= 1:
        pattern = fr"({base_pattern})"
    else:
        separator, sep_count, _ = get_closest_separator(full_text, best_match.start(), possible_separators, tz_matches)
        if not separator:
            separator = detect_separator(full_text) or "|"
            sep_count = count_separators_before(full_text, best_match.start(), separator)
        escaped_sep = re.escape(separator)
        sep_pattern = fr"\s*{escaped_sep}\s*"
        prior_pattern = fr"(?:{sep_pattern}.*?){{{sep_count}}}"
        pattern = fr"{prior_pattern}\s*({base_pattern})"

    return pattern, extracted

def get_closest_separator(full_text, start_idx, possible_separators, tz_matches=None):
    closest_sep = None
    min_distance = float('inf')
    sep_count = 0
    sep_pos = None

    if tz_matches:
        for sep in [s for s in possible_separators if s in tz_matches]:
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

    if not closest_sep:
        for sep in possible_separators:
            if tz_matches and sep in tz_matches:
                continue
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

def get_time_format(time_str):
    time_str_lower = time_str.strip().lower()
    has_am_pm = bool(re.search(r'\d{1,2}(:\d{2})?\s*[ap]m$', time_str_lower))
    sep_match = re.search(r'[:\-.]', time_str_lower)
    separator = sep_match.group(0) if sep_match else ''
    space_option = " " if re.search(r'\s+[ap]m$', time_str_lower) else ""
    formats = []
    hours = int(re.search(r"\d{1,2}", time_str_lower).group(0)) if re.search(r"\d{1,2}", time_str_lower) else 0

    if has_am_pm:
        if re.search(rf"\d{{1,2}}{separator}\d{{2}}\s*[ap]m$", time_str_lower):
            if hours <= 12:
                formats.append(f"h{separator}mm{space_option}a")
            formats.append(f"hh{separator}mm{space_option}a")
        elif re.search(rf"\d{{1,2}}\s*[ap]m$", time_str_lower):
            if hours <= 12:
                formats.append(f"h{space_option}a")
            formats.append(f"hh{space_option}a")
    else:
        if separator and re.search(rf"\d{{1,2}}{separator}\d{{2}}$", time_str_lower):
            formats.append(f"H{separator}mm")
            formats.append(f"HH{separator}mm")

    return ";".join(formats) if formats else "No format detected"

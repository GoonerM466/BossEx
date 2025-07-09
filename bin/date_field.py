import re

def process_date_field(selected_text, full_text, start_idx, end_idx, date_formats, possible_separators, days, months, anchor_enabled, detect_separator, count_separators_before, tz_matches=None):
    pattern, extracted = get_date_pattern(selected_text, full_text, start_idx, possible_separators, date_formats, anchor_enabled, detect_separator, count_separators_before, days, months, tz_matches)
    format_str = get_date_format(extracted, possible_separators, days, months)
    return pattern, extracted, format_str

def refresh_date_field(selected_text, full_text, start_idx, end_idx, date_formats, possible_separators, days, months, anchor_enabled, detect_separator, count_separators_before):
    components = identify_components(selected_text, days, months)
    if not components:
        return "No pattern detected", selected_text, "No format detected"

    base_pattern = build_base_pattern(components, days, months)
    matches = [(m.start(), m.end(), m.group(0)) for m in re.finditer(base_pattern, full_text, re.IGNORECASE)]
    matches.sort(key=lambda x: x[0])

    if not matches:
        return "No pattern detected", selected_text, "No format detected"

    current_idx = min(range(len(matches)), key=lambda i: abs(matches[i][0] - start_idx))
    next_idx = (current_idx + 1) % len(matches)
    new_start_idx, new_end_idx, new_selected_text = matches[next_idx]

    pattern, extracted = get_date_pattern(new_selected_text, full_text, new_start_idx, possible_separators, date_formats, anchor_enabled, detect_separator, count_separators_before, days, months)
    format_str = get_date_format(extracted, possible_separators, days, months)
    return pattern, extracted, format_str

def identify_components(selected_text, days, months):
    cleaned_text = re.sub(r"(?<=\d)(st|nd|rd|th)\b", "", selected_text).strip()
    parts = re.findall(r'\S+', cleaned_text)
    components = []

    for i, part in enumerate(parts):
        part_lower = part.lower()
        if part_lower in [d.lower() for d in days["short"]] or part_lower in [d.lower() for d in days["long"]]:
            continue  # Skip day components from output
        elif part_lower in [m.lower() for m in months["short"]]:
            components.append(("month", part, i, "short"))
        elif part_lower in [m.lower() for m in months["long"]]:
            components.append(("month", part, i, "long"))
        elif re.match(r"^\d{1,2}$", part):
            try:
                if int(part) <= 31:
                    components.append(("date", part, i, None))
            except ValueError:
                pass
        elif re.match(r"^\d{2,4}$", part):
            components.append(("year", part, i, None))

    return sorted(components, key=lambda x: x[2])

def build_base_pattern(components, days, months):
    month_short_pattern = "|".join(months["short"])
    month_long_pattern = "|".join(months["long"])
    date_pattern = r"(\d{1,2})(?:st|nd|rd|th)?"
    year_pattern = r"\d{2,4}"

    pattern_parts = []
    for comp_type, _, _, length in components:
        if comp_type == "month":
            pattern = f"({month_short_pattern})" if length == "short" else f"({month_long_pattern})"
        elif comp_type == "date":
            pattern = date_pattern  # already has outer capture group
        elif comp_type == "year":
            pattern = f"({year_pattern})"
        pattern_parts.append(pattern)

    return r"\s+".join(pattern_parts)

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

def get_date_pattern(selected_text, full_text, start_idx, possible_separators, date_formats, anchor_enabled, detect_separator, count_separators_before, days, months, tz_matches=None):
    cleaned_text = selected_text.strip()
    components = identify_components(cleaned_text, days, months)

    if not components:
        for pattern in date_formats:
            if re.search(fr"^{pattern}$", cleaned_text, re.IGNORECASE):
                base_pattern = pattern
                break
        else:
            base_pattern = r"\d{1,2}[-./]\d{1,2}(?:[-./]\d{2,4})?"
    else:
        base_pattern = build_base_pattern(components, days, months)

    matches = list(re.finditer(base_pattern, full_text, re.IGNORECASE))
    if not matches:
        return "No pattern detected", cleaned_text

    if tz_matches and anchor_enabled:
        best_match = None
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
        if not best_match:
            best_match = matches[0]
    else:
        best_match = matches[0]

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

    # Do not clean suffixes here — they are already excluded from capture
    extracted = extracted.strip()

    return pattern, extracted

def get_date_format(date_str, possible_separators, days, months):
    cleaned_date = re.sub(r"(th|st|nd|rd)", "", date_str.lower()).strip()
    components = identify_components(cleaned_date, days, months)

    if not components:
        parts = re.split(fr"[{''.join(map(re.escape, possible_separators))}]", cleaned_date)
        parts = [p for p in parts if p]
        num_parts = len(parts)
        if num_parts == 2:
            first_part = "d" if len(parts[0].lstrip("0")) == 1 else "dd"
            second_part = "M" if len(parts[1].lstrip("0")) == 1 else "MM"
            return f"{first_part}-{second_part}"
        elif num_parts == 3:
            first_part = "d" if len(parts[0].lstrip("0")) == 1 else "dd"
            second_part = "M" if len(parts[1].lstrip("0")) == 1 else "MM"
            third_part = "yyyy" if len(parts[2]) == 4 else "yy"
            if len(parts[2]) == 4:
                return f"{first_part}-{second_part}-{third_part}"
            return f"{third_part}-{second_part}-{first_part}"
        return "No format detected"

    format_parts = []
    for comp_type, value, _, length in components:
        if comp_type == "month":
            format_parts.append("MMM" if length == "short" else "MMMM")
        elif comp_type == "date":
            format_parts.append("dd")
        elif comp_type == "year":
            format_parts.append("yyyy" if len(re.search(r"\d{4}", cleaned_date).group()) == 4 else "yy")

    return " ".join(format_parts) if format_parts else "No format detected"

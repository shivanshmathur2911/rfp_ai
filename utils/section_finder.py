def find_section(text: str, start_keywords: list, end_keywords: list) -> str:
    text_lower = text.lower()

    start_idx = -1
    for kw in start_keywords:
        idx = text_lower.find(kw.lower())
        if idx != -1:
            start_idx = idx
            break

    if start_idx == -1:
        return ""

    end_idx = len(text)
    for kw in end_keywords:
        idx = text_lower.find(kw.lower(), start_idx + 1)
        if idx != -1:
            end_idx = idx
            break

    return text[start_idx:end_idx]

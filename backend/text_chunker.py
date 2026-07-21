import re
from chapter_splitter import normalize_text

def chunk_text_by_paragraphs(
    text: str,
    max_chars: int = 8000,
    first_max_chars: int | None = None,
):
    chunk=[]
    input_text=normalize_text(text).split("\n\n")
    current_part=""

    for t in input_text:
        t = t.strip()
        if not t:
            continue
        if not current_part:
            current_part=t
        else:
            candidate=current_part + "\n\n" + t
            current_limit = (
                first_max_chars
                if first_max_chars is not None and not chunk
                else max_chars
            )
            if current_part and len(candidate) > current_limit:
                chunk.append(current_part)
                current_part=t
            else:
                current_part=candidate
    if current_part:
        chunk.append(current_part)
    return chunk


STOP_WORDS = {
    "this", "that", "with", "from", "have", "they", "their",
    "were", "been", "into", "about", "would", "could", "should",
    "watson", "holmes",
}


def scene_keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z']+", text.lower())

    return {
        word
        for word in words
        if len(word) >= 4 and word not in STOP_WORDS
    }


def retrieve_scene_source(
    source_chunks: list[str],
    known_context: str,
    locked_clue_content: list[str],
    max_paragraphs: int = 5,
) -> str:
    allowed_text = "\n".join(
        [known_context, *locked_clue_content]
    )
    query_words = scene_keywords(allowed_text)

    paragraphs = [
        paragraph.strip()
        for chunk in source_chunks
        for paragraph in chunk.split("\n\n")
        if paragraph.strip()
    ]

    ranked = []

    for paragraph_index, paragraph in enumerate(paragraphs):
        overlap = len(query_words & scene_keywords(paragraph))

        if overlap >= 2:
            ranked.append((overlap, paragraph_index, paragraph))

    ranked.sort(key=lambda item: (-item[0], item[1]))

    selected = sorted(
        ranked[:max_paragraphs],
        key=lambda item: item[1],
    )

    return "\n\n".join(
        paragraph
        for _, _, paragraph in selected
    )
    

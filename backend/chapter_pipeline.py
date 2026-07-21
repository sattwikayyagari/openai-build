from database import (
    delete_playable_scenes_after,
    get_chapter_details,
    save_playable_scene,
    save_scene_bible,
)
from scene_builder import build_playable_scene_from_plan
from scene_generator import (
    generate_chapter_storyboard,
    generate_chunk_summary,
    generate_scene_bible_from_summaries,
    generate_scene_plan,
)
from schemas import SceneBible, Setting
from text_chunker import chunk_text_by_paragraphs


def generate_playable_chapter(chapter_id: str) -> dict:
    chapter = get_chapter_details(chapter_id)
    if chapter is None:
        raise ValueError("Chapter not found.")

    _, _, _, title, chapter_content = chapter
    # A broad first chunk can contain both the chapter's opening and a later
    # journey or discovery. Smaller chronological chunks keep scene 1 anchored
    # to the actual opening moment.
    chunks = chunk_text_by_paragraphs(
        chapter_content,
        max_chars=4000,
        # Keep the inciting moment separate from later travel or investigation.
        first_max_chars=1200,
    )
    if not chunks:
        raise ValueError("Chapter contains no usable text.")

    provisional_bible = SceneBible(
        chapter_id=chapter_id,
        summary="Source text awaiting chapter analysis.",
        setting=Setting(location="Unspecified", time_context="Unspecified", mood="Unspecified"),
        characters=[],
        clues=[],
        story_beats=[],
        guardrails=["Do not invent facts not present in the supplied source."],
    )
    chunk_summaries = [
        generate_chunk_summary(chunk, chunk_index, provisional_bible)
        for chunk_index, chunk in enumerate(chunks, start=1)
    ]

    scene_bible = generate_scene_bible_from_summaries(chapter_id, chunk_summaries)
    save_scene_bible(scene_bible)
    storyboard = generate_chapter_storyboard(chunk_summaries, scene_bible)

    saved_scenes = []
    for storyboard_scene in storyboard.scenes:
        locked_facts = "\n".join(storyboard_scene.locked_clue_content)
        scene_input = f"""
KNOWN CONTEXT:
{storyboard_scene.known_context}

FACTS THE PLAYER LEARNS ONLY BY INVESTIGATING:
{locked_facts}

FINAL REVEAL:
{storyboard_scene.is_final_reveal}
""".strip()
        plan = generate_scene_plan(
            chapter_excerpt=scene_input,
            scene_bible=scene_bible,
            position=storyboard_scene.position,
            known_context=storyboard_scene.known_context,
            locked_clue_content=storyboard_scene.locked_clue_content,
        )
        playable_scene = build_playable_scene_from_plan(plan)
        save_playable_scene(playable_scene)
        saved_scenes.append(playable_scene)

    delete_playable_scenes_after(chapter_id, len(saved_scenes))
    return {
        "chapter_id": chapter_id,
        "title": title,
        "scene_count": len(saved_scenes),
    }

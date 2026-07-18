from database import save_scene_progress, get_scene_progress
from schemas import SceneProgress
from uuid import uuid4

scene_progress_data = {
    "playthrough_id": "a7e57338-4ddc-4b72-a64a-7ef22b617c01",
    "chapter_id": "fbc2c27a-5ce5-4c50-bc70-aa117416aa1c",
    "intro_seen": True,
    "current_scene_position": 1,
    "chapter_complete": False,
    "completed_scene_ids": [],
    "examined_entity_ids": ["dartmoor-telegram"],
}

validated_progress=SceneProgress(**scene_progress_data)
save_scene_progress(validated_progress)
print(validated_progress)
returned_progress=get_scene_progress(scene_progress_data["playthrough_id"],scene_progress_data["chapter_id"])
print(returned_progress.examined_entity_ids)
print(returned_progress.chapter_complete)
print(returned_progress.intro_seen)
print(returned_progress.current_scene_position)
print(returned_progress.completed_scene_ids)
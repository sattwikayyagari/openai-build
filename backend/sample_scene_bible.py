from schemas import SceneBible
from database import save_scene_bible, get_scene_bible

silver_blaze_scene_bible = {
    "chapter_id": "fbc2c27a-5ce5-4c50-bc70-aa117416aa1c",
    "summary": (
        "At breakfast in Baker Street, Holmes tells Watson that the celebrated "
        "racehorse Silver Blaze has vanished and its trainer, John Straker, has "
        "been found dead. A telegram summons Holmes to Dartmoor, and Watson "
        "prepares to join him."
    ),
    "setting": {
        "location": "221B Baker Street, London",
        "time_context": "Early morning, before Holmes and Watson depart for Dartmoor",
        "mood": "Warm, alert, and quietly urgent",
    },
    "characters": [
        {
            "name": "Sherlock Holmes",
            "role_in_chapter": "Investigator preparing to take the case",
            "description": (
                "A composed detective who treats the troubling news as a puzzle "
                "and quickly focuses on the journey ahead."
            ),
        },
        {
            "name": "Dr. Watson",
            "role_in_chapter": "Narrator and companion",
            "description": (
                "Holmes's observant friend, surprised by the sudden trip but ready "
                "to accompany him."
            ),
        },
    ],
    "clues": [
        "Silver Blaze, a famous racehorse, has disappeared.",
        "John Straker, the horse's trainer, has been found dead.",
        "A telegram has summoned Holmes to King's Pyland on Dartmoor.",
    ],
    "story_beats": [
        {
            "order": 1,
            "summary": "Holmes announces that he must leave Baker Street immediately.",
        },
        {
            "order": 2,
            "summary": "Watson learns that the destination is King's Pyland on Dartmoor.",
        },
        {
            "order": 3,
            "summary": "Holmes explains that Silver Blaze is missing and John Straker is dead.",
        },
        {
            "order": 4,
            "summary": "Watson decides to travel with Holmes and the investigation begins.",
        },
    ],
    "guardrails": [
        "Do not reveal the solution, culprit, or final fate of Silver Blaze.",
        "Keep the scene in Baker Street before the journey to Dartmoor.",
        "Preserve Holmes and Watson as observant collaborators from the public-domain source.",
    ],
}

validated_scene_bible=SceneBible(**silver_blaze_scene_bible)
save_scene_bible(validated_scene_bible)
# print(validated_scene_bible)
# print("Successfully saved the scene")
scene_output=get_scene_bible(validated_scene_bible.chapter_id)
print(scene_output)
print(scene_output.setting.location)
print(scene_output.characters[0].name)

scene_output1=get_scene_bible("fbc2c27a-5ce5-4c50-bc70-aa117416aa1casdasdjnf")
print(scene_output1)
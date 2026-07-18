from schemas import PlayableScene
from database import save_playable_scene, get_playable_scene, get_playable_scenes

baker_street_playable_scene = {
    "chapter_id": "fbc2c27a-5ce5-4c50-bc70-aa117416aa1c",
    "scene_id": "silver-blaze-baker-street",
    "position": 1,
    "title": "Silver Blaze",
    "objective": "Examine Holmes's telegram before leaving for Dartmoor.",
    "width": 640,
    "height": 360,
    "walkable_area": {
        "x": 0,
        "y": 190,
        "width": 640,
        "height": 170,
    },
    "completion_entity_id": "dartmoor-telegram",
    "player": {
        "x": 294,
        "y": 264,
        "width": 18,
        "height": 24,
        "speed": 142,
    },
    "entities": [
        {
            "id": "baker-street-window",
            "type": "window",
            "x": 64,
            "y": 47,
            "width": 82,
            "height": 96,
            "solid": True,
        },
        {
            "id": "portrait",
            "type": "portrait",
            "x": 491,
            "y": 40,
            "width": 48,
            "height": 65,
            "solid": True,
        },
        {
            "id": "flat-door",
            "type": "door",
            "x": 560,
            "y": 128,
            "width": 58,
            "height": 151,
            "solid": True,
            "interaction": {
                "label": "the flat door",
                "speaker": "Narrator",
                "text": "Beyond it, the stairs wait. Dartmoor feels very far from Baker Street.",
                "status": "The journey to Dartmoor cannot wait.",
            },
        },
        {
            "id": "writing-desk",
            "type": "solid",
            "x": 193,
            "y": 135,
            "width": 205,
            "height": 57,
            "solid": True,
        },
        {
            "id": "desk-lamp",
            "type": "lamp",
            "x": 353,
            "y": 118,
            "width": 17,
            "height": 29,
            "solid": False,
            "interaction": {
                "label": "the lamp",
                "speaker": "Narrator",
                "text": "Its amber light makes the telegram's urgent message easier to read.",
                "status": "The lamp burns steadily.",
            },
        },
        {
            "id": "dartmoor-telegram",
            "type": "letter",
            "x": 278,
            "y": 145,
            "width": 28,
            "height": 19,
            "solid": False,
            "interaction": {
                "label": "the telegram",
                "speaker": "Sherlock Holmes",
                "text": (
                    "A wire from Colonel Ross. Silver Blaze is missing, "
                    "and his trainer lies dead at King's Pyland."
                ),
                "status": "You have examined the Dartmoor telegram.",
            },
        },
        {
            "id": "central-rug",
            "type": "rug",
            "x": 151,
            "y": 213,
            "width": 292,
            "height": 91,
            "solid": False,
        },
        {
            "id": "left-side-table",
            "type": "solid",
            "x": 18,
            "y": 266,
            "width": 110,
            "height": 53,
            "solid": True,
        },
        {
            "id": "right-side-table",
            "type": "solid",
            "x": 443,
            "y": 276,
            "width": 126,
            "height": 43,
            "solid": True,
        },
    ],
}
king_pylans_stable_scene = {
    "chapter_id": "fbc2c27a-5ce5-4c50-bc70-aa117416aa1c",
    "scene_id": "silver-blaze-kings-pyland-stable",
    "position": 2,
    "title": "The Silent Stable",
    "objective": "Search the stable for the detail everyone else overlooked.",
    "width": 640,
    "height": 360,
    "walkable_area": {"x": 0, "y": 190, "width": 640, "height": 170},
    "completion_entity_id": "silent-dog-clue",
    "player": {"x": 292, "y": 262, "width": 18, "height": 24, "speed": 142},
    "entities": [
        {"id": "stable-window", "type": "window", "x": 62, "y": 46, "width": 86, "height": 95, "solid": True},
        {"id": "silver-blaze-stall", "type": "solid", "x": 205, "y": 78, "width": 222, "height": 104, "solid": True},
        {
            "id": "silent-dog-clue", "type": "letter", "x": 282, "y": 172, "width": 32, "height": 15, "solid": False,
            "interaction": {
                "label": "the quiet stable",
                "speaker": "Sherlock Holmes",
                "text": "The dog made no sound. It knew the person who entered the stable.",
                "status": "You have noticed the silent dog clue.",
            },
        },
        {
            "id": "stable-lantern", "type": "lamp", "x": 455, "y": 122, "width": 18, "height": 28, "solid": False,
            "interaction": {
                "label": "the lantern",
                "speaker": "Dr. Watson",
                "text": "Its light reaches the stall, but not the answer hidden in it.",
                "status": "The stable lantern burns low.",
            },
        },
        {"id": "stable-door", "type": "door", "x": 556, "y": 121, "width": 58, "height": 151, "solid": True},
        {"id": "hay-bale-left", "type": "solid", "x": 22, "y": 266, "width": 110, "height": 53, "solid": True},
        {"id": "hay-bale-right", "type": "solid", "x": 442, "y": 272, "width": 122, "height": 47, "solid": True},
    ],
}
dartmoor_moor_scene = {
    "chapter_id": "fbc2c27a-5ce5-4c50-bc70-aa117416aa1c",
    "scene_id": "silver-blaze-dartmoor-moor",
    "position": 3,
    "title": "Across the Moor",
    "objective": "Follow the trail that leads away from the obvious answer.",
    "width": 640,
    "height": 360,
    "walkable_area": {"x": 0, "y": 190, "width": 640, "height": 170},
    "completion_entity_id": "moor-hoofprints",
    "player": {"x": 294, "y": 264, "width": 18, "height": 24, "speed": 142},
    "entities": [
        {"id": "moor-cottage", "type": "solid", "x": 56, "y": 75, "width": 142, "height": 108, "solid": True},
        {"id": "moor-window", "type": "window", "x": 96, "y": 108, "width": 44, "height": 46, "solid": True},
        {
            "id": "moor-hoofprints", "type": "letter", "x": 280, "y": 174, "width": 68, "height": 15, "solid": False,
            "interaction": {
                "label": "the hoofprints",
                "speaker": "Sherlock Holmes",
                "text": "They do not lead simply away. The trail turns with purpose across the wet ground.",
                "status": "You have followed the hoofprints.",
            },
        },
        {
            "id": "moor-candle-stub", "type": "lamp", "x": 463, "y": 160, "width": 16, "height": 23, "solid": False,
            "interaction": {
                "label": "the candle stub",
                "speaker": "Dr. Watson",
                "text": "A small object, easily overlooked, but strange enough to matter.",
                "status": "You have noted an unusual object on the moor.",
            },
        },
        {"id": "moor-rock-left", "type": "solid", "x": 34, "y": 270, "width": 112, "height": 45, "solid": True},
        {"id": "moor-rock-right", "type": "solid", "x": 461, "y": 272, "width": 115, "height": 43, "solid": True},
    ],
}
racecourse_reveal_scene = {
    "chapter_id": "fbc2c27a-5ce5-4c50-bc70-aa117416aa1c",
    "scene_id": "silver-blaze-racecourse-reveal",
    "position": 4,
    "title": "The Case Resolved",
    "objective": "Hear Holmes connect the final clues.",
    "width": 640,
    "height": 360,
    "walkable_area": {"x": 0, "y": 190, "width": 640, "height": 170},
    "completion_entity_id": "holmes-conclusion",
    "player": {"x": 294, "y": 264, "width": 18, "height": 24, "speed": 142},
    "entities": [
        {"id": "racecourse-stand", "type": "solid", "x": 86, "y": 69, "width": 470, "height": 113, "solid": True},
        {"id": "racecourse-window-left", "type": "window", "x": 132, "y": 104, "width": 66, "height": 49, "solid": True},
        {"id": "racecourse-window-right", "type": "window", "x": 429, "y": 104, "width": 66, "height": 49, "solid": True},
        {
            "id": "holmes-conclusion", "type": "letter", "x": 286, "y": 172, "width": 36, "height": 16, "solid": False,
            "interaction": {
                "label": "Holmes's conclusion",
                "speaker": "Sherlock Holmes",
                "text": "The silent dog, the trail, and the strange object tell one story. Silver Blaze is safe, and the case is clear.",
                "status": "The case of Silver Blaze is solved.",
            },
        },
        {
            "id": "colonel-ross-note", "type": "letter", "x": 484, "y": 175, "width": 30, "height": 16, "solid": False,
            "interaction": {
                "label": "Colonel Ross's note",
                "speaker": "Narrator",
                "text": "Relief has replaced suspicion. The racehorse will be returned.",
                "status": "You have read Colonel Ross's note.",
            },
        },
        {"id": "racecourse-rug", "type": "rug", "x": 154, "y": 217, "width": 292, "height": 88, "solid": False},
        {"id": "racecourse-door", "type": "door", "x": 555, "y": 126, "width": 58, "height": 147, "solid": True},
    ],
}
playable_scene_output=PlayableScene(**baker_street_playable_scene)
save_playable_scene(playable_scene_output)
playable_scene_output=PlayableScene(**king_pylans_stable_scene )
save_playable_scene(playable_scene_output)
playable_scene_output=PlayableScene(**dartmoor_moor_scene )
save_playable_scene(playable_scene_output)
playable_scene_output=PlayableScene(**racecourse_reveal_scene  )
save_playable_scene(playable_scene_output)

output=get_playable_scenes("fbc2c27a-5ce5-4c50-bc70-aa117416aa1c")
print(len(output))
for i in output:
    print(i.title)
    print(i.position)
    print(i.scene_id)
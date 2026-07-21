from schemas import Deduction,DeductionOption,SpawnPoint,Inspection,Interaction,NarrativeBeat,PlayableScene,Player,SceneEntity,ScenePlan,WalkableArea

def build_playable_scene_from_plan(plan:ScenePlan)->PlayableScene:
    player = Player(
        x=294,
        y=264,
        width=18,
        height=24,
        speed=142,
    )
    walkable_area = WalkableArea(
        x=0,
        y=190,
        width=640,
        height=170,
    )
    opening_beats = [
    NarrativeBeat(
        id=beat.id,
        kind=beat.kind,
        speaker=beat.speaker or None,
        text=beat.text,
    )
    for beat in plan.opening_beats
    ]
    closing_beats = [
        NarrativeBeat(
            id=beat.id,
            kind=beat.kind,
            speaker=beat.speaker or None,
            text=beat.text,
        )
        for beat in plan.closing_beats
    ]
    if plan.layout_preset == "compact_interior":
        base_entities=[
            SceneEntity(
                id="room-window",
                type="window",
                x=64,
                y=47,
                width=82,
                height=96,
                solid=True,
                interaction=None,
                spawn_points=[]
            ),
            SceneEntity(
                id="writing-desk",
                type="solid",
                x=193,
                y=135,
                width=205,
                height=57,
                solid=True,
                interaction=None,
                spawn_points=[],
            ),
            SceneEntity(
                id="flat-door",
                type="door",
                x=560,
                y=128,
                width=58,
                height=151,
                solid=True,
                interaction=None,
                spawn_points=[],
            ),
            SceneEntity(
                id="central-rug",
                type="rug",
                x=151,
                y=213,
                width=292,
                height=91,
                solid=False,
                interaction=None,
                spawn_points=[],
            ),
            SceneEntity(
                id="desk-lamp",
                type="lamp",
                x=353,
                y=118,
                width=17,
                height=29,
                solid=False,
                interaction=None,
                spawn_points=[],
            ),
            SceneEntity(
                id="left-side-table",
                type="solid",
                x=18,
                y=266,
                width=110,
                height=53,
                solid=True,
                interaction=None,
                spawn_points=[],
            ),
            SceneEntity(
                id="right-side-table",
                type="solid",
                x=443,
                y=276,
                width=126,
                height=43,
                solid=True,
                interaction=None,
                spawn_points=[],
            ),
            ]
    elif plan.layout_preset == "long_interior":
        base_entities = [
            SceneEntity(
                id="left-window",
                type="window",
                x=58, y=48, width=82, height=96,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="right-window",
                type="window",
                x=500, y=48, width=82, height=96,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="upper-shelf",
                type="solid",
                x=205, y=118, width=230, height=38,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="left-bench",
                type="solid",
                x=18, y=280, width=120, height=39,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="right-bench",
                type="solid",
                x=502, y=280, width=120, height=39,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="runner",
                type="rug",
                x=155, y=213, width=290, height=91,
                solid=False, interaction=None, spawn_points=[],
            ),
        ]

    elif plan.layout_preset == "open_floor":
        base_entities = [
            SceneEntity(
                id="far-window-left",
                type="window",
                x=52, y=52, width=72, height=82,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="far-window-right",
                type="window",
                x=516, y=52, width=72, height=82,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="far-landmark",
                type="portrait",
                x=291, y=60, width=56, height=72,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="left-low-object",
                type="solid",
                x=18, y=284, width=106, height=35,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="right-low-object",
                type="solid",
                x=516, y=284, width=106, height=35,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="open-ground",
                type="rug",
                x=146, y=218, width=348, height=82,
                solid=False, interaction=None, spawn_points=[],
            ),
        ]

    else:  # threshold
        base_entities = [
            SceneEntity(
                id="arrival-door",
                type="door",
                x=526, y=113, width=72, height=166,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="arrival-window",
                type="window",
                x=58, y=52, width=82, height=94,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="arrival-desk",
                type="solid",
                x=230, y=132, width=170, height=55,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="arrival-lamp",
                type="lamp",
                x=365, y=104, width=17, height=29,
                solid=False, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="left-arrival-object",
                type="solid",
                x=18, y=278, width=112, height=41,
                solid=True, interaction=None, spawn_points=[],
            ),
            SceneEntity(
                id="arrival-rug",
                type="rug",
                x=150, y=213, width=290, height=91,
                solid=False, interaction=None, spawn_points=[],
            ),
        ]
    clue_spawn_groups = [
        [
            SpawnPoint(x=158, y=236),
            SpawnPoint(x=205, y=236),
            SpawnPoint(x=158, y=274),
        ],
        [
            SpawnPoint(x=390, y=236),
            SpawnPoint(x=390, y=274),
            SpawnPoint(x=435, y=236),
        ],
        [
            SpawnPoint(x=496, y=208),
            SpawnPoint(x=496, y=250),
            SpawnPoint(x=450, y=208),
        ],
    ]

    clue_entities = []

    for index, clue in enumerate(plan.clues[:3]):
        scene_clue_id = f"scene-{plan.position}-{clue.id}"
        entity_type = clue.evidence_type

        clue_entity = SceneEntity(
            id=scene_clue_id,
            type=entity_type,
            x=clue_spawn_groups[index][0].x,
            y=clue_spawn_groups[index][0].y,
            width=38,
            height=24,
            solid=False,
            interaction=Interaction(
                label={
                    "letter": "the letter",
                    "newspaper": "the newspaper",
                    "note": "the note",
                    "map": "the map",
                    "evidence": "the evidence",
                }.get(clue.evidence_type, "the evidence"),
                speaker="Dr. Watson",
                text=clue.paragraphs[0],
                status=f"You have examined {clue.label.lower()}.",
                inspection=Inspection(
                    visual_type=clue.evidence_type,
                    title=clue.title,
                    subtitle=None,
                    paragraphs=clue.paragraphs,
                ),
            ),
            spawn_points=clue_spawn_groups[index],
        )

        clue_entities.append(clue_entity)
        opening_beats = [
    NarrativeBeat(
        id=beat.id,
        kind=beat.kind,
        text=beat.text,
        speaker=beat.speaker or None,
    )
    for beat in plan.opening_beats
    ]

    closing_beats = [
        NarrativeBeat(
            id=beat.id,
            kind=beat.kind,
            text=beat.text,
            speaker=beat.speaker or None,
        )
        for beat in plan.closing_beats
    ]

    deduction = Deduction(
        prompt=plan.deduction_prompt,
        options=[
            DeductionOption(
                id=f"scene-{plan.position}-{option.id}",
                label=option.label,
                response=option.response,
                score=option.score,
            )
            for option in plan.deduction_options
        ],
    )
    return PlayableScene(
        chapter_id=plan.chapter_id,
        scene_id=f"{plan.chapter_id}-scene-{plan.position}",
        position=plan.position,
        title=plan.title,
        objective=plan.objective,
        width=640,
        height=360,
        player=player,
        entities=base_entities + clue_entities,
        walkable_area=walkable_area,
        opening_beats=opening_beats,
        required_entity_ids=[f"scene-{plan.position}-{clue.id}" for clue in plan.clues[:3]],
        deduction=deduction,
        closing_beats=closing_beats,
        visual_theme=plan.visual_theme,
        layout_preset=plan.layout_preset
    )

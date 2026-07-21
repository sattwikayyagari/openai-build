from pydantic import BaseModel, Field, ConfigDict
from typing import List, Literal

class StrictScenePlanModel(BaseModel):
    model_config=ConfigDict(extra="forbid")

class PlannedBeat(StrictScenePlanModel):
    id: str
    kind: Literal['narration', 'dialogue','thought']
    speaker: str
    text: str

class PlannedClue(StrictScenePlanModel):
    id: str
    evidence_type: Literal[
        "newspaper",
        "letter",
        "note",
        "map",
        "evidence"]
    label: str
    title: str
    paragraphs: list[str]

class PlannedDeductionOption(StrictScenePlanModel):
    id: str
    label: str
    response: str
    score: int


class ScenePlan(StrictScenePlanModel):
    chapter_id: str
    position: int
    title: str
    objective: str
    visual_theme: Literal[
        "warm-morning",
        "overcast-afternoon",
        "rain-dusk",
        "foggy-moor",
        "race-day",
    ]
    opening_beats: list[PlannedBeat]
    clues: list[PlannedClue]
    deduction_prompt: str
    deduction_options: list[PlannedDeductionOption]
    closing_beats: list[PlannedBeat]
    layout_preset: Literal[
        "compact_interior",
        "long_interior",
        "open_floor",
        "threshold",
    ]
class StoryboardScene(BaseModel):
    position: int
    known_context: str
    source_chunk_indices: List[int]
    locked_clue_content: List[str]
    is_final_reveal: bool = False

class ScenePlanReview(BaseModel):
    approved: bool
    issues: List[str] = Field(default_factory=list)

class ChapterStoryboard(BaseModel):
    chapter_id: str
    scenes: List[StoryboardScene]

class Character(BaseModel):
    name: str
    role_in_chapter: str
    description: str

class Setting(BaseModel):
    location: str
    time_context: str
    mood: str

class StoryBeat(BaseModel):
    order: int
    summary: str

class ChunkSummary(BaseModel):
    chunk_index: int
    summary: str
    key_events: List[str]=Field(min_length=3, max_length=6)
    clues: List[str] =Field(max_length=5)

class SceneBible(BaseModel):
    chapter_id: str
    summary: str
    setting: Setting
    characters: List[Character]
    clues: List[str]
    story_beats:List[StoryBeat]
    guardrails: List[str]

class Player(BaseModel):
    x: int
    y: int
    width: int
    height: int
    speed: int

class Inspection(BaseModel):
    visual_type: str
    title: str
    subtitle: str|None=None
    paragraphs: List[str]

class Interaction(BaseModel):
    label: str
    speaker: str
    text: str
    status: str
    inspection: Inspection|None=None

class SpawnPoint(BaseModel):
    x: int
    y: int


class SceneEntity(BaseModel):
    id: str
    type: str
    x: int
    y: int
    width: int
    height: int
    solid: bool=False
    interaction: Interaction | None = None
    spawn_points: List[SpawnPoint] = Field(default_factory=list)

class WalkableArea(BaseModel):
    x:int
    y:int
    height:int
    width: int

class NarrativeBeat(BaseModel):
    id: str
    kind:str
    text: str
    speaker: str|None=None

class DeductionOption(BaseModel):
    id: str
    label: str
    response:str
    score: int

class Deduction(BaseModel):
    prompt: str
    options: List[DeductionOption]

class SceneGenerationRequest(BaseModel):
    chapter_excerpt: str
    position: int

class PlayableScene(BaseModel):
    chapter_id: str
    scene_id: str
    position: int
    title: str
    objective: str
    width: int
    height: int
    player: Player
    entities: List[SceneEntity]
    walkable_area: WalkableArea
    opening_beats: List[NarrativeBeat]
    required_entity_ids:List[str]
    deduction: Deduction
    closing_beats: List[NarrativeBeat]
    visual_theme: str="warm-morning"
    layout_preset: Literal[
        "compact_interior",
        "long_interior",
        "open_floor",
        "threshold",
    ]

class SceneProgress(BaseModel):
    playthrough_id: str
    chapter_id:str
    intro_seen: bool=False
    current_scene_position: int = 1
    chapter_complete: bool = False
    completed_scene_ids: List[str]=Field(default_factory=list)
    examined_entity_ids: List[str]=Field(default_factory=list)
    scene_phase: str="opening"
    current_beat_index: int=0
    selected_choice_ids: List[str]=Field(default_factory=list)
    deduction_score: int=0
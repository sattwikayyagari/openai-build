from pydantic import BaseModel, Field
from typing import List

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

class Interaction(BaseModel):
    label: str
    speaker: str
    text: str
    status: str

class SceneEntity(BaseModel):
    id: str
    type: str
    x: int
    y: int
    width: int
    height: int
    solid: bool=False
    interaction: Interaction | None = None

class WalkableArea(BaseModel):
    x:int
    y:int
    height:int
    width: int

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
    completion_entity_id: str

class SceneProgress(BaseModel):
    playthrough_id: str
    chapter_id:str
    intro_seen: bool=False
    current_scene_position: int = 1
    chapter_complete: bool = False
    completed_scene_ids: List[str]=Field(default_factory=list)
    examined_entity_ids: List[str]=Field(default_factory=list)

import os
from dotenv import load_dotenv
from groq import Groq
from schemas import PlayableScene,SceneBible,ScenePlan, StoryboardScene, ChapterStoryboard, ChunkSummary,ScenePlanReview
from typing import List
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from groq import Groq, BadRequestError
from pydantic import ValidationError
load_dotenv(Path(__file__).resolve().parent / ".env")

GENERATION_MODEL = os.getenv("GENERATION_MODEL", "llama-3.3-70b-versatile")
REVIEW_MODEL = os.getenv("REVIEW_MODEL", "llama-3.1-8b-instant")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_GENERATION_MODEL = os.getenv(
    "ANTHROPIC_GENERATION_MODEL",
    "claude-sonnet-4-20250514",
)
ANTHROPIC_REVIEW_MODEL = os.getenv(
    "ANTHROPIC_REVIEW_MODEL",
    "claude-3-5-haiku-20241022",
)

def get_groq_client():
    api_key=os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ API key is missing. Add it in .env file")
    client=Groq(api_key=api_key)
    return client


def list_anthropic_models() -> List[str]:
    """Return the model IDs available to the configured Anthropic API key."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is missing. Add it to .env.")
    request = Request(
        "https://api.anthropic.com/v1/models?limit=100",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=30) as result:
            data = json.loads(result.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Anthropic model listing failed: HTTP {error.code}: {detail}"
        ) from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError(f"Anthropic model listing failed: {error}") from error

    return [model["id"] for model in data.get("data", [])]


def generate_json_response(
    messages: List[dict[str, str]],
    model: str,
    max_completion_tokens: int,
    output_schema: dict | None = None,
) -> str:
    """Return JSON text from the configured local Ollama or Groq provider."""
    if LLM_PROVIDER == "ollama":
        payload = json.dumps(
            {
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.2,
                    "num_predict": max_completion_tokens,
                },
            }
        ).encode("utf-8")
        request = Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=300) as result:
                data = json.loads(result.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as error:
            raise RuntimeError(f"Ollama request failed: {error}") from error

        response = data.get("message", {}).get("content")
        if not response:
            raise RuntimeError("Ollama returned an empty response.")
        return response

    if LLM_PROVIDER == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is missing. Add it to .env.")

        system_prompt = "\n\n".join(
            message["content"]
            for message in messages
            if message["role"] == "system"
        )
        conversation = [
            {"role": message["role"], "content": message["content"]}
            for message in messages
            if message["role"] != "system"
        ]
        anthropic_model = (
            ANTHROPIC_REVIEW_MODEL
            if model == REVIEW_MODEL
            else ANTHROPIC_GENERATION_MODEL
        )
        payload = json.dumps(
            {
                "model": anthropic_model,
                "max_tokens": max_completion_tokens,
                "temperature": 0.2,
                "system": system_prompt,
                "messages": conversation,
                "tools": [
                    {
                        "name": "return_json",
                        "description": "Return only the requested JSON object.",
                        "input_schema": output_schema or {
                            "type": "object",
                            "additionalProperties": True,
                        },
                    }
                ],
                "tool_choice": {"type": "tool", "name": "return_json"},
            }
        ).encode("utf-8")
        request = Request(
            ANTHROPIC_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=300) as result:
                data = json.loads(result.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Anthropic request failed: HTTP {error.code}: {detail}"
            ) from error
        except (URLError, TimeoutError) as error:
            raise RuntimeError(f"Anthropic request failed: {error}") from error

        tool_block = next(
            (
                block
                for block in data.get("content", [])
                if block.get("type") == "tool_use" and block.get("name") == "return_json"
            ),
            None,
        )
        if tool_block is None:
            raise RuntimeError("Anthropic did not return structured JSON.")
        return json.dumps(tool_block.get("input", {}))

    client = get_groq_client()
    request_args = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "max_completion_tokens": max_completion_tokens,
    }
    if model.startswith("openai/gpt-oss"):
        request_args["reasoning_effort"] = "low"
        request_args["reasoning_format"] = "hidden"
    elif model.startswith("qwen/"):
        request_args["reasoning_effort"] = "none"
        request_args["reasoning_format"] = "hidden"

    response = client.chat.completions.create(**request_args).choices[0].message.content
    if not response:
        raise RuntimeError("Model response could not be generated.")
    return response

def build_scene_bible_messages(
    chapter_id: str,
    chunk_summaries: List[ChunkSummary],
) -> List[dict[str, str]]:
    system_prompt = """
    You are preparing source-grounded metadata for an interactive-fiction chapter.
    Return one JSON object matching the SceneBible schema and no markdown.

    Use only the supplied chunk summaries. Do not invent characters, locations,
    motives, documents, or solutions. Keep the summary concise. The chapter_id
    must exactly match the supplied ID. Guardrails must prevent spoilers until a
    final-reveal scene. Use empty lists rather than inventing unsupported facts.
    """.strip()
    user_prompt = f"""
    CHAPTER ID: {chapter_id}

    CHUNK SUMMARIES:
    {json.dumps([summary.model_dump() for summary in chunk_summaries])}
    """.strip()
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

def generate_scene_bible_from_summaries(
    chapter_id: str,
    chunk_summaries: List[ChunkSummary],
) -> SceneBible:
    response = generate_json_response(
        build_scene_bible_messages(chapter_id, chunk_summaries),
        GENERATION_MODEL,
        1200,
        SceneBible.model_json_schema(),
    )
    scene_bible_data = parse_model_json(response)

    # A chapter can legitimately have no explicit global clues or beats. Claude
    # occasionally omits empty collection fields despite the tool schema, so
    # supply source-grounded fallbacks before validating the Bible.
    scene_bible_data.setdefault(
        "clues",
        [
            clue
            for chunk_summary in chunk_summaries
            for clue in chunk_summary.clues
        ],
    )
    # Characters may be absent in a chapter with no named cast, and some
    # providers omit the key instead of returning the required empty list.
    scene_bible_data.setdefault("characters", [])
    scene_bible_data.setdefault(
        "story_beats",
        [
            {"order": index, "summary": chunk_summary.summary}
            for index, chunk_summary in enumerate(chunk_summaries, start=1)
        ],
    )
    scene_bible_data.setdefault(
        "guardrails",
        ["Do not invent facts not present in the supplied source."],
    )

    # The chapter ID is database-owned metadata, not a model decision. Preserve
    # the uploaded chapter's ID even if the model echoes a UUID from an example.
    scene_bible_data["chapter_id"] = chapter_id
    return SceneBible.model_validate(scene_bible_data)

def parse_model_json(response: str) -> dict:
    cleaned_response = response.strip()

    start = cleaned_response.find("{")
    end = cleaned_response.rfind("}")

    if start == -1 or end == -1:
        raise RuntimeError(
            f"Model did not return a JSON object. Response: {cleaned_response[:300]}"
        )

    return json.loads(cleaned_response[start : end + 1])

def build_scene_messages(chapter_excerpt:str, scene_bible: SceneBible, position: int)->List[dict[str,str]]:
    system_prompt=f"""You are a source-faithful interactive-fiction game designer. You should take the given story excerpt and convert it into a factual representation that can further be used to generate a playable scene. Remember not to give away any spoilers or final solutions unless specified the scene is final reveal. The dimensions of the scene are 640X360.Use one of our themes 'warm-morning','overcast-afternoon','rain-dusk','foggy-moor','race-day' for generating the scene. Also give the clues random valid spawn_points that do not coincide with any other object. Write crisp, concise narration and dialogue that does not deviate from the theme of the book but also do not just copy and paste the book. Return JSON only matching the Playable Scene schema. Do not add markdown or commentary.Make sure the chapter_id of the output matches the scene bible's chapter_id. Also make sure the output's position must match the position argument
        Include every required top-level field. Do not replace nested objects with strings.
        For an entity interaction, use either null or an Interaction object matching the schema.
        
        RESPONSE SHAPE:
        Return one JSON object with every PlayableScene field:
        chapter_id, scene_id, position, title, objective, width, height,
        player, entities, walkable_area, opening_beats, required_entity_ids,
        deduction, closing_beats, and visual_theme.

        Every entity must include:
        id, type, x, y, width, height, solid, interaction, and spawn_points.

        Every deduction must include:
        prompt and options. Each option needs id, label, response, and score.
        DEDUCTION CONTRACT:

        ENGINE CONTRACT — FOLLOW EXACTLY:

        The player is Dr. Watson. Never create Watson as an entity.

        Set player values exactly:
        x: 294
        y: 264
        width: 18
        height: 24
        speed: 142

        Set walkable_area exactly:
        x: 0
        y: 190
        width: 640
        height: 170

        Use only these entity types:
        window, portrait, door, solid, lamp, newspaper, bowl, rug, kennel.

        Do not use entity types such as character, object, clue, NPC, or item.

        Every required_entity_id must:
        - match the id of an entity in entities;
        - refer to a non-solid entity;
        - include an interaction;
        - include an inspection object with visual_type, title, optional subtitle, and paragraphs;
        - have at least three distinct valid spawn_points.

        Spawn points must be inside the walkable area and must not overlap any solid entity. Required clues must not start directly beside the player's starting position.

        Use only these NarrativeBeat kinds:
        narration, dialogue, thought.

        Use a unique kebab-case scene_id. Create 3 to 5 opening beats and 2 to 4 closing beats. Do not reveal the final solution unless the supplied scene is explicitly a final reveal.     
        Your final JSON must include required_entity_ids, deduction, and closing_beats. Never omit them.
        Return strict RFC 8259 JSON. Use double quotes for all JSON strings. Never escape an apostrophe with a backslash: write King's or King's, never King\'s.
        JSON ENCODING RULE:
        Never output a backslash character.
        Use double quotes for JSON strings.
        Never escape apostrophes.
        Avoid ASCII apostrophes entirely: use the typographic apostrophe (') or rephrase the sentence.
        HARD GEOMETRY REQUIREMENT:
        Before returning JSON, verify that the player's starting rectangle does not overlap any solid entity.
        For every required clue spawn point, verify that the clue rectangle is fully inside walkable_area and does not overlap any solid entity.
        If either condition fails, revise the coordinates before returning JSON.
        EVIDENCE VS ENVIRONMENT:
        Required clues must be direct evidence from SceneBible.clues or the supplied chapter excerpt. Never infer evidence from room decoration.

        Only direct evidence may appear in required_entity_ids or unlock deduction.
        Portraits, windows, lamps, doors, rugs, kennels, and generic furniture are environmental props. They must never be required clues and must not have inspection content.

        Environmental props may be non-interactive, or have a short optional interaction without inspection content. They must not affect scene completion or deduction.

        Use one to three required clues, depending on how many distinct source-grounded facts the excerpt provides.
        INSPECTION CONTENT RULES:
        Set inspection.visual_type to the actual evidence format: newspaper, letter, note, map, or evidence. Never use "image" for written evidence.

        Each required clue inspection must contain 2 to 3 concise paragraphs with distinct, source-grounded facts that help Watson make the scene's deduction.

        Do not invent named newspapers, headlines, or factual claims not supported by the excerpt or SceneBible.
        Use the inspection to reveal evidence, not merely repeat that Holmes plans to travel.
        EXACT PLAYABLESCENE JSON SCHEMA:

        {json.dumps(PlayableScene.model_json_schema(), indent=2)}
    """
    user_prompt=f"""
        Create scene position: {position}.

        SCENE BIBLE: {scene_bible.model_dump_json()}

        CHAPTER EXCERPT: 
        {chapter_excerpt}"""
    return [
        {
            "role":"system",
            "content": system_prompt
         },
         {
             "role": "user",
             "content": user_prompt
         }
         ]
def build_scene_review_messages(
    scene_plan: ScenePlan,
    known_context: str,
    locked_clue_content: List[str],
) -> List[dict[str, str]]:
    system_prompt = """
    You are a strict source-grounding reviewer for an interactive-fiction scene.

    All deduction options, including incorrect options, must be grounded in the
    allowed scene information. Reject unrelated characters, invented events, and
    joke distractors.

    Every generated clue must directly communicate at least one fact from LOCKED
    FACTS. Reject decorative props, invented belongings, and actions that do not
    advance the current investigation.

    Reject the plan if it introduces a proper noun absent from KNOWN CONTEXT and
    LOCKED FACTS, creates a clue that does not reveal a LOCKED FACT, or includes a
    deduction option unsupported by the allowed information.

    Return one JSON object only:
    {
    "approved": true or false,
    "issues": ["short explanation"]
    }

    Approve only when the generated scene plan uses facts supported by the allowed
    scene information.

    Apply a literal entailment test to every factual clause. A clause is allowed
    only when it is directly stated by its permitted allowlist; stylistic wording
    may be added, but not factual detail. Reject added delivery details, dates,
    documents, named sources, locations, people, physical props, motives, police
    conclusions, or interpretation. For example, if a locked fact says only that
    a trainer was found dead, reject claims about murder, violence, the body,
    where it was found, a newspaper report, or how the news arrived.

    Opening beats, title, objective, deduction prompt/options, and closing beats
    may use KNOWN CONTEXT only. Clue inspections may use one LOCKED FACT each, but
    must not add surrounding facts. A generic evidence format such as "the note"
    is allowed only as a UI label; its inspection text must still pass the literal
    entailment test.

    Approve a clue title when it exactly repeats its locked fact; the clue label
    may be generic UI wording such as "the evidence" or "the note". Reject a
    clue only when its title or paragraphs add explanatory or atmospheric detail.

    Reject the plan if it:
    - invents a person, location, document, clue, motive, event, or outcome;
    - changes a stated fact, such as treating a missing subject as found, harmed,
    or recovered;
    - reveals a locked fact in the title, objective, opening beats, or closing beats;
    - gives a clue inspection a fact not present in LOCKED FACTS.
    - includes an idle, comic, or deliberately unreasonable deduction option
      that does not represent a plausible response to the current situation.

    Incorrect options must still be serious, plausible responses to the current
    situation. Do not use idle, comic, or deliberately unreasonable options such
    as sleeping, ignoring the event, or abandoning the investigation.

    Do not reject a source-grounded option merely because it is broad. If KNOWN
    CONTEXT states that Holmes must leave, an option such as "Prepare to leave
    with Holmes" is valid even when the destination or motive is not yet known.

    Do not require a deduction option to use a LOCKED FACT. Judge only whether
    the option is supported by the allowed information and fits the current
    scene. Do not invent additional requirements or preferred actions.

    The deduction may refer to facts the player has investigated, but it must not
    change the canonical story outcome.
    """.strip()

    user_prompt = f"""
    KNOWN CONTEXT:
    {known_context}

    LOCKED FACTS:
    {chr(10).join(f"- {fact}" for fact in locked_clue_content)}

    GENERATED SCENE PLAN:
    {scene_plan.model_dump_json()}
    """.strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def review_scene_plan(
    scene_plan: ScenePlan,
    known_context: str,
    locked_clue_content: List[str],
) -> ScenePlanReview:
    messages = build_scene_review_messages(
        scene_plan=scene_plan,
        known_context=known_context,
        locked_clue_content=locked_clue_content,
    )

    response = generate_json_response(
        messages,
        REVIEW_MODEL,
        350,
        ScenePlanReview.model_json_schema(),
    )

    review_data = parse_model_json(response)

    return ScenePlanReview.model_validate(review_data)

def validate_playable_scene_rules(playable_scene: PlayableScene, expected_chapter_id:str,expected_position:int)->None:
    if playable_scene.chapter_id!=expected_chapter_id or playable_scene.position!=expected_position:
        raise ValueError("Generated chapter ID or scene position is incorrect.")
    entities_by_id = {
        entity.id: entity
        for entity in playable_scene.entities
    }

    for required_entity_id in playable_scene.required_entity_ids:
        entity = entities_by_id.get(required_entity_id)

        if entity is None:
            raise ValueError(
                f"Required entity '{required_entity_id}' does not exist."
            )

        if entity.solid or entity.interaction is None:
            raise ValueError(
                f"Required entity '{required_entity_id}' must be non-solid and interactable."
            )

    if len(playable_scene.deduction.options) < 2:
        raise ValueError("A scene deduction needs at least two options.")
    
def build_scene_plan_messages(chapter_excerpt: str,scene_bible: SceneBible,position: int,) -> List[dict[str, str]]:
    system_prompt = """
    TITLE RULE:

    The title must describe only the current scene's known location or its immediate
    action. Never name a location that is absent from KNOWN CONTEXT. Keep it plain,
    specific, and 2 to 6 words long.
    FACTUAL-STATE RULE:

    Never state that a missing person, animal, object, or clue has been found unless
    that fact appears explicitly in KNOWN CONTEXT or LOCKED FACTS.

    Never introduce a new named location. Use only locations named in KNOWN CONTEXT
    or LOCKED FACTS.

    CLOSED-BOOK SCENE RULES:

    Treat KNOWN CONTEXT and LOCKED FACTS as the complete allowlist for this scene.
    Do not use any other fact, name, place, event, object, suspect, document, or
    conclusion, even if it appears elsewhere in SOURCE EXCERPT.

    KNOWN CONTEXT may appear only in:
    - title;
    - objective;
    - opening beats;
    - deduction prompt and options;
    - closing beats.

    LOCKED FACTS may appear only inside clue inspections. A locked fact must not
    appear in the title, objective, opening beats, deduction prompt, options, or
    closing beats before the player inspects its clue.

    Do not invent proper nouns. Every named person, organisation, place, document,
    or animal in the output must appear verbatim in KNOWN CONTEXT or LOCKED FACTS.

    Do not invent decorative clues. Every clue must directly reveal at least one
    LOCKED FACT. Do not create clues about coats, bags, furniture, newspapers,
    letters, witnesses, or reports unless that specific item is supported by a
    LOCKED FACT.

    CLUE PRESENTATION:
    Choose each clue's evidence_type to match its scenario: newspaper for printed
    news or public reports; letter for correspondence, telegrams, or official
    messages; note for brief written notices; map for location or route details;
    and evidence for physical objects, observations, tracks, testimony, or any
    clue that is not naturally a document. Give each clue a short, concrete label
    describing what Watson can inspect without revealing its conclusion.

    Create no more clues than there are distinct LOCKED FACTS.
    If there are no LOCKED FACTS, create an empty clues list.

    Create exactly one clue for each LOCKED FACT. For every clue, set its title
    and its single paragraphs entry to the matching LOCKED FACT verbatim. Do not
    add a date, place, source, delivery detail, interpretation, or any other
    sentence around that fact.

    Do not convert a fact into an accusation, motive, or conclusion. Present only
    what the evidence directly establishes.

    DEDUCTION RULES:

    Create exactly three options. Every option must be grounded in KNOWN CONTEXT
    or in facts the player has just investigated.

    Incorrect options must be plausible but source-grounded alternative priorities.
    Never use unrelated people, joke answers, invented crimes, or events absent
    from the allowlist.

    Give score 10 only to the source-faithful next step: the choice that best
    matches the chapter's canonical progression after the information currently
    available to Watson. Give the other two options score 0. The response must
    only evaluate the option the player selected. Never claim Watson selected a
    different option, and never change the canonical story outcome.

    Use short responses in Holmes's voice when speaker is Holmes. Do not write
    dialogue where Holmes speaks but Watson's actions or first-person words are
    placed inside Holmes's quotation.

    Each option must be an action Watson and Holmes can take in the current
    scene or immediately after it. Do not offer actions at a later location.

    Do not offer searching for a missing person, animal, or object unless the
    current scene explicitly places Watson at the search location.

    Do not mention or question a person unless that person is named in KNOWN
    CONTEXT or revealed by an investigated clue.

    Do not mention a room, object, or place unless it is named in KNOWN CONTEXT
    or an investigated clue.

    Never rewrite "found dead" as killed, murdered, violent, suspicious, or
    foul play unless that exact stronger claim appears in the allowed facts.
    If KNOWN CONTEXT does not name a destination, deduction options must not
    name one. Prefer immediate actions such as preparing to leave with Holmes,
    asking Holmes for clarification, or reviewing the evidence already found.

    Incorrect options must still be serious, plausible responses to the current
    situation. Do not use idle, comic, or deliberately unreasonable options such
    as sleeping, ignoring the event, or abandoning the investigation.

    STORY FLOW:

    Opening beats establish only the immediate situation.
    Clues reveal the scene's locked facts.
    Closing beats move toward NEXT SCENE CONTEXT without revealing that scene's
    locked discoveries.
    
    NEXT SCENE CONTEXT is transition metadata only. It may guide the final
    closing beat, but must never appear in the title, objective, opening beats,
    clues, deduction prompt, or deduction options.

    Closing beats may signal departure or transition, but must not name the next
    location unless that location is already present in KNOWN CONTEXT.

    Never state that a missing person, animal, or object has been found unless
    that fact is explicitly present in KNOWN CONTEXT or LOCKED FACTS.

    Required top-level keys:
    chapter_id, position, title, objective, visual_theme, layout_preset,
    opening_beats, clues, deduction_prompt, deduction_options, closing_beats.

    Use the supplied chapter ID and position exactly. Do not create coordinates,
    entities, spawn points, or PlayableScene fields.

    SCENE BOUNDARY — NON-NEGOTIABLE:

    The CURRENT SCENE is authoritative. It is a sealed moment in the chapter:
    preserve its location, chronology, and available knowledge exactly.
    Do not reinterpret it as a different moment in the chapter.

    Before writing every title, beat, clue, option, or response, check that every
    named person, place, object, event, and conclusion is present in KNOWN CONTEXT
    or has already been revealed by a clue in this same scene. If it is not, omit
    it completely. Do not use later story knowledge as a tempting distractor.

    For scene position 1, begin at the opening moment stated in KNOWN CONTEXT.
    Never replace that opening with later travel, an arrival, a police theory, a
    crime scene, or any later chapter event. If the opening supplies only an
    announcement, the scene stays with that announcement and the player's
    immediate investigation of it.
    NESTED JSON CONTRACT:

    opening_beats and closing_beats must be arrays of objects with exactly:
    id, kind, speaker, text

    kind must be one of: narration, dialogue, thought.

    Each clue must be an object with exactly:
    id, evidence_type, label, title, paragraphs

    A clue label must name the physical object Watson examines, not the fact
    discovered. Use labels such as "the telegram", "the note", "the newspaper",
    "the map", or "the evidence".

    A clue title may name the discovered fact, such as "Silver Blaze Vanished".
    Never use facts such as "Trainer's Death" or "Missing Horse" as clue labels.

    evidence_type must be exactly one of:
    newspaper, letter, note, map, evidence.
    Never use report as an evidence_type.

    Each deduction option must be an object with exactly:
    id, label, response, score

    deduction_options is mandatory. Always return exactly three complete option
    objects, even when the scene has no clues. Never omit this field.

    Never use a string where an object is required.
    Never use "text" instead of a deduction option's "label" and "response".

    NARRATIVE:
    - Opening beats use only KNOWN CONTEXT and must be concrete, not generic.
    - Locked facts appear only in their matching clue inspection.
    - Closing beats bridge naturally toward NEXT SCENE CONTEXT without exposing
    that next scene's locked facts.
    - Create 3-5 opening beats and 2-4 closing beats.

    Do not invent physical staging in openings or closings: no packing, coats,
    stairs, cabs, gestures, arrivals, or departures unless explicitly stated in
    KNOWN CONTEXT. Do not infer that an event is serious, criminal, mysterious,
    or alarming unless the allowed facts say so.

    Use one visual_theme:
    warm-morning, overcast-afternoon, rain-dusk, foggy-moor, race-day.

    Choose layout_preset from staging:
    compact_interior (small room), long_interior (carriage/corridor),
    open_floor (outdoor/stable/large space), threshold (arrival/transition).

    chapter_id must exactly equal CHAPTER ID.
    position must exactly equal SCENE POSITION.
    Return one valid JSON object only. No markdown or commentary.
        """

    user_prompt = f"""
    CHAPTER ID: {scene_bible.chapter_id}

    SCENE POSITION: {position}

    GUARDRAILS:
    {chr(10).join(f"- {guardrail}" for guardrail in scene_bible.guardrails)}

    CURRENT SCENE:
    {chapter_excerpt}
    """.strip()

    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

def generate_scene_plan(chapter_excerpt: str,scene_bible: SceneBible,position: int,known_context: str,locked_clue_content: List[str]) -> ScenePlan:
    model_input = build_scene_plan_messages(
        chapter_excerpt=chapter_excerpt,
        scene_bible=scene_bible,
        position=position,
    )
    
    revision_feedback = ""
    last_error = None
    last_valid_plan = None

    for attempt in range(3):
        try:
            request_messages = list(model_input)
            if revision_feedback:
                request_messages.append(
                    {
                        "role": "user",
                        "content": (
                            "The previous plan was rejected by the factual reviewer. "
                            "Replace the rejected content; do not preserve it. "
                            "Use only this allowlist for the replacement:\n\n"
                            f"KNOWN CONTEXT:\n- {known_context}\n\n"
                            "LOCKED FACTS (clue inspections only):\n"
                            f"{chr(10).join(f'- {fact}' for fact in locked_clue_content) or '- none'}\n\n"
                            "Deduction options must not mention anything outside this "
                            "allowlist. Fix these issues and return one complete JSON object:\n"
                            f"{revision_feedback}"
                        ),
                    }
                )
            response = generate_json_response(
                request_messages,
                GENERATION_MODEL,
                2000,
                ScenePlan.model_json_schema(),
            )

            scene_plan_data = parse_model_json(response)
            if (
                "closing_teats" in scene_plan_data
                and "closing_beats" not in scene_plan_data
            ):
                scene_plan_data["closing_beats"] = scene_plan_data.pop(
                    "closing_teats"
                )
            # A closing transition is optional in the player experience. Small
            # models sometimes omit the field even when the scene content is
            # otherwise valid, so retain the playable plan with no extra beat.
            scene_plan_data.setdefault("closing_beats", [])
            for field_name in (
                "opening_beats",
                "closing_beats",
                "clues",
                "deduction_options",
            ):
                for item in scene_plan_data.get(field_name, []):
                    if "id" in item:
                        item["id"] = str(item["id"])
            scene_plan_data.pop("evidence_type", None)
            allowed_evidence_types = {
                "newspaper",
                "letter",
                "note",
                "map",
                "evidence",
            }

            for clue in scene_plan_data.get("clues", []):
                if clue.get("evidence_type") not in allowed_evidence_types:
                    clue["evidence_type"] = "evidence"

                # Models often default every clue to generic "evidence". When
                # the clue itself clearly describes a document, preserve that
                # meaning in the playable world's visual treatment.
                if clue.get("evidence_type") == "evidence":
                    clue_text = " ".join(
                        [
                            str(clue.get("label", "")),
                            str(clue.get("title", "")),
                            *[str(item) for item in clue.get("paragraphs", [])],
                        ]
                    ).lower()
                    if any(word in clue_text for word in ("telegram", "letter", "wire", "message")):
                        clue["evidence_type"] = "letter"
                    elif any(word in clue_text for word in ("newspaper", "headline", "gazette", "times", "clipping")):
                        clue["evidence_type"] = "newspaper"
                    elif any(word in clue_text for word in ("map", "route", "plan of")):
                        clue["evidence_type"] = "map"
                    elif any(word in clue_text for word in ("note", "memo", "record", "entry")):
                        clue["evidence_type"] = "note"

            # The playable builder has room for at most three clue entities.
            # Trimming here also prevents surplus model clues from introducing
            # unrelated later-story details that can never be inspected.
            generated_clues = scene_plan_data.get("clues", [])[:3]
            if locked_clue_content:
                generated_clues = generated_clues[: len(locked_clue_content)]
                for clue_index, clue in enumerate(generated_clues):
                    fact = locked_clue_content[clue_index]
                    clue["title"] = fact
                    clue["paragraphs"] = [fact]

            # Classify after the source-locked fact replaces the model's prose.
            # Otherwise every model-default "evidence" clue becomes the same
            # generic token in the room even when it is clearly a letter or note.
            for clue in generated_clues:
                if clue.get("evidence_type") != "evidence":
                    continue
                clue_text = " ".join(
                    [
                        str(clue.get("label", "")),
                        str(clue.get("title", "")),
                        *[str(item) for item in clue.get("paragraphs", [])],
                    ]
                ).lower()
                if any(word in clue_text for word in ("telegram", "letter", "wire", "message")):
                    clue["evidence_type"] = "letter"
                elif any(word in clue_text for word in ("newspaper", "headline", "gazette", "times", "clipping")):
                    clue["evidence_type"] = "newspaper"
                elif any(word in clue_text for word in ("map", "route", "plan of")):
                    clue["evidence_type"] = "map"
                elif any(word in clue_text for word in ("note", "memo", "record", "entry")):
                    clue["evidence_type"] = "note"
            scene_plan_data["clues"] = generated_clues

            # Scene changes are driven by the ordered storyboard. A speculative
            # closing transition can otherwise leak the next location or outcome.
            scene_plan_data["closing_beats"] = []

            for field_name in ("opening_beats", "closing_beats"):
                for beat in scene_plan_data.get(field_name, []):
                    if beat.get("speaker") is None:
                        beat["speaker"] = ""
            scene_plan = ScenePlan.model_validate(scene_plan_data)

            if scene_plan.chapter_id != scene_bible.chapter_id:
                raise RuntimeError("Generated ScenePlan has the wrong chapter ID.")

            if scene_plan.position != position:
                raise RuntimeError("Generated ScenePlan has the wrong scene position.")

            # Keep a schema-valid plan available as a safe fallback if the
            # reviewer rejects all three generated deduction variants.
            last_valid_plan = scene_plan

            review = review_scene_plan(
                scene_plan=scene_plan,
                known_context=known_context,
                locked_clue_content=locked_clue_content,
            )

            # A reviewer rejection without issues gives the generator no
            # actionable correction. Keep the schema-valid plan in that case.
            if review.approved or not review.issues:
                return scene_plan

            revision_feedback = "\n".join(
                f"- {issue}"
                for issue in review.issues
            )

            raise RuntimeError(
                f"Scene plan rejected by factual reviewer:\n{revision_feedback}"
            )
        except (
            BadRequestError,
            ValidationError,
            RuntimeError,
            json.JSONDecodeError,
        ) as error:
            last_error = error

    # A malformed or unsupported deduction option should not make the complete
    # chapter-generation request fail after the scene itself was valid. These
    # neutral options introduce no characters, places, or story facts, so they
    # remain safe for any uploaded book.
    if last_valid_plan is not None:
        fallback_data = last_valid_plan.model_dump()
        fallback_facts = locked_clue_content[:3]

        def compact_fact(fact: str) -> str:
            normalized = " ".join(fact.split())
            if len(normalized) <= 76:
                return normalized
            return normalized[:76].rsplit(" ", 1)[0] + "…"

        if fallback_facts:
            fallback_data["deduction_prompt"] = (
                "Which observation should guide the investigation's next step?"
            )
            fallback_options = [
                {
                    "id": "fallback-1",
                    "label": f"Give priority to: {compact_fact(fallback_facts[0])}",
                    "response": "That observation provides the clearest direction for the inquiry.",
                    "score": 10,
                }
            ]
            for index, fact in enumerate(fallback_facts[1:], start=2):
                fallback_options.append(
                    {
                        "id": f"fallback-{index}",
                        "label": f"Consider instead: {compact_fact(fact)}",
                        "response": "It is relevant, but another observation should lead the next step.",
                        "score": 0,
                    }
                )
            while len(fallback_options) < 3:
                fallback_options.append(
                    {
                        "id": f"fallback-{len(fallback_options) + 1}",
                        "label": "Review the observations together",
                        "response": "A sensible precaution, though one observation gives the clearest lead.",
                        "score": 0,
                    }
                )
        else:
            fallback_data["deduction_prompt"] = "What should the investigation consider next?"
            fallback_options = [
                {
                    "id": "fallback-1",
                    "label": "Ask for clarification before acting",
                    "response": "A sound course. The situation should be understood clearly.",
                    "score": 10,
                },
                {
                    "id": "fallback-2",
                    "label": "Review what has been observed",
                    "response": "Observation is useful, but it does not settle the next step.",
                    "score": 0,
                },
                {
                    "id": "fallback-3",
                    "label": "Proceed with care",
                    "response": "Caution is sensible, though the inquiry still needs direction.",
                    "score": 0,
                },
            ]
        fallback_data["deduction_options"] = fallback_options
        return ScenePlan.model_validate(fallback_data)

    raise RuntimeError(
        "Scene plan generation failed after three attempts."
    ) from last_error
# def generate_playable_scene(chapter_excerpt:str,scene_bible:SceneBible,position:int)->PlayableScene:
#     client=get_groq_client()
#     model_input=build_scene_messages(chapter_excerpt=chapter_excerpt,scene_bible=scene_bible,position=position)
#     model_output=client.chat.completions.create(model="openai/gpt-oss-120b",messages=model_input,response_format={
#     "type": "json_object",
# },temperature=0.2,max_completion_tokens=3000)
#     response=model_output.choices[0].message.content
#     if not response:
#         raise RuntimeError("Response could not be generated") 
#     playable_scene=PlayableScene.model_validate_json(response)
#     validate_playable_scene_rules(playable_scene,scene_bible.chapter_id,position)
#     return playable_scene
def build_storyboard_messages(chunk_summaries:List[ChunkSummary], scene_bible:SceneBible)->list[dict[str,str]]:
    system_prompt="""
        You are a source-faithful interactive-fiction game designer.

        Return exactly one valid JSON object matching the ChapterStoryboard schema.
        Do not return markdown, commentary, or text outside the JSON object.
        OPENING DISCLOSURE:

        The first scene may reveal only the inciting incident and immediate call to
        action. Do not introduce named suspects, arrests, police theories, motives, or
        other investigative developments until later scenes, unless they are essential
        to understanding the initial premise.

        Create a complete playable storyboard for the supplied chapter.
        Each storyboard scene must have exactly one primary location and one coherent
        moment in time. Never combine travel, arrival, investigation, and later
        discussion in the same scene.

        Do not use hedging such as “or”, “perhaps”, “may have”, or “has just”.
        Choose only the event order explicitly supported by the source.

        Reserve the final scene for the final explanation. Earlier scenes may introduce
        evidence, but must not explain the solution or repeat the final reasoning.

        The JSON object must contain:
        - chapter_id: exactly matching the supplied Scene Bible chapter_id;
        - scenes: an ordered list of 4 to 6 storyboard scenes.

        Every storyboard scene must contain:
        - position: consecutive integers beginning at 1;
        - known_context: concise information Watson can know when entering;
        - locked_clue_content: a list of facts Watson learns only after investigating;
        - is_final_reveal: a boolean.

        Use only facts supported by the supplied ordered chunk summaries. Do not invent events,
        evidence, documents, motives, or conclusions.

        Use the full ordered range of supplied chunk_index values. The final storyboard
        scene must include at least one fact from the highest chunk_index, so it covers
        the actual ending rather than repeating the opening.

        OPENING-ORDER REQUIREMENT:
        Scene position 1 must be grounded in the earliest supplied source material
        and depict the first clear narrative moment. Do not skip an earlier moment
        established by the source. Every later scene must preserve source chronology.

        SCENE-TO-SCENE ORDER REQUIREMENT:
        Assign every scene consecutive source_chunk_indices in ascending order.
        A scene may use only its assigned chunks and information established by
        earlier scenes. Never introduce a location, character encounter, discovery,
        object, outcome, or explanation before the source chunk that establishes it.
        Do not move a later event into an earlier scene merely to make the sequence
        more dramatic. Each scene must end before the next scene's new discovery.

        known_context must not reveal information from locked_clue_content.
        Opening scenes must preserve uncertainty. Only the final storyboard scene may
        set is_final_reveal to true and include the chapter's final explanation.
        Every other scene must set is_final_reveal to false.

        Turn the chapter into distinct playable moments with a clear progression:
        arrival or premise, investigation, discovery, and resolution.

        The ordered chunk summaries represent the entire chapter. Your storyboard must
        cover the chapter's beginning, middle, and ending—not only its opening chunks.

        The final storyboard scene must be based on the final supplied chunk summaries.
        It must set is_final_reveal to true.

        Exactly one scene may set is_final_reveal to true, and it must be the final
        scene. Every earlier scene must set it to false.

        Do not put a locked fact into known_context for the same scene.
        known_context includes what Watson directly observes when the scene begins,
        facts established in earlier completed scenes, and facts explicitly spoken or
        delivered to Watson in the opening moment before free exploration begins. For
        example, if the source opens with Holmes announcing the case premise, that
        announcement belongs in known_context, not locked_clue_content.

        locked_clue_content is only for information first discovered by inspecting an
        object, location, person, or evidence during that scene. Do not lock an opening
        announcement merely to turn it into a clue. known_context must not disclose a
        future event, unseen location, identity, cause, or outcome.

        For the final-reveal scene only, explain the source-supported resolution using
        facts from the final chapter summaries. Earlier scenes must preserve uncertainty.

        CHRONOLOGY AND GROUNDING:
        Do not invent props, actions, letters, documents, or transitions to make scenes
        more dramatic. Every concrete detail must be supported by a supplied chunk
        summary.

        Use plain descriptive scene titles of 2 to 6 words based only on the scene's
        known location or action. Do not use metaphorical titles such as “signal,”
        “disaster,” “framework,” “chain,” or “conclusion.”

        For the final scene, use the actual source-supported place and manner in which
        the explanation occurs. Do not invent a letter, private meeting, or new event.

        Create scenes in the exact chronological order of the supplied chunk summaries.
        Do not move an event, discovery, location, or character encounter earlier or later
        than its supporting source chunk.

        Each scene must be grounded in its listed source_chunk_indices. Do not combine
        facts from distant chunks into one scene unless they are consecutive and the
        transition is explicitly supported by the source.

        known_context describes only what Watson knows on entering that scene.
        locked_clue_content contains discoveries made during that scene only.

        Never invent travel routes, arrivals, discoveries, or scene transitions.
        If the source is unclear, use neutral wording rather than adding a detail.
        DEDUCTION CONTRACT:

        The deduction is a non-branching knowledge check, not a branch in the story.

        Exactly one option is correct and scores 10. The other options score 0.

        Each option response must evaluate the player's choice only. It must not claim that
        the canonical story changed because of the player's answer.

        Closing beats must always show the source-supported next event, regardless of
        which deduction option the player selected.   
        """
    user_prompt=f"""
            SCENE BIBLE:
            {scene_bible.model_dump_json()}

            ORDERED CHUNK SUMMARIES:
            {json.dumps([summary.model_dump() for summary in chunk_summaries])}
            """
    return [
         {
             "role":"system",
             "content":system_prompt
         } ,  
         {
             "role":"user",
             "content":user_prompt
         }
    ]
def validate_chapter_storyboard(
    storyboard: ChapterStoryboard,
    expected_chapter_id: str,
) -> None:
    if storyboard.chapter_id != expected_chapter_id:
        raise RuntimeError(
            "Generated storyboard chapter ID does not match the requested chapter."
        )

    if not 3 <= len(storyboard.scenes) <= 8:
        raise RuntimeError(
            "A chapter storyboard must contain between 3 and 8 scenes."
        )

    actual_positions = [scene.position for scene in storyboard.scenes]
    expected_positions = list(range(1, len(storyboard.scenes) + 1))

    if actual_positions != expected_positions:
        raise RuntimeError(
            "Storyboard scene positions must be consecutive and start at 1."
        )

    final_reveal_scenes = [
        scene
        for scene in storyboard.scenes
        if scene.is_final_reveal
    ]

    if len(final_reveal_scenes) != 1:
        raise RuntimeError(
            "A storyboard must contain exactly one final-reveal scene."
        )

    if not storyboard.scenes[-1].is_final_reveal:
        raise RuntimeError(
            "The final storyboard scene must be the final-reveal scene."
        )

def generate_chapter_storyboard(
    chunk_summaries: List[ChunkSummary],
    scene_bible: SceneBible,
    max_attempts: int = 3,
) -> ChapterStoryboard:
    model_input=build_storyboard_messages(chunk_summaries=chunk_summaries,scene_bible=scene_bible)
    last_error = None

    for attempt in range(max_attempts):
        try:
            request_messages = list(model_input)
            if attempt:
                request_messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response omitted or malformed scenes. "
                            "Return the complete ChapterStoryboard now, including a "
                            "4–6 item scenes array with every required field."
                        ),
                    }
                )

            response = generate_json_response(
                request_messages,
                GENERATION_MODEL,
                2600,
                ChapterStoryboard.model_json_schema(),
            )
            storyboard_data = parse_model_json(response)
            raw_scenes = storyboard_data.get("scenes", [])
            if not raw_scenes:
                raise RuntimeError("Chapter storyboard did not contain any scenes.")

            # The first playable scene must begin where the chapter begins.
            # Keeping it tied to the deliberately small opening summary prevents
            # a model from opening on a later train ride or crime scene.
            raw_scenes[0]["source_chunk_indices"] = [1]
            raw_scenes[0]["known_context"] = chunk_summaries[0].summary
            raw_scenes[0]["locked_clue_content"] = chunk_summaries[0].clues[:2]

            chunk_count = len(chunk_summaries)
            scene_count = len(raw_scenes)
            for scene_index, scene_data in enumerate(raw_scenes):
                if not scene_data.get("source_chunk_indices"):
                    start_index = (scene_index * chunk_count) // scene_count + 1
                    end_index = ((scene_index + 1) * chunk_count) // scene_count
                    scene_data["source_chunk_indices"] = list(
                        range(start_index, end_index + 1)
                    )

            for scene_data in raw_scenes:
                known_context = scene_data.get("known_context")
                if isinstance(known_context, list):
                    scene_data["known_context"] = " ".join(
                        str(item).strip()
                        for item in known_context
                        if str(item).strip()
                    )

            storyboard_data["chapter_id"] = scene_bible.chapter_id
            storyboard = ChapterStoryboard.model_validate(storyboard_data)
            validate_chapter_storyboard(storyboard, scene_bible.chapter_id)
            return storyboard
        except (RuntimeError, ValidationError, json.JSONDecodeError) as error:
            last_error = error

    raise RuntimeError(
        f"Chapter storyboard generation failed after {max_attempts} attempt(s)."
    ) from last_error

def build_chunk_summary_messages(chunk_string: str, chunk_index: int, scene_bible: SceneBible)->List[dict[str,str]]:
    system_prompt="""
        You are a source-faithful literary analyst preparing a compact chapter outline.

        Return exactly one valid JSON object matching the ChunkSummary schema.
        Do not return markdown, commentary, or text outside the JSON object.

        The JSON object must contain:
        - chunk_index: exactly matching the supplied chunk index;
        - summary: a concise factual summary of this chapter chunk;
        - key_events: a list of 3 to 6 distinct events in chronological order;
        - clues: a list of concrete clues, observations, or reported facts from this chunk.

        Use only facts supported by the supplied chapter chunk. Do not invent
        characters, documents, evidence, causes, motives, or conclusions.

        Do not reveal the final solution unless it is explicitly contained in this
        chapter chunk. Preserve uncertainty where the source preserves uncertainty.
        Use neutral language for unresolved events. Say “found dead” rather than
        “murdered” unless the supplied source explicitly confirms murder.
        Use exactly these JSON keys and no others:

        {
        "chunk_index": 1,
        "summary": "one concise paragraph",
        "key_events": ["event one", "event two", "event three"],
        "clues": ["optional clue one", "optional clue two"]
        }

        Return exactly 3 to 5 key_events and no more than 3 clues.
        Keep the summary under 90 words.
        Do not invent, merge, or infer locations. Name a setting only when the supplied chunk explicitly names it; otherwise describe it generically.
    """
    user_prompt=f"""
        SCENE BIBLE: 
        {scene_bible.model_dump_json()}

        CHAPTER CHUNK {chunk_index}: 
        {chunk_string}
        """
    return [
        {
            "role":"system",
            "content":system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

def generate_chunk_summary(chunk_string: str, chunk_index: int, scene_bible: SceneBible)->ChunkSummary:
    model_input=build_chunk_summary_messages(chunk_string=chunk_string,chunk_index=chunk_index,scene_bible=scene_bible)
    last_error = None

    for attempt in range(3):
        try:
            response = generate_json_response(
                model_input,
                GENERATION_MODEL,
                800,
                ChunkSummary.model_json_schema(),
            )
            chunk_data = parse_model_json(response)

            chunk_data["key_events"] = chunk_data.get("key_events", [])[:6]
            chunk_data["clues"] = chunk_data.get("clues", [])[:5]

            chunk_summary = ChunkSummary.model_validate(chunk_data)
            if chunk_summary .chunk_index != chunk_index:
                raise RuntimeError("Incorrect chunk index")
            return chunk_summary 
        except (
            BadRequestError,
            ValidationError,
            RuntimeError,
            json.JSONDecodeError,
        ) as error:
            last_error = error

    raise RuntimeError(
        "Chunk summary generation failed after three attempts."
    ) from last_error
# if __name__=="__main__":
#     client=get_groq_client()
#     model_list=client.models.list()
#     for i in model_list.data:
#         if i.id=="openai/gpt-oss-20b":
#             print("Model is Available")

if __name__ == "__main__":
    client = get_groq_client()

    for model in client.models.list().data:
        print(model.id)

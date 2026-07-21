const world = document.querySelector("#game-world");
const layer = document.querySelector("#entities-layer");
const playerNode = document.querySelector("#player");
const prompt = document.querySelector("#interaction-prompt");
const magnifier = document.querySelector("#magnifier");
const magnifierButton = document.querySelector("#magnifier-button");
const dialogue = document.querySelector("#dialogue");
const speaker = document.querySelector("#speaker");
const dialogueText = document.querySelector("#dialogue-text");
const status = document.querySelector("#status");
const reset = document.querySelector("#reset-button");
const continueButton = document.querySelector("#continue-button");
const closeDialogue = document.querySelector("#close-dialogue");
const inspectionReader = document.querySelector("#inspection-reader");
const inspectionPaper = document.querySelector("#inspection-paper");
const inspectionType = document.querySelector("#inspection-type");
const inspectionTitle = document.querySelector("#inspection-title");
const inspectionSubtitle = document.querySelector("#inspection-subtitle");
const inspectionCopy = document.querySelector("#inspection-copy");
const closeInspection = document.querySelector("#close-inspection");
const beginCase = document.querySelector("#begin-case");
const replayButton = document.querySelector("#replay-case");
const briefing = document.querySelector("#case-briefing");
const gameCard = document.querySelector("#game-card");
const completeCard = document.querySelector("#case-complete");
const caseRating = document.querySelector("#case-rating");
const completionTitle = document.querySelector("#completion-title");
const completionCopy = document.querySelector("#completion-copy");
const storyPanel = document.querySelector("#story-panel");
const storySpeaker = document.querySelector("#story-speaker");
const storyText = document.querySelector("#story-text");
const storyNext = document.querySelector("#story-next");
const deductionPanel = document.querySelector("#deduction-panel");
const deductionPrompt = document.querySelector("#deduction-prompt");
const deductionOptions = document.querySelector("#deduction-options");
const deductionResponse = document.querySelector("#deduction-response");
const deductionNext = document.querySelector("#deduction-next");
const bookTitle = document.querySelector("#book-title");
const sidebarCopy = document.querySelector("#sidebar-copy");
const sceneObjective = document.querySelector("#scene-objective");
const sceneLocation = document.querySelector("#scene-location");
const sceneNumber = document.querySelector("#scene-number");
const roomLabel = document.querySelector("#room-label");
const chapterIndex = document.querySelector("#chapter-index");
const chapterTotal = document.querySelector("#chapter-total");
const beatTitle = document.querySelector("#beat-title");
const sceneTitle = document.querySelector("#scene-title");
const narration = document.querySelector("#narration");
const libraryButton = document.querySelector("#library-button");
const libraryPanel = document.querySelector("#library-panel");
const closeLibrary = document.querySelector("#close-library");
const uploadForm = document.querySelector("#upload-form");
const uploadStatus = document.querySelector("#upload-status");
const chapterList = document.querySelector("#chapter-list");

const API_BASE_URL = "http://127.0.0.1:8000";
let chapterId = "fbc2c27a-5ce5-4c50-bc70-aa117416aa1c";
const PLAYTHROUGH_STORAGE_KEY = "storyloom-playthrough-id";
const TABLE_PROPS = {
  "writing-desk": ["book-rust", "book-blue", "book-gold", "book-red"],
  "left-side-table": ["book-blue", "book-rust", "book-green"],
  "right-side-table": ["book-gold", "book-red", "book-blue"]
};
const heldKeys = new Set();
const player = { x: 0, y: 0, width: 0, height: 0, speed: 0 };
let scenes = [];
let activeScene = null;
let sceneBible = null;
let sceneProgress = null;
let nearby = null;
let lastTime = 0;
let animationStarted = false;
let magnifiedNode = null;
let magnifierEnabled = false;
let inspectedEntity = null;
const clueSpawnIndexes = new Map();
const environmentStates = new Map();

function getPlaythroughId() {
  const savedId = localStorage.getItem(PLAYTHROUGH_STORAGE_KEY);
  if (savedId) return savedId;
  const newId = crypto.randomUUID();
  localStorage.setItem(PLAYTHROUGH_STORAGE_KEY, newId);
  return newId;
}

function openLibrary({ landing = false } = {}) {
  libraryPanel.hidden = false;
  libraryPanel.classList.toggle("landing", landing);
  if (landing) {
    briefing.hidden = true;
    gameCard.hidden = true;
  }
}

function hideLibrary() {
  libraryPanel.hidden = true;
  libraryPanel.classList.remove("landing");
}

function renderImportedChapters(chapters) {
  chapterList.replaceChildren(...chapters.map((chapter) => {
    const item = document.createElement("li");
    const meta = document.createElement("span");
    meta.textContent = `Chapter ${chapter.source_number ?? chapter.position}`;
    const title = document.createElement("strong");
    title.textContent = chapter.title || "Untitled chapter";
    const generateButton = document.createElement("button");
    generateButton.type = "button";
    generateButton.textContent = "Generate playable chapter";
    generateButton.addEventListener("click", () => void generateImportedChapter(chapter));
    item.append(meta, title, generateButton);
    return item;
  }));
}

async function generateImportedChapter(chapter) {
  uploadStatus.textContent = `Generating ${chapter.title || "chapter"}… this may take a few minutes.`;
  try {
    const response = await fetch(`${API_BASE_URL}/chapters/${chapter.chapter_id}/generate`, { method: "POST" });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "Chapter generation failed.");
    chapterId = chapter.chapter_id;
    // A regenerated chapter is a fresh playthrough. Otherwise an older saved
    // position for this same chapter can reopen the player on scene 2 or later.
    sceneProgress = defaultProgress();
    await saveProgress();
    uploadStatus.textContent = `${result.scene_count} playable scenes generated. Opening chapter…`;
    hideLibrary();
    await loadExperience();
    if (!briefing.hidden) await beginPlaythrough();
  } catch (error) {
    console.error(error);
    uploadStatus.textContent = error.message;
  }
}

async function importBook(event) {
  event.preventDefault();
  const file = document.querySelector("#book-file").files[0];
  if (!file) return;

  uploadStatus.textContent = "Importing text…";
  chapterList.replaceChildren();
  const formData = new FormData();
  formData.append("file", file);

  try {
    const uploadResponse = await fetch(`${API_BASE_URL}/books`, { method: "POST", body: formData });
    const uploadedBook = await uploadResponse.json();
    if (!uploadResponse.ok) throw new Error(uploadedBook.detail || "Text import failed.");

    uploadStatus.textContent = "Detecting chapters…";
    const splitResponse = await fetch(`${API_BASE_URL}/books/${uploadedBook.book_id}/chapters`, { method: "POST" });
    const splitResult = await splitResponse.json();
    if (!splitResponse.ok) throw new Error(splitResult.detail || "Chapter detection failed.");

    const chaptersResponse = await fetch(`${API_BASE_URL}/books/${uploadedBook.book_id}/chapters`);
    const chapters = await chaptersResponse.json();
    if (!chaptersResponse.ok) throw new Error(chapters.detail || "Could not load chapters.");

    bookTitle.textContent = uploadedBook.filename.replace(/\.txt$/i, "");
    uploadStatus.textContent = `${splitResult.chapter_count} chapters imported. Select a chapter when generation is available.`;
    renderImportedChapters(chapters);
  } catch (error) {
    console.error(error);
    uploadStatus.textContent = error.message;
  }
}

const playthroughId = getPlaythroughId();

function defaultProgress() {
  return {
    playthrough_id: playthroughId,
    chapter_id: chapterId,
    intro_seen: false,
    current_scene_position: 1,
    chapter_complete: false,
    completed_scene_ids: [],
    examined_entity_ids: [],
    scene_phase: "opening",
    current_beat_index: 0,
    selected_choice_ids: [],
    deduction_score: 0
  };
}

function normaliseProgress(progress) {
  return { ...defaultProgress(), ...progress };
}

function overlaps(a, b) {
  return a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
}

function isBlocked(next) {
  const area = activeScene.walkable_area;
  const outside = next.x < area.x || next.y < area.y || next.x + next.width > area.x + area.width || next.y + next.height > area.y + area.height;
  return outside || activeScene.entities.some((entity) => entity.solid && overlaps(next, entity));
}

function nearestClearPlayerPosition(preferred) {
  if (!isBlocked(preferred)) return preferred;

  const area = activeScene.walkable_area;
  let closest = null;
  let closestDistance = Infinity;
  for (let y = area.y; y <= area.y + area.height - preferred.height; y += 4) {
    for (let x = area.x; x <= area.x + area.width - preferred.width; x += 4) {
      const candidate = { ...preferred, x, y };
      if (isBlocked(candidate)) continue;
      const distance = (x - preferred.x) ** 2 + (y - preferred.y) ** 2;
      if (distance < closestDistance) {
        closest = candidate;
        closestDistance = distance;
      }
    }
  }
  return closest ?? preferred;
}

function move(axis, amount) {
  const next = { ...player, [axis]: player[axis] + amount };
  if (!isBlocked(next)) player[axis] = next[axis];
}

function requiredEntityIds() {
  return activeScene.required_entity_ids ?? (activeScene.completion_entity_id ? [activeScene.completion_entity_id] : []);
}

function isSceneClue(entity) {
  return requiredEntityIds().includes(entity.id);
}

function environmentStateKey(entity) {
  return `${activeScene.scene_id}:${entity.id}`;
}

function isToggleableEnvironment(entity) {
  return entity.type === "lamp" && !entity.interaction?.inspection;
}

function isEnvironmentActive(entity) {
  return environmentStates.get(environmentStateKey(entity)) ?? true;
}

function interactionLabel(entity) {
  if (isToggleableEnvironment(entity)) {
    return isEnvironmentActive(entity) ? "switch off the lamp" : "switch on the lamp";
  }
  return entity.interaction.label;
}

function isClueRevealed(entity) {
  return sceneProgress.examined_entity_ids.includes(entity.id) || distanceTo(entity) < 52;
}

function areRequiredCluesFound() {
  return requiredEntityIds().every((id) => sceneProgress.examined_entity_ids.includes(id));
}

function isActiveSceneComplete() {
  return sceneProgress.completed_scene_ids.includes(activeScene?.scene_id);
}

function distanceTo(entity) {
  const placement = positionForEntity(entity);
  const horizontalGap = Math.max(
    placement.x - (player.x + player.width),
    player.x - (placement.x + placement.width),
    0
  );
  const verticalGap = Math.max(
    placement.y - (player.y + player.height),
    player.y - (placement.y + placement.height),
    0
  );
  return Math.hypot(horizontalGap, verticalGap);
}

function pointDistanceToEntity(point, entity) {
  const placement = positionForEntity(entity);
  const horizontalGap = Math.max(placement.x - point.x, point.x - (placement.x + placement.width), 0);
  const verticalGap = Math.max(placement.y - point.y, point.y - (placement.y + placement.height), 0);
  return Math.hypot(horizontalGap, verticalGap);
}

function closestInspectableAtPoint(point) {
  return activeScene.entities
    .filter((entity) => entity.interaction)
    .map((entity) => ({ entity, distance: pointDistanceToEntity(point, entity) }))
    .filter(({ distance }) => distance < 28)
    .sort((a, b) => a.distance - b.distance)[0]?.entity ?? null;
}

function usableSpawnPoints(entity) {
  const spawnPoints = entity.spawn_points ?? [];
  return spawnPoints.filter((spawn) => {
    const candidate = { ...entity, x: spawn.x, y: spawn.y };
    return !activeScene.entities.some((other) => other.id !== entity.id && other.solid && overlaps(candidate, other));
  });
}

function positionForEntity(entity) {
  const spawnPoints = usableSpawnPoints(entity);
  if (!spawnPoints.length) return entity;
  const key = `${activeScene.scene_id}:${entity.id}`;
  if (!clueSpawnIndexes.has(key)) {
    clueSpawnIndexes.set(key, Math.floor(Math.random() * spawnPoints.length));
  }
  const spawn = spawnPoints[clueSpawnIndexes.get(key)];
  return { ...entity, x: spawn.x, y: spawn.y };
}

function rerollActiveSceneClues() {
  activeScene.entities.forEach((entity) => {
    const spawnPoints = usableSpawnPoints(entity);
    const key = `${activeScene.scene_id}:${entity.id}`;
    if (spawnPoints.length < 2) return;
    const currentIndex = clueSpawnIndexes.get(key) ?? 0;
    const offset = 1 + Math.floor(Math.random() * (spawnPoints.length - 1));
    clueSpawnIndexes.set(key, (currentIndex + offset) % spawnPoints.length);
  });
  buildRoom();
}

function resetActiveSceneProgress() {
  if (!activeScene || !sceneProgress) return;

  const activeClueIds = new Set(requiredEntityIds());
  const activeOptionIds = new Set((activeScene.deduction?.options ?? []).map((option) => option.id));

  sceneProgress.examined_entity_ids = sceneProgress.examined_entity_ids.filter((id) => !activeClueIds.has(id));
  sceneProgress.completed_scene_ids = sceneProgress.completed_scene_ids.filter((id) => id !== activeScene.scene_id);
  sceneProgress.selected_choice_ids = sceneProgress.selected_choice_ids.filter((id) => !activeOptionIds.has(id));
  sceneProgress.deduction_score = scenes.reduce((score, scene) => {
    const selected = new Set(sceneProgress.selected_choice_ids);
    return score + (scene.deduction?.options ?? [])
      .filter((option) => selected.has(option.id))
      .reduce((optionScore, option) => optionScore + option.score, 0);
  }, 0);
  sceneProgress.chapter_complete = false;
  sceneProgress.scene_phase = "opening";
  sceneProgress.current_beat_index = 0;

  for (const key of clueSpawnIndexes.keys()) {
    if (key.startsWith(`${activeScene.scene_id}:`)) clueSpawnIndexes.delete(key);
  }
  for (const key of environmentStates.keys()) {
    if (key.startsWith(`${activeScene.scene_id}:`)) environmentStates.delete(key);
  }

  inspectedEntity = null;
  closeInteraction();
  inspectionReader.hidden = true;
  deductionPanel.hidden = true;
  setMagnifierEnabled(false);
  Object.assign(player, activeScene.player);
  Object.assign(player, nearestClearPlayerPosition(player));

  void saveProgress();
  activateScene(activeScene.position);
}

function isOverlayOpen() {
  return !storyPanel.hidden || !deductionPanel.hidden || !dialogue.hidden || !inspectionReader.hidden || !completeCard.hidden;
}

function clearMagnifier() {
  magnifier.hidden = true;
  magnifiedNode?.classList.remove("magnified");
  magnifiedNode = null;
}

function setMagnifiedNode(node) {
  if (magnifiedNode === node) return;
  magnifiedNode?.classList.remove("magnified");
  magnifiedNode = node;
  magnifiedNode?.classList.add("magnified");
}

function setMagnifierEnabled(enabled) {
  magnifierEnabled = enabled;
  world.classList.toggle("searching", enabled);
  magnifierButton.setAttribute("aria-pressed", String(enabled));
  magnifierButton.setAttribute("aria-label", enabled ? "Disable magnifying glass" : "Enable magnifying glass");
  if (!enabled) clearMagnifier();
}

function updateNearby() {
  if (!activeScene || sceneProgress.scene_phase !== "exploration") return;
  activeScene.entities.filter(isSceneClue).forEach((entity) => {
    layer.querySelector(`[data-entity-id="${entity.id}"]`)?.classList.toggle("revealed", isClueRevealed(entity));
  });
  nearby = activeScene.entities
    .filter((entity) => entity.interaction && (!isSceneClue(entity) || isClueRevealed(entity)))
    .map((entity) => ({ entity, distance: distanceTo(entity) }))
    .filter(({ distance }) => distance < 64)
    .sort((a, b) => a.distance - b.distance)[0]?.entity ?? null;
  prompt.hidden = !nearby || !dialogue.hidden;
  if (nearby && dialogue.hidden) {
    const placement = positionForEntity(nearby);
    prompt.querySelector("span").textContent = interactionLabel(nearby);
    prompt.style.left = `${((placement.x + placement.width / 2) / activeScene.width) * 100}%`;
    prompt.style.top = `${(placement.y / activeScene.height) * 100}%`;
    status.textContent = `Near ${interactionLabel(nearby)}. Press E to interact.`;
  } else if (!nearby && dialogue.hidden) {
    status.textContent = areRequiredCluesFound()
      ? "The evidence is ready. Share your deduction."
      : "Find something worth examining.";
  }
}

function renderPlayer() {
  playerNode.style.left = `${((player.x + player.width / 2) / activeScene.width) * 100}%`;
  playerNode.style.top = `${((player.y + player.height / 2) / activeScene.height) * 100}%`;
}

function updateStoryCopy() {
  chapterIndex.textContent = String(activeScene.position).padStart(2, "0");
  chapterTotal.textContent = String(scenes.length).padStart(2, "0");
  sceneLocation.textContent = activeScene.title.toUpperCase();
  sceneNumber.textContent = `Scene ${activeScene.position} of ${scenes.length}`;
  roomLabel.textContent = activeScene.title.toUpperCase();
  sidebarCopy.textContent = "Read, observe, then use arrow keys or WASD when the room opens.";
  sceneObjective.textContent = "Pay attention to what Watson notices. Holmes will test your deductions.";
  beatTitle.textContent = activeScene.position === 1 ? (sceneBible?.setting?.mood ?? "The case begins") : `Case file ${String(activeScene.position).padStart(2, "0")}`;
  sceneTitle.textContent = activeScene.title;
  narration.textContent = sceneProgress.scene_phase === "deduction"
    ? "Weigh the observations before deciding what deserves Holmes's attention."
    : sceneProgress.scene_phase === "closing"
      ? "Holmes considers what Watson has noticed."
      : sceneProgress.scene_phase === "complete"
        ? "This part of the case is complete."
        : "Search the scene. The story unfolds through what Watson notices.";
}

function buildRoom() {
  layer.replaceChildren();
  world.dataset.sceneId = activeScene.scene_id;
  world.dataset.visualTheme = activeScene.visual_theme ?? "default";
  world.dataset.layoutPreset = activeScene.layout_preset ?? "compact_interior";
  activeScene.entities.forEach((entity) => {
    const placement = positionForEntity(entity);
    const node = document.createElement("div");
    const examined = sceneProgress.examined_entity_ids.includes(entity.id);
    node.className = `entity ${entity.type}${entity.solid ? " solid" : ""}${entity.interaction ? " interactable" : ""}${isSceneClue(entity) ? " scene-clue" : ""}${examined ? " examined" : ""}`;
    node.dataset.entityId = entity.id;
    if (isToggleableEnvironment(entity)) {
      node.classList.toggle("is-off", !isEnvironmentActive(entity));
      node.setAttribute("aria-label", isEnvironmentActive(entity) ? "Lit lamp" : "Unlit lamp");
    }
    Object.assign(node.style, {
      left: `${(placement.x / activeScene.width) * 100}%`,
      top: `${(placement.y / activeScene.height) * 100}%`,
      width: `${(placement.width / activeScene.width) * 100}%`,
      height: `${(placement.height / activeScene.height) * 100}%`
    });
    if (TABLE_PROPS[entity.id]) {
      const props = document.createElement("div");
      props.className = "table-props";
      TABLE_PROPS[entity.id].forEach((prop) => {
        const book = document.createElement("span");
        book.className = `book-sprite ${prop}`;
        props.append(book);
      });
      node.append(props);
    }
    if (entity.interaction) node.addEventListener("click", () => {
      if (sceneProgress.scene_phase !== "exploration") return;
      if (distanceTo(entity) < 64) {
        nearby = entity;
        interact();
      } else {
        status.textContent = "Watson needs to move closer before examining that.";
      }
    });
    layer.append(node);
  });
  world.classList.toggle(
    "lamp-lit",
    activeScene.entities.some((entity) => isToggleableEnvironment(entity) && isEnvironmentActive(entity))
  );
}

function progressUrl() {
  return `${API_BASE_URL}/playthroughs/${playthroughId}/chapters/${chapterId}/progress`;
}

async function saveProgress() {
  try {
    const response = await fetch(progressUrl(), { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(sceneProgress) });
    if (!response.ok) throw new Error(`Progress save failed (${response.status})`);
  } catch (error) {
    console.error(error);
    status.textContent = "Your progress could not be saved. Try again.";
  }
}

function activeBeats() {
  return sceneProgress.scene_phase === "opening" ? (activeScene.opening_beats ?? []) : (activeScene.closing_beats ?? []);
}

function showNarrativeBeat() {
  const beats = activeBeats();
  const beat = beats[sceneProgress.current_beat_index];
  if (!beat) {
    finishNarrativePhase();
    return;
  }
  storySpeaker.textContent = beat.speaker ?? (beat.kind === "thought" ? "Dr. Watson" : "Narrator");
  storyText.textContent = beat.text;
  storyNext.textContent = sceneProgress.current_beat_index === beats.length - 1 ? "Continue" : "Next";
  storyPanel.hidden = false;
  clearMagnifier();
  magnifierButton.hidden = true;
  setMagnifierEnabled(false);
  prompt.hidden = true;
}

async function advanceNarrative() {
  sceneProgress.current_beat_index += 1;
  await saveProgress();
  showNarrativeBeat();
}

function finishNarrativePhase() {
  storyPanel.hidden = true;
  sceneProgress.current_beat_index = 0;
  if (sceneProgress.scene_phase === "opening") {
    sceneProgress.scene_phase = "exploration";
    void saveProgress();
    magnifierButton.hidden = false;
    if (areRequiredCluesFound()) openDeduction();
    else {
      status.textContent = "The room is yours. Look closely.";
      world.focus();
    }
    return;
  }
  sceneProgress.completed_scene_ids.push(activeScene.scene_id);
  sceneProgress.scene_phase = "complete";
  continueButton.hidden = false;
  status.textContent = activeScene.position === scenes.length ? "The case is ready to be closed." : "This part of the case is complete.";
  void saveProgress();
}

function interact() {
  if (!nearby || sceneProgress.scene_phase !== "exploration") return;
  const { interaction } = nearby;
  if (isToggleableEnvironment(nearby)) {
    toggleEnvironment(nearby);
    return;
  }
  if (interaction.inspection) {
    openInspection(nearby);
    return;
  }
  speaker.textContent = interaction.speaker;
  dialogueText.textContent = `“${interaction.text}”`;
  dialogue.hidden = false;
  clearMagnifier();
  prompt.hidden = true;
  status.textContent = interaction.status;
  recordInteraction(nearby.id);
}

function toggleEnvironment(entity) {
  const key = environmentStateKey(entity);
  const nowLit = !isEnvironmentActive(entity);
  environmentStates.set(key, nowLit);
  layer.querySelector(`[data-entity-id="${entity.id}"]`)?.classList.toggle("is-off", !nowLit);
  world.classList.toggle(
    "lamp-lit",
    activeScene.entities.some((item) => isToggleableEnvironment(item) && isEnvironmentActive(item))
  );
  status.textContent = nowLit ? "Watson switches on the lamp." : "Watson switches off the lamp.";
  prompt.querySelector("span").textContent = nowLit ? "switch off the lamp" : "switch on the lamp";
}

function openInspection(entity) {
  const { interaction } = entity;
  const { inspection } = interaction;
  inspectedEntity = entity;
  inspectionPaper.dataset.visualType = inspection.visual_type;
  inspectionType.textContent = inspection.visual_type.replace(/[-_]/g, " ");
  inspectionTitle.textContent = inspection.title;
  inspectionSubtitle.textContent = inspection.subtitle ?? "";
  inspectionSubtitle.hidden = !inspection.subtitle;
  inspectionCopy.replaceChildren(...inspection.paragraphs.map((paragraph) => {
    const text = document.createElement("p");
    text.textContent = paragraph;
    return text;
  }));
  closeInspection.textContent = isSceneClue(entity) ? "File this clue away" : "Close";
  inspectionReader.hidden = false;
  clearMagnifier();
  setMagnifierEnabled(false);
  magnifierButton.hidden = true;
  prompt.hidden = true;
  status.textContent = `Reading ${interaction.label}.`;
}

function closeInspectionReader() {
  if (!inspectedEntity) return;
  const { interaction } = inspectedEntity;
  inspectionReader.hidden = true;
  recordInteraction(inspectedEntity.id);
  status.textContent = interaction.status;
  inspectedEntity = null;
  if (areRequiredCluesFound() && !isActiveSceneComplete()) openDeduction();
  else {
    magnifierButton.hidden = false;
    updateNearby();
    world.focus();
  }
}

function closeInteraction() {
  dialogue.hidden = true;
  if (areRequiredCluesFound() && !isActiveSceneComplete()) openDeduction();
  else {
    updateNearby();
    world.focus();
  }
}

function recordInteraction(entityId) {
  if (!sceneProgress.examined_entity_ids.includes(entityId)) {
    sceneProgress.examined_entity_ids.push(entityId);
    layer.querySelector(`[data-entity-id="${entityId}"]`)?.classList.add("examined");
    void saveProgress();
  }
}

function selectedOption() {
  return activeScene.deduction?.options.find((option) => sceneProgress.selected_choice_ids.includes(option.id));
}

function openDeduction() {
  if (!activeScene.deduction || isActiveSceneComplete()) {
    sceneProgress.scene_phase = "closing";
    showNarrativeBeat();
    return;
  }
  sceneProgress.scene_phase = "deduction";
  deductionPrompt.textContent = activeScene.deduction.prompt;
  deductionOptions.replaceChildren();
  deductionResponse.hidden = true;
  deductionNext.hidden = true;
  const chosen = selectedOption();
  activeScene.deduction.options.forEach((option) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = option.label;
    button.disabled = Boolean(chosen);
    button.classList.toggle("selected", chosen?.id === option.id);
    button.addEventListener("click", () => chooseDeduction(option));
    deductionOptions.append(button);
  });
  if (chosen) showDeductionResponse(chosen);
  deductionPanel.hidden = false;
  clearMagnifier();
  magnifierButton.hidden = true;
  setMagnifierEnabled(false);
  prompt.hidden = true;
}

function showDeductionResponse(option) {
  deductionResponse.textContent = `Holmes: “${option.response}”`;
  deductionResponse.hidden = false;
  deductionNext.hidden = false;
}

async function chooseDeduction(option) {
  if (selectedOption()) return;
  sceneProgress.selected_choice_ids.push(option.id);
  sceneProgress.deduction_score += option.score;
  deductionOptions.querySelectorAll("button").forEach((button) => { button.disabled = true; button.classList.toggle("selected", button.textContent === option.label); });
  showDeductionResponse(option);
  await saveProgress();
}

async function startClosing() {
  deductionPanel.hidden = true;
  sceneProgress.scene_phase = "closing";
  sceneProgress.current_beat_index = 0;
  await saveProgress();
  showNarrativeBeat();
}

function activateScene(position) {
  activeScene = scenes.find((scene) => scene.position === position) ?? scenes[0];
  Object.assign(player, activeScene.player);
  Object.assign(player, nearestClearPlayerPosition(player));
  nearby = null;
  dialogue.hidden = true;
  storyPanel.hidden = true;
  deductionPanel.hidden = true;
  magnifierButton.hidden = sceneProgress.scene_phase !== "exploration";
  if (magnifierButton.hidden) setMagnifierEnabled(false);
  continueButton.hidden = !isActiveSceneComplete();
  updateStoryCopy();
  buildRoom();
  renderPlayer();
  if (sceneProgress.scene_phase === "opening") {
    status.textContent = "The scene is about to begin.";
    showNarrativeBeat();
  }
  else if (sceneProgress.scene_phase === "closing") {
    status.textContent = "Holmes considers what Watson has noticed.";
    showNarrativeBeat();
  }
  else if (sceneProgress.scene_phase === "deduction") openDeduction();
  else {
    status.textContent = isActiveSceneComplete() ? "This part of the case is complete." : "The room is yours. Look closely.";
    world.focus();
  }
}

function showCaseComplete() {
  const maximumDeductionScore = scenes.reduce((total, scene) => total + Math.max(0, ...(scene.deduction?.options ?? []).map((option) => option.score)), 0);
  const scoreRatio = maximumDeductionScore ? sceneProgress.deduction_score / maximumDeductionScore : 0;
  const rating = scoreRatio >= 0.7 ? "Keen Eye" : scoreRatio >= 0.4 ? "Steady Observer" : "Case Closed";
  completionTitle.textContent = "The chapter is complete.";
  completionCopy.textContent = `You explored ${scenes.length} generated scenes from ${bookTitle.textContent}. Replay the chapter to revisit its evidence and deductions.`;
  caseRating.textContent = `${rating} — source-faithfulness score ${sceneProgress.deduction_score} / ${maximumDeductionScore}.`;
  completeCard.hidden = false;
  continueButton.hidden = true;
}

async function advanceScene() {
  if (!isActiveSceneComplete()) return;
  if (activeScene.position === scenes.length) {
    sceneProgress.chapter_complete = true;
    await saveProgress();
    showCaseComplete();
    return;
  }
  sceneProgress.current_scene_position = activeScene.position + 1;
  sceneProgress.scene_phase = "opening";
  sceneProgress.current_beat_index = 0;
  await saveProgress();
  activateScene(sceneProgress.current_scene_position);
}

async function beginPlaythrough() {
  sceneProgress.intro_seen = true;
  await saveProgress();
  briefing.hidden = true;
  gameCard.hidden = false;
  activateScene(sceneProgress.current_scene_position);
}

async function replayCase() {
  sceneProgress = defaultProgress();
  await saveProgress();
  completeCard.hidden = true;
  gameCard.hidden = true;
  briefing.hidden = false;
}

function frame(time) {
  const elapsed = Math.min((time - lastTime) / 1000, 0.05);
  lastTime = time;
  if (activeScene && !isOverlayOpen() && sceneProgress.scene_phase === "exploration") {
    const speed = activeScene.player.speed * elapsed;
    if (heldKeys.has("arrowleft") || heldKeys.has("a")) move("x", -speed);
    if (heldKeys.has("arrowright") || heldKeys.has("d")) move("x", speed);
    if (heldKeys.has("arrowup") || heldKeys.has("w")) move("y", -speed);
    if (heldKeys.has("arrowdown") || heldKeys.has("s")) move("y", speed);
    updateNearby();
    renderPlayer();
  }
  requestAnimationFrame(frame);
}

async function loadExperience() {
  try {
    const [scenesResponse, bibleResponse, progressResponse] = await Promise.all([
      fetch(`${API_BASE_URL}/chapters/${chapterId}/playable-scenes`),
      fetch(`${API_BASE_URL}/chapters/${chapterId}/scene-bible`),
      fetch(progressUrl())
    ]);
    if (!scenesResponse.ok) throw new Error(`Playable scenes request failed (${scenesResponse.status})`);
    scenes = await scenesResponse.json();
    if (!scenes.length) throw new Error("No playable scenes have been seeded.");
    sceneBible = bibleResponse.ok ? await bibleResponse.json() : null;
    sceneProgress = normaliseProgress(progressResponse.ok ? await progressResponse.json() : null);
    if (sceneProgress.chapter_complete) {
      gameCard.hidden = false;
      activateScene(scenes.at(-1).position);
      showCaseComplete();
    } else if (!sceneProgress.intro_seen) briefing.hidden = false;
    else {
      gameCard.hidden = false;
      activateScene(sceneProgress.current_scene_position);
    }
    if (!animationStarted) { animationStarted = true; requestAnimationFrame(frame); }
  } catch (error) {
    console.error(error);
    gameCard.hidden = false;
    sceneLocation.textContent = "Scene unavailable";
    sceneTitle.textContent = "Storyloom could not load the saved case.";
    narration.textContent = "Update the playable-scene narrative data, then reload this page.";
    status.textContent = "Waiting for the local Storyloom API.";
  }
}

window.addEventListener("keydown", (event) => {
  const key = event.key.toLowerCase();
  if (["arrowleft", "arrowright", "arrowup", "arrowdown", "w", "a", "s", "d", "e", "enter", " "].includes(key)) event.preventDefault();
  if (key === "e" || key === "enter" || key === " ") {
    if (!storyPanel.hidden) { void advanceNarrative(); return; }
    if (!inspectionReader.hidden) { closeInspectionReader(); return; }
    if (!dialogue.hidden) { closeInteraction(); return; }
  }
  if (key === "escape" && !inspectionReader.hidden) {
    closeInspectionReader();
    return;
  }
  if (!activeScene || !completeCard.hidden) return;
  if (key === "e") interact();
  else if (key === "escape") closeInteraction();
  else heldKeys.add(key);
});
window.addEventListener("keyup", (event) => heldKeys.delete(event.key.toLowerCase()));
world.addEventListener("pointerdown", () => world.focus());
world.addEventListener("pointermove", (event) => {
  if (!activeScene || !magnifierEnabled || sceneProgress?.scene_phase !== "exploration" || isOverlayOpen()) {
    clearMagnifier();
    return;
  }
  const bounds = world.getBoundingClientRect();
  const pointerX = event.clientX - bounds.left;
  const pointerY = event.clientY - bounds.top;
  magnifier.style.left = `${pointerX}px`;
  magnifier.style.top = `${pointerY}px`;
  world.style.setProperty("--lens-x", `${(pointerX / bounds.width) * 100}%`);
  world.style.setProperty("--lens-y", `${(pointerY / bounds.height) * 100}%`);
  magnifier.hidden = false;
  const scenePoint = {
    x: (pointerX / bounds.width) * activeScene.width,
    y: (pointerY / bounds.height) * activeScene.height
  };
  const entity = closestInspectableAtPoint(scenePoint);
  setMagnifiedNode(entity ? layer.querySelector(`[data-entity-id="${entity.id}"]`) : null);
});
world.addEventListener("pointerleave", clearMagnifier);
magnifierButton.addEventListener("click", () => setMagnifierEnabled(!magnifierEnabled));
closeDialogue.addEventListener("click", closeInteraction);
closeInspection.addEventListener("click", closeInspectionReader);
libraryButton.addEventListener("click", () => openLibrary());
closeLibrary.addEventListener("click", hideLibrary);
uploadForm.addEventListener("submit", importBook);
storyNext.addEventListener("click", () => void advanceNarrative());
deductionNext.addEventListener("click", () => void startClosing());
beginCase.addEventListener("click", () => void beginPlaythrough());
continueButton.addEventListener("click", () => void advanceScene());
replayButton.addEventListener("click", () => void replayCase());
reset.addEventListener("click", resetActiveSceneProgress);

openLibrary({ landing: true });

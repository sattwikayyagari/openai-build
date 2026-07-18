const world = document.querySelector("#game-world");
const layer = document.querySelector("#entities-layer");
const playerNode = document.querySelector("#player");
const prompt = document.querySelector("#interaction-prompt");
const dialogue = document.querySelector("#dialogue");
const speaker = document.querySelector("#speaker");
const dialogueText = document.querySelector("#dialogue-text");
const status = document.querySelector("#status");
const reset = document.querySelector("#reset-button");
const continueButton = document.querySelector("#continue-button");
const closeDialogue = document.querySelector("#close-dialogue");
const beginCase = document.querySelector("#begin-case");
const replayButton = document.querySelector("#replay-case");
const briefing = document.querySelector("#case-briefing");
const gameCard = document.querySelector("#game-card");
const completeCard = document.querySelector("#case-complete");
const caseRating = document.querySelector("#case-rating");
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

const API_BASE_URL = "http://127.0.0.1:8000";
const CHAPTER_ID = "fbc2c27a-5ce5-4c50-bc70-aa117416aa1c";
const PLAYTHROUGH_STORAGE_KEY = "storyloom-playthrough-id";

const heldKeys = new Set();
const player = { x: 0, y: 0, width: 0, height: 0, speed: 0 };
let scenes = [];
let activeScene = null;
let sceneBible = null;
let sceneProgress = null;
let nearby = null;
let lastTime = 0;
let animationStarted = false;

function getPlaythroughId() {
  const savedId = localStorage.getItem(PLAYTHROUGH_STORAGE_KEY);
  if (savedId) return savedId;
  const newId = crypto.randomUUID();
  localStorage.setItem(PLAYTHROUGH_STORAGE_KEY, newId);
  return newId;
}

const playthroughId = getPlaythroughId();

function defaultProgress() {
  return {
    playthrough_id: playthroughId,
    chapter_id: CHAPTER_ID,
    intro_seen: false,
    current_scene_position: 1,
    chapter_complete: false,
    completed_scene_ids: [],
    examined_entity_ids: []
  };
}

function normaliseProgress(progress) {
  return { ...defaultProgress(), ...progress };
}

function overlaps(a, b) {
  return a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
}

function isBlocked(next) {
  const { walkable_area: walkableArea } = activeScene;
  const outsideWalkableArea = next.x < walkableArea.x
    || next.y < walkableArea.y
    || next.x + next.width > walkableArea.x + walkableArea.width
    || next.y + next.height > walkableArea.y + walkableArea.height;
  return outsideWalkableArea || activeScene.entities.some((entity) => entity.solid && overlaps(next, entity));
}

function move(axis, amount) {
  const next = { ...player, [axis]: player[axis] + amount };
  if (!isBlocked(next)) player[axis] = next[axis];
}

function isActiveSceneComplete() {
  return sceneProgress?.completed_scene_ids.includes(activeScene?.scene_id);
}

function distanceTo(entity) {
  const playerCenter = { x: player.x + player.width / 2, y: player.y + player.height / 2 };
  const entityCenter = { x: entity.x + entity.width / 2, y: entity.y + entity.height / 2 };
  return Math.hypot(playerCenter.x - entityCenter.x, playerCenter.y - entityCenter.y);
}

function updateNearby() {
  nearby = activeScene.entities
    .filter((entity) => entity.interaction)
    .map((entity) => ({ entity, distance: distanceTo(entity) }))
    .filter(({ distance }) => distance < 54)
    .sort((a, b) => a.distance - b.distance)[0]?.entity ?? null;

  prompt.hidden = !nearby || !dialogue.hidden;
  if (nearby && dialogue.hidden) {
    prompt.querySelector("span").textContent = nearby.interaction.label;
    prompt.style.left = `${((nearby.x + nearby.width / 2) / activeScene.width) * 100}%`;
    prompt.style.top = `${(nearby.y / activeScene.height) * 100}%`;
    status.textContent = `Near ${nearby.interaction.label}. Press E to examine.`;
  } else if (!nearby && dialogue.hidden) {
    status.textContent = isActiveSceneComplete()
      ? "The key clue is recorded. Continue when you are ready."
      : "Find something worth examining.";
  }
}

function renderPlayer() {
  playerNode.style.left = `${((player.x + player.width / 2) / activeScene.width) * 100}%`;
  playerNode.style.top = `${((player.y + player.height / 2) / activeScene.height) * 100}%`;
}

function interact() {
  if (!nearby) return;
  const { interaction } = nearby;
  speaker.textContent = interaction.speaker;
  dialogueText.textContent = `“${interaction.text}”`;
  dialogue.hidden = false;
  prompt.hidden = true;
  status.textContent = interaction.status;
  recordInteraction(nearby.id);
}

function closeInteraction() {
  dialogue.hidden = true;
  updateNearby();
  world.focus();
}

function buildRoom() {
  layer.replaceChildren();
  world.dataset.sceneId = activeScene.scene_id;
  activeScene.entities.forEach((entity) => {
    const node = document.createElement("div");
    const examined = sceneProgress.examined_entity_ids.includes(entity.id);
    node.className = `entity ${entity.type}${entity.solid ? " solid" : ""}${entity.interaction ? " interactable" : ""}${examined ? " examined" : ""}`;
    node.dataset.entityId = entity.id;
    Object.assign(node.style, {
      left: `${(entity.x / activeScene.width) * 100}%`,
      top: `${(entity.y / activeScene.height) * 100}%`,
      width: `${(entity.width / activeScene.width) * 100}%`,
      height: `${(entity.height / activeScene.height) * 100}%`
    });
    if (entity.interaction) node.addEventListener("click", () => { nearby = entity; interact(); });
    layer.append(node);
  });
}

function updateStoryCopy() {
  bookTitle.textContent = "The Memoirs of Sherlock Holmes";
  chapterIndex.textContent = String(activeScene.position).padStart(2, "0");
  chapterTotal.textContent = String(scenes.length).padStart(2, "0");
  sceneLocation.textContent = activeScene.title.toUpperCase();
  sceneNumber.textContent = `Scene ${activeScene.position} of ${scenes.length}`;
  roomLabel.textContent = activeScene.title.toUpperCase();
  sidebarCopy.textContent = "Walk with arrow keys or WASD. Press E when prompted.";
  sceneObjective.textContent = "Search the room. The story begins with what you notice.";
  beatTitle.textContent = activeScene.position === 1
    ? (sceneBible?.setting?.mood ?? "The case begins")
    : `Case file ${String(activeScene.position).padStart(2, "0")}`;
  sceneTitle.textContent = activeScene.title;
  narration.textContent = activeScene.objective;
}

function progressUrl() {
  return `${API_BASE_URL}/playthroughs/${playthroughId}/chapters/${CHAPTER_ID}/progress`;
}

async function saveProgress() {
  try {
    const response = await fetch(progressUrl(), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sceneProgress)
    });
    if (!response.ok) throw new Error(`Progress save failed (${response.status})`);
  } catch (error) {
    console.error(error);
    status.textContent = "Your progress could not be saved. Try again.";
  }
}

function recordInteraction(entityId) {
  if (!sceneProgress) return;
  if (!sceneProgress.examined_entity_ids.includes(entityId)) {
    sceneProgress.examined_entity_ids.push(entityId);
    layer.querySelector(`[data-entity-id="${entityId}"]`)?.classList.add("examined");
  }

  if (entityId === activeScene.completion_entity_id && !isActiveSceneComplete()) {
    sceneProgress.completed_scene_ids.push(activeScene.scene_id);
    continueButton.hidden = false;
    status.textContent = activeScene.position === scenes.length
      ? "The case is ready to be closed."
      : "The key clue is recorded. Continue when you are ready.";
  }
  void saveProgress();
}

function activateScene(position) {
  activeScene = scenes.find((scene) => scene.position === position) ?? scenes[0];
  Object.assign(player, activeScene.player);
  nearby = null;
  dialogue.hidden = true;
  continueButton.hidden = !isActiveSceneComplete();
  updateStoryCopy();
  buildRoom();
  renderPlayer();
  status.textContent = isActiveSceneComplete()
    ? "The key clue is recorded. Continue when you are ready."
    : "Find something worth examining.";
  world.focus();
}

function showCaseComplete() {
  const interactiveCount = scenes.flatMap((scene) => scene.entities).filter((entity) => entity.interaction).length;
  const examinedCount = sceneProgress.examined_entity_ids.length;
  const rating = examinedCount >= interactiveCount
    ? "Keen Eye — every available clue was examined."
    : examinedCount >= Math.ceil(interactiveCount * 0.6)
      ? "Steady Observer — Holmes would approve of your attention."
      : "Case Closed — the essential clues carried you through.";
  caseRating.textContent = `${rating} ${examinedCount} of ${interactiveCount} observations recorded.`;
  completeCard.hidden = false;
  continueButton.hidden = true;
  world.blur();
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
  if (activeScene && !dialogue.hidden && heldKeys.size) heldKeys.clear();
  if (activeScene && dialogue.hidden && !completeCard.hidden) {
    renderPlayer();
    requestAnimationFrame(frame);
    return;
  }
  if (activeScene && dialogue.hidden) {
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
      fetch(`${API_BASE_URL}/chapters/${CHAPTER_ID}/playable-scenes`),
      fetch(`${API_BASE_URL}/chapters/${CHAPTER_ID}/scene-bible`),
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
    } else if (!sceneProgress.intro_seen) {
      briefing.hidden = false;
    } else {
      gameCard.hidden = false;
      activateScene(sceneProgress.current_scene_position);
    }

    if (!animationStarted) {
      animationStarted = true;
      requestAnimationFrame(frame);
    }
  } catch (error) {
    console.error(error);
    gameCard.hidden = false;
    sceneLocation.textContent = "Scene unavailable";
    sceneTitle.textContent = "Storyloom could not load the saved case.";
    narration.textContent = "Start the FastAPI server, then reload this page.";
    status.textContent = "Waiting for the local Storyloom API.";
  }
}

window.addEventListener("keydown", (event) => {
  const key = event.key.toLowerCase();
  if (["arrowleft", "arrowright", "arrowup", "arrowdown", "w", "a", "s", "d", "e"].includes(key)) event.preventDefault();
  if (!activeScene || completeCard.hidden === false) return;
  if (key === "e") {
    if (dialogue.hidden) interact(); else closeInteraction();
  } else if (key === "escape") {
    closeInteraction();
  } else {
    heldKeys.add(key);
  }
});
window.addEventListener("keyup", (event) => heldKeys.delete(event.key.toLowerCase()));
world.addEventListener("pointerdown", () => world.focus());
closeDialogue.addEventListener("click", closeInteraction);
beginCase.addEventListener("click", beginPlaythrough);
continueButton.addEventListener("click", advanceScene);
replayButton.addEventListener("click", replayCase);
reset.addEventListener("click", () => {
  if (!activeScene) return;
  Object.assign(player, activeScene.player);
  closeInteraction();
  renderPlayer();
});

loadExperience();

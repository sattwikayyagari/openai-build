import { detectiveOffice } from "./mock-data.js";

const world = document.querySelector("#game-world");
const layer = document.querySelector("#entities-layer");
const playerNode = document.querySelector("#player");
const prompt = document.querySelector("#interaction-prompt");
const dialogue = document.querySelector("#dialogue");
const speaker = document.querySelector("#speaker");
const dialogueText = document.querySelector("#dialogue-text");
const status = document.querySelector("#status");
const reset = document.querySelector("#reset-button");
const closeDialogue = document.querySelector("#close-dialogue");

const heldKeys = new Set();
const player = { ...detectiveOffice.player };
let nearby = null;
let lastTime = 0;

function overlaps(a, b) {
  return a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
}

function isBlocked(next) {
  const outsideRoom = next.x < 0 || next.y < 0 || next.x + next.width > detectiveOffice.width || next.y + next.height > detectiveOffice.height;
  return outsideRoom || detectiveOffice.entities.some((entity) => entity.solid && overlaps(next, entity));
}

function move(axis, amount) {
  const next = { ...player, [axis]: player[axis] + amount };
  if (!isBlocked(next)) player[axis] = next[axis];
}

function distanceTo(entity) {
  const playerCenter = { x: player.x + player.width / 2, y: player.y + player.height / 2 };
  const entityCenter = { x: entity.x + entity.width / 2, y: entity.y + entity.height / 2 };
  return Math.hypot(playerCenter.x - entityCenter.x, playerCenter.y - entityCenter.y);
}

function updateNearby() {
  nearby = detectiveOffice.entities
    .filter((entity) => entity.interaction)
    .map((entity) => ({ entity, distance: distanceTo(entity) }))
    .filter(({ distance }) => distance < 54)
    .sort((a, b) => a.distance - b.distance)[0]?.entity ?? null;
  prompt.hidden = !nearby || !dialogue.hidden;
  if (nearby && dialogue.hidden) {
    prompt.querySelector("span").textContent = nearby.interaction.label;
    prompt.style.left = `${((nearby.x + nearby.width / 2) / detectiveOffice.width) * 100}%`;
    prompt.style.top = `${(nearby.y / detectiveOffice.height) * 100}%`;
    status.textContent = `Near ${nearby.interaction.label}. Press E to examine.`;
  } else if (!nearby && dialogue.hidden) status.textContent = "Find something worth examining.";
}

function renderPlayer() {
  playerNode.style.left = `${((player.x + player.width / 2) / detectiveOffice.width) * 100}%`;
  playerNode.style.top = `${((player.y + player.height / 2) / detectiveOffice.height) * 100}%`;
}

function interact() {
  if (!nearby) return;
  const { interaction } = nearby;
  speaker.textContent = interaction.speaker;
  dialogueText.textContent = `“${interaction.text}”`;
  dialogue.hidden = false;
  prompt.hidden = true;
  status.textContent = interaction.status;
}

function closeInteraction() {
  dialogue.hidden = true;
  updateNearby();
  world.focus();
}

function buildRoom() {
  detectiveOffice.entities.forEach((entity) => {
    const node = document.createElement("div");
    node.className = `entity ${entity.type}${entity.solid ? " solid" : ""}${entity.interaction ? " interactable" : ""}`;
    Object.assign(node.style, {
      left: `${(entity.x / detectiveOffice.width) * 100}%`, top: `${(entity.y / detectiveOffice.height) * 100}%`,
      width: `${(entity.width / detectiveOffice.width) * 100}%`, height: `${(entity.height / detectiveOffice.height) * 100}%`
    });
    if (entity.interaction) node.addEventListener("click", () => { nearby = entity; interact(); });
    layer.append(node);
  });
}

function frame(time) {
  const elapsed = Math.min((time - lastTime) / 1000, 0.05);
  lastTime = time;
  if (dialogue.hidden) {
    const speed = detectiveOffice.player.speed * elapsed;
    if (heldKeys.has("arrowleft") || heldKeys.has("a")) move("x", -speed);
    if (heldKeys.has("arrowright") || heldKeys.has("d")) move("x", speed);
    if (heldKeys.has("arrowup") || heldKeys.has("w")) move("y", -speed);
    if (heldKeys.has("arrowdown") || heldKeys.has("s")) move("y", speed);
    updateNearby();
  }
  renderPlayer();
  requestAnimationFrame(frame);
}

window.addEventListener("keydown", (event) => {
  const key = event.key.toLowerCase();
  if (["arrowleft", "arrowright", "arrowup", "arrowdown", "w", "a", "s", "d", "e"].includes(key)) event.preventDefault();
  if (key === "e") interact(); else if (key === "escape") closeInteraction(); else heldKeys.add(key);
});
window.addEventListener("keyup", (event) => heldKeys.delete(event.key.toLowerCase()));
world.addEventListener("pointerdown", () => world.focus());
closeDialogue.addEventListener("click", closeInteraction);
reset.addEventListener("click", () => { Object.assign(player, detectiveOffice.player); closeInteraction(); renderPlayer(); });

buildRoom(); renderPlayer(); world.focus(); requestAnimationFrame(frame);

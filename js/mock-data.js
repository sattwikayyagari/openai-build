// This fixed geometry is the contract for generated scenes: all coordinates use the 16:9 room grid (640 × 360).
export const detectiveOffice = {
  width: 640,
  height: 360,
  player: { x: 294, y: 264, width: 18, height: 24, speed: 142 },
  entities: [
    { type: "window", x: 64, y: 47, width: 82, height: 96, solid: true },
    { type: "portrait", x: 491, y: 40, width: 48, height: 65, solid: true },
    { type: "door", x: 560, y: 116, width: 58, height: 151, solid: true, interaction: { label: "the door", speaker: "Narrator", text: "Someone is climbing the stairs. The expected visitor has not yet knocked.", status: "The visitor is nearly here." } },
    { type: "solid", x: 193, y: 91, width: 205, height: 57, solid: true },
    { type: "lamp", x: 353, y: 64, width: 17, height: 29, interaction: { label: "the lamp", speaker: "Narrator", text: "Its steady amber light holds the rain-darkened room at bay.", status: "The lamp burns warmly." } },
    { type: "letter", x: 278, y: 102, width: 28, height: 19, interaction: { label: "the sealed letter", speaker: "Sherlock Holmes", text: "The paper is Bohemian, Watson. Its sender has gone to unusual lengths.", status: "You have examined the letter." } },
    { type: "rug", x: 151, y: 213, width: 292, height: 91 },
    { type: "solid", x: 18, y: 266, width: 110, height: 53, solid: true },
    { type: "solid", x: 443, y: 276, width: 126, height: 43, solid: true }
  ]
};

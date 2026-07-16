# Storyloom

An interactive, chapter-level experience for public-domain literature.

## Current stage

The frontend is a static vanilla HTML/CSS/JavaScript playable prototype. It currently contains a warm Baker Street detective-office scene with:

- WASD / arrow-key movement
- rectangle collision against fixed room objects
- proximity prompts and `E` interactions
- a small dialogue layer for scene discoveries

The scene data lives in `js/mock-data.js`. Each generated scene should use the same `640 x 360` logical coordinate grid and provide `entities` with `x`, `y`, `width`, `height`, `solid`, and optional `interaction` fields. The renderer maps that grid responsively to the visible game area.

## Planned API boundary

- `POST /books` — upload a public-domain book
- `GET /books/{book_id}/chapters` — list extracted chapters
- `POST /chapters/{chapter_id}/bible` — create a cached scene bible
- `POST /chapters/{chapter_id}/scene` — create a validated playable scene
- `GET` / `PUT /progress/{chapter_id}` — resume state

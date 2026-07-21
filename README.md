# Storyloom

An interactive, chapter-level experience for public-domain literature. Upload a UTF-8 `.txt` book, select a detected chapter, and Storyloom generates scenes, clues, and deductions that can be explored as Dr. Watson.

# Description of the project

There are many people who prefer visual and interactive forms of entertainment than reading books. Because of that they lose on a lot of great stories. This project is for people like them. I am one of such people who absolutely loves a great story but I do not have the patience to sit through and read hundreds or thousands of pages. So this is the project I came up with to handle that. Storyloom takes a .txt files and based on the user chapter choice converts it into a playable scene with save persistance.

# Codex collaberation

I had this idea for some time but I was not sure on how to proceed as I was unfamiliar with any frontend frameworks and my backend knowledge was mostly theoritical, centred on FastAPI. So when I began the project, I mentioned to Codex that I will be in charge of backend and that it will be in charge of frontend. Because my goal was to learn fastapi as a absoulte beginner, I instruced codex to explain concepts to me whenever I needed a primer. I have used GPT 5.6 Terra throughout the project starting with ideation: deciding what to build, which book to demo and what architecture to choose. As I was unaware with most of these, Codex helped me with this enormously. Even for the demo recording part, I consulted with Codex and followed the steps it generated to do it. Architecturally, Storyloom uses a  640 × 360 2D coordinate plane for every playable scene and has objects and collision objects taht can be reusable. An LLM produces a structured, source-grounded scene plan and our backend converts that into playable JSON with all the entities. We initially used a single model to generate scenes. After several iterations, we added a separate reviewer pass to evaluate the generated output for consistency, source grounding, and hallucinations. We used Anthropic models for the final generation and review workflow after testing the pipeline with multiple providers.

## Judge quick start — no API key required

This repository includes a pre-generated **Silver Blaze** demo in `data/storyloom.db`. Judges can play it without rebuilding the pipeline, uploading a book, or providing an LLM key.

Requirements: Python 3.12+ and [uv](https://docs.astral.sh/uv/). The frontend uses only browser-native HTML, CSS, and JavaScript.

Open two terminals from the repository root.

```powershell
# Terminal 1: API
uv run fastapi dev backend/main.py
```

```powershell
# Terminal 2: frontend
python -m http.server 5500
```

Then open [http://127.0.0.1:5500](http://127.0.0.1:5500). The preloaded **Silver Blaze** playable chapter opens automatically. Use arrow keys or WASD to walk, press `E` at a prompt to inspect evidence, and complete the deduction prompts to continue.

The default local API is `http://127.0.0.1:8000`; the frontend server must use port `5500` because that is the development CORS origin.

## Generate a new playable chapter

Generation is optional for judging the included demo. To generate from another public-domain `.txt` file, set one provider in a root `.env` file:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_GENERATION_MODEL=claude-sonnet-4-5-20250929
ANTHROPIC_REVIEW_MODEL=claude-sonnet-4-5-20250929
```

Groq and Ollama are also supported by the backend. Start the two local servers above, use the upload panel, import a UTF-8 `.txt` file, select a chapter, then choose **Generate playable chapter**.

## What the project demonstrates

- Chapter extraction from uploaded public-domain text
- Long-chapter chunking and source-grounded storyboard generation
- Retrieval of the relevant source chunks per scene
- Structured scene plans validated with Pydantic
- Evidence interactions, deductions, persistent playthrough progress, and replay
- A static, browser-playable detective scene rendered from generated data

## How Codex and GPT-5.6 were used

Codex was used throughout the build to design the chapter-to-scene pipeline,
implement the FastAPI and browser game integration, refine source-grounding
rules, debug structured-output validation, and prepare the testing workflow.
GPT-5.6 powered that implementation work in Codex.

At runtime, Storyloom uses an LLM-backed generation pipeline to turn source
text into a scene bible, a chapter storyboard, and structured playable scene
plans. The plans are validated before they become the evidence, dialogue, and
deductions shown in the game.

## Platforms

The app has been developed and tested on Windows with PowerShell. It should run on macOS and Linux with Python 3.12+, uv, and equivalent commands for starting a static server.

## Demo recording

The submitted demo video shows the upload-to-playable-chapter workflow and a complete Silver Blaze playthrough. The pre-generated database above is the fastest way to test the same interaction locally.

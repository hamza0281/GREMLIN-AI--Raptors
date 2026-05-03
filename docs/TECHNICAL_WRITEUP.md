# 🛠️ TECHNICAL WRITEUP — Garage Inference Hackathon

## 1. The Core Problem
QA testing is expensive and manual. Edge cases (what happens when a user pastes a massive emoji string into an email field?) are almost impossible to write traditional unit tests for because human developers don't naturally think in chaos.

## 2. The "Wow Gap" Thesis
Our thesis is simple but contrarian: **"We didn't fix the model's hallucinations. We weaponized them."**

Inference on tiny, Tier 1 models (like the 0.6B Qwen) usually results in poor instruction following, hallucinations, and formatting errors. Every other team is trying to prompt-engineer their small model to act like GPT-4. 

We realized that a model that naturally generates garbage is the **perfect fuzzing engine**. We engineered a wrapper around its stupidity to build an autonomous QA tool.

## 3. Engineering Implementation Details
We implemented the hackathon's required methodologies to turn random outputs into structured testing:

### A. Multi-Step Pipelines
The LLM does NOT navigate the web. It only does one tiny subtask.
1. Playwright crawls the DOM deterministically.
2. Playwright extracts the interactive element (e.g., `<input type="email" id="email">`).
3. The LLM is given this single context and asked: "Generate a chaotic input."
4. Playwright injects the input and presses submit.

### B. Structured Prompts (The Personas)
Instead of asking for "random text", we use 6 personas to channel the chaos into specific vectors:
* **The Hacker:** Natural tendency to output code -> Finds XSS/SQLi.
* **The Grandma:** Natural tendency to misunderstand fields -> Finds validation logic flaws.
* **The International Traveler:** Natural tendency to output Unicode/RTL -> Finds encoding crashes.

### C. Validation Layers
Small models often output empty strings or refuse to answer. We implemented a **Retry Engine**. If the output is unusable, a deterministic heuristic steps in, or the prompt is simplified and retried.

### D. Tool Use
The model has no direct internet access. All actions are executed via Python Playwright.

## 4. Why This Works
By isolating the LLM strictly to the "Chaos Generation" phase and using rigid, deterministic Python code for execution and error detection, we created a highly reliable tool powered by a highly unreliable model. 

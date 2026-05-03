# 🔥 Chaos-QA
> *"The model's stupidity IS its intelligence"*

![Chaos QA Banner](https://via.placeholder.com/1200x400/04060f/00f0ff?text=Chaos-QA:+Autonomous+Fuzzing+with+0.6B+LLMs)

**Chaos-QA** is an autonomous, AI-powered website testing tool built for the **GARAGE INFERENCE Hackathon**. It uses a deliberately tiny LLM's (Qwen 3 0.6B) natural tendency to hallucinate and output garbage as a *feature* — simulating chaotic users, finding real bugs, and generating professional reports.

## 🏆 Hackathon Alignment (Tier 1 Absolute Garage)
* **Model:** Qwen 3 0.6B Q4_K_M (via Ollama)
* **Cost:** $0.00
* **Data Privacy:** 100% Local Inference
* **Hackathon Techniques Used:** Multi-Step Pipeline, Tool Use (Playwright), Structured Prompts, Validation Layers.

## ✨ Features
1. **6 Specialized AI Personas**: Grandma, Accidental Hacker, Speed Demon, Toddler, Overthinking Dev, International Traveler.
2. **Autonomous DOM Parsing**: Extracts interactive elements and feeds context to the model.
3. **Real-time Live Feed**: WebSocket-powered telemetry showing the attack vectors live.
4. **Resilience Scoring**: Gamified "Chaos Score" based on survivability.
5. **Detailed Bug Reports**: Tracks reproduction steps, injected payloads, and severity.

## 🚀 One-Command Quickstart
Run the entire platform (Frontend Next.js + Backend FastAPI) with Docker:
```bash
docker-compose up --build
```
> **Note:** Ensure you have [Ollama](https://ollama.com/) running natively on your host machine and have pulled the model (`ollama pull qwen:0.5b`).

## 💻 CLI Usage
Don't like web interfaces? Run Chaos-QA straight from your terminal!
```bash
python -m cli https://your-target.com --duration 60 --personas hacker toddler
```

## 📂 Documentation Directory
Please refer to the `docs/` folder for the official hackathon submission requirements:
- [`TECHNICAL_WRITEUP.md`](./docs/TECHNICAL_WRITEUP.md) - Deep dive into the "Wow Gap".
- [`ARCHITECTURE.md`](./docs/ARCHITECTURE.md) - System design and pipeline steps.
- [`COST_METRICS.md`](./docs/COST_METRICS.md) - Inference latency and hardware requirements.
- [`KNOWN_FAILURES.md`](./docs/KNOWN_FAILURES.md) - Honest assessment of edge cases.

## 🤝 License
MIT License

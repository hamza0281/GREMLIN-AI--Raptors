
<div align="center">

```
  ██████╗ ██████╗ ███████╗███╗   ███╗██╗     ██╗███╗   ██╗    █████╗ ██╗
 ██╔════╝ ██╔══██╗██╔════╝████╗ ████║██║     ██║████╗  ██║   ██╔══██╗██║
 ██║  ███╗██████╔╝█████╗  ██╔████╔██║██║     ██║██╔██╗ ██║   ███████║██║
 ██║   ██║██╔══██╗██╔══╝  ██║╚██╔╝██║██║     ██║██║╚██╗██║   ██╔══██║██║
 ╚██████╔╝██║  ██║███████╗██║ ╚═╝ ██║███████╗██║██║ ╚████║   ██║  ██║██║
  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝  ╚═╝╚═╝
```

# 🔥 GREMLIN-AI — Autonomous AI-Powered Web Testing

### *"We didn't fix the model's hallucinations. We weaponized them."*

[![License: MIT](https://img.shields.io/badge/License-MIT-00f0ff.svg?style=for-the-badge)](LICENSE)
[![Model: Qwen 0.6B](https://img.shields.io/badge/LLM-Qwen%203%200.6B-ff0040.svg?style=for-the-badge)](https://ollama.com)
[![Cost: $0.00](https://img.shields.io/badge/Inference%20Cost-$0.00-00ff88.svg?style=for-the-badge)](#)
[![Built With: Playwright](https://img.shields.io/badge/Automation-Playwright-45ba4b.svg?style=for-the-badge)](https://playwright.dev)
[![Stack: Next.js + FastAPI](https://img.shields.io/badge/Stack-Next.js%20%2B%20FastAPI-8b5cf6.svg?style=for-the-badge)](#)

**[🌐 Live Demo](https://gremlin-ai-git-main-hamza0281s-projects.vercel.app)** · **[📖 Docs](#-documentation)** · **[🚀 Quick Start](#-one-command-setup)**

<img src="https://via.placeholder.com/900x400/04060f/00f0ff?text=🌐+3D+Cyber+Globe+%7C+Real-time+Attack+Telemetry+%7C+Live+Bug+Feed" alt="Gremlin-AI Dashboard" width="100%" style="border-radius: 12px; border: 1px solid #00f0ff33;" />

</div>

---

## 💡 The Idea That Changes Everything

Every startup, developer, and QA team faces the same nightmare:

> *"What happens when a user puts their home address in the email field? Or pastes SQL code into the search bar? Or clicks submit 12 times in a row?"*

**Hiring human chaos testers costs $50,000/year.** Writing edge case tests manually takes weeks. And even then — you miss things.

We found a better way.

**A 0.6B parameter AI model is naturally bad at following instructions.** It hallucinates. It forgets context. It outputs garbage. Every other team is trying to fix this problem.

**We turned it into a $50K/year QA engineer.**

```
Expected from a 0.6B model:     What GREMLIN-AI does with it:
─────────────────────────────   ──────────────────────────────────────
Barely completes a sentence  →  Finds REAL XSS vulnerabilities
Hallucinates random nonsense →  That nonsense IS the perfect fuzz input
Forgets instructions midway  →  Simulates distracted/confused users
Mixes up languages & formats →  Tests i18n and encoding robustness
Can't follow multi-step tasks→  Each task is ONE tiny step — it nails it
```

> **Hackathon Tier:** Absolute Garage (Tier 1) · **Model:** Qwen 3 0.6B Q4_K_M · **Cost:** $0.00

---

## ⚡ Features That Will Blow Your Mind

### 🎭 6 Specialized AI Gremlin Personas
Not random noise — **engineered chaos vectors** that target specific bug categories:

| Persona | Attack Vector | Bugs It Finds |
|---------|--------------|---------------|
| 👵 **The Confused Grandma** | Puts phone numbers in email fields, birthdays in names | Input validation failures, missing error messages |
| 🏴‍☠️ **The Accidental Hacker** | Naturally outputs SQL snippets, `<script>` tags | XSS vulnerabilities, SQL injection, unescaped HTML |
| ⚡ **The Speed Demon** | Double-clicks buttons, submits forms in 0.2s | Race conditions, double-submit bugs, loading failures |
| 🧒 **The Toddler** | Pure keyboard smash, random clicks | Unhandled exceptions, null pointer errors, crashes |
| 🤓 **The Overthinking Dev** | Pastes JSON, markdown, 10,000-char strings | Buffer overflows, rendering bugs, data truncation |
| 🌍 **The International Traveler** | RTL text, emojis, Unicode chaos | Encoding issues, RTL layout breaks, i18n failures |

### 🔴 Real-Time Live Dashboard
Watch the AI attack your app in real time:
- **Live telemetry feed** — every action streamed via WebSockets
- **Animated 3D globe** — shows attack origins globally
- **Chaos Resilience Score** — gamified score from 0-100
- **Professional bug reports** — severity, payload, reproduction steps, screenshots

### 🛡️ 8-Layer Engineering Scaffold
The model only does ONE thing — generate chaotic input. Everything else is bulletproof deterministic code:

```
Layer 1: DOM Parser          → Extracts all interactive elements intelligently
Layer 2: Structured Prompts  → Forces model output into JSON schema
Layer 3: Retry Engine        → Handles empty/broken model outputs automatically  
Layer 4: Action Validator    → Confirms action is executable before running
Layer 5: Console Monitor     → Catches JS errors, warnings, unhandled rejections
Layer 6: Network Monitor     → Captures 500 errors, failed API calls, timeouts
Layer 7: Screenshot Differ   → Before/after visual regression detection
Layer 8: Error Classifier    → Heuristic severity rating (Critical/High/Medium/Low)
```

---

## 📊 The Chaos Resilience Score

After every test, your app gets a battle-tested score:

```
╔══════════════════════════════════════════════════════╗
║           🎯 CHAOS RESILIENCE REPORT                 ║
╠══════════════════════════════════════════════════════╣
║  Target: https://your-awesome-app.com                ║
║  Pages Tested:        12                             ║
║  Elements Attacked:   47                             ║
║  Total Chaos Actions: 312                            ║
║                                                      ║
║  ✅ Survived:  287  (92%)                            ║
║  ❌ Crashed:     8  (2.5%)                           ║
║  ⚠️  Errors:    17  (5.5%)                           ║
║                                                      ║
║  🔒 Security Issues:  3  (1 Critical)                ║
║  🎨 UI/UX Issues:     7                              ║
║  💥 Crashes:          4                              ║
║  📱 Responsiveness:   3                              ║
║                                                      ║
║  CHAOS SCORE: 78 / 100  ⭐⭐⭐⭐                    ║
╚══════════════════════════════════════════════════════╝
```

---

## 🚀 One-Command Setup

**The entire platform — AI engine, backend, and beautiful dashboard — in one command:**

### Prerequisites
Make sure you have these installed:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com/) (for local AI inference)

### Step 1 — Pull the AI Model (One Time Only)
```bash
ollama pull qwen:0.5b
```

### Step 2 — Clone & Launch
```bash
git clone https://github.com/hamza0281/GREMLIN-AI--Raptors.git
cd GREMLIN-AI--Raptors
docker-compose up --build
```

### Step 3 — Open Dashboard
```
🌐 Frontend Dashboard:  http://localhost:3000
⚡ Backend API:         http://localhost:8000/docs
```

**That's it. Seriously. Three commands.**

---

## 💻 CLI Usage

Prefer the terminal? Run GREMLIN-AI as a one-liner:

```bash
# Test any website instantly
python -m cli https://your-target.com

# Specify which personas to unleash
python -m cli https://your-target.com --personas hacker grandma toddler

# Run for 2 minutes with custom output dir
python -m cli https://your-target.com --duration 120 --output ./my-reports
```

**Example output:**
```
   ☣  GREMLIN-AI ENGINE INITIALIZED
────────────────────────────────────
🎯  Target: https://your-target.com
🧠  Model:  Qwen 3 0.6B (Local, $0.00)
🎭  Personas: hacker, grandma, toddler
────────────────────────────────────
[⚡ LIVE] [Hacker]  → Injected SQL payload into input#email
[⚡ LIVE] [Grandma] → Typed phone number into email field
[⚡ LIVE] [Toddler] → Keyboard smash on textarea#message
[!] CRITICAL BUG FOUND: SQL Error leaked in HTTP 500 response
────────────────────────────────────
✅  Passed:           45 actions
❌  Vulnerabilities:   2 found
⚠️  UI Bugs:           3 found
📊  Chaos Score:      87 / 100
📄  Reports saved to: ./reports/
```

---

## 🔌 CI/CD Integration (GitHub Actions)

Add GREMLIN-AI to your pipeline in seconds. Every push automatically chaos-tests your staging environment:

```yaml
# .github/workflows/gremlin-test.yml
name: Gremlin-AI Security Scan

on: [push, pull_request]

jobs:
  chaos-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./github-action
        with:
          target_url: 'https://staging.your-app.com'
          duration: '120'
          personas: 'hacker grandma toddler'
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   USER / CI PIPELINE                 │
└──────────────────────┬──────────────────────────────┘
                       │ URL Input
┌──────────────────────▼──────────────────────────────┐
│         GREMLIN-AI MULTI-STEP PIPELINE               │
│                                                      │
│  Step 1 ──▶ Playwright crawls DOM                    │
│  Step 2 ──▶ Extract interactive elements             │
│  Step 3 ──▶ Select AI persona                        │
│  Step 4 ──▶ Qwen 0.6B generates chaotic input        │
│  Step 5 ──▶ Playwright executes action               │
│  Step 6 ──▶ Capture errors/screenshots/network       │
│  Step 7 ──▶ Generate bug report                      │
│  Step 8 ──▶ Update Chaos Score                       │
└──────────────────────┬──────────────────────────────┘
                       │ WebSocket stream
┌──────────────────────▼──────────────────────────────┐
│           NEXT.JS REAL-TIME DASHBOARD                │
│  3D Globe · Live Feed · Score Gauge · Bug Reports    │
└─────────────────────────────────────────────────────┘
```

**Tech Stack:**

| Layer | Technology | Why |
|-------|-----------|-----|
| 🧠 LLM | Qwen 3 0.6B via Ollama | Tier 1, local, $0, deliberately chaotic |
| 🕷️ Automation | Playwright (Python) | Best-in-class browser control |
| ⚡ Backend | FastAPI + WebSockets | Real-time streaming, async, fast |
| 🎨 Frontend | Next.js + React | Beautiful real-time dashboard |
| 🐳 Deploy | Docker + docker-compose | One-command setup |

---

## 📁 Project Structure

```
gremlin-ai/
├── 📂 backend/
│   ├── 📂 core/
│   │   ├── crawler.py         ← Playwright DOM discovery
│   │   ├── personas.py        ← 6 AI persona definitions
│   │   ├── chaos_engine.py    ← Main 8-step pipeline
│   │   ├── model_client.py    ← Ollama interface
│   │   ├── action_executor.py ← Browser action execution
│   │   ├── error_detector.py  ← Console/network/visual capture
│   │   ├── bug_reporter.py    ← Professional report generator
│   │   └── chaos_scorer.py    ← Resilience score calculator
│   └── 📂 api/
│       ├── main.py            ← FastAPI entry point
│       ├── routes.py          ← REST endpoints
│       └── websocket.py       ← Real-time chaos feed
│
├── 📂 frontend/
│   └── 📂 app/
│       ├── page.tsx           ← Landing page + 3D Globe
│       ├── dashboard/         ← Live testing dashboard
│       └── reports/           ← Bug reports view
│
├── 📂 cli/                    ← Terminal interface
├── 📂 github-action/          ← CI/CD integration
├── 📂 docs/                   ← Full documentation
├── 📂 demo/                   ← Vulnerable demo targets
├── docker-compose.yml         ← One-command setup ✅
└── README.md
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [📋 Technical Writeup](./docs/TECHNICAL_WRITEUP.md) | Deep dive into the "Wow Gap" thesis |
| [🏗️ Architecture](./docs/ARCHITECTURE.md) | System design and pipeline walkthrough |
| [💸 Cost Metrics](./docs/COST_METRICS.md) | $0 inference proof + latency benchmarks |
| [⚠️ Known Failures](./docs/KNOWN_FAILURES.md) | Honest assessment of current limitations |

---

## 🏆 Why This Wins

> **"A $0 model doing the job of a $50,000/year QA engineer."**
> **"The model doesn't even know it's testing software."**

- ✅ **Zero Cost** — Runs entirely on your CPU, no GPU needed
- ✅ **Zero Config** — One command to start everything
- ✅ **Zero API Keys** — No OpenAI, no Anthropic, fully local
- ✅ **Works Offline** — No internet needed for inference
- ✅ **Finds Real Bugs** — Not simulated — actual XSS, SQLi, race conditions
- ✅ **CI/CD Ready** — GitHub Action included, zero integration effort
- ✅ **Privacy First** — Your app's data never leaves your machine

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

MIT License — Free to use, modify, and distribute.

---

<div align="center">

### Built with ☣️ chaos and 💡 insight

*"Everyone else is trying to make small models smarter.*
*We celebrated our model's stupidity — and turned it into a product."*

---

**Made by Hamza** 🚀

</div>

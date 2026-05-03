# 🏗️ SYSTEM ARCHITECTURE

## High-Level Architecture Diagram

```mermaid
graph TD
    A["🌐 Target URL"] --> B["🕷️ Playwright Crawler (Backend)"]
    B --> C["🔍 DOM Parser"]
    C --> D["🎭 Persona Engine"]
    
    subgraph "The Chaos Loop"
        D --> E["🧠 Local Ollama (Qwen 0.6B)"]
        E --> F["⚡ Playwright Action Executor"]
        F --> G["🔎 Error & Crash Detector"]
    end
    
    G --> H{"Crash Detected?"}
    H -->|Yes| I["📋 Bug Reporter (Markdown/JSON)"]
    H -->|No| J["🔄 Next Element"]
    
    I --> K["📊 WebSockets"]
    K --> L["💻 Next.js Real-time Dashboard"]
```

## Component Breakdown

1. **Crawler & DOM Parser (`backend/core/crawler.py`)**
   - Headless Chromium intercepts the page.
   - Extracts all actionable nodes (inputs, buttons, textareas).
   - Strips visually hidden or disabled elements.

2. **Model Interface (`backend/core/model_client.py`)**
   - Connects to native Ollama API via REST.
   - Enforces fast timeouts to prevent hang-ups.

3. **Error Detector (`backend/core/error_detector.py`)**
   - Injects JS into the browser context to catch `window.onerror`.
   - Listens to HTTP Network responses (captures 500s).
   - Takes pre- and post-action screenshots.

4. **Frontend (`frontend/app/`)**
   - Receives data over WebSockets for ultra-low latency updates.
   - Computes the final Chaos Score client-side for immediate visual feedback.

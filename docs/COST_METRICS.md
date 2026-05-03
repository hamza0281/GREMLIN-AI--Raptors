# 💸 COST & PERFORMANCE METRICS

## 1. Inference Cost
* **Model Used:** Qwen 3 0.6B Q4_K_M
* **Provider:** Local Ollama Installation
* **API Cost:** `$0.00`
* **Network Cost:** `$0.00` (Offline Capable)

## 2. Hardware Requirements
Because we specifically chose a 0.6B parameter model and quantized it to 4-bit (Q4_K_M), the memory footprint is extremely small.
* **RAM Requirement:** ~500 MB for Model Weights
* **VRAM Requirement:** 0 MB (Runs comfortably on CPU)
* **Total Application Footprint:** < 1 GB (Including Node.js and Python overhead)

## 3. Latency Benchmarks
*Tested on an Apple M2 Chip (CPU Inference)*

| Action | Avg Latency (ms) | Notes |
|--------|------------------|-------|
| DOM Extraction | 120ms | Playwright deterministic speed |
| Prompt Assembly | 5ms | Python string formatting |
| **LLM Chaos Generation** | **180ms - 300ms** | *Extremely fast due to 0.6B size* |
| Playwright Execution | 200ms | DOM rendering delay |
| **Total Pipeline Cycle** | **~600ms per element** | Can test ~100 elements per minute |

## 4. Token Metrics
* **Tokens Per Prompt (Avg):** 80-150 tokens (Context includes single HTML element)
* **Tokens Per Output (Avg):** 10-50 tokens (The chaos injection payload)
* **Tokens / Second (CPU):** ~45 t/s

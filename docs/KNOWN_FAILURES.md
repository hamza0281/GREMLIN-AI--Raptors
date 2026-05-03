# ⚠️ KNOWN FAILURES (Honesty Section)

As per the GARAGE INFERENCE Hackathon requirements, here is an honest assessment of where Chaos-QA currently fails and our plans to fix it.

## 1. The "Too Stupid" Problem
While weaponizing the model's stupidity is our core thesis, sometimes the 0.6B model is *too* small. 
- **Failure Mode:** It sometimes outputs completely empty strings or gets stuck in a repetitive loop (e.g., "Hello Hello Hello Hello").
- **Current Mitigation:** Our Retry Engine catches empty strings and timeouts, instantly generating a deterministic fallback payload.

## 2. Visual Context Blindness
- **Failure Mode:** The model only reads the DOM tree text. It does not "see" the page. It might try to click a button that is hidden behind a modal overlay or pushed off-screen by CSS.
- **Current Mitigation:** Playwright throws an `ElementNotInteractableException` which our backend catches gracefully and moves to the next element without crashing.

## 3. Complex Authentication Flows
- **Failure Mode:** Chaos-QA cannot autonomously register an account, check an email for a verification code, and then log in to test authenticated routes.
- **Future Solution:** We plan to add a "Pre-flight Script" feature in the CLI where users can define a Playwright login script to run *before* the Chaos Engine takes over.

## 4. High Client-Side Interactivity (React/Vue SPAs)
- **Failure Mode:** If an app relies heavily on React state that changes dynamically on hover (without DOM updates until click), our DOM extraction might miss interactive zones. 

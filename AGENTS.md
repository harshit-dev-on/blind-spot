# BlindSpot Development Directives & Rules

## 1. Primary Rule: Strix Codebase Parity (`d:\Projects\BlindSpot\strix`)
- **Never hallucinate or invent patterns from scratch**: When designing, coding, configuring, or refactoring anything in BlindSpot, **ALWAYS refer directly to the Strix codebase** at [`d:/Projects/BlindSpot/strix`](file:///d:/Projects/BlindSpot/strix) as the gold standard.
- **Port and adapt directly from Strix**:
  - `strix/strix/config/` -> Configuration loading, universal env variables (`STRIX_LLM`, `BLINDSPOT_LLM`, `LLM_API_KEY`, `LLM_API_BASE`), JSON config parsing, and `persist_current()`.
  - `strix/strix/interface/` -> CLI arguments (`-t`, `-u`, `-i`, `-c`, `-m`, `-n`, `--config`), start screens, environment validation panels (`validate_environment()`).
  - `strix/strix/agents/` -> Agent design, worker loops, tool calling, execution prompts.
  - `strix/strix/runtime/` -> Safe session management, context isolation, navigation safety.
  - `strix/strix/report/` -> Report state, models, SARIF generation, structured findings.
- **Zero Docker Requirement**: Maintain native host Playwright browser execution for BlindSpot while preserving 100% of Strix's CLI and configuration ergonomics.
- **Always verify against Strix source**: Before writing new code, search and view the relevant Strix implementation in [`strix/`](file:///d:/Projects/BlindSpot/strix) to mirror function signatures, argument conventions, and design patterns.

## 2. Zero References in BlindSpot
- **Never mention Strix**: Absolutely zero references, mentions, docstrings, comments, environment variable examples, or credits to Strix anywhere in the BlindSpot codebase, documentation, CLI outputs, or configuration files. BlindSpot is a completely standalone project.

## 3. Mandatory Interactive Browsing Workflow & Zero Exploration Delay
- **Zero Exploration Delay**: When asked to audit a website or run BlindSpot, Antigravity MUST NOT inspect, search, grep, view, or analyze the BlindSpot repository, python packages, or CLI help before executing. Start immediately in Step 1.
- **The Core Philosophy: Human Perception-Action Loop & Living Context Window**:
  - **No Rigid Pre-Scripted Sequences**: Just like a normal human browses a website, the site is opened and the user waits for it to load properly. The brain sees what is rendered on screen, processes the visual information, and decides what single action to perform. After performing the action, the user waits for new information to show up. There is NEVER a fixed set of "do this and that" scripted steps—one can only decide the next move by seeing what is visually present on screen.
  - **The Living Context Window (`browser_interaction.md`)**: The markdown file acts as an evolving, cumulative context window where one by one all step screenshots, persona observations, and actions are recorded in chronological order. Antigravity inspects this file and the latest screenshot at every turn to retain complete temporal memory and make dynamic, visually grounded decisions anytime it needs.
- **The Mandatory Browsing Workflow**:
  1. **Launch Live Browser**: Execute `blindspot live "<TARGET_URL>" --allow-local -o "blindspot_reports/<run_id>"` as a background command (`IsDaemon=True, WaitMsBeforeAsync=1000`).
  2. **Page Load & Screenshot Capture**: The website opens in the visible live browser window (`headless=False`). BlindSpot waits a few seconds for the website to load, takes the initial screenshot, records it into `browser_interaction.md`, and writes `action_needed.json`.
  3. **Wait for Antigravity**: BlindSpot pauses and waits for Antigravity to analyze the image and decide the next action.
  4. **Antigravity Visual Reasoning**: Antigravity reads `action_needed.json`, inspects `screenshots/step-000.png` via `read_file`, and reasons about the next action from the perspective of **Elena – Senior User (Low Vision & Novice Tech)** (evaluating headline contrast, button affordances, and navigation).
  5. **Antigravity Writes Next Action**: Antigravity writes `next_action.json` into the report folder:
     `{"action": "<click|scroll|hover|press|fill>", "target": "@eN", "value": "...", "rationale": "..."}`
  6. **BlindSpot Executes & Captures New Screenshot**: BlindSpot reads `next_action.json`, executes the action in the visible live browser, waits for the DOM to settle, captures `step-NNN.png`, appends the action and new screenshot to `browser_interaction.md`, and writes a new `action_needed.json`.
  7. **Iterative Feedback Loop**: Antigravity waits for the new screenshot, inspects it, decides the next action, and writes `next_action.json`. This loop keeps repeating until the desired audit task is completed.
  8. **Completion & Reporting**: When the audit goals are achieved, Antigravity sends `{"action": "finish", "summary": "...", "findings_markdown": "..."}`. BlindSpot writes `improvements_suggestions.md`, closes the browser, and completes.
- **Strict Journey Persistence & Zero Form Abandonment**:
  - **Never Give Up Prematurely**: Elena must follow through with the entire user journey (e.g. discovery -> item selection -> cart -> checkout -> form fill -> order placement & confirmation) to actual completion. Never conclude after just a few random clicks or scrolls.
  - **Form Completion Requirement**: When Elena encounters a form (such as checkout delivery details, shipping address, or contact form), she MUST NOT blindly click "Submit" or "Place Order" with empty fields and then give up or wander off to unrelated tabs! She must systematically inspect the form controls, fill all required fields (Name: "Elena Rostova", Mobile: "9876543210", Address: "124 Market Street, Apt 4B", City: "Kolkata", Pincode: "700001", etc.) with sensible demo data, select appropriate delivery/payment options, submit the form, and verify the confirmation or success page.
  - **No Disjointed Tab Jumping**: Elena must NEVER perform random activities or abandon an active workflow to click unrelated navigation links (such as jumping from an active checkout to 'Prescription', 'About', or 'Terms') unless the active journey is completely resolved.
- **Exact Audit Commands**:
  - **Live Interactive Audit (Default & Required)**:
    `blindspot live "<URL>" --allow-local -o "blindspot_reports/<run_id>"`
  - **Audit with Specific Persona**:
    `blindspot live "<URL>" --persona "elena" --allow-local -o "blindspot_reports/<run_id>"`
- **Default Persona Blueprint**: By default, BlindSpot uses strictly 1 single persona blueprint: **Elena – Senior User (Low Vision & Novice Tech)** to evaluate clarity, text contrast, button affordance, and intuitive navigation across all applications. Multiple personas are NEVER launched unless explicitly requested by the user.

## 4. Antigravity-First & Zero External API Requirement
- **Zero External API Requirement**: ALWAYS assume the user has NO external cloud API keys (no Gemini, no OpenAI, no Anthropic, etc.). BlindSpot MUST NEVER fail or throw errors because an external API key is missing.
- **Antigravity Native Operation**: The application MUST run 100% fine using Antigravity natively. Persona planning, live browser task execution, DOM heuristic inspection, and reporting must operate smoothly with zero external API tokens.
- **Default AI Provider**: The default provider is `antigravity` (`AntigravityProvider`), which uses intelligent DOM-guided heuristics and local execution without reaching out to external cloud AI APIs.

## 5. Mandatory Visible Live Browser Execution (Always On-Screen)
- **Live Visible Browser Mandatory**: Headless browser execution is STRICTLY PROHIBITED. Every audit MUST launch an actual visible desktop Chromium window (`headless=False`) directly in front of the user so they can watch live browsing, clicks, and page transitions in real time.
- **Always Brought to Foreground**: The browser window must be restored, maximized or appropriately sized, brought to the front of desktop windows, and pinned (`stay_topmost=True`) during live interactions.

## 6. Strict Black-Box Browser Auditing (No Code Access)
- **Zero Source Code Access**: BlindSpot is strictly forbidden from reading, opening, analyzing, or referencing repository source code, backend files, or local implementation files. It must audit the target website purely as an external user through the visible Playwright browser.
- **Never suggest code fixes or open code files**: Do NOT analyze codebase files, do NOT quote code line numbers, and do NOT propose code patches or remediation code blocks.

## 7. Silent Chat Window Policy (Report Folder Only)
- **No In-Chat Output Dumps**: Never reveal, print, or summarize audit findings, markdown contents, or step-by-step interaction logs in the AI chat window.
- **Status & Folder Link Only**: The agent response in the chat window must strictly be limited to:
  1. Current status (e.g., `Status: In Progress` or `Status: Completed`).
  2. The path to the report folder where the artifacts (`browser_interaction.md`, `improvements_suggestions.md`, and `screenshots/`) are stored.

## 8. Strict 3-Artifact Output Mandate
All legacy test suites, verification pipelines, code recommendations, and test assertion tables are completely eliminated. Every audit run must output ONLY:
1. `browser_interaction.md` (timeline of actions, rationale, and screenshots)
2. `improvements_suggestions.md` (evidence-based UX improvement suggestions based strictly on browser observations)
3. `screenshots/` (all step screenshots)

### Required Template: `improvements_suggestions.md`
```markdown
# UX Improvement Suggestions: [Target Website / Name]

- **Target URL:** [URL]
- **Audit Goal:** [Goal]
- **Date:** [ISO Timestamp / Date]

## 1. Executive Summary
[2-3 sentences providing an evidence-based overview of the user experience and primary friction areas observed during the live session.]

## 2. Interactive Journey Summary
- **Total Steps Taken:** [Count]
- **Key Milestones Explored:** [Summary of paths and pages explored]

## 3. Improvement Suggestions
*(Every suggestion must be backed by an observed screenshot evidence link)*

### Suggestion 1: [Category: Contrast | Touch Target | Navigation | Typography | Layout | Form] <Issue Title>
- **Observed Behavior:** [Exact visual or functional behavior observed on the page during the step]
- **UX Friction / Impact:** [Why this hinders the user, especially users with low vision or low technical knowledge]
- **Suggested Improvement:** [Clear, concrete design or code fix recommendation]
- **Evidence:** `screenshots/step-NNN.png`
```

### Required Template: `browser_interaction.md`
```markdown
# Live Browser Interaction

- **Target URL:** [URL]
- **Current URL:** [Current URL]
- **Page Title:** [Title]
- **Audit Goal:** [Goal]
- **Status:** [IN PROGRESS / COMPLETED]

## Step 0: Initial page observation
[Initial page observation text]

![Initial page](screenshots/step-000.png)

## Step 1: `[action]`
- **Agent reasoning:** [Explanation of why this action was selected based on screenshot evidence]
- **Target:** `[target]` ([strategy])
- **Value:** `[value]`
- **URL after action:** [URL]

![Step 1 screenshot](screenshots/step-001.png)

## Run completed
- **Actions taken:** [Count]
- **Summary:** [Final summary]
- **Output Report:** `improvements_suggestions.md`
```

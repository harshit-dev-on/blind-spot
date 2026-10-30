<p align="center">
  <a href="https://github.com/harshit-dev-on/blind-spot">
    <img src="src/blindspot/web/static/blindspot-logo.svg" alt="BlindSpot1 Logo" width="160">
  </a>
</p>

<div align="center">

# BlindSpot1

### Autonomous AI UX & Accessibility Testing Tool. Simulate real human users exploring, auditing, and validating user journeys on your live web application.

<br/>

<a href="docs/TECHNICAL_SPECIFICATION.md"><img src="https://img.shields.io/badge/Docs-Technical%20Spec-2b9246?style=for-the-badge&logo=gitbook&logoColor=white" alt="Docs"></a>
<a href="https://github.com/harshit-dev-on/blind-spot"><img src="https://img.shields.io/badge/Repository-blind--spot-f0f0f0?style=for-the-badge&logo=github&logoColor=000000" alt="GitHub Repo"></a>
<a href="https://github.com/harshit-dev-on/blind-spot/discussions"><img src="https://img.shields.io/badge/Community-Discussions-blue?style=for-the-badge&logo=github&logoColor=white" alt="Community"></a>

<a href="#-antigravity-native--zero-external-api-keys"><img src="https://img.shields.io/badge/Antigravity%20Native-Zero%20API%20Keys-success?style=for-the-badge&logoColor=white" alt="Antigravity Native"></a>
<a href="#-screenshot-first-visual-perception"><img src="https://img.shields.io/badge/Screenshot--First-Visual%20Perception-7c3aed?style=for-the-badge&logoColor=white" alt="Screenshot First"></a>
<a href="#-zero-docker-requirement"><img src="https://img.shields.io/badge/Zero%20Docker-Native%20Playwright-3b82f6?style=for-the-badge&logoColor=white" alt="Zero Docker"></a>

<a href="https://github.com/harshit-dev-on/blind-spot"><img src="https://img.shields.io/github/stars/harshit-dev-on/blind-spot?style=flat-square" alt="GitHub Stars"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-3b82f6?style=flat-square" alt="License"></a>
<a href="https://pypi.org/project/blindspot1/"><img src="https://img.shields.io/badge/PyPI-blindspot1-orange?style=flat-square" alt="PyPI Package"></a>
<a href="https://github.com/harshit-dev-on/blind-spot/actions"><img src="https://img.shields.io/badge/tests-run%20locally-informational?style=flat-square" alt="Tests"></a>

</div>

<br/>

> [!TIP]
> **Screenshot → Decision → Action Loop**
> For each action, BlindSpot captures the current browser viewport and passes that image with page DOM/text context to the configured decision provider. The action runs in the browser, a resulting screenshot is recorded, and the loop continues until success criteria are met or the action limit is reached. Local heuristic mode uses the DOM evidence; visual reasoning requires a connected image-capable provider or IDE bridge.

---

## BlindSpot1 Overview

**BlindSpot1** deploys autonomous AI testing agents that interact with your website just like real diverse human users. Instead of relying solely on static linters or artificial code assertions, BlindSpot1 agents navigate dynamically, experience cognitive friction, uncover broken interactions, and evaluate WCAG 2.2 Level AA accessibility standards through live exploratory execution.

**Key Capabilities:**

- **Screenshot-Grounded Action Cycle** — Captures the current viewport before each decision, passes it to the provider with DOM context, executes the selected action, then captures the resulting state.
- **Real-Time Incremental Markdown Reporting** — Reports (`browser_interaction.md` and `problems_found.md`) are created the instant auditing begins and flushed to disk live after each step.
- **Native Operation** — The default provider uses local DOM heuristics and requires no cloud API keys. Hosted-model adapters are included; Ollama and OpenAI-compatible endpoints are also supported.
- **Live Visible Headed Browser** — Watch personas navigate in real time with human typing cadence, element highlighting, and a sleek status navbar.
- **Clean Artifact Output** — Clean report directories containing strictly `browser_interaction.md`, `problems_found.md`, and visual evidence in `screenshots/` with zero raw HTML dumps.
- **UX & Accessibility Evidence** — Collects browser evidence for UX and accessibility review. It is an exploratory audit aid and does not certify WCAG conformance.
- **Zero Docker Requirement** — Runs natively on host Playwright across Windows, macOS, and Linux without containers or background daemons.
- **Developer & Agent Ready** — Rich CLI ergonomics via `blindspot1` (`-t`, `-u`, `-i`, `-c`, `-m`, `-n`, `--headed`, `--personas`), native Model Context Protocol (MCP) server, and open SKILL.md specs.

<br/>

```
                    Target Website URL + Context
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: Website Inspection & Baseline Calibration             │
│ • Viewport initialization (Chromium 1280x800 desktop default)   │
│ • Full rendered baseline screenshot capture                     │
│ • Interactive element extraction (buttons, anchors, inputs)    │
│ • Visible accessibility attributes & bounding box mapping      │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2: Grounded Persona Synthesis & Task Planning             │
│ • Technical literacy, motor abilities & visual needs modeling   │
│ • Observable tasks & verifiable success criteria synthesis       │
│ • Instant real-time report initialization (`browser_interaction.md`) │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3: DOM-Guided Action & Evidence Cycle                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. Capture Page State Screenshot (`stepN_before.png`)       │ │
│ │ 2. Analyze Visual State, Layout & Formulate Decision        │ │
│ │ 3. Execute Action with Human Typing Cadence & Pacing        │ │
│ │ 4. Capture Resulting State Screenshot (`stepN_after.png`)   │ │
│ │ 5. Incrementally Append Step & Evidence to Interaction Log  │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 4: Prioritized Findings & Actionable Remediation          │
│ • Objective verification of defect reproduction steps           │
│ • Generates `problems_found.md` with prioritized UX issues      │
│ • SARIF export for GitHub Security Code Scanning integration    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Use Cases

- **Autonomous E-Commerce Auditing** — Test product search, variant selection, price transparency, and cart checkout funnels.
- **WCAG 2.2 Level AA Compliance** — Validate contrast ratios, keyboard navigation order, focus visibility, and accessible ARIA labels.
- **Mobile & Responsive Usability** — Detect layout overflow, undersized touch targets, and mobile navigation friction.
- **Continuous CI/CD Regression Testing** — Run headless audits on pull requests to catch user-facing regressions before shipping to production.

---

## 🚀 Install and Configure

Install the complete native application with one command. The installer bootstraps a managed Python runtime, installs BlindSpot and its declared dependencies, downloads Playwright Chromium, and starts the first-run configuration wizard. No repository checkout, separate package installation, or Docker setup is needed.

The GitHub repository must be public for these anonymous installer commands to download its source archive.

**Windows PowerShell:**

```powershell
irm https://raw.githubusercontent.com/harshit-dev-on/blind-spot/master/scripts/install.ps1 | iex
```

**macOS or Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/harshit-dev-on/blind-spot/master/scripts/install.sh | bash
```

The setup wizard defaults to Antigravity local mode, which needs no cloud API key. To change providers later, run `blindspot1 setup`. The wizard saves your configuration under `~/.blindspot/` and can configure a local Ollama model or a hosted provider.

### Let your coding agent drive a live audit without a separate API key

Connect BlindSpot's MCP server to your coding agent (see [MCP setup](#channel-2-model-context-protocol-mcp-server)). The agent opens a visible Chromium session, receives a screenshot and page evidence, decides the next step using its own model, then sends one browser action. Each action returns a new screenshot for the next decision. No separate BlindSpot API key or model provider is needed; the coding agent uses its existing model access.

The final artifacts follow the same format each run: `website_context.md`, `browser_interaction.md` with the agent's rationale and screenshots after each action, `problems_found.md`, and a `screenshots/` folder. Install the bundled skill to teach compatible agents this loop:

```sh
blindspot1 skill install
```

Then ask the coding agent to audit a site, for example: “Audit Flipkart's product search.” For local development targets, the agent must use `allow_local: true` when opening the session.

> [!NOTE]
> On Linux, Chromium may require system browser libraries. The installer asks Playwright to provision these automatically. New shell windows may be needed before the `blindspot1` command appears on PATH.

### Run your first audit

```bash
blindspot1 inspect -u https://example.com -c "Explore the main user journey" --headed
```

Run `blindspot1 --help` to see all commands. Generated reports are saved under `reports/` in the current directory.

For development from a source checkout, use the contributor instructions in [`dev/README.md`](dev/README.md). The default install includes the CLI, web studio, MCP server, local heuristics, native Playwright support, and hosted-model adapters. Antigravity remains the default and does not need a cloud key. The alternative Browser Use engine remains optional.

---

## 🔄 Updating & Upgrading

Run the same one-line installer again to upgrade BlindSpot. Your saved configuration is kept:

```powershell
irm https://raw.githubusercontent.com/harshit-dev-on/blind-spot/master/scripts/install.ps1 | iex
```

```bash
curl -fsSL https://raw.githubusercontent.com/harshit-dev-on/blind-spot/master/scripts/install.sh | bash
```

---

## 🗑️ Uninstallation & System Cleanup

Use one command to remove BlindSpot and its managed Python environment. The default keeps your saved settings and bridge data; `--clean-config` also removes them.

**Windows PowerShell:**

```powershell
irm https://raw.githubusercontent.com/harshit-dev-on/blind-spot/main/scripts/uninstall.ps1 | iex
```

To remove configuration too:

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/harshit-dev-on/blind-spot/main/scripts/uninstall.ps1))) -CleanConfig
```

**macOS or Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/harshit-dev-on/blind-spot/main/scripts/uninstall.sh | bash
```

To remove configuration too, use `curl -fsSL https://raw.githubusercontent.com/harshit-dev-on/blind-spot/main/scripts/uninstall.sh | bash -s -- --clean-config`.

---

## 📊 Clean Report Output Directory

Every audit generates a clean, readable, self-contained report folder:

```
blindspot_reports/059/
├── browser_interaction.md   # Live step-by-step screenshot interaction log
├── problems_found.md        # Prioritized UX & WCAG accessibility findings
├── task_tracker.md          # Step-gate milestone matrix & progress tracking
└── screenshots/             # Visual before & after snapshot evidence
    ├── task_1_1_step1_before.png
    ├── task_1_1_step1_after.png
    ├── task_1_1_step2_before.png
    └── ...
```

### 1. `browser_interaction.md`
- **Zero Raw HTML Dumps**: Free of formatted DOM code blobs and raw HTML strings.
- **Created Instantly**: File is initialized the moment auditing begins so you can monitor progress.
- **Incremental Real-Time Logging**: Every before-screenshot, persona observation, action result, and after-screenshot is appended in real time.

### 2. `problems_found.md`
- **Prioritized Usability Findings**: Ranked by severity, task completion impact, and Nielsen usability heuristics.
- **WCAG Accessibility Defects**: Clear remediation guidance and code recommendations for accessibility compliance.
- **Structured JSON Metadata**: Embedded machine-readable payload for programmatic parsing and report viewing.

### 3. `task_tracker.md`
- **Strict Precondition Step-Gate**: Decomposes multi-step user tasks into ordered milestones. Step $N+1$ unlocks only when Step $N$ is verified `PASSED`.
- **Human-in-the-Loop Authentication**: Halts automation with `WAITING_USER` when login walls, OTP prompts, or credentials are required, prompting you in Antigravity or Terminal.
- **Zero Arbitrary Action Limits**: When running with `--unlimited`, journeys run until full completion with built-in stall and cycle detectors.

---

## Ways to Run BlindSpot1

- **Direct Inspection CLI** — Streamlined testing with instant visual feedback: `blindspot1 inspect -u <url> -c <context> --headed`
- **Interactive Terminal Start Screen** — Guided wizard with target history and setup: `blindspot1`
- **Local Report Viewer** — View audit reports directly in your browser: `blindspot1 view`
- **Local Web Studio UI** — Full graphical studio with live runner and persona editor: `blindspot1 web --port 8000`
- **Model Context Protocol (MCP)** — Native server for AI coding agents: `blindspot1 mcp`

---

## 🖥️ Local Web Studio & Report Viewer

```bash
# View the most recent audit report in your browser
blindspot1 view

# ...or view a specific report folder
blindspot1 view blindspot_reports/059/

# Launch the visual BlindSpot1 Web Studio UI (FastAPI + Modern Web App)
blindspot1 web --port 8000
```

---

## 🤖 Use BlindSpot1 from Your Coding Agent

BlindSpot1 is agent-native. Coding agents like **Antigravity**, **Claude Code**, **Cursor**, **Windsurf**, and **Goose** can discover and operate BlindSpot1 through three dedicated integration channels:

| Integration Channel | Setup Command / Location | How the Agent Discovers It |
| :--- | :--- | :--- |
| **1. Agent Skills** *(Recommended)* | `blindspot1 skill install` | Agent auto-indexes `.agents/skills/**/SKILL.md` and activates autonomously on prompts like *"audit my website"* |
| **2. Model Context Protocol (MCP)** | `mcp_config.json` / `.cursor/mcp.json` | Exposes the live browser loop (`live_browser_open`, `live_browser_action`, `live_browser_observe`, `live_browser_finish`) plus audit tools directly to the coding agent |
| **3. Workspace Directives** | [`AGENTS.md`](AGENTS.md) in repo root | Agent automatically reads project guidelines and follows instructions for testing and running audits |

---

### Channel 1: Agent Skills (Zero MCP Config Required ⭐ Recommended)

Agents that support the open Agent Skills standard (including **Antigravity**, **Cursor**, and **Claude Code**) automatically discover and trigger tools without requiring manual JSON configuration.

In your project repository, run:
```bash
# Install bundled skills into your workspace (.agents/skills/ and .github/skills/):
blindspot1 skill install

# List all available agent skills:
blindspot1 skill list
```

This installs 8 self-documenting skill bundles into `.agents/skills/`:
- `blindspot-task-tracker/SKILL.md`: Strict step-gate task tracking, sequential milestone progression, and human-in-the-loop auth prompter.
- `blindspot-ux-audit/SKILL.md`: Conducts end-to-end UX, accessibility, and user-journey audits.
- `blindspot-ecommerce-audit/SKILL.md`: Audits shopping carts, pricing transparency, and checkout funnels.
- `blindspot-wcag-audit/SKILL.md`: Audits WCAG 2.2 Level AA accessibility compliance, keyboard navigation, and ARIA labels.
- `blindspot-mobile-audit/SKILL.md`: Audits responsive layouts, viewport overflow, and touch target dimensions.
- `blindspot-verify-fix/SKILL.md`: Verifies developer code patches to prevent UX regressions.
- `blindspot-persona-designer/SKILL.md`: Tailors realistic synthetic persona journeys.
- `blindspot-website-context/SKILL.md`: Guides the coding agent through a visible, screenshot-driven browser loop using its own reasoning, then saves a Markdown audit.

**How Antigravity & Coding Agents Discover It:**  
Antigravity automatically indexes any `SKILL.md` files in `.agents/skills/`. The moment you type in chat:
> *"Audit our signup flow at http://localhost:3000"* or *"Check WCAG compliance for the checkout page"*

Antigravity matches the intent against the skill description, activates the BlindSpot1 skill, and runs `blindspot1 inspect` directly in the integrated terminal.

---

### Channel 2: Model Context Protocol (MCP Server)

Launch the native Model Context Protocol server to give AI coding agents direct function-calling access:

```bash
blindspot1 mcp
```

#### Configuration by Editor / Agent:

#### A. Google Antigravity & Gemini Code Assist
Add to your global config (`~/.gemini/config/mcp_config.json` on macOS/Linux or `%USERPROFILE%\.gemini\config\mcp_config.json` on Windows):

```json
{
  "mcpServers": {
    "blindspot1": {
      "command": "blindspot1",
      "args": ["mcp"]
    }
  }
}
```

#### B. Cursor & Windsurf
Add to `.cursor/mcp.json` in your workspace, or under **Cursor Settings → MCP**:
```json
{
  "mcpServers": {
    "blindspot1": {
      "command": "blindspot1",
      "args": ["mcp"]
    }
  }
}
```

#### C. Claude Code & Claude Desktop
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "blindspot1": {
      "command": "blindspot1",
      "args": ["mcp"]
    }
  }
}
```

#### D. Zero-Install On-Demand MCP via `uvx`
If `blindspot1` is not installed globally on your machine, you can run the MCP server directly on demand using `uvx`:
```json
{
  "mcpServers": {
    "blindspot1": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/harshit-dev-on/blind-spot.git", "blindspot1", "mcp"]
    }
  }
}
```

#### Available MCP Tools Exposed to Coding Agents:
- `live_browser_open`: Open visible Chromium and return the initial screenshot/page evidence to the coding agent.
- `live_browser_action`: Execute one agent-chosen browser action and return a fresh screenshot/evidence.
- `live_browser_observe`: Capture the current page again without acting.
- `live_browser_finish` / `live_browser_close`: Save the agent's audit and close, or close while preserving existing evidence.
- `inspect_website`: Initiate an autonomous UX and accessibility audit run.
- `get_test_status`: Poll execution progress, active stage, and running persona tasks.
- `get_test_results`: Retrieve pass/fail metrics, defect summaries, and report paths.
- `get_findings`: Query validated defects, Nielsen heuristic violations, and remediation steps.
- `verify_fixes`: Run targeted regression tests to verify that developer code changes resolved reported issues.
- `list_skills` / `get_skill`: Discover and read specialized audit workflows.

---

### Channel 3: Workspace Directives (`AGENTS.md`)

Antigravity and other coding assistants automatically load instructions from [`AGENTS.md`](AGENTS.md) when opening a workspace. Including testing guidelines in `AGENTS.md` ensures the agent proactively runs `blindspot1` before merging UI changes:

```markdown
# Autonomous UX Verification
Before submitting frontend PRs, run an autonomous usability audit:
`blindspot1 inspect -u http://localhost:3000 -c "Test checkout funnel" --headed`
Review findings in `blindspot_reports/` and ensure zero blocking defects.
```

---

## Usage Examples

### Live Visible Browser Testing
Watch personas operate on your website live on screen with human typing cadence and top status navbar:

```bash
# Watch a single persona operate live
blindspot1 inspect -u https://example.com -c "Evaluate onboarding flow" --headed --personas 1

# Long, complex e-commerce journey with unlimited actions and step-gate task tracking
blindspot1 -t https://www.flipkart.com -i "Search Apple iPhone 16 and add to cart" --headed --unlimited --skill blindspot-task-tracker

# Paced multi-task journey with action limits
blindspot1 -t https://shop.example.com -i "Search shoes and add to bag" --headed --max-actions 15
```

### Local Development Server Testing
Safely test local servers (`localhost` / `127.0.0.1`) using `--allow-local`:

```bash
blindspot1 -t http://localhost:3000 -i "Test checkout flow" --allow-local --headed
```

### Headless CI Mode
Run BlindSpot1 programmatically without interactive prompts using `-n/--non-interactive`:

```bash
blindspot1 -n -t https://staging.example.com -i "Smoke test main navigation"
```

### CI/CD (GitHub Actions)

Add BlindSpot1 to your GitHub Actions pipeline to audit every pull request and upload SARIF accessibility findings:

```yaml
name: blindspot1-ux-audit

on:
  pull_request:

jobs:
  ux-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install BlindSpot1
        run: pip install git+https://github.com/harshit-dev-on/blind-spot.git

      - name: Install Playwright Browsers
        run: playwright install chromium

      - name: Run BlindSpot1 Audit
        run: blindspot1 -n -t https://staging.example.com --personas 1

      - name: Upload SARIF Results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: blindspot_reports/
        continue-on-error: true
```

---

## Configuration

BlindSpot1 works out of the box with zero external API keys via native Antigravity. If you wish to connect cloud models, BlindSpot1 supports universal environment variables:

```bash
# Model selection (format: <provider>/<model>)
export BLINDSPOT1_LLM="gemini/gemini-2.5-flash"

# API Key
export LLM_API_KEY="your-api-key"

# Optional: custom API base for local models (e.g. Ollama, LMStudio)
export LLM_API_BASE="http://localhost:11434"
```

> [!NOTE]
> BlindSpot1 persists configuration to `~/.blindspot/cli-config.json` and `~/.blindspot/config.toml`. Run `blindspot1 setup` anytime for interactive configuration.

### Recommended Models:

- [Google Gemini 2.5 Flash](https://aistudio.google.com/) — `gemini/gemini-2.5-flash` *(Fast, highly cost-effective, excellent vision & DOM reasoning)*
- [Anthropic Claude 3.7 Sonnet](https://console.anthropic.com/) — `anthropic/claude-3-7-sonnet` *(Top-tier UX reasoning and heuristic synthesis)*
- [OpenAI GPT-4o-mini](https://platform.openai.com/) — `openai/gpt-4o-mini` *(Reliable, high speed, structured JSON output)*
- [Ollama Gemma 4 / Llama 3](https://ollama.com/) — `ollama/gemma4` *(100% offline, zero API costs, runs on localhost)*
- [OpenRouter](https://openrouter.ai/) — `openrouter/deepseek/deepseek-chat` *(Universal gateway across 100+ open-source and proprietary models)*

---

## Documentation

Full architectural documentation, data models, Nielsen heuristic mappings, and WCAG evaluation criteria are preserved in **[`docs/TECHNICAL_SPECIFICATION.md`](docs/TECHNICAL_SPECIFICATION.md)**.

## Contributing

We welcome contributions of code, heuristics, test personas, and new agent skills! Check out our [Contributing Guidelines](CONTRIBUTING.md) or open an [Issue](https://github.com/harshit-dev-on/blind-spot/issues) or [Pull Request](https://github.com/harshit-dev-on/blind-spot/pulls).

## Join Our Community

Have questions? Found a usability bug? Want to discuss autonomous testing agents?
**[Join our GitHub Discussions!](https://github.com/harshit-dev-on/blind-spot/discussions)**

## Support the Project

**Love BlindSpot1?** Give us a ⭐ on GitHub!

## Acknowledgements

BlindSpot1 builds on the incredible work of open-source projects like [Playwright](https://github.com/microsoft/playwright), [LiteLLM](https://github.com/BerriAI/litellm), [Rich](https://github.com/Textualize/rich), and [Typer](https://github.com/tiangolo/typer). Huge thanks to their maintainers!

---

> [!WARNING]
> **Authorized use only.** BlindSpot1 actively navigates and interacts with the web targets you specify. Only run tests against applications you own or have explicit permission to test. Always use `--allow-local` cautiously on development servers.

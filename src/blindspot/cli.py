"""Command-line interface for BlindSpot using Typer."""

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Optional
import typer
import blindspot.utils.console  # noqa: F401


from typing_extensions import Annotated

from blindspot import __version__
from blindspot.ai import (
    DEFAULT_KEY_ENVS,
    create_provider,
    get_models_for_provider,
    mask_api_key,
)
from blindspot.ai.exceptions import AIProviderError
from blindspot.browser import inspect_website
from blindspot.config import find_config_file, load_config, parse_model_route
from blindspot.core.models import InspectConfig
from blindspot.core.validation import validate_context, validate_url
from blindspot.execution import execute_persona_tasks
from blindspot.personas import generate_personas_and_tasks
from blindspot.reporting import generate_ux_report
from blindspot.skills import (
    get_bundled_skills_dir,
    install_skills_to_workspace,
    list_bundled_skills,
    validate_skill,
)
from blindspot.utils.console import (
    console,
    print_ai_prompt_result,
    print_browser_inspection_summary,
    print_error,
    print_execution_summary,
    print_inspection_start,
    print_inspection_summary,
    print_model_list,
    print_personas_summary,
    print_provider_list,
    print_provider_status,
    print_report_summary,
    print_skills_installed,
    print_skills_list,
    print_skills_validation_results,
)

app = typer.Typer(
    name="blindspot1",
    help="BlindSpot1: Open-source AI-powered website UX testing tool.\n\n"
    "Simulates real user personas exploring websites to uncover UX flaws, "
    "accessibility barriers, and confusing user journeys.",
    no_args_is_help=False,
    add_completion=False,
)

provider_app = typer.Typer(
    name="provider",
    help="Configure, inspect, and test AI model providers.",
    no_args_is_help=True,
)
app.add_typer(provider_app)

model_app = typer.Typer(
    name="model",
    help="Discover and list AI models.",
    no_args_is_help=True,
)
app.add_typer(model_app)

skill_app = typer.Typer(
    name="skill",
    help="Manage, list, validate, and install Agent Skills following the open specification.",
    no_args_is_help=True,
)
app.add_typer(skill_app)

from blindspot.interface.cli_args import SUPPORTED_BROWSERS, version_callback


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    target: Annotated[
        Optional[str],
        typer.Option(
            "--target",
            "-t",
            help="Target website URL to test (e.g. https://example.com).",
            show_default=False,
        ),
    ] = None,
    url: Annotated[
        Optional[str],
        typer.Option(
            "--url",
            "-u",
            help="Alias for --target.",
            show_default=False,
        ),
    ] = None,
    desc: Annotated[
        Optional[str],
        typer.Option(
            "--desc",
            "--description",
            help="Description of what the website is for (e-commerce, SaaS, landing page, etc.).",
            show_default=False,
        ),
    ] = None,
    instruction: Annotated[
        Optional[str],
        typer.Option(
            "--instruction",
            "-i",
            help="Custom focus or instruction for testing.",
            show_default=False,
        ),
    ] = None,
    context: Annotated[
        Optional[str],
        typer.Option(
            "--context",
            "-c",
            help="Alias for --instruction.",
            show_default=False,
        ),
    ] = None,
    instruction_file: Annotated[
        Optional[Path],
        typer.Option(
            "--instruction-file",
            "--persona-file",
            "--personas-file",
            help="Path to markdown or text file containing custom persona instructions.",
            show_default=False,
        ),
    ] = None,
    model: Annotated[
        Optional[str],
        typer.Option(
            "--model",
            "-m",
            help="AI model route in <provider>/<model> format (e.g. gemini/gemini-2.5-flash, openai/gpt-4o-mini).",
            show_default=False,
        ),
    ] = None,
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive",
            "-n",
            help="Run non-interactively in headless mode.",
            show_default=False,
        ),
    ] = False,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            help="Path to custom config file (JSON or TOML) instead of ~/.blindspot/config.toml.",
            show_default=False,
        ),
    ] = None,
    headed: Annotated[
        bool,
        typer.Option(
            "--headed",
            help="Run browser in visible live window (default).",
            show_default=False,
        ),
    ] = True,
    headless: Annotated[
        bool,
        typer.Option(
            "--headless",
            help="Run browser in headless background mode.",
            show_default=False,
        ),
    ] = False,
    allow_local: Annotated[
        bool,
        typer.Option(
            "--allow-local",
            help="Permit testing local loopback servers (localhost / 127.0.0.1).",
            show_default=False,
        ),
    ] = False,
    personas: Annotated[
        Optional[int],
        typer.Option(
            "--personas",
            "-p",
            help="Number of AI user personas to generate and test (default: 1).",
            show_default=False,
        ),
    ] = None,
    persona: Annotated[
        Optional[str],
        typer.Option(
            "--persona",
            "-P",
            help="Choose a specific persona by name or archetype (e.g. 'elena', 'ecommerce', 'mobile', 'accessibility', 'tech', 'skeptical', 'first-time').",
            show_default=False,
        ),
    ] = None,
    concurrency: Annotated[
        Optional[int],
        typer.Option(
            "--concurrency",
            "--simultaneous",
            help="Number of personas to execute simultaneously (default: 1).",
            show_default=False,
        ),
    ] = None,
    output_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--output-dir",
            "-o",
            help="Custom directory to store artifacts.",
            show_default=False,
        ),
    ] = None,
    iteration: Annotated[
        Optional[str],
        typer.Option(
            "--iteration",
            help="Iteration identifier or number (creates subfolder under reports directory, e.g. iteration_1).",
            show_default=False,
        ),
    ] = None,
    skill: Annotated[
        Optional[str],
        typer.Option(
            "--skill",
            "-s",
            help="Activate a specialized Agent Skill (e.g. wcag, ecommerce, mobile, ux).",
            show_default=False,
        ),
    ] = None,
    skip_ai: Annotated[
        bool,
        typer.Option(
            "--skip-ai",
            help="Skip persona synthesis; capture browser evidence without initializing an AI provider.",
            show_default=False,
        ),
    ] = False,
    skip_execution: Annotated[
        bool,
        typer.Option(
            "--skip-execution",
            help="Skip browser task execution.",
            show_default=False,
        ),
    ] = False,
    skip_report: Annotated[
        bool,
        typer.Option(
            "--skip-report",
            help="Skip JSON and HTML UX report generation.",
            show_default=False,
        ),
    ] = False,
    unlimited: Annotated[
        bool,
        typer.Option(
            "--unlimited",
            help="Run tasks with unlimited actions until goal completion or verified success.",
            show_default=False,
        ),
    ] = False,
    keep_open: Annotated[
        bool,
        typer.Option(
            "--keep-open",
            help="Keep visible browser window open indefinitely after audit completion.",
            show_default=False,
        ),
    ] = False,
    live: Annotated[
        bool,
        typer.Option(
            "--live",
            help="Run interactive live browser loop controlled by Antigravity.",
            show_default=False,
        ),
    ] = False,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            help="Show the version of BlindSpot and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """BlindSpot CLI entry point."""
    if ctx.invoked_subcommand is not None:
        return

    effective_target = target or url
    effective_instruction = desc or instruction or context
    if instruction_file and instruction_file.is_file():
        effective_instruction = instruction_file.read_text(encoding="utf-8").strip()

    ai_prov, ai_mod = None, None
    if model:
        _, ai_prov, ai_mod = parse_model_route(model)

    effective_headed = False if headless else True
    effective_personas = max(1, min(int(personas if personas is not None else 1), 5))
    effective_concurrency = concurrency if concurrency is not None else 1

    if iteration and not output_dir:
        iter_name = str(iteration).strip()
        if not iter_name.startswith("iteration"):
            iter_name = f"iteration_{iter_name}"
        reports_base = Path(os.environ.get("BLINDSPOT_REPORTS_DIR", "blindspot_reports" if Path("blindspot_reports").is_dir() else "reports"))
        reports_base.mkdir(parents=True, exist_ok=True)
        output_dir = reports_base / iter_name

    if effective_target:
        if live:
            live_cmd(
                target_arg=effective_target,
                goal=effective_instruction or "Audit website usability and user journey",
                persona=persona,
                personas=effective_personas,
                output_dir=str(output_dir) if output_dir else None,
                allow_local=allow_local,
            )
            return

        inspect(
            url=effective_target,
            context=effective_instruction,
            instruction_file=instruction_file,
            output_dir=output_dir,
            headed=effective_headed,
            personas=effective_personas,
            persona=persona,
            concurrency=effective_concurrency,
            skip_ai=skip_ai,
            skip_execution=skip_execution,
            skip_report=skip_report,
            allow_local=allow_local,
            ai_provider=ai_prov,
            ai_model=ai_mod,
            config=config,
            non_interactive=non_interactive,
            skill=skill,
            unlimited=unlimited,
            keep_open=keep_open,
        )
        return

    # If bare `blindspot` command is run:
    # Launch interactive start screen
    from blindspot.interface.interactive import show_interactive_start_screen
    start_res = show_interactive_start_screen()
    chosen_target, chosen_instruction = start_res[0], start_res[1]
    if not chosen_target:
        from blindspot.web import run_web_studio
        console.print("[bold cyan]→[/bold cyan] Launching BlindSpot Web Studio...")
        run_web_studio(port=8501, host="127.0.0.1")
        return

    interactive_headed = getattr(start_res, "headed", False)
    effective_headed = interactive_headed if (not non_interactive and not headed) else effective_headed

    interactive_personas = getattr(start_res, "personas", 1)
    effective_personas = personas if personas is not None else interactive_personas

    interactive_concurrency = getattr(start_res, "concurrency", 1)
    effective_concurrency = concurrency if concurrency is not None else interactive_concurrency

    inspect(
        url=chosen_target,
        context=chosen_instruction,
        instruction_file=instruction_file,
        output_dir=output_dir,
        headed=effective_headed,
        personas=effective_personas,
        persona=persona,
        concurrency=effective_concurrency,
        allow_local=allow_local,
        ai_provider=ai_prov,
        ai_model=ai_mod,
        config=config,
        non_interactive=non_interactive,
        skill=skill,
        unlimited=unlimited,
        keep_open=keep_open,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Setup Wizard
# ─────────────────────────────────────────────────────────────────────────────


@app.command(
    name="setup",
    help="Interactive setup wizard to configure your preferred AI provider and model.",
)
def setup_command() -> None:
    """Run interactive setup wizard to configure AI provider and credentials."""
    from blindspot.interface.scan_setup import run_setup_wizard

    try:
        run_setup_wizard()
    except (KeyboardInterrupt, typer.Abort):
        console.print("\n[yellow]Setup cancelled by user.[/yellow]")
        raise typer.Exit(code=0)


# ─────────────────────────────────────────────────────────────────────────────
# Model Discovery Commands
# ─────────────────────────────────────────────────────────────────────────────


@model_app.command(
    name="list",
    help="List discoverable and verified models for an AI provider.",
)
def model_list_command(
    provider: Annotated[
        Optional[str],
        typer.Option(
            "--provider",
            "-p",
            help="Provider to query models for (default: active provider).",
            show_default=False,
        ),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-C",
            help="Path to custom configuration file.",
            show_default=False,
        ),
    ] = None,
) -> None:
    """Display discoverable local models or curated cloud models."""
    try:
        loaded = load_config(custom_path=config, provider=provider)
    except Exception as exc:
        print_error("Configuration Error", str(exc))
        raise typer.Exit(code=1)

    ai_cfg = loaded.ai
    selected_provider = provider.lower().strip() if provider else ai_cfg.provider
    if selected_provider == "openai_compatible":
        selected_provider = "custom"

    from blindspot.ai import get_models_for_provider
    models = get_models_for_provider(selected_provider, base_url=ai_cfg.base_url)
    print_model_list(provider=selected_provider, models=models)


# ─────────────────────────────────────────────────────────────────────────────
# AI Provider Commands
# ─────────────────────────────────────────────────────────────────────────────


@provider_app.command(
    name="list",
    help="List supported AI providers and show active configuration.",
)
def provider_list(
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-C",
            help="Path to custom configuration file.",
            show_default=False,
        ),
    ] = None,
) -> None:
    """Display supported AI providers and the currently active model configuration."""
    try:
        loaded = load_config(custom_path=config)
    except Exception as exc:
        print_error("Configuration Error", str(exc))
        raise typer.Exit(code=1)

    ai_cfg = loaded.ai
    config_file = find_config_file(config)
    config_source = str(config_file) if config_file else "Built-in Defaults / Environment"

    key_source = "(not required)"
    if ai_cfg.provider in ("gemini", "openai", "anthropic", "openrouter", "custom", "openai_compatible"):
        env_var_name = ai_cfg.api_key_env or DEFAULT_KEY_ENVS.get(ai_cfg.provider, "")
        env_val = os.environ.get(env_var_name)
        if env_val:
            key_source = f"env:{env_var_name} ({mask_api_key(env_val)})"
        elif ai_cfg.api_key:
            key_source = f"direct config ({mask_api_key(ai_cfg.api_key)})"
        else:
            key_source = f"env:{env_var_name} [dim](NOT SET)[/dim]"

    print_provider_list(
        active_provider=ai_cfg.provider,
        active_model=ai_cfg.model,
        active_base_url=ai_cfg.base_url or "",
        active_key_source=key_source,
        active_category=ai_cfg.category,
        config_source=config_source,
    )


@provider_app.command(
    name="test",
    help="Test connectivity and model readiness for an AI provider.",
)
def provider_test(
    provider: Annotated[
        Optional[str],
        typer.Option(
            "--provider",
            "-p",
            help="Override AI provider (ollama, gemini, openai, anthropic, openrouter, custom).",
            show_default=False,
        ),
    ] = None,
    model: Annotated[
        Optional[str],
        typer.Option(
            "--model",
            "-m",
            help="Override model name/identifier.",
            show_default=False,
        ),
    ] = None,
    base_url: Annotated[
        Optional[str],
        typer.Option(
            "--base-url",
            help="Override provider base URL.",
            show_default=False,
        ),
    ] = None,
    api_key_env: Annotated[
        Optional[str],
        typer.Option(
            "--api-key-env",
            help="Override environment variable holding the API key.",
            show_default=False,
        ),
    ] = None,
    prompt: Annotated[
        Optional[str],
        typer.Option(
            "--prompt",
            help="Optional test prompt to send to the model if reachable.",
            show_default=False,
        ),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-C",
            help="Path to custom configuration file.",
            show_default=False,
        ),
    ] = None,
) -> None:
    """Verify endpoint reachability, model existence, and test prompt response."""
    try:
        loaded = load_config(
            custom_path=config,
            provider=provider,
            model=model,
            base_url=base_url,
            api_key_env=api_key_env,
        )
    except Exception as exc:
        print_error("Configuration Error", str(exc))
        raise typer.Exit(code=1)

    ai_cfg = loaded.ai
    console.print(
        f"[bold cyan]→[/bold cyan] Testing provider [bold]{ai_cfg.provider}[/bold] with model [bold]{ai_cfg.model}[/bold]..."
    )

    try:
        p = create_provider(ai_cfg)
        status = p.check_health()
    except AIProviderError as exc:
        print_error("Provider Setup Error", exc.message, exc.suggestion)
        raise typer.Exit(code=1)
    except Exception as exc:
        print_error("Provider Error", str(exc))
        raise typer.Exit(code=1)

    print_provider_status(
        provider=status.provider,
        model=status.model,
        base_url=status.base_url,
        is_reachable=status.is_reachable,
        model_available=status.model_available,
        latency_ms=status.latency_ms,
        message=status.message,
    )

    if not status.is_reachable or not status.model_available:
        raise typer.Exit(code=1)

    # Run verification prompt
    test_prompt = prompt or "Say hello in one brief sentence to confirm you are online."
    console.print(f"[bold cyan]→[/bold cyan] Sending test verification prompt: [dim]\"{test_prompt}\"[/dim]")

    try:
        response = p.generate(prompt=test_prompt)
        print_ai_prompt_result(
            prompt=test_prompt,
            model=response.model,
            provider=response.provider,
            content=response.content.strip(),
        )
    except AIProviderError as exc:
        print_error("Model Generation Failed", exc.message, exc.suggestion)
        raise typer.Exit(code=1)
    except Exception as exc:
        print_error("Generation Error", str(exc))
        raise typer.Exit(code=1)


@provider_app.command(
    name="prompt",
    help="Send a prompt directly to the configured AI model.",
)
def provider_prompt(
    text: Annotated[
        str,
        typer.Argument(
            help="Prompt text to send to the model.",
        ),
    ],
    provider: Annotated[
        Optional[str],
        typer.Option(
            "--provider",
            "-p",
            help="Override AI provider (ollama, gemini, openai, anthropic, openrouter, custom).",
        ),
    ] = None,
    model: Annotated[
        Optional[str],
        typer.Option(
            "--model",
            "-m",
            help="Override model name/identifier.",
        ),
    ] = None,
    base_url: Annotated[
        Optional[str],
        typer.Option(
            "--base-url",
            help="Override provider base URL.",
        ),
    ] = None,
    system: Annotated[
        Optional[str],
        typer.Option(
            "--system",
            "-s",
            help="Optional system prompt instructions.",
        ),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-C",
            help="Path to custom configuration file.",
        ),
    ] = None,
) -> None:
    """Send a user prompt to the configured model and display the response."""
    try:
        loaded = load_config(
            custom_path=config,
            provider=provider,
            model=model,
            base_url=base_url,
        )
        ai_cfg = loaded.ai
        p = create_provider(ai_cfg)
    except Exception as exc:
        print_error("Configuration Error", str(exc))
        raise typer.Exit(code=1)

    console.print(
        f"[bold cyan]→[/bold cyan] Querying [bold]{ai_cfg.provider}[/bold] ({ai_cfg.model})..."
    )

    try:
        response = p.generate(prompt=text, system_prompt=system)
        print_ai_prompt_result(
            prompt=text,
            model=response.model,
            provider=response.provider,
            content=response.content.strip(),
        )
    except AIProviderError as exc:
        print_error("AI Generation Error", exc.message, exc.suggestion)
        raise typer.Exit(code=1)
    except Exception as exc:
        print_error("AI Error", str(exc))
        raise typer.Exit(code=1)


# ─────────────────────────────────────────────────────────────────────────────
# Browser Inspection Command
# ─────────────────────────────────────────────────────────────────────────────


@app.command(
    name="inspect",
    help="Inspect a target website using browser automation.\n\n"
    "Navigates to the website with Playwright, captures interactive elements, "
    "page content, full-page screenshot, and structured inspection data.",
    no_args_is_help=True,
)
def inspect(
    target_url: Annotated[
        Optional[str],
        typer.Argument(
            metavar="[URL]",
            help="Target website URL to test (e.g. https://example.com).",
            show_default=False,
        ),
    ] = None,
    url: Annotated[
        Optional[str],
        typer.Option(
            "--url",
            "-u",
            help="Target website URL to test (e.g. https://example.com).",
            show_default=False,
        ),
    ] = None,
    target: Annotated[
        Optional[str],
        typer.Option(
            "--target",
            "-t",
            help="Alias for --url.",
            show_default=False,
        ),
    ] = None,
    desc: Annotated[
        Optional[str],
        typer.Option(
            "--desc",
            "--description",
            help="Description of what the website is for (e-commerce, SaaS, landing page, etc.).",
            show_default=False,
        ),
    ] = None,
    context: Annotated[
        Optional[str],
        typer.Option(
            "--context",
            "-c",
            help="Context describing website purpose & audience, or path to text file.",
            show_default=False,
        ),
    ] = None,
    instruction: Annotated[
        Optional[str],
        typer.Option(
            "--instruction",
            "-i",
            help="Alias for --context.",
            show_default=False,
        ),
    ] = None,
    output_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--output-dir",
            "-o",
            help="Custom directory to store artifacts (default: unique folder in blindspot_reports/).",
            show_default=False,
        ),
    ] = None,
    iteration: Annotated[
        Optional[str],
        typer.Option(
            "--iteration",
            help="Iteration identifier or number (creates subfolder under reports directory, e.g. iteration_1).",
            show_default=False,
        ),
    ] = None,
    skill: Annotated[
        Optional[str],
        typer.Option(
            "--skill",
            "-s",
            help="Activate a specialized Agent Skill (e.g. wcag, ecommerce, mobile, ux).",
            show_default=False,
        ),
    ] = None,
    browser: Annotated[
        str,
        typer.Option(
            "--browser",
            "-b",
            help="Browser engine to use: chromium, firefox, webkit.",
            show_default=True,
        ),
    ] = "chromium",
    headless: Annotated[
        bool,
        typer.Option(
            "--headless/--no-headless",
            help="Run browser in headless background mode or visible live window.",
            show_default=True,
        ),
    ] = False,
    headed: Annotated[
        bool,
        typer.Option(
            "--headed",
            help="Run browser in visible live window (default).",
            show_default=False,
        ),
    ] = True,
    personas: Annotated[
        int,
        typer.Option(
            "--personas",
            "-p",
            help="Number of AI user personas to generate and test (default: 1).",
            show_default=True,
        ),
    ] = 1,
    persona: Annotated[
        Optional[str],
        typer.Option(
            "--persona",
            "-P",
            help="Choose a specific persona by name or archetype (e.g. 'elena', 'ecommerce', 'mobile', 'accessibility', 'tech', 'skeptical', 'first-time').",
            show_default=False,
        ),
    ] = None,
    concurrency: Annotated[
        int,
        typer.Option(
            "--concurrency",
            "--simultaneous",
            help="Number of personas to execute simultaneously (default: 1).",
            show_default=True,
        ),
    ] = 1,
    skip_ai: Annotated[
        bool,
        typer.Option(
            "--skip-ai",
            help="Skip AI persona generation (browser inspection only).",
            show_default=False,
        ),
    ] = False,
    ai_provider: Annotated[
        Optional[str],
        typer.Option(
            "--ai-provider",
            help="Override AI provider for persona generation (e.g. ollama, gemini, openai).",
            show_default=False,
        ),
    ] = None,
    ai_model: Annotated[
        Optional[str],
        typer.Option(
            "--ai-model",
            help="Override AI model identifier for persona generation.",
            show_default=False,
        ),
    ] = None,
    model: Annotated[
        Optional[str],
        typer.Option(
            "--model",
            "-m",
            help="AI model route in <provider>/<model> format (e.g. gemini/gemini-2.5-flash, openai/gpt-4o-mini).",
            show_default=False,
        ),
    ] = None,
    instruction_file: Annotated[
        Optional[Path],
        typer.Option(
            "--instruction-file",
            "--persona-file",
            "--personas-file",
            help="Path to markdown or text file containing custom persona instructions.",
            show_default=False,
        ),
    ] = None,
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive",
            "-n",
            help="Run non-interactively in headless mode.",
            show_default=False,
        ),
    ] = False,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            help="Path to custom config file (JSON or TOML) instead of ~/.blindspot/config.toml.",
            show_default=False,
        ),
    ] = None,
    skip_execution: Annotated[
        bool,
        typer.Option(
            "--skip-execution",
            help="Skip simulated user actions; only inspect the initial website state.",
            show_default=False,
        ),
    ] = False,
    max_actions: Annotated[
        int,
        typer.Option(
            "--max-actions",
            help="Maximum actions per persona task (set 0 or pass --unlimited for no step limit).",
            show_default=True,
        ),
    ] = 35,
    unlimited: Annotated[
        bool,
        typer.Option(
            "--unlimited",
            help="Run tasks with unlimited actions until goal completion or verified success.",
            show_default=False,
        ),
    ] = False,
    keep_open: Annotated[
        bool,
        typer.Option(
            "--keep-open",
            help="Keep visible browser window open indefinitely after audit completion.",
            show_default=False,
        ),
    ] = False,
    skip_report: Annotated[
        bool,
        typer.Option(
            "--skip-report",
            help="Skip JSON and HTML UX report generation.",
            show_default=False,
        ),
    ] = False,
    allow_local: Annotated[
        bool,
        typer.Option(
            "--allow-local",
            help="Permit testing local loopback servers (localhost / 127.0.0.1).",
            show_default=False,
        ),
    ] = False,
    engine: Annotated[
        str,
        typer.Option(
            "--engine",
            help="Browser automation execution engine ('auto', 'browser-use', 'native').",
            show_default=True,
        ),
    ] = "auto",
) -> None:
    """Run website inspection, capture page state, screenshot, elements, and synthesize AI personas."""
    # Determine effective headless mode (visible live browser window is the strict default)
    effective_headless = True if (headless or not headed) else False
    effective_personas = max(1, min(int(personas), 5))

    # Determine effective target and context
    effective_url = target_url or target or url
    if not effective_url:
        print_error(
            title="Missing Target URL",
            message="Target website URL was not provided.",
            suggestion="Specify a target URL (e.g. blindspot inspect https://example.com or blindspot -t https://example.com).",
        )
        raise typer.Exit(code=1)

    effective_context = (
        desc
        or instruction
        or context
        or "Autonomous exploration of user journeys, interface accessibility, and usability."
    )
    if instruction_file and instruction_file.is_file():
        effective_context = instruction_file.read_text(encoding="utf-8").strip()

    # Agent Skill Activation & Progressive Disclosure
    active_skill = None
    from blindspot.skills.activator import SkillActivator, SkillInjectionMode
    from blindspot.skills.registry import SkillRegistry

    skill_reg = SkillRegistry()
    skill_act = SkillActivator(skill_reg)

    if skill:
        active_skill = skill_reg.get_skill(skill)
        if not active_skill:
            print_error(
                title="Skill Not Found",
                message=f"No registered Agent Skill found matching '{skill}'.",
                suggestion="Run 'blindspot skill list' to see available skills (e.g. wcag, ecommerce, mobile, ux).",
            )
            raise typer.Exit(code=1)
    elif effective_context.startswith("/"):
        parsed_skill, rest = skill_reg.try_parse_slash_command(effective_context)
        if parsed_skill:
            active_skill = parsed_skill
            effective_context = rest or active_skill.description

    if active_skill:
        console.print(
            f"[bold cyan]● Activated Agent Skill:[/bold cyan] [bold white]{active_skill.name}[/bold white] "
            f"[dim](v{active_skill.version})[/dim]"
        )
        effective_context = skill_act.format_for_injection(
            active_skill, mode=SkillInjectionMode.USER_MESSAGE, user_request=effective_context
        )

    if iteration and not output_dir:
        iter_name = str(iteration).strip()
        if not iter_name.startswith("iteration"):
            iter_name = f"iteration_{iter_name}"
        reports_base = Path(os.environ.get("BLINDSPOT_REPORTS_DIR", "blindspot_reports" if Path("blindspot_reports").is_dir() else "reports"))
        output_dir = reports_base / iter_name

    if model:
        _, parsed_prov, parsed_mod = parse_model_route(model)
        ai_provider = ai_provider or parsed_prov
        ai_model = ai_model or parsed_mod

    # Startup environment validation and persistence
    if not skip_ai:
        from blindspot.config.loader import load_config, persist_current
        from blindspot.interface.environment import validate_environment

        prospective_cfg = load_config(
            custom_path=config,
            provider=ai_provider,
            model=ai_model,
        )
        validate_environment(prospective_cfg)
        persist_current()

    # 1. Validate Target URL
    url_res = validate_url(effective_url)
    if not url_res.is_valid:
        print_error(
            title="Invalid URL Provided",
            message=url_res.error_message or "Invalid URL.",
            suggestion=url_res.suggestion,
        )
        raise typer.Exit(code=1)

    # SSRF & Private Network Security Check
    from blindspot.execution.safety import validate_navigation_url
    is_safe, ssrf_reason = validate_navigation_url(effective_url, allow_local=allow_local)
    if not is_safe:
        print_error(
            title="Security Policy Blocked URL",
            message=ssrf_reason or "Target URL failed safety policies.",
            suggestion="Target URL must be a publicly accessible HTTP/HTTPS address, or pass '--allow-local' if testing a local development server.",
        )
        raise typer.Exit(code=1)

    # 2. Validate Context Description
    context_res, resolved_context = validate_context(effective_context)
    if not context_res.is_valid:
        print_error(
            title="Invalid Context Provided",
            message=context_res.error_message or "Invalid Context.",
            suggestion=context_res.suggestion,
        )
        raise typer.Exit(code=1)

    # 3. Validate Browser Choice
    selected_browser = browser.lower().strip()
    if selected_browser not in SUPPORTED_BROWSERS:
        print_error(
            title="Invalid Browser Selected",
            message=f"Browser engine '{browser}' is not supported.",
            suggestion=f"Please choose one of: {', '.join(SUPPORTED_BROWSERS)} (e.g. --browser chromium).",
        )
        raise typer.Exit(code=1)

    # 4. Display Input Validation Summary & Initialize Report Directory
    reports_base = Path(os.environ.get("BLINDSPOT_REPORTS_DIR", "blindspot_reports" if Path("blindspot_reports").is_dir() else "reports"))
    reports_base.mkdir(parents=True, exist_ok=True)
    if not output_dir:
        from blindspot.core.runner import generate_run_id
        run_output_dir = reports_base / generate_run_id(reports_base)
    else:
        run_output_dir = Path(output_dir)
    run_output_dir.mkdir(parents=True, exist_ok=True)
    if not skip_report:
        screenshots_dir = run_output_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        # Instantly create browser_interaction.md the moment auditing starts
        live_md = run_output_dir / "browser_interaction.md"
        init_header = (
            f"# Live Browser Interaction\n\n"
            f"- **Target URL:** {effective_url.strip()}\n"
            f"- **Current URL:** {effective_url.strip()}\n"
            f"- **Page Title:** Initializing...\n"
            f"- **Audit Goal:** {resolved_context}\n"
            f"- **Status:** IN PROGRESS\n\n"
            f"## Step 0: Initial page observation\n\n"
            f"Target website loaded into live browser. Ready for inspection.\n\n"
            f"![Initial page](screenshots/step-000.png)\n"
        )
        live_md.write_text(init_header, encoding="utf-8")

    inspect_input_config = InspectConfig(url=effective_url.strip(), context=resolved_context)
    print_inspection_summary(url=inspect_input_config.url, context=inspect_input_config.context)
    print_inspection_start(
        url=inspect_input_config.url,
        browser=selected_browser,
        headed=not effective_headless,
        personas=effective_personas,
        concurrency=concurrency,
    )

    # 5. Launch Browser Inspection (always visible live window)
    try:
        with console.status("[bold cyan]Crawling target DOM and capturing viewport state...[/bold cyan]", spinner="dots"):
            result = inspect_website(
                url=inspect_input_config.url,
                context=inspect_input_config.context,
                output_dir=run_output_dir,
                browser_type=selected_browser,
                headless=effective_headless,
                allow_local=allow_local,
            )
    except Exception as exc:
        print_error(
            title="Browser Inspection Failed",
            message=str(exc),
            suggestion="Verify the URL is accessible. If browser binaries are missing, run 'playwright install chromium'.",
        )
        raise typer.Exit(code=1)

    # 6. Display Browser Result Summary
    print_browser_inspection_summary(
        title=result.title,
        final_url=result.final_url,
        viewport_width=result.viewport.width,
        viewport_height=result.viewport.height,
        browser=result.browser,
        total_elements=result.summary.total_interactive_elements,
        links_count=result.summary.links_count,
        buttons_count=result.summary.buttons_count,
        form_fields_count=result.summary.form_fields_count,
        text_length=result.summary.text_length,
        screenshot_path=result.screenshot_path,
        result_json_path=result.result_json_path,
    )

    # 7. AI Persona Synthesis and Task Planning
    if skip_ai:
        console.print("[dim]AI persona synthesis skipped (--skip-ai flag provided).[/dim]")
        return

    try:
        loaded_cfg = load_config(custom_path=config, provider=ai_provider, model=ai_model)
        ai_cfg = loaded_cfg.ai
        effective_model = (
            ai_model
            or (ai_cfg.tasks.persona_generation if ai_cfg.tasks else None)
            or ai_cfg.model
        )
        effective_cfg = ai_cfg.model_copy(update={"model": effective_model})
        provider_instance = create_provider(effective_cfg)
    except Exception as exc:
        print_error(
            title="AI Configuration Error",
            message=f"Could not initialize AI provider: {exc}",
            suggestion="Run 'blindspot setup' to configure an AI provider or pass '--skip-ai' to perform browser inspection only.",
        )
        raise typer.Exit(code=1)

    try:
        run_output_dir = Path(result.result_json_path).parent if result.result_json_path else output_dir
        personas_file_to_use = None
        if instruction_file and instruction_file.is_file():
            try:
                content_sample = instruction_file.read_text(encoding="utf-8")[:500]
                if "Persona" in content_sample or "persona" in instruction_file.name.lower():
                    personas_file_to_use = instruction_file
            except Exception:
                pass

        if not personas_file_to_use and persona:
            from blindspot.personas.generator import find_specific_persona_file
            personas_file_to_use = find_specific_persona_file(persona)

        import inspect as py_inspect
        sig = py_inspect.signature(generate_personas_and_tasks)
        supports_persona_name = "persona_name" in sig.parameters or any(p.kind == py_inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())

        gen_kwargs = {
            "inspection_result": result,
            "provider": provider_instance,
            "num_personas": effective_personas,
            "output_dir": run_output_dir,
        }
        if personas_file_to_use:
            gen_kwargs["personas_file"] = personas_file_to_use
        if persona and supports_persona_name:
            gen_kwargs["persona_name"] = persona

        status_msg = (
            f"Loading manual user personas from {personas_file_to_use.name}..."
            if personas_file_to_use
            else f"Synthesizing {effective_personas} AI user persona(s) & test tasks ({provider_instance.name})..."
        )
        with console.status(f"[bold cyan]{status_msg}[/bold cyan]", spinner="dots"):
            plan = generate_personas_and_tasks(**gen_kwargs)
        print_personas_summary(plan)
    except AIProviderError as exc:
        print_error(
            title="AI Persona Generation Failed",
            message=exc.message,
            suggestion=exc.suggestion or "Verify your API key, local model status, or network connection. Re-run 'blindspot setup'.",
        )
        raise typer.Exit(code=1)
    except Exception as exc:
        print_error(
            title="Persona Synthesis Error",
            message=str(exc),
            suggestion="Verify model output schema compliance or run with '--skip-ai'.",
        )
        raise typer.Exit(code=1)

    # 8. Automated Browser Task Execution
    execution_result = None
    if skip_execution:
        console.print("[dim]Persona task execution skipped (--skip-execution flag provided).[/dim]")
    else:
        try:
            def _live_event_handler(event: dict) -> None:
                etype = event.get("type")
                if etype == "task_start":
                    pname = event.get("persona_name", "")
                    tobj = event.get("task_objective", "")
                    console.print(f"  [bold cyan]›[/bold cyan] [bold white]{pname}[/bold white] [dim]executing:[/dim] {tobj}")
                elif etype == "action_step":
                    step = event.get("step")
                    act = event.get("action", "")
                    tgt = event.get("target") or ""
                    reasoning = event.get("reasoning") or ""
                    ok = event.get("success", True)
                    status_badge = "[green]✓[/green]" if ok else "[red]✖[/red]"
                    target_display = f" '{tgt}'" if tgt else ""
                    console.print(f"    {status_badge} [dim]Step {step}:[/dim] [cyan]{act}[/cyan]{target_display}")
                    if reasoning:
                        console.print(f"      [dim]Thought: {reasoning}[/dim]")

            console.print()
            console.print("[bold cyan]●[/bold cyan] [bold white]Executing Persona User Journeys[/bold white] [dim](live browser sessions)[/dim]\n")
            effective_actions = None if (unlimited or (max_actions is not None and max_actions <= 0)) else max_actions
            execution_result = execute_persona_tasks(
                plan=plan,
                provider=provider_instance,
                output_dir=run_output_dir or Path(result.result_json_path).parent,
                browser_type=selected_browser,
                headless=effective_headless,
                max_actions_per_task=effective_actions,
                allow_local=allow_local,
                concurrency=concurrency,
                max_personas=personas,
                on_event=_live_event_handler,
                skill=active_skill.name if active_skill else None,
                engine=engine,
                keep_open=keep_open,
            )
            print_execution_summary(execution_result)
        except Exception as exc:
            print_error(
                title="Browser Task Execution Error",
                message=str(exc),
                suggestion="Check browser reachability or try running with '--skip-execution'.",
            )
            raise typer.Exit(code=1)

    # 9. Evidence Aggregation, UX Analysis, and Report Generation
    if skip_report:
        console.print("[dim]UX report generation skipped (--skip-report flag provided).[/dim]")
        return

    try:
        with console.status(
            "[bold cyan]Synthesizing UX findings and generating reports...[/bold cyan]",
            spinner="dots",
        ):
            report, json_path, html_path = generate_ux_report(
                inspection_result=result,
                plan=plan,
                execution_result=execution_result,
                provider=provider_instance,
                output_dir=run_output_dir or Path(result.result_json_path).parent,
                context=resolved_context,
                skill=active_skill.name if active_skill else None,
            )
        print_report_summary(
            report_id=report.report_id,
            target_url=report.target_url,
            total_tasks=report.task_metrics.total_tasks,
            passed_tasks=report.task_metrics.passed_tasks,
            failed_tasks=report.task_metrics.failed_tasks,
            verified_issues=report.verified_issues_count,
            usability_observations=report.usability_observations_count,
            potential_improvements=report.potential_improvements_count,
            json_path=json_path,
            html_path=html_path,
            top_findings=report.findings,
        )
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print_error(
            title="Report Generation Error",
            message=str(exc),
            suggestion="Verify directory write permissions or check previous task logs.",
        )
        raise typer.Exit(code=1)


@app.command(
    name="web",
    help="Launch the interactive BlindSpot web demonstration studio.",
)
def web(
    host: Annotated[
        str,
        typer.Option(
            "--host",
            "-h",
            help="Host address to bind the web server to.",
            show_default=True,
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(
            "--port",
            "-p",
            help="TCP port to listen on.",
            show_default=True,
        ),
    ] = 8000,
    open_browser: Annotated[
        bool,
        typer.Option(
            "--open/--no-open",
            help="Automatically open the web demonstration interface in your browser.",
            show_default=True,
        ),
    ] = True,
    reload: Annotated[
        bool,
        typer.Option(
            "--reload",
            help="Enable auto-reload for local development.",
            show_default=False,
        ),
    ] = False,
) -> None:
    """Launch the interactive BlindSpot web demonstration server."""
    try:
        import uvicorn
        from blindspot.web.app import app as fastapi_app
    except ImportError as exc:
        print_error(
            title="Web Dependencies Missing",
            message=f"The BlindSpot web demonstration requires 'fastapi' and 'uvicorn' ({exc}).",
            suggestion="Repair the installation with:\n    python -m pip install --upgrade blindspot1",
        )
        raise typer.Exit(code=1)

    url = f"http://{host}:{port}"
    console.print()
    console.print(f"[bold cyan]BlindSpot UX Testing Studio[/bold cyan] [dim](Web Server Online)[/dim]\n")
    console.print(f"  • Local URL:   [bold green]{url}[/bold green]")
    console.print(f"  • API Docs:    [dim]{url}/docs[/dim]")
    console.print(f"  • Bound Host:  [dim]{host}[/dim]")
    console.print(f"  • Port:        [dim]{port}[/dim]\n")
    console.print(f"  [dim]Press Ctrl+C to stop the web server.[/dim]\n")

    if open_browser:
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass

    uvicorn.run("blindspot.web.app:app", host=host, port=port, reload=reload)


@app.command(
    name="view",
    help="Open an interactive local web view of a BlindSpot audit run.",
)
def view_cmd(
    run: Annotated[
        Optional[str],
        typer.Argument(
            help="Run ID or path to report (defaults to the most recent run).",
            show_default=False,
        ),
    ] = None,
    no_open: Annotated[
        bool,
        typer.Option(
            "--no-open",
            help="Do not open the browser automatically.",
            show_default=False,
        ),
    ] = False,
) -> None:
    """Open and view completed or running BlindSpot audit report in the default browser."""
    import webbrowser

    reports_dirs = []
    if os.environ.get("BLINDSPOT_REPORTS_DIR"):
        reports_dirs.append(Path(os.environ["BLINDSPOT_REPORTS_DIR"]))
    reports_dirs.extend([Path("blindspot_reports"), Path("reports")])

    target_report_html = None

    if run:
        p = Path(run)
        if p.is_file() and p.suffix == ".html":
            target_report_html = p
        elif (p / "report.html").is_file():
            target_report_html = p / "report.html"
        else:
            for r_dir in reports_dirs:
                if (r_dir / run / "report.html").is_file():
                    target_report_html = r_dir / run / "report.html"
                    break
                elif (r_dir / f"iteration_{run}" / "report.html").is_file():
                    target_report_html = r_dir / f"iteration_{run}" / "report.html"
                    break

    if not target_report_html:
        # Find latest run across reports directories
        all_candidates = []
        for r_dir in reports_dirs:
            if r_dir.is_dir():
                all_candidates.extend(
                    [d for d in r_dir.iterdir() if d.is_dir() and (d / "report.html").is_file()]
                )
        if all_candidates:
            all_candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            target_report_html = all_candidates[0] / "report.html"

    if not target_report_html or not target_report_html.is_file():
        print_error(
            title="Report Not Found",
            message=f"Could not locate an HTML report for '{run or 'latest run'}'.",
            suggestion="Run an audit first with: blindspot --target https://example.com",
        )
        raise typer.Exit(code=1)

    console.print(f"\nServing [bold white]{target_report_html.parent.name}[/bold white] at:")
    console.print(f"  [#60a5fa]{target_report_html.resolve().as_uri()}[/]", soft_wrap=True)
    console.print("[dim]Report opened in your browser. Press Ctrl-C or close browser window when finished.[/dim]\n")

    if not no_open:
        webbrowser.open(target_report_html.resolve().as_uri())


@app.command(
    name="mcp",
    help="Launch the BlindSpot Model Context Protocol (MCP) server for AI coding agents.",
)
def mcp_cmd(
    transport: Annotated[
        str,
        typer.Option(
            "--transport",
            "-t",
            help="Transport mechanism: 'stdio' (default for AI coding agents) or 'sse'.",
            show_default=True,
        ),
    ] = "stdio",
) -> None:
    """Launch the BlindSpot MCP server for local AI coding agent pair programming."""
    try:
        from blindspot.mcp.server import run_mcp_server
    except ImportError as exc:
        print_error(
            title="MCP Dependencies Missing",
            message=f"The BlindSpot MCP server requires the official 'mcp' SDK ({exc}).",
            suggestion="Repair the installation with:\n    python -m pip install --upgrade blindspot1",
        )
        raise typer.Exit(code=1)

    run_mcp_server(transport=transport)


@app.command(
    name="live",
    help="Launch an agentic live browser session that writes screenshots to Markdown and waits for Antigravity's instructions.",
)
def live_cmd(
    target_arg: Annotated[
        Optional[str],
        typer.Argument(
            metavar="[URL]",
            help="Target website URL to inspect (e.g. https://www.flipkart.com).",
            show_default=False,
        ),
    ] = None,
    target: Annotated[
        Optional[str],
        typer.Option(
            "--target",
            "-t",
            help="Target website URL to inspect.",
            show_default=False,
        ),
    ] = None,
    url: Annotated[
        Optional[str],
        typer.Option(
            "--url",
            "-u",
            help="Alias for --target.",
            show_default=False,
        ),
    ] = None,
    goal: Annotated[
        str,
        typer.Option(
            "--goal",
            "-g",
            "--context",
            "-c",
            "--instruction",
            "-i",
            help="Audit goal or specific user task to achieve.",
            show_default=True,
        ),
    ] = "Audit website usability and user journey",
    persona: Annotated[
        Optional[str],
        typer.Option(
            "--persona",
            "-P",
            help="Specify a persona profile or archetype for live audit (default: 'elena').",
            show_default=False,
        ),
    ] = None,
    personas: Annotated[
        int,
        typer.Option(
            "--personas",
            "-p",
            help="Number of personas to test (default: 1).",
            show_default=False,
        ),
    ] = 1,
    output_dir: Annotated[
        Optional[str],
        typer.Option(
            "--output-dir",
            "-o",
            help="Custom directory to store screenshots and markdown logs.",
            show_default=False,
        ),
    ] = None,
    allow_local: Annotated[
        bool,
        typer.Option(
            "--allow-local",
            help="Allow inspection of loopback local development servers (e.g. http://localhost:3000).",
        ),
    ] = False,
    timeout: Annotated[
        int,
        typer.Option(
            "--timeout",
            help="Timeout in seconds while waiting for agent actions.",
        ),
    ] = 1800,
) -> None:
    """Run interactive live browser loop controlled by Antigravity via Markdown & next_action.json."""
    try:
        from blindspot.runtime.desktop_utils import ensure_default_desktop
        ensure_default_desktop()
    except Exception:
        pass

    effective_target = target_arg or target or url
    if not effective_target:
        print_error(
            title="Missing Target URL",
            message="Target website URL was not provided.",
            suggestion="Specify a target URL (e.g. blindspot live https://example.com or blindspot live -t https://example.com).",
        )
        raise typer.Exit(code=1)

    from blindspot.mcp.live_browser import run_live_bridge

    effective_goal = f"{goal} (Persona: {persona})" if persona and persona.lower() not in goal.lower() else goal
    run_dir = run_live_bridge(
        url=effective_target,
        goal=effective_goal,
        output_dir=Path(output_dir) if output_dir else None,
        allow_local=allow_local,
        timeout_seconds=timeout,
    )
    console.print(f"\n[bold green]Live audit completed![/bold green] Report saved to: [cyan]{run_dir}[/cyan]")


@app.command(
    name="step",
    help="Alias for 'live' command to drive step-by-step browser audits.",
)
def step_cmd(
    target_arg: Annotated[
        Optional[str],
        typer.Argument(
            metavar="[URL]",
            help="Target website URL.",
            show_default=False,
        ),
    ] = None,
    target: Annotated[
        Optional[str],
        typer.Option(
            "--target",
            "-t",
            help="Target website URL to inspect.",
            show_default=False,
        ),
    ] = None,
    url: Annotated[
        Optional[str],
        typer.Option(
            "--url",
            "-u",
            help="Alias for --target.",
            show_default=False,
        ),
    ] = None,
    goal: Annotated[str, typer.Option("--goal", "-g", "--context", "-c", "--instruction", "-i", help="Audit goal.")] = "Audit website usability",
    persona: Annotated[Optional[str], typer.Option("--persona", "-P", help="Specify a persona profile or archetype.")] = None,
    personas: Annotated[int, typer.Option("--personas", "-p", help="Number of personas to test.")] = 1,
    output_dir: Annotated[Optional[str], typer.Option("--output-dir", "-o", help="Custom output directory.")] = None,
    allow_local: Annotated[bool, typer.Option("--allow-local", help="Allow loopback.")] = False,
    timeout: Annotated[int, typer.Option("--timeout", help="Timeout in seconds.")] = 1800,
) -> None:
    """Alias for live_cmd."""
    live_cmd(target_arg=target_arg, target=target, url=url, goal=goal, persona=persona, personas=personas, output_dir=output_dir, allow_local=allow_local, timeout=timeout)


@app.command(
    name="scroll",
    help="Perform a zero-AI live browser scrolling test in front of you.",
)
def scroll_cmd(
    target: Annotated[
        str,
        typer.Argument(
            help="Target website URL to scroll (e.g. https://amazon.com).",
        ),
    ] = "https://amazon.com",
) -> None:
    """Launch a visible Chromium window and smoothly scroll down and back up with 0 AI tokens."""
    from blindspot.runtime.scroll_test import run_live_scroll_test

    run_live_scroll_test(target)


@skill_app.command(
    name="list",
    help="List all packaged BlindSpot Agent Skills available for AI coding agents.",
)
def list_skills_cmd() -> None:
    """List all bundled Agent Skills conforming to the open standard."""
    skills = list_bundled_skills()
    if not skills:
        console.print("[dim]No bundled Agent Skills found.[/dim]")
        return
    print_skills_list(skills)


@skill_app.command(
    name="validate",
    help="Validate a SKILL.md file or directory against the Agent Skills specification checklist.",
)
def validate_skills_cmd(
    target_path: Annotated[
        Optional[Path],
        typer.Argument(
            help="Path to a SKILL.md file or directory containing skills. Defaults to bundled skills.",
        ),
    ] = None,
) -> None:
    """Validate skill files against the open Agent Skills specification."""
    search_dir = target_path or get_bundled_skills_dir()
    results = []

    if search_dir.is_file() and search_dir.name == "SKILL.md":
        results.append(validate_skill(search_dir))
    elif search_dir.is_dir():
        if (search_dir / "SKILL.md").is_file():
            results.append(validate_skill(search_dir / "SKILL.md"))
        else:
            for item in sorted(search_dir.iterdir()):
                if item.is_dir() and (item / "SKILL.md").is_file():
                    results.append(validate_skill(item / "SKILL.md"))
    else:
        print_error(
            title="Invalid Path",
            message=f"Path '{search_dir}' is neither a directory nor a SKILL.md file.",
        )
        raise typer.Exit(code=2)

    if not results:
        console.print(f"[dim]No SKILL.md files found in {search_dir}[/dim]")
        return

    print_skills_validation_results(results)

    if not all(r.is_valid for r in results):
        raise typer.Exit(code=1)


@skill_app.command(
    name="install",
    help="Install BlindSpot Agent Skills into a project workspace (.agents/skills and/or .github/skills).",
)
def install_skills_cmd(
    target: Annotated[
        str,
        typer.Option(
            "--target",
            "-t",
            help="Target agent directory: 'agents' (.agents/skills), 'github' (.github/skills), 'global' (~/.gemini/config/plugins/blindspot), 'both', or 'all'.",
            show_default=True,
        ),
    ] = "both",
    global_plugin: Annotated[
        bool,
        typer.Option(
            "--global",
            "--antigravity",
            help="Install globally into Antigravity plugins directory (~/.gemini/config/plugins/blindspot).",
            show_default=False,
        ),
    ] = False,
    dest: Annotated[
        Optional[Path],
        typer.Option(
            "--dest",
            "-d",
            help="Destination project root folder. Defaults to current working directory.",
        ),
    ] = None,
) -> None:
    """Export and install BlindSpot skills into the local workspace or global Antigravity configuration."""
    project_root = dest or Path.cwd()
    if global_plugin or target in ("global", "antigravity"):
        target_modes = ["global"]
    elif target == "both":
        target_modes = ["agents", "github"]
    elif target in ("all", "full"):
        target_modes = ["agents", "github", "global"]
    else:
        target_modes = [target]

    valid_targets = ("agents", "github", "both", "global", "antigravity", "all", "full")
    if target not in valid_targets:
        print_error(
            title="Invalid Target",
            message=f"Invalid target '{target}'. Must be one of: {', '.join(valid_targets)}.",
        )
        raise typer.Exit(code=2)

    installed = install_skills_to_workspace(project_root, targets=target_modes)
    print_skills_installed(installed)


@skill_app.command(
    name="show",
    help="Display the full instructions, rules, output format, and metadata for a specific skill.",
)
def show_skill_cmd(
    name: Annotated[
        str,
        typer.Argument(
            help="Name or alias of the skill (e.g. wcag, ecommerce, mobile, ux).",
        ),
    ],
) -> None:
    """Tier 2 Progressive Disclosure: display full skill instructions and playbook."""
    from blindspot.skills.registry import SkillRegistry

    reg = SkillRegistry()
    skill = reg.get_skill(name)
    if not skill:
        print_error(
            title="Skill Not Found",
            message=f"No Agent Skill found matching '{name}'.",
            suggestion="Run 'blindspot skill list' to see available skills.",
        )
        raise typer.Exit(code=1)

    console.print(f"\n[bold white]Agent Skill:[/bold white] [#38bdf8]{skill.name}[/] [dim](v{skill.version})[/dim]")
    console.print(f"[bold cyan]Description:[/bold cyan] {skill.description}")
    if skill.allowed_tools:
        console.print(f"[bold cyan]Approved Tools:[/bold cyan] {skill.allowed_tools}")
    if skill.skill_path:
        console.print(f"[bold cyan]File Path:[/bold cyan] {skill.skill_path}")
    console.print("\n" + "─" * 60 + "\n")
    console.print(skill.body)
    console.print("\n" + "─" * 60 + "\n")


@skill_app.command(
    name="match",
    help="Match natural language query or user goal to the best Agent Skill.",
)
def match_skill_cmd(
    query: Annotated[
        str,
        typer.Argument(
            help="User prompt, testing goal, or scenario (e.g. 'check keyboard focus accessibility').",
        ),
    ],
) -> None:
    """Find and rank matching Agent Skills using keyword and intent scoring."""
    from blindspot.skills.registry import SkillRegistry

    reg = SkillRegistry()
    matches = reg.find_matches(query)
    if not matches:
        console.print(f"[dim]No matching Agent Skills found for query: \"{query}\"[/dim]")
        return

    console.print(f"\n[bold]Matched Agent Skills for:[/bold] \"[italic]{query}[/italic]\"\n")
    for skill, score in matches:
        pct = int(score * 100)
        console.print(f"  [bold green]{pct}% match[/bold green] → [bold white]{skill.name}[/bold white] [dim]({skill.description})[/dim]")
    console.print()


@app.command(
    name="uninstall",
    help="Safely and completely uninstall BlindSpot1 / BlindSpot, removing command shims, PATH entries, and configs.",
)
def uninstall_cmd(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-y",
            help="Perform full uninstallation without interactive confirmation prompts.",
            show_default=False,
        ),
    ] = False,
    clean_config: Annotated[
        bool,
        typer.Option(
            "--clean-config",
            help="Also remove configuration and cache directory (~/.blindspot).",
            show_default=False,
        ),
    ] = False,
) -> None:
    """Safely uninstall BlindSpot1, remove all global shims, links, and optional configs."""
    from blindspot.uninstall import perform_uninstall
    success = perform_uninstall(force=force, clean_config=clean_config)
    if not success:
        raise typer.Exit(code=1)


def main_entry() -> None:
    """Entry point for CLI that automatically routes bare URL arguments to inspect subcommand."""
    import sys

    # On Windows, ensure execution on the visible interactive user desktop (WinSta0\Default)
    try:
        from blindspot.runtime.desktop_utils import ensure_default_desktop
        ensure_default_desktop()
    except Exception:
        pass

    if len(sys.argv) > 1:
        first_arg = sys.argv[1].strip()
        known_commands = {
            "inspect",
            "verify",
            "web",
            "mcp",
            "config",
            "provider",
            "model",
            "providers",
            "skill",
            "setup",
            "uninstall",
            "live",
            "step",
            "scroll",
            "--help",
            "-h",
            "--version",
            "-v",
        }
        if (first_arg not in known_commands and not first_arg.startswith("-")) or first_arg in ("-t", "-u", "--target", "--url"):
            # It's a bare URL or target option flag, route to live agentic audit
            sys.argv.insert(1, "live")
    app()


if __name__ == "__main__":
    main_entry()

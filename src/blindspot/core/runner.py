"""Central orchestration pipeline for BlindSpot inspection, persona testing, and reporting."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
import secrets
from typing import Any, Callable, Dict, Optional, Union

from blindspot.ai import create_provider
from blindspot.ai.base import BaseAIProvider
from blindspot.browser import BrowserInspectionResult, inspect_website
from blindspot.config.loader import load_config
from blindspot.core.validation import validate_context, validate_url
from blindspot.execution.models import ExecutionRunResult
from blindspot.execution.runner import execute_persona_tasks
from blindspot.execution.safety import validate_navigation_url
from blindspot.personas.generator import generate_personas_and_tasks, load_personas_from_markdown
from blindspot.personas.models import PersonaPlan
from blindspot.reporting.generator import generate_ux_report
from blindspot.reporting.models import BlindSpotReport


@dataclass
class PipelineConfig:
    """Configuration options for a complete BlindSpot testing run."""

    url: str
    context: str
    output_dir: Optional[Path] = None
    iteration: Optional[str] = None
    personas: int = 1
    persona: Optional[str] = None
    browser: str = "chromium"
    headless: bool = False
    max_actions: int = 35
    skip_ai: bool = False
    skip_execution: bool = False
    skip_report: bool = False
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    allow_local: bool = False
    skill: Optional[str] = None
    personas_file: Optional[Path] = None
    engine: str = "auto"
    keep_open: bool = False


@dataclass
class PipelineResult:
    """Result of an end-to-end BlindSpot testing run."""

    run_id: str
    target_url: str
    output_dir: Path
    status: str  # "completed", "cancelled", "failed"
    inspection_result: Optional[BrowserInspectionResult] = None
    plan: Optional[PersonaPlan] = None
    execution_result: Optional[ExecutionRunResult] = None
    report: Optional[BlindSpotReport] = None
    json_path: Optional[str] = None
    html_path: Optional[str] = None
    error_message: Optional[str] = None


def get_next_run_id(reports_dir: Optional[Union[str, Path]] = None) -> str:
    """Find the next sequential run number (001, 002, 003...) based on existing folders in reports_dir."""
    if reports_dir is None:
        base = Path(os.environ.get("BLINDSPOT_REPORTS_DIR", "blindspot_reports" if Path("blindspot_reports").is_dir() else "reports"))
    else:
        base = Path(reports_dir)

    max_num = 0
    if base.exists() and base.is_dir():
        for entry in base.iterdir():
            if entry.is_dir():
                name = entry.name.strip()
                if name.isdigit():
                    try:
                        max_num = max(max_num, int(name))
                    except ValueError:
                        pass
                elif name.startswith("iteration_") and name[10:].isdigit():
                    try:
                        max_num = max(max_num, int(name[10:]))
                    except ValueError:
                        pass

    next_num = max_num + 1
    return f"{next_num:03d}"


def generate_run_id(reports_dir: Optional[Union[str, Path]] = None) -> str:
    """Generate a simple sequential run ID (e.g. '001', '002', '003')."""
    return get_next_run_id(reports_dir)


def run_pipeline(
    config: PipelineConfig,
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> PipelineResult:
    """Execute the full BlindSpot testing pipeline with real-time event reporting.

    Stages:
    1. Input Validation & SSRF Safety
    2. Browser Inspection & DOM Extraction
    3. AI Persona & Task Synthesis
    4. Autonomous Persona Browser Task Execution
    5. Evidence Aggregation & UX Report Generation
    """

    def emit(event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        if on_event:
            payload = {
                "type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if data:
                payload.update(data)
            try:
                on_event(payload)
            except Exception:
                pass

    # 1. Input Validation
    url_res = validate_url(config.url)
    if not url_res.is_valid:
        raise ValueError(f"Invalid URL: {url_res.error_message}")

    # SSRF & Private Network Defense
    is_safe_url, ssrf_reason = validate_navigation_url(config.url, allow_local=config.allow_local)
    if not is_safe_url:
        raise ValueError(f"Security Policy Blocked: {ssrf_reason}")

    context_res, resolved_context = validate_context(config.context)
    if not context_res.is_valid:
        raise ValueError(f"Invalid Context: {context_res.error_message}")

    reports_root = Path(os.environ.get("BLINDSPOT_REPORTS_DIR", "blindspot_reports" if Path("blindspot_reports").is_dir() else "reports"))
    reports_root.mkdir(parents=True, exist_ok=True)
    if config.output_dir:
        run_output_dir = Path(config.output_dir)
        run_id = run_output_dir.name
    elif getattr(config, "iteration", None):
        iter_name = str(config.iteration).strip()
        if iter_name.isdigit():
            run_id = f"{int(iter_name):03d}"
        else:
            run_id = iter_name
        run_output_dir = reports_root / run_id
    else:
        run_id = generate_run_id(reports_root)
        run_output_dir = reports_root / run_id

    run_output_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir = run_output_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # Instantly create browser_interaction.md the moment auditing starts
    interaction_md_path = run_output_dir / "browser_interaction.md"
    init_header = (
        f"# Live Browser Interaction\n\n"
        f"- **Target URL:** {config.url.strip()}\n"
        f"- **Current URL:** {config.url.strip()}\n"
        f"- **Page Title:** Initializing...\n"
        f"- **Audit Goal:** {resolved_context}\n"
        f"- **Status:** IN PROGRESS\n\n"
        f"## Step 0: Initial page observation\n\n"
        f"Target website loaded into live browser. Ready for inspection.\n\n"
        f"![Initial page](screenshots/step-000.png)\n"
    )
    interaction_md_path.write_text(init_header, encoding="utf-8")

    result = PipelineResult(
        run_id=run_id,
        target_url=config.url.strip(),
        output_dir=run_output_dir,
        status="running",
    )

    emit("pipeline_start", {
        "run_id": run_id,
        "target_url": config.url.strip(),
        "output_dir": str(run_output_dir),
        "personas_count": config.personas,
        "headless": config.headless,
    })

    try:
        # Check cancellation
        if cancel_check and cancel_check():
            result.status = "cancelled"
            emit("pipeline_cancelled", {"run_id": run_id})
            return result

        # 2. Browser Inspection (DOM analysis and baseline viewport capture)
        emit("stage_start", {"stage": "inspection", "message": "Analyzing website structure..."})
        inspection = inspect_website(
            url=config.url.strip(),
            context=resolved_context,
            output_dir=run_output_dir,
            browser_type=config.browser,
            headless=config.headless,
            allow_local=config.allow_local,
        )
        result.inspection_result = inspection
        # Save baseline screenshot as step-000.png
        try:
            if inspection.screenshot_path and Path(inspection.screenshot_path).exists():
                import shutil
                step0_shot = screenshots_dir / "step-000.png"
                shutil.copy2(inspection.screenshot_path, step0_shot)
        except Exception:
            pass

        emit("stage_finish", {
            "stage": "inspection",
            "title": inspection.title,
            "final_url": inspection.final_url,
            "total_elements": inspection.summary.total_interactive_elements,
            "links_count": inspection.summary.links_count,
            "buttons_count": inspection.summary.buttons_count,
            "screenshot_path": inspection.screenshot_path,
        })

        if cancel_check and cancel_check():
            result.status = "cancelled"
            emit("pipeline_cancelled", {"run_id": run_id})
            return result

        # 3. AI Persona Generation
        provider_instance: Optional[BaseAIProvider] = None
        plan: Optional[PersonaPlan] = None
        if not config.skip_ai:
            if config.personas_file and Path(config.personas_file).exists():
                emit("stage_start", {"stage": "personas", "message": f"Loading manual personas from {config.personas_file}..."})
                plan = load_personas_from_markdown(
                    source=config.personas_file,
                    website_url=inspection.final_url,
                    context=inspection.context,
                )
                plan_path = run_output_dir / "personas.json"
                plan.plan_file_path = str(plan_path)
                with open(plan_path, "w", encoding="utf-8") as f:
                    f.write(plan.model_dump_json(indent=2))
                result.plan = plan
                if not config.skip_execution or not config.skip_report:
                    try:
                        loaded_cfg = load_config(provider=config.ai_provider, model=config.ai_model)
                        ai_cfg = loaded_cfg.ai
                        provider_instance = create_provider(ai_cfg)
                        if hasattr(provider_instance, "start_session"):
                            try:
                                provider_instance.start_session()
                            except Exception:
                                pass
                    except Exception:
                        pass
            else:
                emit("stage_start", {"stage": "personas", "message": "Synthesizing AI user personas & test tasks..."})
                loaded_cfg = load_config(provider=config.ai_provider, model=config.ai_model)
                ai_cfg = loaded_cfg.ai
                effective_model = (
                    config.ai_model
                    or (ai_cfg.tasks.persona_generation if ai_cfg.tasks else None)
                    or ai_cfg.model
                )
                effective_cfg = ai_cfg.model_copy(update={"model": effective_model})
                provider_instance = create_provider(effective_cfg)
                if hasattr(provider_instance, "start_session"):
                    try:
                        provider_instance.start_session()
                    except Exception:
                        pass

                plan = generate_personas_and_tasks(
                    inspection_result=inspection,
                    provider=provider_instance,
                    num_personas=config.personas,
                    output_dir=run_output_dir,
                    persona_name=config.persona,
                )
                result.plan = plan
            emit("stage_finish", {
                "stage": "personas",
                "personas_count": len(plan.personas),
                "total_tasks": sum(len(p.tasks) for p in plan.personas),
                "personas": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "experience": getattr(p, "experience_level", "Standard"),
                        "goals": getattr(p, "goals", []),
                        "tasks_count": len(p.tasks),
                    }
                    for p in plan.personas
                ],
            })

        if cancel_check and cancel_check():
            result.status = "cancelled"
            emit("pipeline_cancelled", {"run_id": run_id})
            return result

        # 4. Browser Task Execution
        execution_res: Optional[ExecutionRunResult] = None
        if not config.skip_execution and plan and provider_instance:
            emit("stage_start", {"stage": "execution", "message": "Running automated persona browser tasks..."})
            execution_res = execute_persona_tasks(
                plan=plan,
                provider=provider_instance,
                output_dir=run_output_dir,
                browser_type=config.browser,
                headless=config.headless,
                max_actions_per_task=config.max_actions,
                allow_local=config.allow_local,
                on_event=on_event,
                cancel_check=cancel_check,
                skill=config.skill,
                engine=config.engine,
                keep_open=config.keep_open,
            )
            result.execution_result = execution_res
            emit("stage_finish", {
                "stage": "execution",
                "total_tasks": execution_res.total_tasks,
                "passed_tasks": execution_res.passed_tasks,
                "failed_tasks": execution_res.failed_tasks,
                "inconclusive_tasks": execution_res.inconclusive_tasks,
            })

        if cancel_check and cancel_check():
            result.status = "cancelled"
            emit("pipeline_cancelled", {"run_id": run_id})
            return result

        # 5. UX Report Generation
        if not config.skip_report:
            emit("stage_start", {"stage": "reporting", "message": "Aggregating evidence & generating UX reports..."})
            report, json_path, html_path = generate_ux_report(
                inspection_result=inspection,
                plan=plan,
                execution_result=execution_res,
                provider=provider_instance,
                output_dir=run_output_dir,
                context=resolved_context,
                skill=config.skill,
            )
            result.report = report
            result.json_path = json_path
            result.html_path = html_path
            emit("stage_finish", {
                "stage": "reporting",
                "report_id": report.report_id,
                "verified_issues": report.verified_issues_count,
                "usability_observations": report.usability_observations_count,
                "potential_improvements": report.potential_improvements_count,
                "json_path": json_path,
                "html_path": html_path,
            })

        result.status = "completed"
        emit("pipeline_finish", {
            "run_id": run_id,
            "status": "completed",
            "report_id": result.report.report_id if result.report else None,
            "json_path": result.json_path,
            "html_path": result.html_path,
        })
        return result

    except Exception as exc:
        result.status = "failed"
        result.error_message = str(exc)
        emit("pipeline_error", {
            "run_id": run_id,
            "error": str(exc),
        })
        raise
    finally:
        if provider_instance and hasattr(provider_instance, "stop_session"):
            try:
                provider_instance.stop_session()
            except Exception:
                pass

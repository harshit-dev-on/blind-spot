"""Orchestrator for executing persona tasks in isolated browser contexts."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from playwright.sync_api import Error as PlaywrightError, sync_playwright

from blindspot.ai.base import BaseAIProvider
from blindspot.execution.agent import PersonaTaskAgent
from blindspot.execution.models import (
    ExecutionRunResult,
    PersonaExecutionResult,
)
from blindspot.personas.models import PersonaPlan


class PersonaTestRunner:
    """Manages browser execution lifecycle, context isolation, and evidence persistence."""

    def __init__(
        self,
        provider: BaseAIProvider,
        browser_type: str = "chromium",
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 800,
        max_actions_per_task: Optional[int] = 15,
        action_timeout_ms: int = 15000,
        allow_local: bool = False,
        concurrency: int = 1,
        max_personas: Optional[int] = None,
        skill: Optional[str] = None,
        engine: str = "auto",
        keep_open: bool = False,
    ) -> None:
        self.provider = provider
        self.browser_type = browser_type.lower().strip()
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.max_actions_per_task = max_actions_per_task
        self.action_timeout_ms = action_timeout_ms
        self.allow_local = allow_local
        self.concurrency = max(1, int(concurrency))
        self.max_personas = max(1, int(max_personas)) if max_personas else None
        self.skill = skill
        self.engine = "antigravity"
        self.keep_open = keep_open

    def run_plan(
        self,
        plan: PersonaPlan,
        output_dir: Union[str, Path],
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> ExecutionRunResult:
        """Execute tasks for all personas in the plan across isolated browser contexts.

        Args:
            plan: Synthesized PersonaPlan containing personas and assigned tasks.
            output_dir: Directory where execution artifacts, screenshots, and results are stored.
            on_event: Optional callback for progress and action events.
            cancel_check: Optional callable that returns True when task should be cancelled.

        Returns:
            ExecutionRunResult summarizing all persona task outcomes.
        """
        # All inspection runs strictly via the Antigravity native execution engine
        run_dir = Path(output_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        evidence_base = run_dir / "evidence"
        evidence_base.mkdir(parents=True, exist_ok=True)

        personas_to_run = plan.personas
        if self.max_personas and self.max_personas > 0:
            personas_to_run = personas_to_run[: self.max_personas]

        if hasattr(self.provider, "start_session"):
            try:
                self.provider.start_session()
            except Exception:
                pass

        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed

        event_lock = threading.Lock()

        def _safe_emit(data: Dict[str, Any]) -> None:
            if on_event:
                with event_lock:
                    try:
                        on_event(data)
                    except Exception:
                        pass

        def _execute_single_persona(persona) -> PersonaExecutionResult:
            agent = PersonaTaskAgent(
                provider=self.provider,
                max_actions=self.max_actions_per_task,
                action_timeout_ms=self.action_timeout_ms,
                allow_local=self.allow_local,
                headless=self.headless,
                skill=self.skill,
            )
            with sync_playwright() as p:
                launcher = getattr(p, self.browser_type, None)
                if launcher is None:
                    raise ValueError(f"Browser engine '{self.browser_type}' is not supported.")

                slow_mo = 900 if not self.headless else 0
                launch_args = []
                if not self.headless and self.browser_type == "chromium":
                    launch_args.extend([
                        "--window-position=40,40",
                        "--window-size=1280,850",
                        "--disable-blink-features=AutomationControlled",
                    ])

                try:
                    browser = launcher.launch(headless=self.headless, slow_mo=slow_mo, args=launch_args)
                except PlaywrightError as exc:
                    err_msg = str(exc)
                    if "Executable doesn't exist" in err_msg or "Please run" in err_msg:
                        from blindspot.runtime import ensure_browser_engine
                        ensure_browser_engine(self.browser_type)
                        browser = launcher.launch(headless=self.headless, slow_mo=slow_mo, args=launch_args)
                    else:
                        raise

                try:
                    context_kwargs = {
                        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    }
                    if not self.headless and self.browser_type == "chromium":
                        context_kwargs["no_viewport"] = True
                    else:
                        context_kwargs["viewport"] = {"width": self.viewport_width, "height": self.viewport_height}

                    context_obj = browser.new_context(**context_kwargs)
                    page = context_obj.new_page()
                    if not self.headless:
                        try:
                            page.bring_to_front()
                            from blindspot.runtime.window_utils import bring_browser_window_to_foreground
                            bring_browser_window_to_foreground(stay_topmost=True)
                        except Exception:
                            pass
                    task_results = []
                    journey_history: List[Dict[str, Any]] = []
                    try:
                        for task in persona.tasks:
                            if cancel_check and cancel_check():
                                break

                            page = agent._get_active_page(page)

                            _safe_emit({
                                "type": "task_start",
                                "persona_id": persona.id,
                                "persona_name": persona.name,
                                "task_id": task.id,
                                "task_objective": task.objective,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            })

                            task_evidence_dir = run_dir / "personas" / persona.id / "evidence" / task.id
                            task_evidence_dir.mkdir(parents=True, exist_ok=True)
                            compat_evidence_dir = evidence_base / persona.id / task.id
                            compat_evidence_dir.mkdir(parents=True, exist_ok=True)
                            result = agent.execute_task(
                                page=page,
                                persona=persona,
                                task=task,
                                evidence_dir=task_evidence_dir,
                                initial_url=plan.website_url,
                                on_step=_safe_emit,
                                cancel_check=cancel_check,
                                journey_history=journey_history,
                                run_output_dir=run_dir,
                            )
                            task_results.append(result)
                            page = agent._get_active_page(page)

                            _safe_emit({
                                "type": "task_finish",
                                "persona_id": persona.id,
                                "persona_name": persona.name,
                                "task_id": task.id,
                                "status": result.status.value,
                                "evidence": result.collected_evidence,
                                "error": result.error_message,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            })
                    finally:
                        if not self.headless:
                            try:
                                page.evaluate("""
                                    () => {
                                        try {
                                            const banner = document.getElementById('__blindspot_status_banner') || document.createElement('div');
                                            banner.id = '__blindspot_status_banner';
                                            banner.innerHTML = '⚡ BlindSpot1 Session Complete — Inspecting Final Page (Close window to exit)...';
                                            banner.style.cssText = 'position:fixed;top:12px;left:50%;transform:translateX(-50%);background:#10b981;color:#ffffff;font-size:15px;font-weight:700;padding:12px 28px;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,0.4);z-index:99999999;font-family:system-ui,-apple-system,sans-serif;letter-spacing:0.3px;pointer-events:none;';
                                            if (!document.getElementById('__blindspot_status_banner')) document.body.appendChild(banner);
                                        } catch (e) {}
                                    }
                                """)
                            except Exception:
                                pass
                            try:
                                import time
                                wait_seconds = 180 if self.keep_open else 12
                                for _ in range(wait_seconds):
                                    if page.is_closed():
                                        break
                                    time.sleep(1.0)
                            except Exception:
                                pass
                        context_obj.close()

                    return PersonaExecutionResult(
                        persona_id=persona.id,
                        persona_name=persona.name,
                        task_results=task_results,
                    )
                finally:
                    if not self.headless:
                        try:
                            from blindspot.runtime.window_utils import unpin_browser_window
                            unpin_browser_window()
                        except Exception:
                            pass
                    browser.close()

        # Multi-worker simultaneous execution
        if self.concurrency > 1 and len(personas_to_run) > 1:
            workers = min(self.concurrency, len(personas_to_run))
            results_dict: Dict[str, PersonaExecutionResult] = {}
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_persona = {
                    executor.submit(_execute_single_persona, persona): persona
                    for persona in personas_to_run
                }
                for future in as_completed(future_to_persona):
                    p = future_to_persona[future]
                    try:
                        res = future.result()
                        results_dict[p.id] = res
                    except Exception:
                        results_dict[p.id] = PersonaExecutionResult(
                            persona_id=p.id,
                            persona_name=p.name,
                            task_results=[],
                        )
            persona_results = [results_dict[p.id] for p in personas_to_run if p.id in results_dict]
        else:
            # Sequential single-browser execution (optimal for 1 persona testing and focused headed observation)
            persona_results = []
            agent = PersonaTaskAgent(
                provider=self.provider,
                max_actions=self.max_actions_per_task,
                action_timeout_ms=self.action_timeout_ms,
                allow_local=self.allow_local,
                headless=self.headless,
                skill=self.skill,
            )

            with sync_playwright() as p:
                launcher = getattr(p, self.browser_type, None)
                if launcher is None:
                    raise ValueError(f"Browser engine '{self.browser_type}' is not supported.")

                slow_mo = 400 if not self.headless else 0
                launch_args = []
                if not self.headless and self.browser_type == "chromium":
                    launch_args.extend(["--start-maximized", "--disable-blink-features=AutomationControlled"])

                try:
                    browser = launcher.launch(headless=self.headless, slow_mo=slow_mo, args=launch_args)
                except PlaywrightError as exc:
                    err_msg = str(exc)
                    if "Executable doesn't exist" in err_msg or "Please run" in err_msg:
                        from blindspot.runtime import ensure_browser_engine
                        ensure_browser_engine(self.browser_type)
                        browser = launcher.launch(headless=self.headless, slow_mo=slow_mo, args=launch_args)
                    else:
                        raise

                try:
                    for persona in personas_to_run:
                        if cancel_check and cancel_check():
                            break

                        context_kwargs = {
                            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        }
                        if not self.headless and self.browser_type == "chromium":
                            context_kwargs["no_viewport"] = True
                        else:
                            context_kwargs["viewport"] = {"width": self.viewport_width, "height": self.viewport_height}

                        context_obj = browser.new_context(**context_kwargs)
                        page = context_obj.new_page()
                        if not self.headless:
                            try:
                                page.bring_to_front()
                                from blindspot.runtime.window_utils import bring_browser_window_to_foreground
                                bring_browser_window_to_foreground()
                            except Exception:
                                pass

                        task_results = []
                        journey_history: List[Dict[str, Any]] = []
                        try:
                            for task in persona.tasks:
                                if cancel_check and cancel_check():
                                    break

                                page = agent._get_active_page(page)

                                if on_event:
                                    try:
                                        on_event({
                                            "type": "task_start",
                                            "persona_id": persona.id,
                                            "persona_name": persona.name,
                                            "task_id": task.id,
                                            "task_objective": task.objective,
                                            "timestamp": datetime.now(timezone.utc).isoformat(),
                                        })
                                    except Exception:
                                        pass

                                task_evidence_dir = run_dir / "personas" / persona.id / "evidence" / task.id
                                task_evidence_dir.mkdir(parents=True, exist_ok=True)
                                compat_evidence_dir = evidence_base / persona.id / task.id
                                compat_evidence_dir.mkdir(parents=True, exist_ok=True)
                                result = agent.execute_task(
                                    page=page,
                                    persona=persona,
                                    task=task,
                                    evidence_dir=task_evidence_dir,
                                    initial_url=plan.website_url,
                                    on_step=on_event,
                                    cancel_check=cancel_check,
                                    journey_history=journey_history,
                                    run_output_dir=run_dir,
                                )
                                task_results.append(result)
                                page = agent._get_active_page(page)

                                if self.keep_open and not self.headless:
                                    page.wait_for_timeout(10000)

                                if on_event:
                                    try:
                                        on_event({
                                            "type": "task_finish",
                                            "persona_id": persona.id,
                                            "persona_name": persona.name,
                                            "task_id": task.id,
                                            "status": result.status.value,
                                            "evidence": result.collected_evidence,
                                            "error": result.error_message,
                                            "timestamp": datetime.now(timezone.utc).isoformat(),
                                        })
                                    except Exception:
                                        pass
                        finally:
                            context_obj.close()

                        persona_results.append(
                            PersonaExecutionResult(
                                persona_id=persona.id,
                                persona_name=persona.name,
                                task_results=task_results,
                            )
                        )
                finally:
                    browser.close()

        if hasattr(self.provider, "stop_session"):
            try:
                self.provider.stop_session()
            except Exception:
                pass

        # Build run result
        run_result = ExecutionRunResult(
            target_url=plan.website_url,
            browser=self.browser_type,
            headless=self.headless,
            personas=persona_results,
        )

        # Save to disk
        results_file = run_dir / "execution_results.json"
        run_result.results_file_path = str(results_file)
        with open(results_file, "w", encoding="utf-8") as f:
            f.write(run_result.model_dump_json(indent=2))

        return run_result


def execute_persona_tasks(
    plan: PersonaPlan,
    provider: BaseAIProvider,
    output_dir: Union[str, Path],
    browser_type: str = "chromium",
    headless: bool = True,
    max_actions_per_task: Optional[int] = 15,
    allow_local: bool = False,
    concurrency: int = 1,
    max_personas: Optional[int] = None,
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
    skill: Optional[str] = None,
    engine: str = "auto",
    keep_open: bool = False,
) -> ExecutionRunResult:
    """Convenience functional helper to run persona tasks."""
    runner = PersonaTestRunner(
        provider=provider,
        browser_type=browser_type,
        headless=headless,
        max_actions_per_task=max_actions_per_task,
        allow_local=allow_local,
        concurrency=concurrency,
        max_personas=max_personas,
        skill=skill,
        engine=engine,
        keep_open=keep_open,
    )
    return runner.run_plan(
        plan=plan,
        output_dir=output_dir,
        on_event=on_event,
        cancel_check=cancel_check,
    )

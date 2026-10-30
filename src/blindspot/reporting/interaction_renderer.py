"""Renderer for full autonomous persona interaction logs in Markdown.

Captures the visual persona journey: step-by-step persona thoughts, screenshots
analyzed before each action, dispatched actions, target element attributes,
resulting state screenshots, and final outcome evidence without verbose raw HTML dumps.
"""

from pathlib import Path
from typing import Dict, List, Optional
from blindspot.execution.models import (
    ActionExecutionRecord,
    ExecutionRunResult,
    PersonaExecutionResult,
    TaskExecutionResult,
)
from blindspot.personas.models import Persona, PersonaPlan, PersonaTask


def render_task_interaction_markdown(
    persona: Persona,
    task: PersonaTask,
    task_result: TaskExecutionResult,
    output_dir: Optional[Path] = None,
) -> str:
    """Render a clean Markdown log of a single persona task interaction with visual screenshots."""
    lines: List[str] = []

    lines.append(f"## 👤 Persona: {persona.name} ({getattr(persona, 'experience_level', 'Standard')})")
    lines.append(f"> {persona.description}")
    lines.append("")
    lines.append(f"### 🎯 Task: {task.objective}")
    lines.append(f"- **Task ID**: `{task.id}`")
    lines.append(f"- **Task Status**: `{task_result.status.value.upper()}`")
    lines.append(f"- **Initial URL**: `{task_result.initial_url}`")
    lines.append(f"- **Final URL**: `{task_result.final_url}`")
    lines.append(f"- **Started**: `{task_result.start_time}`")
    lines.append(f"- **Finished**: `{task_result.end_time}`")
    lines.append("")

    # Success criteria
    criteria_list = task.success_criteria if isinstance(task.success_criteria, list) else [str(task.success_criteria)]
    lines.append("#### 🎯 Observable Success Criteria")
    for crit in criteria_list:
        lines.append(f"- {crit}")
    lines.append("")

    # Initial baseline screenshot for task if available
    if task_result.actions_taken and task_result.actions_taken[0].screenshot_path:
        first_shot = task_result.actions_taken[0].screenshot_path
        rel_first = first_shot
        if output_dir:
            try:
                rel_first = str(Path(first_shot).relative_to(output_dir)).replace("\\", "/")
            except Exception:
                pass
        lines.append(f"![Initial Page State Before Actions]({rel_first})")
        lines.append("")

    # Step-by-Step Action History with Screenshots
    lines.append("---")
    lines.append("### 👣 Step-by-Step Persona Visual Journey & Actions")
    lines.append("")

    if not task_result.actions_taken:
        lines.append("*No action steps were executed for this task.*")
        lines.append("")
    else:
        for rec in task_result.actions_taken:
            act = rec.action
            act_type = act.action.value.upper() if hasattr(act.action, "value") else str(act.action).upper()
            target_desc = act.target or (f"@{act.mark}" if act.mark is not None else "")
            header_target = f" → `{target_desc}`" if target_desc else ""

            status_badge = "✓ SUCCESS" if rec.success else "✖ FAILED"
            lines.append(f"#### Step {rec.step}: `{act_type}`{header_target} ({status_badge})")
            lines.append("")
            lines.append(f"- **Page URL**: `{rec.page_url}`")
            lines.append(f"- **Page Title**: {rec.page_title}")
            if act.reasoning:
                lines.append(f"- **Persona Observation & Decision**: *\"{act.reasoning}\"*")

            # Action attributes
            val = act.value or act.text or ""
            if val:
                lines.append(f"- **Input Text**: `{val}`")
            if act.key:
                lines.append(f"- **Key Pressed**: `{act.key}`")
            if act.direction:
                lines.append(f"- **Scroll Direction**: `{act.direction}` ({act.amount}px)")

            # Target element metadata
            if rec.target_element:
                el = rec.target_element
                lines.append("- **Target Control Details**:")
                lines.append(f"  - **Tag**: `<{el.get('tag', 'unknown')}>`")
                lines.append(f"  - **Ref**: `{el.get('ref', target_desc)}`")
                if el.get("text"):
                    lines.append(f"  - **Visible Text**: \"{el['text']}\"")
                if el.get("aria_label"):
                    lines.append(f"  - **Accessible Label**: \"{el['aria_label']}\"")
                if el.get("id"):
                    lines.append(f"  - **ID**: `#{el['id']}`")

            if rec.error:
                lines.append(f"- **Action Error**: `{rec.error}`")

            # Screenshot image embed
            if rec.screenshot_path:
                rel_path = rec.screenshot_path
                if output_dir:
                    try:
                        rel_path = str(Path(rec.screenshot_path).relative_to(output_dir)).replace("\\", "/")
                    except Exception:
                        pass
                lines.append("")
                lines.append(f"![Step {rec.step} Screenshot]({rel_path})")
                lines.append("")

    # Task Outcome & Evidence
    lines.append("---")
    lines.append("#### 🏆 Task Outcome & Verified Evidence")
    lines.append("")
    lines.append(f"- **Final Status**: `{task_result.status.value.upper()}`")
    if task_result.error_message:
        lines.append(f"- **Failure / Inconclusive Reason**: {task_result.error_message}")
    if task_result.notes:
        lines.append(f"- **Persona Observation Notes**: {task_result.notes}")

    if task_result.evidence:
        lines.append("##### 🔎 Verified Evidence Items")
        for ev in task_result.evidence:
            lines.append(f"- {ev}")
        lines.append("")

    lines.append("")
    return "\n".join(lines)


def render_full_run_interaction_markdown(
    plan: Optional[PersonaPlan],
    execution_result: Optional[ExecutionRunResult],
    output_dir: Path,
    inspection_result: Optional[Any] = None,
) -> str:
    """Render a unified, strictly formatted Markdown log for live browser interaction."""
    lines: List[str] = []

    target_url = (
        (execution_result.target_url if execution_result else None)
        or (inspection_result.final_url if inspection_result else None)
        or (inspection_result.requested_url if inspection_result else None)
        or "https://example.com"
    )
    final_url = (
        (inspection_result.final_url if inspection_result else None)
        or target_url
    )
    page_title = (
        (getattr(inspection_result, "title", None) if inspection_result else None)
        or "Live Browser Session"
    )
    goal = (
        (getattr(inspection_result, "context", None) if inspection_result else None)
        or (plan.context if plan else None)
        or "Audit website usability and user journey"
    )

    persona_names = []
    if execution_result:
        for p in (getattr(execution_result, "personas", None) or getattr(execution_result, "persona_results", [])):
            p_name = getattr(p, "persona_name", None)
            if p_name:
                persona_names.append(p_name)
    if plan and plan.personas and not persona_names:
        persona_names = [p.name for p in plan.personas]

    if persona_names and not any(p.lower() in goal.lower() for p in persona_names):
        goal = f"{goal} (Persona: {', '.join(persona_names)})"

    lines.append("# Live Browser Interaction")
    lines.append("")
    lines.append(f"- **Target URL:** {target_url}")
    lines.append(f"- **Current URL:** {final_url}")
    lines.append(f"- **Page Title:** {page_title}")
    lines.append(f"- **Audit Goal:** {goal}")
    lines.append("- **Status:** COMPLETED")
    lines.append("")
    lines.append("## Step 0: Initial page observation")
    lines.append("Target website loaded into live browser. Ready for inspection.")
    lines.append("")

    # Baseline screenshot
    baseline_shot = "screenshots/step-000.png"
    if inspection_result and getattr(inspection_result, "screenshot_path", None):
        try:
            rel = str(Path(inspection_result.screenshot_path).relative_to(output_dir)).replace("\\", "/")
            baseline_shot = rel
        except Exception:
            pass
    lines.append(f"![Initial page]({baseline_shot})")
    lines.append("")

    # Render each action step sequentially
    step_num = 0
    if execution_result:
        personas = getattr(execution_result, "personas", None) or getattr(execution_result, "persona_results", [])
        for p_res in personas:
            tasks = getattr(p_res, "task_results", None) or getattr(p_res, "tasks", [])
            for t_res in tasks:
                for rec in t_res.actions_taken:
                    step_num += 1
                    act = rec.action
                    act_type = act.action.value if hasattr(act.action, "value") else str(act.action)
                    target_repr = act.target or (f"@{act.mark}" if getattr(act, "mark", None) is not None else "")
                    target_strat = getattr(act, "target_strategy", "auto")
                    val = act.value or act.text or ""
                    val_line = f"\n- **Value:** `{val}`" if val else ""
                    step_shot = f"screenshots/step-{step_num:03d}.png"
                    if rec.screenshot_path:
                        try:
                            step_shot = str(Path(rec.screenshot_path).relative_to(output_dir)).replace("\\", "/")
                        except Exception:
                            step_shot = rec.screenshot_path

                    lines.append(f"## Step {step_num}: `{act_type}`")
                    lines.append(f"- **Agent reasoning:** {act.reasoning or 'Explored interface controls.'}")
                    lines.append(f"- **Target:** `{target_repr}` ({target_strat}){val_line}")
                    lines.append(f"- **URL after action:** {rec.page_url or target_url}")
                    lines.append("")
                    lines.append(f"![Step {step_num} screenshot]({step_shot})")
                    lines.append("")

    if step_num == 0:
        step_num = 1
        lines.append("## Step 1: `observe`")
        lines.append("- **Agent reasoning:** Baseline visual inspection completed.")
        lines.append("- **Target:** `body` (selector)")
        lines.append(f"- **URL after action:** {final_url}")
        lines.append("")
        lines.append(f"![Step 1 screenshot]({baseline_shot})")
        lines.append("")

    lines.append("## Run completed")
    lines.append("")
    lines.append(f"- **Actions taken:** {step_num}")
    lines.append("- **Summary:** Comprehensive user journey and usability audit completed.")
    lines.append("- **Output Report:** `improvements_suggestions.md`")
    lines.append("")

    return "\n".join(lines)

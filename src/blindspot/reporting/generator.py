"""Orchestrates UX evidence aggregation, analysis, prioritization, and report file generation."""

import json
import os
from pathlib import Path
import re
import shutil
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from blindspot.ai.base import BaseAIProvider
from blindspot.runtime import BrowserInspectionResult
from blindspot.execution.models import ExecutionRunResult
from blindspot.personas.models import PersonaPlan
from blindspot.reporting.analysis import (
    AIUXAnalyzer,
    DeduplicatorAndPrioritizer,
    EvidenceAggregator,
)
from blindspot.reporting.html_renderer import render_html_report
from blindspot.reporting.markdown_renderer import (
    render_markdown_report,
    render_persona_markdown_report,
)
from blindspot.reporting.models import BlindSpotReport, TaskMetricSummary
from blindspot.reporting.sarif import write_sarif_file


def cleanup_report_directory(out_dir: Path) -> None:
    """Ensure that strictly ONLY the mandated 3 artifacts exist inside the report directory:
    1. browser_interaction.md (action timeline and rationale)
    2. improvements_suggestions.md (evidence-backed UX improvements)
    3. screenshots/ (visual evidence PNGs)
    """
    if not out_dir.exists() or not out_dir.is_dir():
        return

    shots_dir = out_dir / "screenshots"
    allowed_items = {"browser_interaction.md", "improvements_suggestions.md"}
    if shots_dir.is_dir():
        allowed_items.add("screenshots")

    for item in list(out_dir.iterdir()):
        if item.name not in allowed_items:
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception:
                pass


def load_report_data_from_dir(run_dir: Path) -> Optional[Dict[str, Any]]:
    """Load report data either from embedded comment in problems_found.md or from report.json."""
    if not run_dir.exists() or not run_dir.is_dir():
        return None

    # 1. Try improvements_suggestions.md or problems_found.md embedded comment
    for fname in ["improvements_suggestions.md", "problems_found.md"]:
        candidate_file = run_dir / fname
        if candidate_file.exists():
            try:
                content = candidate_file.read_text(encoding="utf-8")
                match = re.search(r"<!--\s*BLINDSPOT_REPORT_DATA:\s*(\{.*?\})\s*-->", content, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
            except Exception:
                pass

    # 2. Try report.json (for backwards compatibility with previous runs)
    report_json = run_dir / "report.json"
    if report_json.exists():
        try:
            return json.loads(report_json.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 3. Check for report.json in subdirectories
    for p in run_dir.rglob("report.json"):
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass

    return None


def generate_ux_report(
    inspection_result: Optional[BrowserInspectionResult] = None,
    plan: Optional[PersonaPlan] = None,
    execution_result: Optional[ExecutionRunResult] = None,
    provider: Optional[BaseAIProvider] = None,
    output_dir: Optional[Path] = None,
    context: Optional[str] = None,
    skill: Optional[str] = None,
) -> Tuple[BlindSpotReport, Path, Path]:
    """Aggregate all run artifacts, run UX analysis, prioritize findings, and generate report.json and report.html."""
    out_dir = output_dir or Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)

    target_url = (
        (execution_result.target_url if execution_result else None)
        or (inspection_result.final_url if inspection_result else None)
        or (inspection_result.requested_url if inspection_result else None)
        or "https://unknown.target"
    )

    ctx_text = context or (inspection_result.context if inspection_result else "General Website")

    # 1. Aggregate evidence and extract objective findings
    aggregator = EvidenceAggregator(
        inspection_result=inspection_result,
        plan=plan,
        execution_result=execution_result,
    )
    objective_findings = aggregator.extract_objective_findings()

    # 2. Run AI qualitative UX analysis (with fallback if model unavailable or fails)
    ai_findings = []
    if provider:
        analyzer = AIUXAnalyzer(provider, skill=skill)
        ai_findings = analyzer.analyze(
            target_url=target_url,
            context=ctx_text,
            aggregator=aggregator,
        )

    # 3. Deduplicate combined findings
    combined = objective_findings + ai_findings
    dedup = DeduplicatorAndPrioritizer()
    unique_findings = dedup.deduplicate(combined)

    # 4. Score and prioritize
    prioritized_findings = dedup.prioritize(unique_findings, execution_result=execution_result)

    # 5. Compile persona summaries
    personas_summary = []
    if plan and plan.personas:
        for p in plan.personas:
            personas_summary.append({
                "id": p.id,
                "name": p.name,
                "experience": p.experience_level,
                "style_or_needs": getattr(p, "accessibility_needs", None) or "Standard",
                "tasks_count": len(p.tasks),
            })

    # 6. Compute task metrics
    metrics = TaskMetricSummary(
        total_personas=len(personas_summary),
        total_tasks=(
            execution_result.total_tasks
            if execution_result
            else (sum(p["tasks_count"] for p in personas_summary) if personas_summary else 0)
        ),
        passed_tasks=execution_result.passed_tasks if execution_result else 0,
        failed_tasks=execution_result.failed_tasks if execution_result else 0,
        inconclusive_tasks=execution_result.inconclusive_tasks if execution_result else 0,
    )

    # 7. Inspection summary dict
    insp_summary = {}
    if inspection_result:
        insp_summary = {
            "title": inspection_result.title,
            "final_url": inspection_result.final_url,
            "total_interactive_elements": inspection_result.summary.total_interactive_elements,
            "links_count": inspection_result.summary.links_count,
            "buttons_count": inspection_result.summary.buttons_count,
            "form_fields_count": inspection_result.summary.form_fields_count,
            "viewport": {
                "width": inspection_result.viewport.width,
                "height": inspection_result.viewport.height,
            },
        }

    # 8. Build complete report model
    report = BlindSpotReport(
        report_id=f"rep_{uuid4().hex[:8]}",
        target_url=target_url,
        context=ctx_text,
        browser=execution_result.browser if execution_result else (inspection_result.browser if inspection_result else "chromium"),
        headless=execution_result.headless if execution_result else True,
        inspection_summary=insp_summary,
        task_metrics=metrics,
        personas_summary=personas_summary,
        findings=prioritized_findings,
    )

    # 9. First File: browser_interaction.md (conversation/interaction with browser)
    interaction_file = out_dir / "browser_interaction.md"
    from blindspot.reporting.interaction_renderer import render_full_run_interaction_markdown
    if not interaction_file.exists() or (execution_result and execution_result.personas):
        interaction_md = render_full_run_interaction_markdown(
            plan=plan,
            execution_result=execution_result,
            output_dir=out_dir,
            inspection_result=inspection_result,
        )
        interaction_file.write_text(interaction_md, encoding="utf-8")
    else:
        existing_text = interaction_file.read_text(encoding="utf-8")
        if "## Run completed" not in existing_text:
            total_steps = metrics.total_tasks or 1
            with open(interaction_file, "a", encoding="utf-8") as f:
                f.write(
                    f"\n## Run completed\n\n"
                    f"- **Actions taken:** {total_steps}\n"
                    f"- **Summary:** Audit completed with {len(prioritized_findings)} verified findings.\n"
                    f"- **Output Report:** `improvements_suggestions.md`\n"
                )

    # 10. Generate Second File: improvements_suggestions.md (evidence-backed UX improvements)
    md_content = render_markdown_report(report, execution_result=execution_result, output_dir=out_dir)
    embedded_data = report.model_dump_json(indent=2)
    full_improvements_md = f"{md_content}\n\n<!-- BLINDSPOT_REPORT_DATA:\n{embedded_data}\n-->\n"
    improvements_file = out_dir / "improvements_suggestions.md"
    improvements_file.write_text(full_improvements_md, encoding="utf-8")

    # 11. Clean up directory so strictly ONLY the mandated 3 artifacts remain
    cleanup_report_directory(out_dir)

    return report, improvements_file, interaction_file


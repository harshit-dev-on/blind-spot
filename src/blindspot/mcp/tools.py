"""Tool business logic implementations for the BlindSpot Model Context Protocol (MCP) server."""

import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from blindspot.core.validation import validate_context, validate_url
from blindspot.execution.safety import validate_navigation_url
from blindspot.mcp.comparison import compare_test_runs
from blindspot.web.manager import RUN_ID_REGEX, job_manager
from blindspot.web.models import CreateRunRequest


def _resolve_run_dir(run_id: str) -> Path:
    candidates = [
        job_manager.reports_root / run_id,
        Path.cwd() / "blindspot_reports" / run_id,
        Path.cwd() / "reports" / run_id,
    ]
    if "BLINDSPOT_REPORTS_DIR" in os.environ:
        candidates.insert(0, Path(os.environ["BLINDSPOT_REPORTS_DIR"]) / run_id)
    for c in candidates:
        if c.exists() and c.is_dir():
            return c.resolve()
    return (job_manager.reports_root / run_id).resolve()


def tool_inspect_website(
    url: str,
    context: str,
    personas: int = 1,
    persona: Optional[str] = None,
    headed: bool = True,
    wait_for_completion: bool = False,
    timeout_seconds: int = 180,
    output_dir: Optional[str] = None,
    iteration: Optional[str] = None,
    skill: Optional[str] = None,
) -> Dict[str, Any]:
    """Start an automated BlindSpot website UX inspection and testing run.

    Args:
        url: Target website URL to inspect and test (e.g. 'https://example.com').
        context: Contextual description of the website purpose, capabilities, and target audience.
        personas: Number of synthetic personas to generate and test (1 to 5, default 1).
        persona: Optional specific persona name or archetype (e.g. 'ecommerce', 'mobile', 'accessibility').
        headed: Whether to display a visible browser window on the host desktop.
        wait_for_completion: If True, blocks until the run finishes or timeout is reached.
        timeout_seconds: Maximum seconds to wait when wait_for_completion is True.
        output_dir: Optional custom directory to store inspection artifacts.
        iteration: Optional iteration name or number (e.g. 'iteration_1').
        skill: Optional Agent Skill identifier or alias to activate (e.g. 'wcag', 'ecommerce', 'mobile').

    Returns:
        Structured dictionary containing run_id, status, target_url, output_dir, and instructions.
    """
    # 1. URL syntax validation
    url_res = validate_url(url)
    if not url_res.is_valid:
        return {
            "error": "INVALID_URL",
            "message": url_res.error_message,
            "suggestion": url_res.suggestion,
        }

    # 2. SSRF, Localhost, and Private Network Defense
    is_safe, ssrf_reason = validate_navigation_url(url)
    if not is_safe:
        return {
            "error": "SECURITY_BLOCKED",
            "message": f"Navigation to target blocked: {ssrf_reason}",
            "suggestion": "Target URL must be a publicly routable HTTP or HTTPS endpoint.",
        }

    # 3. Context validation
    ctx_res, resolved_ctx = validate_context(context)
    if not ctx_res.is_valid:
        return {
            "error": "INVALID_CONTEXT",
            "message": ctx_res.error_message,
            "suggestion": ctx_res.suggestion,
        }

    clamped_personas = max(1, min(5, personas))

    # Optional Agent Skill activation
    effective_ctx = resolved_ctx
    active_skill_name = None
    if skill:
        from blindspot.skills.activator import SkillActivator, SkillInjectionMode
        from blindspot.skills.registry import SkillRegistry

        reg = SkillRegistry()
        act_skill = reg.get_skill(skill)
        if act_skill:
            active_skill_name = act_skill.name
            effective_ctx = SkillActivator(reg).format_for_injection(
                act_skill, mode=SkillInjectionMode.USER_MESSAGE, user_request=resolved_ctx
            )

    # 4. Create and start background run
    req = CreateRunRequest(
        url=url.strip(),
        context=effective_ctx,
        personas=clamped_personas,
        persona=persona,
        headed=headed,
        browser="chromium",
        output_dir=output_dir,
        iteration=iteration,
        skill=active_skill_name,
    )

    record = job_manager.create_run(req)
    job_manager.start_run_background(record.run_id)

    # 5. Optional wait
    if wait_for_completion:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            rec = job_manager.get_run(record.run_id)
            if rec and rec.status in ("completed", "failed", "cancelled"):
                break
            time.sleep(1.0)

    current_rec = job_manager.get_run(record.run_id) or record
    output_dir_str = str(current_rec.output_dir)

    return {
        "run_id": current_rec.run_id,
        "status": current_rec.status,
        "target_url": current_rec.target_url,
        "output_dir": output_dir_str,
        "personas_count": clamped_personas,
        "instructions": (
            f"Test run '{current_rec.run_id}' is {current_rec.status}. "
            "Call 'get_test_status' with this run_id to check progress, "
            "and 'get_test_results' or 'get_findings' once complete."
        ),
    }


def tool_get_test_status(run_id: str) -> Dict[str, Any]:
    """Retrieve the real-time execution status and progress for a test run.

    Args:
        run_id: Unique test run identifier (e.g. 'run_20261016_123456_abcdef').

    Returns:
        Structured status dictionary including stage, progress message, task metrics, and errors.
    """
    if not RUN_ID_REGEX.match(run_id):
        return {
            "error": "INVALID_RUN_ID",
            "message": f"Malformed run_id format '{run_id}'. Must be alphanumeric.",
        }

    # In-memory active run
    rec = job_manager.get_run(run_id)
    if rec:
        report_file = (
            (rec.output_dir / "improvements_suggestions.md")
            if (rec.output_dir / "improvements_suggestions.md").exists()
            else (
                (rec.output_dir / "problems_found.md")
                if (rec.output_dir / "problems_found.md").exists()
                else (rec.output_dir / "report.json")
            )
        )
        has_report = report_file.exists()
        rep_path = str(report_file) if has_report else None
        return {
            "run_id": rec.run_id,
            "status": rec.status,
            "target_url": rec.target_url,
            "created_at": rec.created_at,
            "stage": rec.stage,
            "progress_message": rec.progress_message,
            "error_message": rec.error_message,
            "metrics": rec.metrics,
            "has_report": has_report,
            "report_path": rep_path,
        }

    # Historical completed run on disk
    run_dir = _resolve_run_dir(run_id)
    if run_dir.exists() and run_dir.is_dir():
        from blindspot.reporting.generator import load_report_data_from_dir
        try:
            data = load_report_data_from_dir(run_dir)
            if data:
                report_file = (
                    (run_dir / "improvements_suggestions.md")
                    if (run_dir / "improvements_suggestions.md").exists()
                    else (
                        (run_dir / "problems_found.md")
                        if (run_dir / "problems_found.md").exists()
                        else (run_dir / "report.json")
                    )
                )
                rep_path = str(report_file) if report_file.exists() else None
                return {
                    "run_id": run_id,
                    "status": "completed",
                    "target_url": data.get("target_url", "Unknown"),
                    "created_at": data.get("generated_at", run_id),
                    "stage": "reporting",
                    "progress_message": "Historical run completed successfully.",
                    "error_message": None,
                    "metrics": data.get("task_metrics", {}),
                    "has_report": True,
                    "report_path": rep_path,
                }
        except Exception as exc:
            return {
                "run_id": run_id,
                "status": "corrupted",
                "error_message": f"Failed reading report file: {exc}",
            }

        if (run_dir / "execution_results.json").exists():
            return {
                "run_id": run_id,
                "status": "running",
                "stage": "reporting",
                "progress_message": "Persona execution completed, generating final report.",
                "has_report": False,
            }
        elif (run_dir / "inspection_result.json").exists():
            return {
                "run_id": run_id,
                "status": "running",
                "stage": "execution",
                "progress_message": "Inspection complete, persona task execution active.",
                "has_report": False,
            }

    return {
        "error": "NOT_FOUND",
        "message": f"Test run '{run_id}' not found in active memory or reports directory.",
    }


def tool_get_test_results(run_id: str) -> Dict[str, Any]:
    """Retrieve a concise, evidence-backed summary of test outcomes and findings.

    Args:
        run_id: Unique test run identifier.

    Returns:
        Structured test results including task metrics, defect counts, and artifact paths.
    """
    if not RUN_ID_REGEX.match(run_id):
        return {
            "error": "INVALID_RUN_ID",
            "message": f"Malformed run_id format '{run_id}'.",
        }

    # Check if run is still in-progress
    rec = job_manager.get_run(run_id)
    if rec and rec.status in ("queued", "running"):
        return {
            "run_id": run_id,
            "status": rec.status,
            "message": f"Test run '{run_id}' is still in progress (stage: {rec.stage}). Call get_test_status to monitor.",
        }

    run_dir = _resolve_run_dir(run_id)
    from blindspot.reporting.generator import load_report_data_from_dir
    data = load_report_data_from_dir(run_dir)
    if not data:
        if rec and rec.status in ("failed", "cancelled"):
            return {
                "run_id": run_id,
                "status": rec.status,
                "error_message": rec.error_message,
                "message": f"Run ended with status '{rec.status}' without generating a final report.",
            }
        return {
            "error": "REPORT_NOT_READY",
            "message": f"Report for run '{run_id}' is not yet available or run does not exist.",
        }

    try:
        findings = data.get("findings", [])
        verified_count = sum(1 for f in findings if f.get("category") in ("OBJECTIVE_DEFECT", "verified_issue"))
        usability_count = sum(1 for f in findings if f.get("category") == "USABILITY_OBSERVATION")
        improvements_count = sum(1 for f in findings if f.get("category") == "POTENTIAL_IMPROVEMENT")

        interaction_path = run_dir / "browser_interaction.md"
        problems_path = (run_dir / "improvements_suggestions.md") if (run_dir / "improvements_suggestions.md").exists() else (run_dir / "problems_found.md")

        # Summarized top findings (title, severity, category, suggested improvement)
        top_findings_summary = [
            {
                "id": f.get("id"),
                "title": f.get("title"),
                "category": f.get("category"),
                "severity": f.get("severity"),
                "affected_url": f.get("affected_page_url"),
                "suggested_fix": f.get("suggested_improvement"),
            }
            for f in findings[:8]
        ]

        rep_json_path = str(run_dir / "report.json") if (run_dir / "report.json").exists() else (str(problems_path) if problems_path.exists() else None)
        rep_html_path = str(run_dir / "report.html") if (run_dir / "report.html").exists() else None

        return {
            "run_id": run_id,
            "status": "completed",
            "target_url": data.get("target_url"),
            "website_summary": data.get("context"),
            "task_metrics": data.get("task_metrics", {}),
            "summary_counts": {
                "total_findings": len(findings),
                "verified_defects": verified_count,
                "usability_observations": usability_count,
                "potential_improvements": improvements_count,
            },
            "report_paths": {
                "browser_interaction": str(interaction_path) if interaction_path.exists() else None,
                "problems_found": str(problems_path) if problems_path.exists() else None,
                "json_report": rep_json_path,
                "markdown_report": str(problems_path) if problems_path.exists() else (str(run_dir / "report.md") if (run_dir / "report.md").exists() else None),
                "html_report": rep_html_path,
            },
            "top_findings": top_findings_summary,
            "disclaimer": data.get("disclaimer"),
        }
    except Exception as exc:
        return {
            "error": "READ_ERROR",
            "message": f"Failed reading report file: {exc}",
        }


def tool_get_findings(
    run_id: str,
    severity: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve full, validated UX findings with reproduction steps and evidence.

    Args:
        run_id: Unique test run identifier.
        severity: Optional severity filter ('Critical', 'High', 'Medium', 'Low', 'Informational').
        category: Optional category filter ('verified_issue', 'usability_observation', 'potential_improvement').

    Returns:
        Structured list of matching findings with reproduction steps, evidence, and suggested fixes.
    """
    if not RUN_ID_REGEX.match(run_id):
        return {
            "error": "INVALID_RUN_ID",
            "message": f"Malformed run_id format '{run_id}'.",
        }

    run_dir = _resolve_run_dir(run_id)
    from blindspot.reporting.generator import load_report_data_from_dir
    data = load_report_data_from_dir(run_dir)
    if not data:
        return {
            "error": "REPORT_NOT_FOUND",
            "message": f"Report for run '{run_id}' not found.",
        }

    try:

        raw_findings: List[Dict[str, Any]] = data.get("findings", [])
        matched = []

        norm_sev = severity.lower().strip() if severity else None
        norm_cat = category.lower().strip() if category else None

        for f in raw_findings:
            f_sev = str(f.get("severity", "")).lower().strip()
            f_cat = str(f.get("category", "")).lower().strip()

            if norm_sev and norm_sev not in f_sev:
                continue
            if norm_cat and norm_cat not in f_cat:
                continue

            matched.append({
                "id": f.get("id"),
                "title": f.get("title"),
                "category": f.get("category"),
                "severity": f.get("severity"),
                "confidence": f.get("confidence"),
                "affected_page_url": f.get("affected_page_url"),
                "supporting_evidence": f.get("supporting_evidence", []),
                "reproduction_steps": f.get("reproduction_steps", []),
                "suggested_improvement": f.get("suggested_improvement"),
                "expected_benefit": f.get("expected_benefit"),
                "priority_rank": f.get("priority_rank"),
                "priority_reasoning": f.get("priority_reasoning"),
            })

        return {
            "run_id": run_id,
            "target_url": data.get("target_url"),
            "filter_applied": {
                "severity": severity,
                "category": category,
            },
            "findings_count": len(matched),
            "findings": matched,
        }
    except Exception as exc:
        return {
            "error": "PARSE_ERROR",
            "message": f"Failed reading findings: {exc}",
        }


def tool_verify_fixes(
    url: Optional[str] = None,
    context: Optional[str] = None,
    run_id: Optional[str] = None,
    reference_run_id: Optional[str] = None,
    personas: int = 3,
) -> Dict[str, Any]:
    """Verify website bug fixes by comparing a new test run against a previous reference run.

    Usage Modes:
    1. Compare Two Completed Runs:
       Pass run_id (the new run) and reference_run_id (the baseline run).
       Returns immediate objective diff (Resolved, Recurring, New, Inconclusive).
    2. Start Re-Test & Verify:
       Pass url, context, and reference_run_id.
       Starts a new test run in the background and prepares for comparison.

    Args:
        url: Target website URL (required if starting a new test run).
        context: Target website context description (required if starting a new test run).
        run_id: Existing completed re-test run ID (if comparing already completed runs).
        reference_run_id: Previous baseline run ID containing known issues to verify.
        personas: Number of personas to simulate for new re-test run.

    Returns:
        Structured verification results or verification re-test run initiation details.
    """
    # Mode 1: Direct comparison between two completed runs
    if run_id and reference_run_id:
        if not RUN_ID_REGEX.match(run_id) or not RUN_ID_REGEX.match(reference_run_id):
            return {"error": "INVALID_RUN_ID", "message": "Malformed run ID format."}

        cur_dir = _resolve_run_dir(run_id)
        ref_dir = _resolve_run_dir(reference_run_id)
        from blindspot.reporting.generator import load_report_data_from_dir
        cur_data = load_report_data_from_dir(cur_dir)
        ref_data = load_report_data_from_dir(ref_dir)

        if not cur_data:
            return {"error": "CURRENT_REPORT_NOT_FOUND", "message": f"Report for '{run_id}' not found."}
        if not ref_data:
            return {"error": "REFERENCE_REPORT_NOT_FOUND", "message": f"Report for reference '{reference_run_id}' not found."}

        diff_results = compare_test_runs(current_report=cur_data, reference_report=ref_data)
        return {
            "mode": "comparison",
            "current_run_id": run_id,
            "reference_run_id": reference_run_id,
            "target_url": cur_data.get("target_url"),
            "verdict": diff_results["verdict"],
            "summary": diff_results["summary"],
            "resolved_issues": diff_results["resolved"],
            "recurring_issues": diff_results["recurring"],
            "new_issues": diff_results["new"],
            "inconclusive_issues": diff_results["inconclusive"],
        }

    # Mode 2: Start new verification run referencing previous baseline
    if url and context and reference_run_id:
        if not RUN_ID_REGEX.match(reference_run_id):
            return {"error": "INVALID_RUN_ID", "message": f"Malformed reference_run_id '{reference_run_id}'."}

        ref_dir = _resolve_run_dir(reference_run_id)
        from blindspot.reporting.generator import load_report_data_from_dir
        ref_data = load_report_data_from_dir(ref_dir)
        if not ref_data:
            return {
                "error": "REFERENCE_REPORT_NOT_FOUND",
                "message": f"Baseline report for reference '{reference_run_id}' not found. Cannot compare fixes.",
            }

        # Start new test run
        init_res = tool_inspect_website(
            url=url,
            context=context,
            personas=personas,
            headed=False,
            wait_for_completion=False,
        )

        if "error" in init_res:
            return init_res

        new_run_id = init_res["run_id"]
        return {
            "mode": "verification_retest_started",
            "new_run_id": new_run_id,
            "reference_run_id": reference_run_id,
            "target_url": url,
            "status": "queued",
            "instructions": (
                f"New verification run '{new_run_id}' started in the background against reference '{reference_run_id}'. "
                "1. Monitor progress using 'get_test_status(run_id)'. "
                f"2. When complete, call 'verify_fixes(run_id=\"{new_run_id}\", reference_run_id=\"{reference_run_id}\")' "
                "to generate the comparative verification diff."
            ),
        }

    return {
        "error": "MISSING_ARGUMENTS",
        "message": (
            "Provide either: (1) 'run_id' and 'reference_run_id' to compare two completed runs, or "
            "(2) 'url', 'context', and 'reference_run_id' to start a new verification run."
        ),
    }


def tool_list_skills() -> Dict[str, Any]:
    """List all discoverable Agent Skills with Tier 1 metadata summaries."""
    from blindspot.skills.registry import SkillRegistry

    reg = SkillRegistry()
    summaries = reg.list_summaries()
    return {
        "skills_count": len(summaries),
        "skills": [
            {
                "name": s.name,
                "description": s.description,
                "version": s.version,
                "keywords": sorted(list(s.keywords))[:10],
            }
            for s in summaries
        ],
    }


def tool_get_skill(name: str) -> Dict[str, Any]:
    """Retrieve full Tier 2 instructions and rules for a specified skill."""
    from blindspot.skills.registry import SkillRegistry

    reg = SkillRegistry()
    skill = reg.get_skill(name)
    if not skill:
        return {
            "error": "SKILL_NOT_FOUND",
            "message": f"No Agent Skill found matching '{name}'.",
            "available_skills": [s.name for s in reg.list_summaries()],
        }

    return {
        "name": skill.name,
        "description": skill.description,
        "version": skill.version,
        "author": skill.author,
        "allowed_tools": skill.allowed_tools,
        "skill_path": str(skill.skill_path) if skill.skill_path else None,
        "body": skill.body,
    }

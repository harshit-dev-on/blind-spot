# Graph Report - blind-spot  (2026-10-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1722 nodes · 4214 edges · 72 communities (58 shown, 14 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 615 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d90a4164`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 71

## God Nodes (most connected - your core abstractions)
1. `BaseAIProvider` - 75 edges
2. `AntigravityProvider` - 52 edges
3. `PersonaTaskAgent` - 51 edges
4. `PersonaTask` - 49 edges
5. `Persona` - 41 edges
6. `PersonaPlan` - 40 edges
7. `inspect()` - 40 edges
8. `SkillRegistry` - 39 edges
9. `AgentAction` - 39 edges
10. `ExecutionRunResult` - 37 edges

## Surprising Connections (you probably didn't know these)
- `test_openai_compatible_fallback_for_response_format()` --uses--> `OpenAICompatibleProvider`  [INFERRED]
  tests/test_ai_provider.py → src/blindspot/ai/providers/openai_compatible.py
- `test_openai_compatible_generate_success()` --uses--> `OpenAICompatibleProvider`  [INFERRED]
  tests/test_ai_provider.py → src/blindspot/ai/providers/openai_compatible.py
- `test_openai_compatible_generate_with_image()` --uses--> `OpenAICompatibleProvider`  [INFERRED]
  tests/test_ai_provider.py → src/blindspot/ai/providers/openai_compatible.py
- `test_openai_compatible_health_check_401()` --uses--> `OpenAICompatibleProvider`  [INFERRED]
  tests/test_ai_provider.py → src/blindspot/ai/providers/openai_compatible.py
- `test_openai_compatible_reads_env_key()` --uses--> `OpenAICompatibleProvider`  [INFERRED]
  tests/test_ai_provider.py → src/blindspot/ai/providers/openai_compatible.py

## Import Cycles
- None detected.

## Communities (72 total, 14 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (19): build_agent_step_prompt(), build_agent_system_prompt(), build_vision_step_prompt(), BrowserUsePersonaRunner, BrowserUseTaskAgent, build_persona_system_extension(), is_browser_use_available(), ActionExecutionRecord (+11 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (20): AccessibilityBarrierRecord, BaseTool, BrowserActionTool, JourneyTodoItem, JourneyTodoTool, PersonaThoughtRecord, RecordAccessibilityBarrierTool, RecordUXFrictionTool (+12 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (20): list_skills_cmd(), main_entry(), setup_command(), run_mcp_server(), CleanPanel, print_ai_prompt_result(), print_browser_inspection_summary(), print_execution_summary() (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (13): AuthPromptType, _clear_browser_banner(), extract_input_field_label(), prompt_user_credential(), MilestoneStatus, MilestoneStep, TaskTracker, test_agent_detect_active_auth_barrier() (+5 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (17): BaseAIProvider, resolve_browser_use_llm(), build_user_prompt(), deduplicate_and_normalize_ids(), generate_personas_and_tasks(), load_personas_from_markdown(), PersonaGenerator, sanitize_and_condense_website_content() (+9 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (25): AntigravityProvider, ActionType, AgentAction, PersonaPlanPayload, PersonaTask, test_antigravity_provider_direct(), test_active_tab_is_not_keyboard_tab_task(), test_auth_barrier_requests_prompt_user() (+17 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (13): CoverageTracker, RunSession, ScanMode, TokenBudget, get_playbooks_for_persona(), list_available_playbooks(), load_playbook(), test_get_playbooks_for_persona() (+5 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (15): create_persona_agent(), create_test_runner(), execute_persona_tasks(), PersonaTestRunner, _safe_emit(), PersonaPlan, bring_browser_window_to_foreground(), unpin_browser_window() (+7 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (33): extract_json_string(), create_provider(), OllamaProvider, SamplePersona, SampleUXTask, test_antigravity_markdown_persona_parsing(), test_extract_json_string_clean(), test_extract_json_string_fenced() (+25 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (15): find_config_file(), get_user_config_path(), load_config(), load_config_file(), parse_model_route(), persist_current(), save_config(), AIConfig (+7 more)

### Community 10 - "Community 10"
Cohesion: 0.09
Nodes (7): PersonaTaskAgent, detect_auth_input_type(), _execute_single_persona(), test_agent_fill_via_element_ref(), test_overlay_renders_extracted_dom_elements_and_html(), test_top_status_navbar_and_page_offset(), test_task_agent_malformed_model_action_fails_gracefully()

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (21): test_cli_help(), test_cli_version(), test_inspect_custom_output_dir(), test_inspect_executes_and_saves_execution_results(), test_inspect_generates_personas_and_plan_file(), test_inspect_headed_flag(), test_inspect_help(), test_inspect_invalid_browser() (+13 more)

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (17): inspect(), install_skills_cmd(), live_cmd(), match_skill_cmd(), mcp_cmd(), model_list_command(), provider_list(), provider_prompt() (+9 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (12): find_specific_persona_file(), get_bundled_personas_dir(), rank_persona_files(), test_setup_wizard_local_scripted(), test_antigravity_single_persona_generation(), test_cli_persona_options_help(), test_find_specific_persona_file_aliases(), test_load_personas_defaults_to_single_persona() (+4 more)

### Community 14 - "Community 14"
Cohesion: 0.07
Nodes (16): test_build_agent_system_prompt_with_skill(), test_build_analysis_system_prompt_with_skill(), test_bundled_skills_exist(), test_cli_skill_install(), test_cli_skill_list(), test_cli_skill_show_and_match(), test_cli_skill_validate(), test_cli_skill_validate_invalid_path() (+8 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (7): main(), version_callback(), validate_environment(), show_interactive_start_screen(), StartScreenResult, test_interface_exports_and_cli(), test_start_screen_result_unpacking_and_attrs()

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (12): invoke(), main(), tool_inspect_website(), mcp_env(), test_get_test_results_completed_run(), test_get_test_status_active_and_historical(), test_inspect_website_invalid_context(), test_inspect_website_invalid_url() (+4 more)

### Community 17 - "Community 17"
Cohesion: 0.12
Nodes (10): get_models_for_provider(), AIAuthenticationError, AIConnectionError, AIModelNotFoundError, AIProviderError, AIStructuredOutputError, AITimeoutError, get_models_for_provider() (+2 more)

### Community 19 - "Community 19"
Cohesion: 0.07
Nodes (12): client(), test_api_does_not_expose_secrets(), test_cancel_run(), test_create_run_invalid_context_rejected(), test_create_run_invalid_url_rejected(), test_create_run_ssrf_blocked(), test_create_run_valid_payload(), test_get_completed_results() (+4 more)

### Community 20 - "Community 20"
Cohesion: 0.14
Nodes (9): get_bundled_skills_dir(), install_skills_to_workspace(), list_bundled_skills(), parse_skill_file(), SkillMetadata, SkillValidationResult, validate_skill(), SkillSummary (+1 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (11): _resolve_run_dir(), tool_get_findings(), tool_get_test_results(), tool_get_test_status(), tool_list_skills(), tool_verify_fixes(), load_report_data_from_dir(), CreateRunRequest (+3 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (7): UnifiedAIAdapter, AIResponse, ProviderStatus, test_agents_exports_and_factory(), check_health(), generate(), test_run_live_bridge_autonomous_execution()

### Community 23 - "Community 23"
Cohesion: 0.12
Nodes (6): ExecutionRunResult, DeduplicatorAndPrioritizer, cleanup_report_directory(), generate_ux_report(), render_full_run_interaction_markdown(), test_prioritizer_assigns_correct_ranks_and_reasoning()

### Community 24 - "Community 24"
Cohesion: 0.10
Nodes (6): create_app(), get_run_events(), get_run_results(), get_run_status(), list_test_runs(), serve_report_file()

### Community 25 - "Community 25"
Cohesion: 0.11
Nodes (4): tool_get_skill(), build_system_prompt(), build_analysis_system_prompt(), SkillRegistry

### Community 26 - "Community 26"
Cohesion: 0.09
Nodes (8): build_analysis_prompt(), EvidenceAggregator, _mock_gen(), sample_plan(), test_ai_analyzer_graceful_fallback_on_model_failure(), test_deduplicator_merges_duplicate_findings(), test_evidence_aggregator_extracts_verified_issues(), test_evidence_aggregator_handles_sparse_or_none_evidence()

### Community 27 - "Community 27"
Cohesion: 0.15
Nodes (9): BoundingBox, BrowserInspectionResult, InspectionSummary, InteractiveElement, ViewportSize, test_runtime_exports_and_models(), test_dynamic_persona_generation_inherits_user_context(), mock_inspection_result() (+1 more)

### Community 28 - "Community 28"
Cohesion: 0.19
Nodes (23): appendLogEntry(), checkIframeFraming(), checkRunStatusFallback(), cleanupStreaming(), closeUxOverlay(), connectEventSource(), escapeHtml(), formatCategoryLabel() (+15 more)

### Community 30 - "Community 30"
Cohesion: 0.15
Nodes (5): InspectConfig, ValidationResult, generate_run_id(), get_next_run_id(), PipelineResult

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (4): mask_api_key(), strip_thinking_tags(), test_mask_api_key(), test_strip_thinking_tags()

### Community 32 - "Community 32"
Cohesion: 0.11
Nodes (10): validate_navigation_url(), on_frame_navigated(), _page_observation(), run_live_bridge(), on_frame_navigated(), _synthesize_autonomous_report(), test_safety_url_validation_blocked_private_and_metadata(), test_safety_url_validation_blocked_schemes() (+2 more)

### Community 33 - "Community 33"
Cohesion: 0.12
Nodes (5): FindingCategory, SeverityLevel, test_strict_improvements_suggestions_template(), local_sample_site_url(), test_end_to_end_pipeline_offline_smoke()

### Community 34 - "Community 34"
Cohesion: 0.15
Nodes (8): _category_badge_class(), _esc(), render_finding_card(), render_html_report(), _severity_badge_class(), BlindSpotReport, test_html_report_escaping_and_safety(), test_html_report_handles_missing_screenshots()

### Community 35 - "Community 35"
Cohesion: 0.15
Nodes (7): get_installed_shims(), get_known_shim_locations(), perform_uninstall(), remove_config_directory(), remove_editable_pth_files(), remove_shims(), uninstall_pip_package()

### Community 36 - "Community 36"
Cohesion: 0.12
Nodes (3): _write_context(), test_locator_resolves_stamped_refs(), test_write_context_generates_markdown()

### Community 37 - "Community 37"
Cohesion: 0.16
Nodes (17): validate_context(), validate_url(), test_validate_context_empty(), test_validate_context_from_file(), test_validate_context_missing_file(), test_validate_context_too_short(), test_validate_context_valid(), test_validate_url_empty() (+9 more)

### Community 38 - "Community 38"
Cohesion: 0.15
Nodes (6): TaskMetricSummary, build_sarif_report(), write_sarif_file(), test_build_sarif_report_empty(), test_build_sarif_report_with_findings(), test_write_sarif_file()

### Community 39 - "Community 39"
Cohesion: 0.21
Nodes (3): _BrowserWorker, perform_browser_action(), resolve_locator()

### Community 40 - "Community 40"
Cohesion: 0.13
Nodes (3): RunManager, RunRecord, RunListItem

### Community 41 - "Community 41"
Cohesion: 0.14
Nodes (8): result_with_screenshot(), create_mcp_server(), live_browser_action(), live_browser_observe(), live_browser_open(), test_mcp_server_registers_live_browser_tools(), test_result_with_screenshot_returns_image_content(), test_mcp_server_tool_registration()

### Community 42 - "Community 42"
Cohesion: 0.16
Nodes (3): format_html(), PrettyHTMLFormatter, test_html_formatter_indents_nested_dom()

### Community 43 - "Community 43"
Cohesion: 0.15
Nodes (8): _category_icon(), _format_suggestion_category(), render_markdown_report(), render_persona_findings_markdown(), render_persona_journey_log_markdown(), render_persona_markdown_report(), render_persona_profile_markdown(), _severity_icon()

### Community 44 - "Community 44"
Cohesion: 0.19
Nodes (4): ensure_browser_engine(), run_live_scroll_test(), test_ensure_browser_engine_already_installed(), test_ensure_browser_engine_auto_installs_on_missing()

### Community 45 - "Community 45"
Cohesion: 0.16
Nodes (6): BrowserInspector, test_browser_inspection_with_local_html(), test_browser_inspector_custom_directory(), test_browser_inspector_default_run_directory(), test_browser_inspector_defaults(), test_browser_inspector_invalid_browser()

### Community 47 - "Community 47"
Cohesion: 0.16
Nodes (9): test_ai_config_defaults(), test_ai_config_empty_model(), test_ai_config_invalid_provider(), test_load_config_env_var_overrides(), test_load_config_missing_custom_file(), test_universal_llm_env_vars(), test_perform_action_blocks_destructive_actions(), test_perform_action_blocks_sensitive_phone_and_otp() (+1 more)

### Community 49 - "Community 49"
Cohesion: 0.17
Nodes (3): SkillActivator, SkillInjectionMode, test_skill_activator_injection_modes()

### Community 50 - "Community 50"
Cohesion: 0.18
Nodes (8): PipelineConfig, run_pipeline(), emit(), _step_callback(), worker(), cancel_check(), on_event(), test_runner_pipeline_browser_interaction_matches_template()

### Community 51 - "Community 51"
Cohesion: 0.20
Nodes (5): AIUXAnalyzer, AIFindingsOutput, UXFindingDraft, test_ai_analyzer_reclassifies_unverified_subjective_issues(), test_generate_ux_report_end_to_end()

### Community 52 - "Community 52"
Cohesion: 0.17
Nodes (4): ensure_default_desktop(), test_desktop_utils_skips_under_pytest(), test_window_utils_non_win32(), test_window_utils_safe_execution()

### Community 53 - "Community 53"
Cohesion: 0.19
Nodes (4): UXFinding, test_report_exports_and_models(), mock_inspect_ai(), _mock_analyze()

### Community 55 - "Community 55"
Cohesion: 0.22
Nodes (3): compare_test_runs(), _similarity(), test_verify_fixes_comparison_logic()

### Community 56 - "Community 56"
Cohesion: 0.22
Nodes (4): CancelResponse, RunStatusResponse, cancel_active_run(), create_and_start_run()

### Community 57 - "Community 57"
Cohesion: 0.22
Nodes (3): test_is_browser_use_available(), test_persona_test_runner_engine_selection(), test_resolve_browser_use_llm()

### Community 60 - "Community 60"
Cohesion: 0.25
Nodes (3): interactive_html_page(), test_agent_click_via_element_ref(), test_execution_loop_sends_current_screenshot()

### Community 61 - "Community 61"
Cohesion: 0.29
Nodes (3): _decide_autonomous_action(), test_decide_autonomous_action_anti_looping_dynamic_control(), test_decide_autonomous_action_flexible_visual_analysis()

### Community 63 - "Community 63"
Cohesion: 0.33
Nodes (3): is_action_destructive(), test_safety_destructive_actions(), test_destructive_action_guard_allows_demo_and_local_orders()

### Community 64 - "Community 64"
Cohesion: 0.60
Nodes (4): add_path(), PATH, run_step(), install.sh script

### Community 65 - "Community 65"
Cohesion: 0.83
Nodes (3): clean_profile(), remove_managed_dir(), uninstall.sh script

## Knowledge Gaps
- **2 isolated node(s):** `PATH`, `blindspot1`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 742 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BaseAIProvider` connect `Community 4` to `Community 0`, `Community 33`, `Community 5`, `Community 7`, `Community 8`, `Community 10`, `Community 48`, `Community 17`, `Community 18`, `Community 50`, `Community 51`, `Community 22`, `Community 23`, `Community 26`, `Community 60`, `Community 30`, `Community 31`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 36 inferred relationships involving `BaseAIProvider` (e.g. with `create_persona_agent()` and `create_test_runner()`) actually correct?**
  _`BaseAIProvider` has 36 INFERRED edges - model-reasoned connections that need verification._
- **What connects `PATH`, `blindspot1` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.055905220288781934 - nodes in this community are weakly interconnected._
- **Why does `SkillRegistry` connect `Community 25` to `Community 0`, `Community 2`, `Community 4`, `Community 12`, `Community 46`, `Community 14`, `Community 16`, `Community 49`, `Community 51`, `Community 20`, `Community 21`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `AntigravityProvider` (e.g. with `AIResponse` and `ProviderStatus`) actually correct?**
  _`AntigravityProvider` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.057539682539682536 - nodes in this community are weakly interconnected._
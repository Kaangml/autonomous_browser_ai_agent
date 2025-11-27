# agent.md — in-repo agent memory / plan

This file is the agent's on-disk memory and work-plan to implement Faz 2 features. Keep this short and actionable — it will be updated as I complete tasks.

## Current understanding (from `docs/faz1_2.md`)
- Faz 2 focuses on completing the Browser engine, Controller, Agent reasoning and config improvements.
- Browser (Playwright) needs robust actions: goto, click, type/fill, wait_for, extract_text, extract_all_links, screenshot, error handling/retries.
- Controller must convert agent action JSON into browser calls and provide safety checks (URL filters, loop detection, max steps).
- Agent needs multi-step reasoning (Plan → Execute → Reflect), tool-based reasoning, and self-correction.

## Priority (what I'll implement first)
1. Browser actions (Faz 2.1): make sure all core actions exist and are tested.
2. Unit tests for browser actions (pytest style) — file-level tests under `tests/browser`.
3. Controller small improvements / scaffolding (Faz 2.2) — map agent JSON to BrowserActions.
4. Agent reasoning upgrade (Faz 2.3) — design plan + unit tests for planning flow.

## First task breakdown (concrete)
- Add `extract_all_links(page)` to `src/browser/actions.py`.
- Add `screenshot(page)` to `src/browser/actions.py`.
- Add tests for both functions in `tests/browser/test_actions.py`.

After each file-level change:
- Add/update a unit test in `tests/browser/` (pytest async tests where needed).
- Run tests locally to ensure everything passes.

## Testing rules (my memory)
- Every implemented action must have a unit test that covers success and core happy path.
- Use small Dummy classes in tests for `Page`, `BrowserManager` to avoid needing an actual browser.
- Tests must be pytest compatible and located under `tests/browser`.

## Notes / constraints
- Keep changes small and incremental — test after each file.
- Use `BrowserUtils.retry` for network-sensitive operations.

## Next steps after tests
- Expand controller mapping using a lightweight JSON action format and tests.
- Then update agent logic to use multi-step reasoning and enable tools.

## Recent updates (done)

- Planner: `src/agent/planner.py` was added. The agent can now use an injected LLM planner (mockable) to create multi-step plans.
- Memory: improved in-memory workflow; tests added for planner and agent execution.
- Playwright configs: `BrowserConfig` now supports `channel`, and `human_delay_min/max` to add human-like timing jitter for automation to reduce bot detection.

## Faz 2 — status summary ✅

All Faz 2 goals are implemented and tested locally:

- Browser actions: goto, click, fill, wait_for, extract_text, extract_all_links, screenshot, and helper utilities (normalize_url, human_delay, retry).  
- Controller: `BrowserController` with execute_action/execute_sequence, safety checks (URL scheme filter, max steps, loop detection).  
- Agent: simple LLMPlanner interface and async planning pipeline; agent executes steps with injected planner + short-term memory skeleton.  
- Tests: comprehensive unit tests added across browser, controller and agent layers; e2e Playwright tests included (fixture based), with an optional headful test guarded by RUN_HEADFUL for local debugging.

Local test result (most recent run): 29 passed, 1 skipped.

Notes:
- Playwright headful tests can be flaky against public sites (Google blocks automated clients); use local fixtures or less-restrictive targets in CI.  
- Changes are committed locally in logical groups (agent, browser, controller, e2e, ci), but pushing to remote failed due to repository auth; you'll need to run `git push` with the correct credentials or switch accounts if you want me to push from here.

---

# Faz 3 — next phase (high level goals) 🔭

Faz 3 upgrades will move the project from a local POC into a more production-ready, resilient agent.

Planned work (concrete, test-driven)

1) Persistent/smart memory (short + long term) 💾
	- Add a persistent store (SQLite) for short-term memory and a pluggable vector DB adapter for longer-term semantic memory (optional: FAISS / Milvus / SQLite+annlite).  
	- Write migrations, test dataset fixtures, and unit tests for reads/writes and eviction policies.  
	- Optionally add minimal embedding + retrieval using a mock embedding provider to allow offline tests.

2) LLM planning contract and adapter 🧭
	- Implement a strict planner contract requiring structured JSON output (schema) with steps and tool names to reduce hallucinations.  
	- Add an LLM adapter interface to swap providers (mock tests for CI + sample provider configs).  
	- Add unit tests that assert the planner always returns a valid plan or a clear, recoverable error response.

3) Controller hardening & workflow engine 🔧
	- Add a persistent job queue + state machine for long-running workflows (states: pending, running, succeeded, failed, retrying).  
	- Implement retry/backoff policies (max attempts, exponential backoff) and durable input/output logs for observability.  
	- Add safe scheduling and re-entrancy guarantees (so controllers can resume from failure).  

4) Monitoring, instrumentation & CI ✅
	- Add metrics and structured logs for each step (execution time, step result, errors) and unit tests to verify logging of key events.  
	- Harden CI to include unit + e2e fixture tests, and avoid unreliable public-site headful tests in CI.

5) Release & collaboration tasks
	- Push local branch to remote (requires correct auth). If you'd like I can attempt the push again after you switch accounts or provide push access.  
	- Open a PR from the feature branch with Faz 2 changes and Faz 3 follow-up work split into smaller PRs.

If you'd like, I can start with the memory persistence work (SQLite + tests) next.


(Agent memory file — update this as steps complete.)

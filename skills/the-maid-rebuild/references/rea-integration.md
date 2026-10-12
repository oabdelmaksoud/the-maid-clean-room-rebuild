# REA integration: rendered observation, reviewed handoff

REA is an optional external discovery tool. The supported profile is pinned to `rea-agents@6.4.0`, published from [morluto/rea](https://github.com/morluto/rea). The Maid remains usable without REA. Use this profile when the user requests REA or it is connected and the permitted source set supports rendered UI observation.

## Install and connect explicitly

Use a supported Node.js runtime: 22.19+ in 22.x, 24.11+ in 24.x, or 26+. Review the upstream [version-matched setup documentation](https://github.com/morluto/rea/blob/a56f7bb668ab23fec8d33f7af353ac7ed2fe1895/docs/installation.md) before changing client registration. These commands target Codex only and omit upstream investigation instructions and native-analysis providers:

```sh
npx -y rea-agents@6.4.0 setup --client codex --skill=false --dry-run --json
npx -y rea-agents@6.4.0 setup --client codex --skill=false --yes --json
```

The second command changes configuration and requires existing user authorization. Review the proposed actions first. Preserve unrelated configuration and backups. Do not add `--install-hopper` or configure Ghidra/IDA as part of this screenshot profile.

Setup registers the broader REA server. Limit Codex's exposed tools using its MCP configuration:

```toml
[mcp_servers.rea]
command = "npx"
args = ["-y", "rea-agents@6.4.0", "mcp"]
startup_timeout_sec = 30
enabled_tools = ["list_browser_targets", "capture_web_screenshot", "compare_web_screenshots"]
```

Merge those fields into the existing REA stanza; do not replace the full configuration. Confirm the parsed registration with `codex mcp get rea --json`, then restart/reconnect Codex. A registration check is not a live connection test. A separate MCP initialize/ping/tools-list check can verify server availability without inspecting a target. Missing native-analysis providers do not prevent screenshot capture. Never print unrelated client credentials or include configuration backups in the repository.

This is a Codex client filter, not a sandbox around the server or CLI. Other clients and direct REA commands can expose broader capabilities. The Maid's source restrictions still apply.

## Capture only permitted rendered UI

Use an already authorized browser with a loopback CDP endpoint, or an isolated temporary browser for original synthetic fixtures. Do not enable remote debugging on a personal profile or expose a debugging port remotely without an explicit decision. Use a narrow origin allowlist and the exact target ID returned by discovery. Do not invent endpoints or widen an allowlist after rejection.

The supported MCP call is:

```json
{
  "cdp_endpoint": "http://127.0.0.1:9222",
  "target_id": "ID_FROM_SCOPED_DISCOVERY",
  "allowed_origins": ["https://example.com"]
}
```

Pass it to `capture_web_screenshot`. The corresponding CLI is:

```sh
npx -y rea-agents@6.4.0 list-browser-targets http://127.0.0.1:9222 --allowed-origins https://example.com --json
npx -y rea-agents@6.4.0 capture-web-screenshot http://127.0.0.1:9222 ID_FROM_SCOPED_DISCOVERY --allowed-origins https://example.com --json
```

The dedicated capture takes the visible viewport and returns PNG bytes plus metadata; it does not navigate or collect page source/network observations. The page may continue its ordinary activity. See the upstream [browser observation contract](https://github.com/morluto/rea/blob/a56f7bb668ab23fec8d33f7af353ac7ed2fe1895/docs/browser-observation.md). In this clean-room profile do not use `inspect-web-page`, `analyze-web-bundle`, script/source-map extraction, private network inspection, binary decompilation, or copied product assets. Do not treat installation as permission for those operations.

Keep target captures evaluator-only. Exclude account labels, prior personal tasks, credentials and unrelated material; use permitted synthetic state and privacy-preserving capture regions where necessary. Capture comparison still needs matched conditions and frozen baselines from the [visual guide](visual-and-journey.md). Review `compare_web_screenshots` arguments and behavior before using it; the evidence gate below accepts capture records only and does not certify comparison results.

## Evidence and handoff gate

The Maid's record is an independently authored wrapper, not an upstream REA export format. Save PNG bytes as a local file, retain the original REA response outside the author packet, and populate `rea-evidence.json` with actual capture metadata and reviewed observations. Never synthesize a real-tool result from a fixture.

Exact root fields:

- `format_version`: integer 1.
- `target`: `{id, version, origin, allowed_origins}`. IDs follow the core identifier rules. Origins are canonical HTTPS origins, or HTTP loopback origins for isolated local fixtures. No user information, path, query, fragment, whitespace or ambiguous delimiters; valid explicit ports are supported.
- `tool`: `{name: "rea", version: "6.4.0", operation: "capture_web_screenshot"}`. Other operations and unverified versions block this profile.
- `permission`: `{reviewer, observe, basis, scope, source_boundary: "rendered_ui_only"}`. `observe` is `allowed`, `denied`, or `unknown`; permission basis and scope are nonblank declarations, not an authorization granted by the tool.
- `captures`: nonempty records `{id, target_id, origin, artifact, width, height, disposition: "evaluator_only"}`. Artifact is a core `{path, sha256}` reference. Target, declared origin, PNG header dimensions and bounded file identity must agree.
- `observations`: records `{id, target_id, capture_ids, artifact, review}`. Review has `{reviewer, disposition, sanitized, basis}`; disposition is `approved_behavior`, `excluded`, or `unreviewed`. The hashed behavioral artifact is exactly `{format_version: 1, target_id, observation_id, kind: "sanitized_behavior", behavior: "nonblank reviewed behavioral statement"}`.
- `handoff`: `{approved, reviewer, observation_ids, files}`. Files must equal precisely the approved, sanitized behavioral artifacts selected by observation IDs. No raw captures, copied image assets, extra files, or capture digests under renamed paths may enter this handoff.

Run from the kit root:

```sh
python3 skills/the-maid-rebuild/scripts/rea.py PROJECT_DIR --json
```

Exit 0 means the recorded evidence/handoff checks passed, 1 means well-formed evidence is blocked, and 2 means invalid records, paths, hashes or invocation. It reads local records using bounded core file checks, without launching REA, contacting a target, or writing evidence. PNG checks cover headers and declared dimensions; they do not fully decode pixels. Review the tool's output limits and dispositions before a handoff.

The gate cannot authenticate permission or reviewer independence, prove REA captured a file, detect every sensitive statement, or establish completeness. Human review must assess content, source-use permission, observational accuracy and private information. Run the existing readiness, fidelity and acceptance gates separately where applicable. If REA is unavailable or the target cannot be captured within the permitted scope, use permitted browser/manual observations and retain the limitation; do not broaden source access to work around it.

## Reproduce the gate mechanics

```sh
python3 examples/rea-observation/run_trial.py --output ../rea-observation-trial
```

The example authors its own PNG and behavioral records. It expects source-inspection and raw-capture handoffs to be blocked, and reviewed sanitized behavior to pass. It does not execute REA or establish actual target fidelity. Live tool verification uses a separate original local fixture and stays outside the distributed source.

# Development harness validation

Validated 2026-11-08 against installed `codex-cli 0.167.0`.

- Initial inspection: no AGENTS.md; .codex/agents, .agents/skills and specs were empty.
- `codex --strict-config app-server --print-startup-config` passed with CODEX_HOME explicitly pointing to the installed user Codex directory. Returned appServerVersion 0.167.0. Sandbox emitted runtime-directory cleanup/PATH warnings; startup validation itself succeeded.
- All four TOML files parsed using Python 3.13 tomllib. Custom agent files use the current standalone name/description/developer_instructions format and inherit development models and permissions.
- Skill Creator quick_validate.py passed for all four .agents/skills directories.
- `codex debug prompt-input` returned valid JSON and discovered architect, implementer, reviewer and all four project skills. This read-only inspection needed approved execution outside the workspace sandbox because Codex runtime directory access was denied. No model request was made. The debug command does not accept --strict-config; strict startup validation was performed separately.
- Architect and reviewer subagents reviewed the proposed boundaries and limits. Corrections added provider storage settings, requirement-to-acceptance tables, a foundation schema/toolchain acceptance case and an explicit critique-attempt ceiling.
- No application code, database files, commits or pushes were created. No application tests or live provider capability tests were run; those are explicitly unchecked phase tasks.

## Generated file manifest

```text
AGENTS.md
.codex/config.toml
.codex/agents/architect.toml
.codex/agents/implementer.toml
.codex/agents/reviewer.toml
.agents/skills/spec-driven-development/SKILL.md
.agents/skills/langgraph-engineering/SKILL.md
.agents/skills/web-research-engineering/SKILL.md
.agents/skills/frontend-engineering/SKILL.md
specs/architecture.md
specs/harness-validation.md
specs/001-foundation/spec.md
specs/001-foundation/plan.md
specs/001-foundation/tasks.md
specs/002-web-research/spec.md
specs/002-web-research/plan.md
specs/002-web-research/tasks.md
specs/003-critic-loop/spec.md
specs/003-critic-loop/plan.md
specs/003-critic-loop/tasks.md
specs/004-research-ui/spec.md
specs/004-research-ui/plan.md
specs/004-research-ui/tasks.md
specs/005-evaluation/spec.md
specs/005-evaluation/plan.md
specs/005-evaluation/tasks.md
```

## Open implementation gates

Before phase 002 paid requests, verify exact model/account access, pricing, live-public-search request semantics and enforceable hosted internal-action limits. Unsupported action caps must block research configuration rather than silently weakening the policy. No live API compatibility or billing guarantees are claimed by this harness validation.

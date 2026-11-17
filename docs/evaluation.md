# Evaluation

Checked on 2026-11-17 with [NVIDIA SkillEvaluator](https://github.com/NVIDIA/SkillEvaluator) 0.9.0 (security scan by
SkillSpector 2.13.3, run directly because SkillEvaluator's own launch of it did not complete on this setup).

| Check | Result |
| --- | --- |
| Quality score | A, 93.5/100 (correctness 85, discoverability 95, reliability 100, efficiency 100); was B, 86.0 before the Purpose, Examples, Limitations and Troubleshooting sections |
| LLM rubric score (previous revision) | 85.5/100 |
| Tier 1 (schema, version, license, code risk, lint, unicode) | 11 of 12 checks passed, none failed; the 12th (security scan) is the SkillSpector run below |
| Tier 2 (duplicate context, previous revision) | passed, no duplicated content found |
| PII and secrets scans | passed |
| SkillSpector (with LLM review, previous revision) | risk score 37, MEDIUM, recommendation CAUTION; 3 findings confirmed (no declared permissions, broad trigger description, cross-session state), 1 disagreed (subprocess call) |

The confirmed SkillSpector findings are accepted: a memory skill persists notes across sessions by design, it reads and writes files in the project and, only when the user asks for it, reads local transcript stores and runs a local script. The `subprocess` finding was reviewed and rejected (it runs only fixed, read-only `git` commands with no shell).

The latest revision was re-checked with the keyless checks only (quality score, Tier 1 without the LLM rubric, and
SkillSpector without its LLM review, which reported the same findings as before); rows marked "previous revision" come
from the revision before it.

Not run yet: Tier 3, the live agent evaluation (with-skill vs. without-skill runs of a coding agent; it works with
rootless Podman through the Docker CLI, but needs paid model credit). The remaining quality notes are generic ones that
do not fit this skill: a long description that carries the trigger conditions, a `version` field that is set under
`metadata:` rather than at the top level (the Agent Skills spec has no top-level `version`), and `run_script()` examples,
which belong to another agent harness.

Reproduce:

```bash
uvx --python 3.13 --from 'skillevaluator[all]' skillevaluator quality-check ./skills/memory-1
```

## Project benchmark

See [benchmark.md](benchmark.md) for the full setup, results and limitations.

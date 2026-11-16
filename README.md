# memory-1

Long-term project memory for AI coding agents, as plain Markdown in your repo: a short status file (what we are doing,
what is next), one dated fact per file (decisions and why, reversals, preferences, incidents, gotchas), an index the
agent reads at session start, topic pages once memory grows, and an optional archive of condensed past sessions for the
detail notes leave out. It is an [Agent Skill](https://agentskills.io) (a `SKILL.md`,
templates and one export script), so it works in Claude Code, Codex, Cursor and any agent that can read files.

- **Plain Markdown, no service.** `grep` is the search engine. Notes are reviewable in PRs and follow the branch.
- **History is kept, not overwritten.** A changed decision gets a new note that `supersedes` the old one; the old note
  moves to a History section, so "what did we decide before, and what now?" both have answers.
- **Clear trust rules.** Code at HEAD wins for current behaviour; notes win for why, history and preferences; the
  newest current note wins between notes.
- **Portable transcripts.** `scripts/export_sessions.py` turns Claude Code and Codex sessions into small, redacted
  Markdown digests, so the archive works the same whichever agent you used.

## The files

```
memory/
  NOW.md                 status: doing, done recently, next (user's next step first), open questions; rewritten, max 50 lines
  LATER.md               open items for the user and a few follow-up suggestions; not read at session start
  MEMORY.md              index: trust rules, one line per note (or per topic page once large), History last
  notes/<slug>.md        one fact per file: type, date, status, supersedes/superseded_by, source session
  topics/<topic>.md      past ~150 index lines: one wiki page per subject (summary, how it evolved, its notes)
  sessions/              optional: exported session digests (git-ignored by default)
  sessions/INDEX.md      one line per session: date, file, what it was about
```

A note:

```markdown
---
name: secret-scan-per-line-requests
description: Secret scanner sends one candidate line per model request because batching hurt detection
type: decision
date: 2026-10-05
status: current
supersedes:
superseded_by:
source: 2026-10-05-1a2b3c4d.md
---

The secret scanner sends each candidate line to the local model in its own request.

**Why:** batching several lines dropped detection from 0.87 to 0.37; the extra cost is ~70 ms/line.
**Rejected:** batches of 8 lines.
**How to apply:** do not batch candidate lines when changing the scanner.
```

## Install

### Any agent: the `skills` CLI

```bash
npx skills add illescasDaniel/memory-1-skill
```

It asks which agents to install for and whether to install into the current project or globally. Non-interactive:
`npx skills add illescasDaniel/memory-1-skill -a claude-code -a codex -y`, plus `-g` for global.

### By hand

Copy the `skills/memory-1` folder into your agent's skills directory.

| | Project (shared with your team) | All your projects |
|---|---|---|
| Claude Code | `.claude/skills/memory-1/` | `~/.claude/skills/memory-1/` |
| Codex | `.agents/skills/memory-1/` | `~/.agents/skills/memory-1/` |
| Cursor | `.cursor/skills/memory-1/` | `~/.cursor/skills/memory-1/` |
| Others | add the `AGENTS.md` paragraph below | |

## Use it

Ask your agent: *"set up memory-1"* (add *"with the session archive"* to export past sessions too). After that the skill's
description tells the agent when to read and write notes: session start, a decision or reversal, a preference or
correction, a resolved incident, end of session.

For agents that do not load skills, or to make the session-start read guaranteed, add this to `AGENTS.md` (or
`CLAUDE.md`):

```markdown
## Memory

Project memory lives in `memory/`. At session start read `memory/NOW.md` (check it against git) and `memory/MEMORY.md`. Code at HEAD wins for current behaviour;
notes win for why, history and preferences; a `superseded` note is history, not the current answer. For detail, open
the note's `source` session in `memory/sessions/` or grep there. Save decisions (with why), reversals (new note that
supersedes the old), preferences and incidents as one-fact notes. Before ending a session in which work happened,
rewrite `memory/NOW.md` (doing, done, next with the user's next step first). Full protocol: the `memory-1` skill.
```

Export sessions by hand (Python 3.9+, standard library only):

```bash
python3 path/to/skills/memory-1/scripts/export_sessions.py --project . --out memory/sessions
```

Check the memory folder (sizes, notes missing from the index, broken supersession links); the skill runs it at the end
of a session:

```bash
python3 path/to/skills/memory-1/scripts/memory_check.py --memory memory
```

> [!NOTE]
> Recommended with Claude Code: turn off its built-in auto memory for the project, so there is one memory and it is the
> one in the repository that every agent and teammate can read. Add `"autoMemoryEnabled": false` to
> `.claude/settings.json`. It is a recommendation, not a requirement: the two can coexist, but facts then end up in two
> places and only one of them is shared.

## Using it with memory-bank

You do not need both. If [memory-bank](https://github.com/illescasDaniel/memory-bank) is installed, its
`activeContext.md` and `progress.md` take the place of `NOW.md`; memory-1 keeps the dated facts and their history.
Never put "next step is X" in a note, and do not copy decision notes into `activeContext.md`.

## Benchmark

One real project (48 sessions), 30 questions about past decisions, Claude Haiku answering, blind grading, score 0 to 2:

| system | score |
|---|---|
| **memory-1** | **1.59** |
| raw session transcripts, searched with grep | 1.58 |
| Claude-style notes folder | 1.39 |
| memory-bank | 1.13 |
| agemem | 0.87 |
| jev-mem | 0.86 |
| no memory | 0.30 |

memory-1 ties searching the raw transcripts and is clearly above the other memory systems, while reading far less at
session start than a transcript folder. It is one project, and the skill was shaped on it, so treat this as strong
evidence of direction, not a general ranking. Method, per-question-type scores, limits and the cross-agent, scale and
wiki tests are in [docs/benchmark.md](docs/benchmark.md).

## Contributing

Issues and pull requests are welcome. The skill is deliberately short: if a change makes `SKILL.md` longer, it should
earn it.

## License

MIT, see [LICENSE](LICENSE).

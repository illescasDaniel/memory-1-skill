# Benchmark

How memory-1 compares with other ways of giving a coding agent long-term project memory, measured on one real project.
Short version: memory-1 scores the same as searching the raw transcripts and clearly above the other memory systems
tried. It is one project and 30 questions, so read it as strong evidence of direction, not as a general ranking.

## Main result

Mean score per answer, 0 to 2. 30 questions, 2 answers per question and system, 2 blind grading passes (600 answers).

| system | then | now | stale | rationale | history | preference | **mean** | $/answer | turns |
|---|---|---|---|---|---|---|---|---|---|
| memory-1 prototype + LLM-written wiki pages | 1.88 | 1.67 | 1.90 | 1.40 | 1.69 | 1.25 | **1.65** | 0.0047 | 8.7 |
| **memory-1 as published** | 1.71 | 1.75 | 1.60 | 1.45 | 1.75 | 1.19 | **1.59** | 0.0044 | 8.0 |
| raw session transcripts, searched with grep | 1.71 | 1.50 | 1.80 | 1.60 | 1.69 | 1.12 | **1.58** | 0.0058 | 8.7 |
| memory-1 prototype (notes + session archive) | 1.67 | 1.58 | 1.50 | 1.30 | 1.50 | 1.75 | **1.55** | 0.0047 | 8.7 |
| Claude-style notes folder (index + one fact per file) | 1.12 | 1.58 | 1.70 | 1.35 | 1.62 | 0.94 | **1.39** | 0.0035 | 7.8 |
| memory-1 notes without the session archive | 1.00 | 1.58 | 1.80 | 1.35 | 1.50 | 0.94 | **1.37** | 0.0041 | 8.7 |
| [memory-bank](https://github.com/illescasDaniel/memory-bank) skill | 1.04 | 1.38 | 1.60 | 0.65 | 1.81 | 0.25 | **1.13** | 0.0044 | 8.1 |
| agemem (notes engine + `recall`) | 0.71 | 0.38 | 1.80 | 0.90 | 0.75 | 0.75 | **0.87** | 0.0033 | 5.8 |
| jev-mem 0.4.1 (notes engine + `recall`) | 0.71 | 0.42 | 1.65 | 0.80 | 1.12 | 0.56 | **0.86** | 0.0032 | 7.2 |
| no memory (repository only) | 0.00 | 0.17 | 1.55 | 0.05 | 0.00 | 0.00 | **0.30** | 0.0047 | 9.5 |

Difference between memory-1 as published and each other system, per question (mean ± standard error, 30 questions):

| against | difference |
|---|---|
| no memory | +1.29 ± 0.15 |
| jev-mem | +0.73 ± 0.13 |
| agemem | +0.72 ± 0.15 |
| memory-bank | +0.46 ± 0.13 |
| memory-1 notes without the archive | +0.23 ± 0.13 |
| Claude-style notes folder | +0.20 ± 0.09 |
| memory-1 prototype | +0.04 ± 0.10 |
| raw transcripts | +0.01 ± 0.07 |
| prototype + wiki pages | −0.06 ± 0.09 |

What the numbers support:

- memory-1 is well above no memory, jev-mem, agemem and memory-bank (3 to 9 standard errors).
- It is ahead of a Claude-style notes folder by about 2 standard errors: likely, not certain.
- It ties raw transcripts, the earlier prototype and the wiki variant. The top four rows are not separable here.
- The session archive is what answers "what did we decide originally": 1.71 with it, 1.00 without.
- Notes with supersession answer "what is current" best (1.75), better than grepping transcripts (1.50), where the
  search sometimes returns the older decision.

## Setup

- **Project:** a real desktop and web application, about five weeks of work. 48 Claude Code sessions were condensed to
  user and assistant prose with secrets redacted (about 600 KB). The repository was checked out at the last session's
  commit, with its own memory folder removed.
- **Questions:** 30, written by Claude Sonnet from the sessions, each checked with grep so the repository alone does not
  answer it (except the "stale" type, by design).

  | type | n | what it tests |
  |---|---|---|
  | then | 6 | the original decision and its reason, for a decision that later changed |
  | now | 6 | the current choice for the same decision and why it changed (not visible in code) |
  | stale | 5 | a current state that is visible in code, where an earlier session said otherwise |
  | rationale | 5 | why a decision that held was made |
  | history | 4 | what happened (incidents, failed releases) |
  | preference | 4 | how the user wants the agent to work |

- **Answering:** Claude Haiku through `claude -p`, with Read, Grep and Glob only, at most 30 turns, no user settings,
  no MCP servers. Every memory condition got the same sentence: "Memory from past working sessions on this project is in
  the `memory/` folder of this repository; start with its index or README if it has one." The two engines got a recall
  command instead (below). Each answer ran in its own copy of the repository, with the other systems' files moved out
  of reach and reads outside the copy blocked. Tool traces were audited afterwards.
- **Grading:** Claude Sonnet, one call per question with all 20 answers shuffled and unlabeled, against a key of core
  facts. 2 = every core fact right and the current state given as current; 1 = partly right or a material false claim;
  0 = wrong, "not found", or a superseded decision presented as current. Two independent passes agreed on 559 of 600
  answers; scores are their mean.

## How each memory was built

Every system saw the same 48 sessions, oldest first.

| system | how it was built |
|---|---|
| memory-1 as published | A Haiku agent with file tools applied this repository's `SKILL.md` (commit `cb8a717`) after each session, as an agent would at the end of a session. Result: 148 notes, a 158-line index, `NOW.md`, 48 session digests. Cost $0.71. |
| memory-1 prototype | The same procedure with the earlier skill text (no `NOW.md`, no topic pages). 155 notes. Cost $0.55. |
| prototype + wiki pages | The prototype memory plus 18 topic pages written by Sonnet in one batch ($1.67). |
| notes without the archive | The prototype's notes with the session digests removed. |
| Claude-style notes folder | A Haiku agent kept a `MEMORY.md` index plus one fact per file, free to update or delete. 89 files. |
| memory-bank | A Haiku agent applied the memory-bank `SKILL.md` after each session. Cost $0.73. |
| agemem | Haiku extracted up to 10 dated facts per session (438); `Engine.remember` stored them through agemem's local decision model (433 kept). The answering agent ran `agemem recall "<query>"`. |
| jev-mem 0.4.1 | The same 438 facts written with their session dates through jev-mem's `Service` (433 kept), recalled with its defaults (k=8, mode `auto`). The decision model was the same local model as agemem's, not jev-mem's hosted one. |
| raw transcripts | The 48 condensed sessions in a folder, no index. |

## Limits

- **One project, 30 questions, one answering model.** Differences under about 0.15 are noise.
- **The skill was shaped on this project.** Lessons from earlier rounds on the same sessions went into memory-1, so it
  has a home advantage over systems that were not tuned here. A held-out project was not run.
- **The questions favour detail.** They were written from the transcripts, which helps raw transcripts and any system
  that keeps an archive, and hurts systems that only keep summaries.
- **The two engines were tested through a recall command with facts extracted by a generic prompt**, not through their
  hooks or MCP servers and not with their own extractors. An earlier round with agemem's hook contexts injected scored
  the same as without. jev-mem ran with a local decision model instead of its hosted one. Their weak spots were
  retrieval (the agent's paraphrased query missed the note) and trust (answers hedged because the code could not
  confirm a note), not storage.
- **memory-bank is a current-state tool.** It scored well on history and poorly on preferences and rationale, which it
  is not designed to hold. Its role is covered by `NOW.md` here, and that role is not what these questions test.
- **Not all answers were collected on the same day.** jev-mem and memory-1 as published were answered a day after the
  others, with the same prompt, model and tools. All 600 answers were graded together in the same blind calls.
- **Preference is 4 questions.** memory-1 as published scored 1.19 there against the prototype's 1.75; with 4 questions
  that is one or two answers.
- **What the writer did not do, and the fix.** In this run the Haiku writer let `NOW.md` grow to 96 lines and had not
  created topic pages when the index reached 158 lines. The scores above are for that memory as written (skill at
  commit `cb8a717` of the original history). The current skill fixes both; see the next section.

## After the benchmark: keeping `NOW.md` and the index small

The skill now says to rewrite `NOW.md` from scratch with a cap per section (50 lines in all), moves open items that
are not next into `LATER.md` (not read at session start), and ships `memory_check.py`, which the agent runs at the end
of a session and which tells it what to fix, including when to create topic pages. The same 48 sessions were written
again with this version by the same Haiku writer:

| | benchmarked version | current version |
|---|---|---|
| `NOW.md` at the end | 96 lines | 26 lines (never above 26 in 48 sessions) |
| index at the end | 158 lines, no topic pages | 142 lines, 3 topic pages (created when the index neared 150) |
| `LATER.md` | n/a | 109 lines |
| problems reported by the check after a session | n/a | 0 in 48 sessions |
| writer cost | $0.71 | $0.85 |
| score, graded together (30 questions) | 1.37 | 1.42 (difference +0.05 ± 0.10) |

Answer quality did not change, which is the point: the fix is about what every session has to read at its start. The
scores in this table are lower than in the main table because the two versions were graded in a pool of their own,
and the grader is stricter when it sees fewer answers side by side; only the difference is meaningful. `LATER.md` has
no cap yet and reached 109 lines.

## Other tests

**Across agents.** Three chained sessions alternating Claude Code (Haiku) and Codex on a small test repository: a
decision with its reason, a reversal, then "where are we?". The skill text was pointed to from `AGENTS.md`/`CLAUDE.md`.

| | recap score (0 to 6) |
|---|---|
| no memory | 1.7 |
| memory-1 without `NOW.md` | 5.3 |
| memory-1 with `NOW.md` | 5.0 |

Both agents saved notes unprompted when the user said "thanks, that's all", and recorded the reversal as a superseding
note. `NOW.md` saved the next step in 5 of 5 writing sessions. Three chains per row, so the last two rows are a tie.
Whether the skill triggers from its description alone, without the pointer, was not tested.

**Scale.** 24 needle questions (direct, reworded, and old-versus-new) over memories of increasing size, with
same-topic near-duplicate notes as distractors. Fraction answered correctly:

| layout | 235 notes | 1,500 | 5,000 |
|---|---|---|---|
| one flat index | 1.00 | 0.96 | 0.79 |
| topic indexes | 1.00 | 0.94 | 0.98 |
| topic pages (script-built) | 1.00 | 0.96 | 0.98 |
| one big file | 1.00 | 0.92 | 0.83 |

At 5,000 notes the flat index led the agent to a similar but wrong note in 21% of answers; topic layouts in none. This
is why memory-1 switches to topic pages. The exact topic-page layout it ships is a merge of the two that held up and
was not itself run at 5,000 notes. The filler notes were generated, not real.

**Wiki pages.** Adding 18 Sonnet-written topic pages to the prototype memory, graded as a pair on 38 questions: 1.34
without, 1.51 with (+0.17 ± 0.08), mostly on "what did we decide originally" (+0.54). Pages lost points where they
summarised away an exact preference or number, so in memory-1 a page links its notes and specifics come from the notes.
This follows Anthropic's [components of agent memory](https://www.anthropic.com/research/components-of-agent-memory).
Keeping pages accurate over many sessions was not tested.

**Hooks.** memory-1 has none. With no hint in the prompt at all, the agent still found `memory/` by plain search in 50
of 60 answers and scored the same as with the hint. Simulating a per-prompt hook that injects the 4 best-matching notes
made "what is current" answers worse (1.12 against 1.50 to 1.58), because the agent stopped at the injected notes.
Injecting the whole index at session start cost about 7k tokens and gained nothing.

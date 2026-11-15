---
name: memory-1
description: Keep a portable, git-tracked memory of what the code cannot tell a future session (what we are doing and what is next, decisions and why, reversals, user preferences, incidents) as a short status file plus one-fact Markdown notes with dates and supersession, and an optional archive of condensed session transcripts. Use at session start, when the user asks why something is the way it is or what was decided before, after a decision or reversal, when the user states a preference or corrects you, after an incident is resolved, before ending a session, and when asked to set up memory or export past sessions.
---

# memory-1

Project memory lives in `memory/` as plain Markdown, so any agent that can read files can use it (Claude Code, Codex,
Cursor, others). No service and no database: `grep` is the search engine.

```
memory/
  NOW.md                 status: what we are doing, what was just done, what is next, open questions (overwritten)
  LATER.md               optional: open items that are not next, one line each (not read at session start)
  MEMORY.md              index: one line per note (small memory) or one line per topic page (large memory)
  notes/<slug>.md        one fact per file, dated, with status and supersession links
  topics/<topic>.md      optional wiki page per subject: summary, how it evolved, links to its notes (see Growing)
  sessions/              optional: condensed transcripts of past sessions (exported, redacted)
  sessions/INDEX.md      one line per session: date, file, what it was about
```

## How to trust what you read

- **Code and config at HEAD win** for what the code does today. If a note says otherwise, the note is stale: say so,
  answer from the code, and fix or supersede the note.
- **Notes win** for why something is the way it is, what was decided before, what the user prefers, and what happened.
  The code cannot confirm these, so do not discount a note because the repository does not mention it.
- **The newest current note wins** between notes. A note with `status: superseded` is history: use it to answer "what
  did we decide before / what changed", never as the current answer.
- **Sessions hold the detail.** A note is a summary; when you need exact numbers, names, commands or the sequence of
  events, open the session file named in the note's `source`, or search `memory/sessions/` directly.

## Session start

1. Read `memory/NOW.md` and `memory/MEMORY.md`. Check `NOW.md` against `git log` and `git status` since its date:
   work listed as next may already be done. If `memory/` is missing and the user wants memory, set it up from
   `templates/` next to this file (NOW.md, MEMORY.md, and sessions/INDEX.md only if transcripts will be archived).
2. When the user says "continue" or "where were we", answer from `NOW.md` (checked against git), then the notes.
3. Open individual notes only when the task touches them. For history questions, read the topic page if there is
   one, then search `memory/notes/` and `memory/sessions/` with grep before answering. Topic pages summarise: take
   exact numbers, names and preferences from the linked notes, not from the page.

## What to save

Save what a future session cannot derive from the code or `git log`:

- **decision**: what was chosen, the reason, and the rejected alternatives. Keep the specific facts that justify it
  (numbers, versions, error messages, file names): "per-line requests: detection 0.87 vs 0.37 when batched".
- **preference**: how the user wants work done, including corrections ("do not X; do Y"), with their reason if given.
- **incident**: something that went wrong, its cause, and how it was resolved or recovered.
- **gotcha**: a non-obvious constraint or trap in tools, libraries or the environment.
- **context**: who, why or when facts about the project that are not in the repository.

Do not save in notes: what the code, tests or docs already say; git history; work in progress, current status or next
steps (they go in `NOW.md`); secrets.

## NOW.md: what we are doing and what is next

One short file (at most 50 lines) that the next session, in any agent, reads first. Rewrite it from scratch each time
for the work as it stands now; never append to the previous text or keep an "Earlier:" trail.

```markdown
# Now
Updated: 2026-11-15 (session 2026-11-15-ab12cd34.md)

## Doing
Settings screen: moving the in-app help pages to the native WebView.
## Done recently
- Replaced the bundled Chromium view on the login screen (commit 1a2b3c4).
## Next
1. Port the help pages; keep JS bridge off (see notes/webview-native-over-chromium.md).
## Open questions / blocked
- Does Android 9 need the AndroidX WebKit fallback? Waiting for the user.
```

- Write it whenever the plan changes and always before ending a session in which work happened, even if the user did
  not ask. A session that ends without updating `NOW.md` leaves the next agent guessing.
- `Next` starts with the next step the user named, in their words; your own follow-ups go after it, marked as yours.
- Name decisions only by linking their note; the reason lives in the note, not here.
- Keep it small, section by section: `Updated` names one session; `Doing` is the current work only (up to 5 lines);
  `Done recently` has at most 5 one-line items from the latest sessions (delete older ones: git and the notes keep
  them); `Next` has at most 7 items; no other sections.
- Open items that are not among the next steps go to `memory/LATER.md`, one dated line each, marked `(User)` or
  `(Mine)`: things to test on a real device, questions the user has not answered, follow-ups from older sessions.
  `LATER.md` is not read at session start. Read it when the user asks what is pending, or when `Next` is empty, and
  delete lines that are done or no longer matter.
- When a decision changes, update both: supersede the note and rewrite the affected `Next` items.

## How to write a note

One fact per file in `memory/notes/`, named `<slug>.md` (short, kebab-case, specific: `secret-scan-per-line-requests`).

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

**Why:** batching several lines dropped detection from 0.87 to 0.37 (position effects); the extra cost is ~70 ms/line.
**Rejected:** batches of 8 lines.
**How to apply:** do not batch candidate lines when changing the scanner.
```

- Use absolute dates (`date:` is when the fact was established). Convert "today" or "yesterday" from the session date.
- `source:` names the session file in `memory/sessions/` when the archive exists; leave it empty otherwise.
- Write `**Why:**` for decisions and preferences; add `**Rejected:**` and `**How to apply:**` when they exist.

## Before saving: update, supersede, or add

Read `MEMORY.md` and grep `memory/notes/` for the subject first.

- **Same fact, more detail**: edit the existing note.
- **The decision or preference changed** (a reversal): never edit the old note's fact. Create a new note that states
  the new choice and why it changed ("Reversal: ... replaced X because ..."), with `supersedes: <old slug>`. In the old
  note set `status: superseded` and `superseded_by: <new slug>`. Move the old index line to the History section.
- **The note was simply wrong**: fix it, or delete it if it has no historical value.
- **New subject**: add a note and an index line.
- If the subject has a topic page, update the page's summary and note list in the same edit.

## MEMORY.md

```markdown
# Memory

Code at HEAD wins for current behaviour; notes win for why and history; newest current note wins; open `source` sessions for detail.

## Decisions
- [Secret scan: one line per request](notes/secret-scan-per-line-requests.md) 2026-10-05: batching dropped detection 0.87 → 0.37
## Preferences
## Incidents
## Gotchas
## Context
## History (superseded)
- [Task MCP: one tool per task](notes/task-mcp-tool-per-task.md) 2026-10-01 → superseded by task-mcp-single-tool
```

One line per note: link, date, and a hook specific enough to decide whether to open it. Keep it under about 150 lines
(it is read at the start of every session, so its size is paid every time); past that, switch to topic pages.

## Growing: topic pages

When `MEMORY.md` passes 150 lines (the check says so), or one subject has about 8 or more notes, group notes by subject into
`memory/topics/<topic>.md`, one page per subject (a feature, component or area: `phone-picker`, `releases`). Notes stay
where they are; a page is a map and a synthesis, not a copy.

```markdown
# Help pages
Updated: 2026-11-20. Related: [installer](installer.md), [security](security.md)

## Now
Help pages render in a bundled Chromium (CEF) view ([help-view-cef](../notes/help-view-cef-backend.md)); JS bridge off
([help-js-bridge-off](../notes/help-js-bridge-off.md)).
## How it got here
- 2026-11-12 native system WebView chosen: Chromium added ~38 MB to the installer ([note](../notes/help-view-native-webview.md)).
- 2026-11-15 reversed to CEF: WebKitGTK on Ubuntu 20.04 broke the FAQ's CSS grid ([note](../notes/help-view-cef-backend.md)).
## Notes
- [Help view: bundled CEF](../notes/help-view-cef-backend.md) 2026-11-15: consistent rendering over installer size
- [Help pages: JS bridge off](../notes/help-js-bridge-off.md) 2026-11-12: security; no page-to-app calls
## History (superseded)
- [Help view: native WebView](../notes/help-view-native-webview.md) 2026-11-12 → superseded by help-view-cef-backend
```

- Do the switch in the session where the limit is passed, starting with the subjects that have the most notes; it
  does not have to cover every note at once.
- `MEMORY.md` then holds the trust line, one line per topic page (link, note count, what it covers), the newest ~20
  notes, and notes that fit no topic.
- Keep each page shorter than the notes it covers; it should abstract, not repeat. Every claim links its note.
- Keep superseded choices in "How it got here" and History: "what did we decide first" must stay answerable.
- One page per subject, edited by one session at a time; do not merge subjects into one long page.

## Session archive (optional)

The archive keeps the detail that notes summarise away. Export past sessions with the script next to this file:

```bash
python3 <skill dir>/scripts/export_sessions.py --project . --out memory/sessions
```

It reads Claude Code (`~/.claude/projects/`) and Codex (`~/.codex/sessions/`) transcripts for this project, keeps only
user and assistant prose, redacts credential-like strings, and writes one file per session. It prints only the files
that are new or changed (a session that grew since the last export is rewritten), so it is safe to run every time.

After exporting, add one line per new session to `memory/sessions/INDEX.md` (and refresh the line of an updated one):
`- 2026-10-05 [2026-10-05-1a2b3c4d.md](2026-10-05-1a2b3c4d.md): secret scanner batching vs per-line requests; moved v0.3.0 tag`.

Transcripts are personal working history. By default `memory/sessions/` is git-ignored (the template ships a
`.gitignore`); remove it to share the archive with the team, after checking that the redaction is enough.

## End of session

Before finishing a session in which work happened (when the user says thanks, stop, that's all, or the task is done):
rewrite `NOW.md`, write or supersede the notes, update `MEMORY.md` and any affected topic page, and, if the archive
is used, export the session and add its `INDEX.md` line. Keep edits small; do not rewrite notes that did not change.

Then run the check and do what each `FIX` line says (it reports a `NOW.md` or index that grew past its limit, notes
missing from the index, and broken supersession links):

```bash
python3 <skill dir>/scripts/memory_check.py --memory memory
```

Without a shell, count instead: `NOW.md` at most 50 lines, `MEMORY.md` at most 150.

## Alongside other memory

- If memory-bank is installed, its `activeContext.md` and `progress.md` play the role of `NOW.md`: use them instead
  and skip `NOW.md`. Do not copy decision notes into them.
- Rules the agent must always follow belong in `AGENTS.md` or `CLAUDE.md`. Point `AGENTS.md` at `memory/MEMORY.md`
  so agents that do not load skills still find the memory.

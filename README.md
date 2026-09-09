# Game QA Triage Agent

Turning player bug reports into structured and trustworthy data.

An LLM agent that turns player bug reports posted on forums into a filled-in
form with fields such as version number, platform and description. A second
step then validates that the extracted information is grounded in the original
text.

## What it does

1. **Extract** - pull the facts out of a single player post into a typed record
2. **Detect Evidence** - match each extracted field against the original post to
   make sure the model doesn't make things up, which turns the fabrication rate
   into something measurable without manual labelling
3. **Check completeness** - report which fields the player never mentioned
4. **Detect duplicates** - match the report against a set of known issues

Severity rating and team assignment are deliberately out of scope.


## Known limitations

1. The input unit is a single post. Multi-post threads are not supported.
2. Platform comes from the report source, not from the post body, so a post that
   says "I'm on Windows 11" is not treated as more specific than its source.
3. The evidence check catches fabrication, not misinterpretation. A model can
   quote a real sentence and still draw the wrong conclusion from it - for
   example when a player states a guess about the cause and the model records it
   as an observation.
4. Some fields are inferred rather than copied - `frequency` maps "keeps
   crashing" onto a fixed scale, and `expected_result` is often something the
   player never wrote down. No verbatim quote can support them, so they are
   outside what the evidence check can verify at all.

## Data

Development uses real posts from a public Steam bug-report board. Those are kept
locally and excluded from the repository (see `.gitignore`) for copyright and
data-protection reasons, so the scripts need your own reports in
`data/raw_real/` to produce anything.

## Status

Work in progress.

- [x] Typed data model (Pydantic)
- [x] Extraction module and batch runner over the whole sample set
- [ ] Evidence check (with text normalisation)
- [ ] Completeness check
- [ ] Duplicate detection
- [ ] Retry on API errors
- [ ] Evaluation harness and metrics

## Setup

```bash
pip install -r requirements.txt

cp .env.example .env      # then put your Anthropic API key in .env
python scripts/check_key.py
```

## Layout

```
src/triage/models.py     typed records: ReportSource, Evidence, BugReport
src/triage/llm.py        talks to the Anthropic API, returns unvalidated fields
src/triage/extract.py    loads a report, validates the model's answer
scripts/check_key.py     one-off: verify the API key in .env works
scripts/run_all.py       extract every report, print a summary, save to runs/
data/raw_real/           real posts, local only, git-ignored
runs/                    recorded model responses, local only, git-ignored
```

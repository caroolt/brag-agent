# BragDoc Agent

A Claude Code-powered CLI that pulls your Bitbucket pull requests and generates engineering brag documents — monthly summaries and annual reviews written at the depth and calibration expected for performance reviews and promotions.

It also lets you capture contributions that never show up in PRs: architecture decisions, cross-team alignment, technical influence, incident response, and more.

## How it works

1. Fetches your authored PRs from Bitbucket (including diffs)
2. Passes raw data to Claude for analysis
3. Produces structured brag documents filtered to your engineering area and calibrated to your seniority level
4. Lets you register non-PR contributions at any time via `/registrar-contexto`; those entries are incorporated the next time a monthly brag doc is generated

Output lives in `.bragdoc/` (git-ignored) as markdown files.

## Requirements

- Python 3.9+
- Claude Code CLI
- Bitbucket Cloud account with an App Password

## Setup

```bash
pip install -r requirements.txt
```

Then run `/configure` inside Claude Code, or:

```bash
python main.py config
```

You'll be asked for:
- Seniority level (Junior → Principal)
- Engineering area (Frontend, Backend, Fullstack, Mobile, Data/ML, DevOps/Infra)
- Bitbucket workspace slug
- Bitbucket App Password and email
- Repositories to monitor

Credentials are saved to `.env`; configuration is saved to `.bragdoc/config.md`. Both are git-ignored automatically.

### Getting a Bitbucket App Password

Go to **Bitbucket → Personal settings → App passwords** and create one with **Repositories: Read** permission.

## Commands

All commands are available as Claude Code slash commands or via the CLI directly.

| Slash command | CLI equivalent | What it does |
|---|---|---|
| `/configure` | `python main.py config` | Interactive setup wizard |
| `/gerar-bragdoc` | `python main.py gerar` | Fetch PRs and generate monthly brag docs |
| `/re-summarize` | `python main.py resumir` | Regenerate the annual summary from existing monthly files |
| `/status` | `python main.py status` | Show current configuration |
| `/registrar-contexto` | `python main.py registrar` | Record a non-PR contribution |

### Generating brag docs

```
/gerar-bragdoc
```

Claude fetches PRs since the last run, writes raw data to `.bragdoc/raw_[month]_[year].md`, then analyzes each file and produces the final `.bragdoc/bragdoc_[month]_[year].md`. Raw files are deleted after processing. The annual summary is updated automatically.

Any context entries recorded via `/registrar-contexto` that belong to the month being processed are incorporated into a `## Beyond the Code` section. Each entry is marked as processed so it is never duplicated across runs.

On subsequent runs within the same month, new entries are appended under a `### Período: DD/MM - DD/MM` header rather than overwriting.

### Recording non-PR contributions

```
/registrar-contexto
```

Claude walks you through five questions — type, description, impact, date, and optional references — then saves the entry to `.bragdoc/context/[timestamp]_[type].md`.

Supported contribution types:
- Architecture decision
- Technical discussion
- Cross-team alignment
- Technical influence (shaped direction without writing code)
- Incident response
- Mentorship or knowledge sharing
- Other

The date you provide can be in any natural format (`hoje`, `10/04`, `semana passada`). Claude resolves relative dates against the recorded timestamp. Entries are independent of the last PR run date — recording something today about an event last week will place it in the correct month when the brag doc is generated.

## Output structure

```
.bragdoc/
  config.md
  context/
    20260417_143000_architecture_decision.md
    ...
  bragdoc_jan_2026.md     # monthly
  bragdoc_fev_2026.md
  bragdoc_2026.md         # annual summary
  2025/
    bragdoc_2025.md
    bragdoc_jan_2025.md
    ...
```

Each monthly file follows this format:

```markdown
# Brag Document — January 2026

## Key Deliveries

### Feature or system name (TICKET-123)
Context and problem → what was built → impact on system or product.
Related PRs: #42, #43

## Beyond the Code

### Architecture decision — short summary in up to 8 words
What was discussed or decided → impact or direction that resulted.
References: TICKET-456, @person

## Summary
Honest 2-3 sentence summary of the period.
```

## Security

- `BITBUCKET_TOKEN` is never printed or committed
- `.env` and `.bragdoc/` are added to `.gitignore` automatically on first configure
- If the token is invalid, re-run `/configure`

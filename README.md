# BragDoc Agent

A Claude Code-powered CLI that pulls your Bitbucket pull requests and generates engineering brag documents — monthly summaries and annual reviews written at the depth and calibration expected for performance reviews and promotions.

## How it works

1. Fetches your authored PRs from Bitbucket (including diffs)
2. Passes raw data to Claude for analysis
3. Produces structured brag documents filtered to your engineering area and calibrated to your seniority level

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

### Generating brag docs

```
/gerar-bragdoc
```

Claude fetches PRs since the last run, writes raw data to `.bragdoc/raw_[month]_[year].md`, then analyzes each file and produces the final `.bragdoc/bragdoc_[month]_[year].md`. Raw files are deleted after processing. The annual summary is updated automatically.

On subsequent runs within the same month, new entries are appended under a `### Período: DD/MM - DD/MM` header rather than overwriting.

## Output structure

```
.bragdoc/
  config.md
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

## Summary
Honest 2-3 sentence summary of the period.
```

## Security

- `BITBUCKET_TOKEN` is never printed or committed
- `.env` and `.bragdoc/` are added to `.gitignore` automatically on first configure
- If the token is invalid, re-run `/configure`

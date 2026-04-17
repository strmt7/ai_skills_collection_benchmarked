# explain-this-pr

<img width="1280" height="640" alt="explain-this-pr" src="https://github.com/user-attachments/assets/9e76fc64-f982-4c4c-9b58-4398541aab97" />


Point this skill at any GitHub PR and it writes a plain-English explanation of what changed and why, then posts it as a PR comment.

## What It Does

- Fetches the PR diff and metadata via `gh`
- Writes two paragraphs: what changed (technical) and why it matters (impact)
- Posts the explanation as a PR comment with `gh pr comment`
- Works with any public or private repo you have access to via `gh`

## Requirements

| Requirement | Purpose | How to Set Up |
|------------|---------|--------------|
| `gh` CLI | Fetching PR data and posting comments | https://cli.github.com, then run `gh auth login` |

No API keys needed.

## How to Use

Explain a PR by URL:

```
"Explain this PR: https://github.com/owner/repo/pull/123"
"What does this PR do? https://github.com/owner/repo/pull/456"
"Summarize this pull request: [URL]"
```

Explain by PR number (in the current repo):

```
"Explain PR #42"
"Add a summary comment to PR #99"
```

Explain the current branch PR:

```
"Explain the current branch PR"
"Add a plain-English comment to my PR"
```

Output without posting:

```
"Explain this PR but don't post the comment: [URL]"
"What does this PR change? Just give me the text."
```

## Output Format

Two paragraphs, under 150 words total.

Paragraph 1: What it does (technical). Names the specific files, functions, or systems that changed. States the before/after if visible in the diff.

Paragraph 2: Why it matters (impact). Explains who benefits and what problem is solved. Omitted if there is no clear "why" in the diff or commits. The skill never guesses at impact.

## Project Structure

```
explain-this-pr/
├── SKILL.md
├── README.md
└── evals/
    └── evals.json
```

## License

MIT

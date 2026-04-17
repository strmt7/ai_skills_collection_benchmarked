# Google Trends API Skills

<img width="1280" height="640" alt="google-trends-skills-cover" src="https://github.com/user-attachments/assets/848aa1be-64af-4b4b-bf46-af3d0798b7ee" />

Agent Skills for SEO keyword research using Google Trends data via SerpApi. Built for AI agents that generate tech and developer-focused blog content.

## Skills

### 1. `google-trends-api/`
The API layer — knows how to query Google Trends through SerpApi, handle responses, manage rate limits, and cache results.

### 2. `seo-keyword-research/`
The SEO workflow — uses Google Trends data to find breakout keywords, build content structure, and generate SEO-optimized blog outlines.

## Quick Start

```bash
# 1. Get a free API key (250 searches/month)
# https://serpapi.com/

# 2. Set your key
export SERPAPI_KEY="your_key_here"

# 3. Install dependency
pip install requests

# 4. Run keyword research for a blog topic
python seo-keyword-research/scripts/blog_seo_research.py "kubernetes deployment"

# 5. Or just discover trending keywords
python google-trends-api/scripts/discover_keywords.py "AI developer tools"
```

## Directory Structure

```
google-trends-api/
├── SKILL.md                        # API skill (endpoints, params, usage)
├── scripts/
│   └── discover_keywords.py        # Keyword discovery script
└── references/
    └── api-responses.md            # Full API response structures

seo-keyword-research/
├── SKILL.md                        # SEO workflow skill (research -> outline)
├── scripts/
│   └── blog_seo_research.py        # Full blog SEO research script
└── references/
    ├── keyword-placement-guide.md  # Detailed keyword placement rules
    └── tech-blog-examples.md       # Real examples for tech/dev blogs
```

## How It Works

```
User: "Write a blog about kubernetes deployment"
  |
  v
[google-trends-api] RELATED_QUERIES -> finds "kubernetes vs docker" (Breakout!)
[google-trends-api] RELATED_TOPICS  -> finds "Helm", "CI/CD", "Container Orchestration"
  |
  v
[seo-keyword-research] Selects primary keyword, builds outline
  |
  v
Output: SEO-optimized blog outline targeting trending keywords
```

## Specification

These skills follow the [Agent Skills specification](https://agentskills.io/specification). Each skill has:
- `SKILL.md` with YAML frontmatter (name, description, compatibility, metadata)
- `scripts/` for executable code
- `references/` for detailed documentation (loaded on demand)

## License

MIT

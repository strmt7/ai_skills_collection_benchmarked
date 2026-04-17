# Twitter GTM Find Skill

<img width="1280" height="640" alt="Generated_chart__twitter-gtm-find-cover-bw png" src="https://github.com/user-attachments/assets/618b0abe-34fc-4c3e-a345-1a3eaeb3d20b" />

This repository contains the `twitter-GTM-find/` AI Skill.

This pipeline automates the discovery of highly-targeted, Developer-First startups hiring for Go-To-Market (GTM), Developer Relations (DevRel), and Growth roles by scraping Twitter (via Apify) and automatically verifying the startups' funding and product type using Gemini's native Google Search Grounding.

## The Skill Directory

All executable code and documentation are packaged cleanly inside the `twitter-GTM-find/` folder. This is designed to be directly imported and read by AI agents (like OpenClaw or Claude) so they understand how to use the tool.

```text
twitter-GTM-find/
├── SKILL.md             <-- The AI entry point and documentation
├── references/
│   └── icp-checklist.md <-- The strict evaluation criteria (Dev-first + $100K+ funded)
└── scripts/
    ├── run_pipeline.sh  <-- The executable shell script
    └── src/             <-- The TypeScript pipeline source code
```

## Usage

To run the pipeline manually or via an agent:

1. Create a `.env` file at the root of the repository:
   ```env
   APIFY_API_TOKEN=your_apify_token
   GEMINI_API_KEY=your_gemini_api_key
   MAX_POSTS=20
   ```
2. Run the shell script:
   ```bash
   cd twitter-GTM-find/scripts
   bash run_pipeline.sh
   ```

## Output

The pipeline generates two temporary files at the root of the repository (which are `.gitignore`d to prevent leaking data):
- `radar-jobs.json`: The initial raw batch of scraped tech jobs.
- `openclaw-icp-jobs.json`: The final, strict ICP-validated list of highly funded, developer-first startups hiring right now.

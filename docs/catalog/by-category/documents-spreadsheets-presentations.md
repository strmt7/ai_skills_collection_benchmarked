# Documents, spreadsheets & presentations

## docs-from-code - Varnan-Tech/opendirectory `packages/cli/skills/docs-from-code/SKILL.md`

- Skill page: [docs-from-code](../skills/by-category/documents-spreadsheets-presentations/reddit-verified-gtm-registry/docs-from-code.md)
- Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/reddit-verified-gtm-registry/docs-from-code`
- Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/reddit-verified-gtm-registry/docs-from-code/SKILL.md`
- Source: [Varnan-Tech/opendirectory `packages/cli/skills/docs-from-code/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/docs-from-code/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`
- What it covers: Catalog summary: Generates and updates README.md and API reference docs by reading your codebase's functions, routes, types, schemas, and architecture. Uses graphify to build a knowledge graph first, then writes accurate docs from it. Use when asked to write docs, generate a README, document an API, update stale docs, create an API reference from code, add an architecture section, or document a project in any language. Trigger when.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: docs-from-code, Workflow, Step 1: Install graphify and Build the Knowledge Graph, Step 1B: Fallback (if graphify unavailable), TypeScript/JS projects:. Resources: has_scripts, has_references.
- Notability: Included from Reddit r/codex open-source Codex skills signal; GitHub SKILL.md files verified with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-varnan-tech-opendirectory-packages-cli-skills-docs-from-code-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/docs-from-code/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
  - `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
  - `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

## frontend-slides - affaan-m/everything-claude-code `.agents/skills/frontend-slides/SKILL.md`

- Skill page: [frontend-slides](../skills/by-category/documents-spreadsheets-presentations/selected-structure-reference/frontend-slides.md)
- Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/selected-structure-reference/frontend-slides`
- Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/selected-structure-reference/frontend-slides/SKILL.md`
- Source: [affaan-m/everything-claude-code `.agents/skills/frontend-slides/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/frontend-slides/SKILL.md)
- Selected ref: `v1.10.0`; commit `846ffb75da9a`
- What it covers: Catalog summary: Create stunning, animation-rich HTML presentations from scratch or by converting PowerPoint files. Use when the user wants to build a presentation, convert a PPT/PPTX to web, or create slides for a talk/pitch. Helps non-designers discover their aesthetic through visual exploration rather than abstract choices.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Frontend Slides, When to Activate, Non-Negotiables, Workflow, 1. Detect Mode. Resources: has_agents_metadata.
- Notability: Included from selected repository structure reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Assigned benchmark scenarios:
  - `skill-proof-affaan-m-everything-claude-code-agents-skills-frontend-slides-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/frontend-slides/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
  - `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
  - `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

## create-infographics - aizzaku/create-infographics `SKILL.md`

- Skill page: [create-infographics](../skills/by-category/documents-spreadsheets-presentations/creative-reference/create-infographics.md)
- Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/creative-reference/create-infographics`
- Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/creative-reference/create-infographics/SKILL.md`
- Source: [aizzaku/create-infographics `SKILL.md`](https://github.com/aizzaku/create-infographics/blob/5c8c8821026e7ee5998c886780237e64193e54c3/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `5c8c8821026e`
- What it covers: Catalog summary: Creates production-grade infographics as HTML, PNG, and PDF from any data or brief. Use when asked for an infographic, visual summary, one-pager, data visualization, or to convert tables, stats, timelines, or comparisons into a visual format. Also triggers on: "shareable graphic", "visual report", "poster" + data content, "one-pager", or any request where information should be presented as a designed image. Crypto.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Infographic Skill, Designer DNA, Anti-Frontend Checklist (run before delivery), Non-Negotiable Rules, Platform Sizing. Resources: has_scripts, has_examples.
- Notability: Included from creative media skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Move long background material into references/ to keep SKILL.md concise.
- Assigned benchmark scenarios:
  - `skill-proof-aizzaku-create-infographics-skill-md`: Use the immutable source file https://github.com/aizzaku/create-infographics/blob/5c8c8821026e7ee5998c886780237e64193e54c3/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
  - `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
  - `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

## canvas-design - anthropics/skills `skills/canvas-design/SKILL.md`

- Skill page: [canvas-design](../skills/by-category/documents-spreadsheets-presentations/official-reference/canvas-design.md)
- Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/official-reference/canvas-design`
- Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/official-reference/canvas-design/SKILL.md`
- Source: [anthropics/skills `skills/canvas-design/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/canvas-design/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`
- What it covers: Catalog summary: Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the user asks to create a poster, piece of art, design, or other static piece. Create original visual designs, never copying existing artists' work to avoid copyright violations.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: DESIGN PHILOSOPHY CREATION, THE CRITICAL UNDERSTANDING, HOW TO GENERATE A VISUAL PHILOSOPHY, PHILOSOPHY EXAMPLES, ESSENTIAL PRINCIPLES. Resources: none observed.
- Notability: Included from official skill reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-anthropics-skills-skills-canvas-design-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/canvas-design/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
  - `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
  - `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

## docx - anthropics/skills `skills/docx/SKILL.md`

- Skill page: [docx-anthropics](../skills/by-category/documents-spreadsheets-presentations/official-reference/docx-anthropics.md)
- Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/official-reference/docx-anthropics`
- Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/official-reference/docx-anthropics/SKILL.md`
- Source: [anthropics/skills `skills/docx/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/docx/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`
- What it covers: Catalog summary: Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Triggers include: any mention of 'Word doc', 'word document', '.docx', or requests to produce professional documents with formatting like tables of contents, headings, page numbers, or letterheads. Also use when extracting or reorganizing content from .docx files, inserting or replacing images in documents,.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: DOCX creation, editing, and analysis, Overview, Quick Reference, Converting .doc to .docx, Reading Content. Resources: has_scripts.
- Notability: Included from official skill reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Move long background material into references/ to keep SKILL.md concise.
- Assigned benchmark scenarios:
  - `skill-proof-anthropics-skills-skills-docx-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/docx/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
  - `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
  - `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

## pdf - anthropics/skills `skills/pdf/SKILL.md`

- Skill page: [pdf-anthropics](../skills/by-category/documents-spreadsheets-presentations/official-reference/pdf-anthropics.md)
- Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/official-reference/pdf-anthropics`
- Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/official-reference/pdf-anthropics/SKILL.md`
- Source: [anthropics/skills `skills/pdf/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/pdf/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`
- What it covers: Catalog summary: Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: PDF Processing Guide, Overview, Quick Start, Read a PDF, Extract text. Resources: has_scripts.
- Notability: Included from official skill reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-anthropics-skills-skills-pdf-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/pdf/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
  - `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
  - `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

## pptx - anthropics/skills `skills/pptx/SKILL.md`

- Skill page: [pptx-anthropics](../skills/by-category/documents-spreadsheets-presentations/official-reference/pptx-anthropics.md)
- Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/official-reference/pptx-anthropics`
- Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/official-reference/pptx-anthropics/SKILL.md`
- Source: [anthropics/skills `skills/pptx/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/pptx/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`
- What it covers: Catalog summary: Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates,.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: PPTX Skill, Quick Reference, Reading Content, Text extraction, Visual overview. Resources: has_scripts.
- Notability: Included from official skill reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-anthropics-skills-skills-pptx-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/pptx/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
  - `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
  - `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

## theme-factory - anthropics/skills `skills/theme-factory/SKILL.md`

- Skill page: [theme-factory](../skills/by-category/documents-spreadsheets-presentations/official-reference/theme-factory.md)
- Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/official-reference/theme-factory`
- Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/official-reference/theme-factory/SKILL.md`
- Source: [anthropics/skills `skills/theme-factory/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/theme-factory/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`
- What it covers: Catalog summary: Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifact that has been creating, or can generate a new theme on-the-fly.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Theme Factory Skill, Purpose, Usage Instructions, Themes Available, Theme Details. Resources: none observed.
- Notability: Included from official skill reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-anthropics-skills-skills-theme-factory-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/theme-factory/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
  - `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
  - `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

## xlsx - anthropics/skills `skills/xlsx/SKILL.md`

- Skill page: [xlsx-anthropics](../skills/by-category/documents-spreadsheets-presentations/official-reference/xlsx-anthropics.md)
- Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/official-reference/xlsx-anthropics`
- Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/official-reference/xlsx-anthropics/SKILL.md`
- Source: [anthropics/skills `skills/xlsx/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/xlsx/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`
- What it covers: Catalog summary: Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing .xlsx, .xlsm, .csv, or .tsv file (e.g., adding columns, computing formulas, formatting, charting, cleaning messy data); create a new spreadsheet from scratch or from other data sources; or convert between tabular file formats. Trigger especially when the user.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Requirements for Outputs, All Excel files, Professional Font, Zero Formula Errors, Preserve Existing Templates (when updating templates). Resources: has_scripts.
- Notability: Included from official skill reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-anthropics-skills-skills-xlsx-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/xlsx/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
  - `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
  - `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

## ppt-master - hugohe3/ppt-master `skills/ppt-master/SKILL.md`

- Skill page: [ppt-master](../skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master.md)
- Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master`
- Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master/SKILL.md`
- Source: [hugohe3/ppt-master `skills/ppt-master/SKILL.md`](https://github.com/hugohe3/ppt-master/blob/19297c51cce3361d55137f527c010a8886f88bda/skills/ppt-master/SKILL.md)
- Selected ref: `v2.3.0`; commit `19297c51cce3`
- What it covers: Catalog summary: AI-driven multi-format SVG content generation system. Converts source documents (PDF/DOCX/URL/Markdown) into high-quality SVG pages and exports to PPTX through multi-role collaboration. Use when user asks to "create PPT", "make presentation", "生成PPT", "做PPT", "制作演示文稿", or mentions "ppt-master".
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: PPT Master Skill, Main Pipeline Scripts, Template Index, Standalone Workflows, Workflow. Resources: has_scripts, has_references.
- Notability: Included from latest release presentation skill with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-hugohe3-ppt-master-skills-ppt-master-skill-md`: Use the immutable source file https://github.com/hugohe3/ppt-master/blob/19297c51cce3361d55137f527c010a8886f88bda/skills/ppt-master/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
  - `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
  - `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

## ckm:design - nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/design/SKILL.md`

- Skill page: [ckm-design](../skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-design.md)
- Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-design`
- Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-design/SKILL.md`
- Source: [nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/design/SKILL.md`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/design/SKILL.md)
- Selected ref: `v2.5.0`; commit `07f4ef3ac256`
- What it covers: Catalog summary: Comprehensive design skill: brand identity, design tokens, UI styling, logo generation (55 styles, Gemini AI), corporate identity program (50 deliverables, CIP mockups), HTML presentations (Chart.js), banner design (22 styles, social/ads/web/print), icon design (15 styles, SVG, Gemini 3.1 Pro), social photos (HTML→screenshot, multi-platform). Actions: design logo, create CIP, generate mockups, build slides, design.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Design, When to Use, Sub-skill Routing, Logo Design (Built-in), Logo: Generate Design Brief. Resources: has_scripts, has_references.
- Notability: Included from latest release UI/UX skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design-skill-md`: Use the immutable source file https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/design/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
  - `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
  - `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

## ckm:slides - nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/slides/SKILL.md`

- Skill page: [ckm-slides](../skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-slides.md)
- Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-slides`
- Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-slides/SKILL.md`
- Source: [nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/slides/SKILL.md`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/slides/SKILL.md)
- Selected ref: `v2.5.0`; commit `07f4ef3ac256`
- What it covers: Catalog summary: Create strategic HTML presentations with Chart.js, design tokens, responsive layouts, copywriting formulas, and contextual slide strategies.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Slides, When to Use, Subcommands, References (Knowledge Base), Routing. Resources: has_references.
- Notability: Included from latest release UI/UX skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-slides-skill-md`: Use the immutable source file https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/slides/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
  - `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
  - `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

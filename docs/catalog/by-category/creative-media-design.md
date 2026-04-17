# Creative, media & design

## bria-ai - Bria-AI/bria-skill `skills/bria-ai/SKILL.md`

- Skill page: [bria-ai-bria-skill-skills-bria-ai](../skills/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-bria-ai.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-bria-ai`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-bria-ai/SKILL.md`
- Source: [Bria-AI/bria-skill `skills/bria-ai/SKILL.md`](https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/bria-ai/SKILL.md)
- Selected ref: `v1.3.1`; commit `b0e107b0f466`
- What it covers: Source description: AI image generation, editing, and background removal API via Bria.ai — remove backgrounds to get transparent PNGs and cutouts, generate images from text prompts, and edit photos with natural language instructions. Also create product photography and lifestyle shots, replace or blur backgrounds, upscale resolution, restyle, and batch-generate visual assets. Use this skill whenever the user wants to remove a.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Bria — AI Image Generation, Editing & Background Removal, When to Use This Skill, What You Can Build, Setup — Authentication, Step 1: Check for existing credentials. Resources: has_references.
- Notability: Included from latest release creative media skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-bria-ai-bria-skill-skills-bria-ai-skill-md`: Use the immutable source file https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/bria-ai/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## image-utils - Bria-AI/bria-skill `skills/image-utils/SKILL.md`

- Skill page: [bria-ai-bria-skill-skills-image-utils](../skills/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-image-utils.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-image-utils`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-image-utils/SKILL.md`
- Source: [Bria-AI/bria-skill `skills/image-utils/SKILL.md`](https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/image-utils/SKILL.md)
- Selected ref: `v1.3.1`; commit `b0e107b0f466`
- What it covers: Source description: Classic image manipulation with Python Pillow - resize, crop, composite, format conversion, watermarks, brightness/contrast adjustments, and web optimization. Use this skill when post-processing AI-generated images, preparing images for web delivery, batch processing image directories, creating responsive image variants, or performing any deterministic pixel-level image operation. Works standalone or alongside.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Image Utilities, When to Use This Skill, When NOT to Use This Skill — Use `bria-ai` Instead, Quick Reference, Requirements. Resources: has_references.
- Notability: Included from latest release creative media skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-bria-ai-bria-skill-skills-image-utils-skill-md`: Use the immutable source file https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/image-utils/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## remove-background - Bria-AI/bria-skill `skills/remove-background/SKILL.md`

- Skill page: [bria-ai-bria-skill-skills-remove-background](../skills/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-remove-background.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-remove-background`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-remove-background/SKILL.md`
- Source: [Bria-AI/bria-skill `skills/remove-background/SKILL.md`](https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/remove-background/SKILL.md)
- Selected ref: `v1.3.1`; commit `b0e107b0f466`
- What it covers: Source description: Remove backgrounds from images — background removal API for transparent PNGs, cutouts, and masks. Segment foreground from background. Powered by Bria RMBG 2.0. ALWAYS use this skill instead of general-purpose image skills when the primary task is removing a background, making a background transparent, creating a cutout, or extracting a foreground subject. This is the dedicated, specialized background removal skill.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Remove Background — Transparent PNGs & Cutouts with RMBG 2.0, When to Use This Skill, When NOT to Use This Skill, Setup — Authentication, Step 1: Check for existing credentials. Resources: has_references.
- Notability: Included from latest release creative media skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-bria-ai-bria-skill-skills-remove-background-skill-md`: Use the immutable source file https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/remove-background/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## vgl - Bria-AI/bria-skill `skills/vgl/SKILL.md`

- Skill page: [bria-ai-bria-skill-skills-vgl](../skills/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-vgl.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-vgl`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-vgl/SKILL.md`
- Source: [Bria-AI/bria-skill `skills/vgl/SKILL.md`](https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/vgl/SKILL.md)
- Selected ref: `v1.3.1`; commit `b0e107b0f466`
- What it covers: Source description: Maximum control over AI image generation — write structured VGL (Visual Generation Language) JSON that explicitly controls every visual attribute. Define exact object placement, lighting direction, camera angle, lens focal length, composition, color scheme, and artistic style as deterministic JSON instead of ambiguous natural language. Use this skill when you need reproducible image generation, precise control over.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Bria VGL — Full Control Over Image Generation, Core Concept, Operation Modes, JSON Schema, 1. `short_description` (String). Resources: has_references.
- Notability: Included from latest release creative media skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-bria-ai-bria-skill-skills-vgl-skill-md`: Use the immutable source file https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/vgl/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## evolink-music - EvoLinkAI/music-generation-skill-for-openclaw `SKILL.md`

- Skill page: [evolinkai-music-generation-skill-for-openclaw](../skills/by-category/creative-media-design/creative-reference/evolinkai-music-generation-skill-for-openclaw.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/creative-reference/evolinkai-music-generation-skill-for-openclaw`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/creative-reference/evolinkai-music-generation-skill-for-openclaw/SKILL.md`
- Source: [EvoLinkAI/music-generation-skill-for-openclaw `SKILL.md`](https://github.com/EvoLinkAI/music-generation-skill-for-openclaw/blob/a37e5b6ef986c952d0d5ba57ddc6e6f0c3abd858/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `a37e5b6ef986`
- What it covers: Source description: AI music generation with Suno v4, v4.5, v5. Text-to-music, custom lyrics, instrumental, vocal control. 5 models, one API key.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Evolink Music — AI Music Generation, Setup, MCP Tools, Music Models (5, all BETA), Two Modes. Resources: has_scripts, has_references.
- Notability: Included from creative media skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-evolinkai-music-generation-skill-for-openclaw-skill-md`: Use the immutable source file https://github.com/EvoLinkAI/music-generation-skill-for-openclaw/blob/a37e5b6ef986c952d0d5ba57ddc6e6f0c3abd858/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## evolink-video - EvoLinkAI/video-generation-skill-for-openclaw `SKILL.md`

- Skill page: [evolinkai-video-generation-skill-for-openclaw](../skills/by-category/creative-media-design/creative-reference/evolinkai-video-generation-skill-for-openclaw.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/creative-reference/evolinkai-video-generation-skill-for-openclaw`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/creative-reference/evolinkai-video-generation-skill-for-openclaw/SKILL.md`
- Source: [EvoLinkAI/video-generation-skill-for-openclaw `SKILL.md`](https://github.com/EvoLinkAI/video-generation-skill-for-openclaw/blob/83723cdfa9d43eb8dd79287651f0e3e291802e90/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `83723cdfa9d4`
- What it covers: Source description: AI video generation — Sora, Kling, Veo 3, Seedance, Hailuo, WAN, Grok. Text-to-video, image-to-video, video editing. 37 models, one API key.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Evolink Video — AI Video Generation, Setup, Bridge MCP Server (recommended), MCP Tools, Video Models (37). Resources: has_scripts, has_references.
- Notability: Included from creative media skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-evolinkai-video-generation-skill-for-openclaw-skill-md`: Use the immutable source file https://github.com/EvoLinkAI/video-generation-skill-for-openclaw/blob/83723cdfa9d43eb8dd79287651f0e3e291802e90/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## ai-video-editing - Raven7979/ai-video-editing-skill `SKILL.md`

- Skill page: [raven7979-ai-video-editing-skill](../skills/by-category/creative-media-design/creative-reference/raven7979-ai-video-editing-skill.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/creative-reference/raven7979-ai-video-editing-skill`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/creative-reference/raven7979-ai-video-editing-skill/SKILL.md`
- Source: [Raven7979/ai-video-editing-skill `SKILL.md`](https://github.com/Raven7979/ai-video-editing-skill/blob/9bf0a9c3396c181dca45ee969de72bfa57602d4c/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `9bf0a9c3396c`
- What it covers: Source description: 用于 AI 口播初剪、自动剪辑、去气口、去重复、视频转字幕、按口播稿对稿。支持语义级重复判断、剪后重新转字幕并与口播稿复核，还会标出大段 NG / 试讲 / 临场发挥候选段供用户确认。支持中文和英文，默认按电脑语言自动切换，也可手动指定。中文触发词包括 AI剪辑、自动剪辑、初剪、口播初剪、去气口、视频转字幕、对稿；英文触发词包括 AI video editing、auto edit this video、video edit、rough cut、trim pauses、remove repeated takes。开始前先确认用户是否提供口播稿，以及剪辑强度选 一般 或 多点。
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: AI Video Editing, 推荐模型 / Recommended Model, 语言切换 / Language Mode, 开始前先问, 中英文唤醒词 / Trigger Phrases. Resources: has_scripts, has_assets.
- Notability: Included from creative media skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-raven7979-ai-video-editing-skill-skill-md`: Use the immutable source file https://github.com/Raven7979/ai-video-editing-skill/blob/9bf0a9c3396c181dca45ee969de72bfa57602d4c/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## blog-cover-image-cli - Varnan-Tech/opendirectory `packages/cli/skills/blog-cover-image-cli/SKILL.md`

- Skill page: [varnan-tech-opendirectory-packages-cli-skills-blog-cover-image-cli](../skills/by-category/creative-media-design/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-blog-cover-image-cli.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-blog-cover-image-cli`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-blog-cover-image-cli/SKILL.md`
- Source: [Varnan-Tech/opendirectory `packages/cli/skills/blog-cover-image-cli/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/blog-cover-image-cli/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`
- What it covers: Source description: A skill for blog-cover-image-cli
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: none observed. Resources: has_examples.
- Notability: Included from Reddit r/codex open-source Codex skills signal; GitHub SKILL.md files verified with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-varnan-tech-opendirectory-packages-cli-skills-blog-cover-image-cli-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/blog-cover-image-cli/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## article-writing - affaan-m/everything-claude-code `.agents/skills/article-writing/SKILL.md`

- Skill page: [affaan-m-everything-claude-code-agents-skills-article-writing](../skills/by-category/creative-media-design/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-article-writing.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-article-writing`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-article-writing/SKILL.md`
- Source: [affaan-m/everything-claude-code `.agents/skills/article-writing/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/article-writing/SKILL.md)
- Selected ref: `v1.10.0`; commit `846ffb75da9a`
- What it covers: Source description: Write articles, guides, blog posts, tutorials, newsletter issues, and other long-form content in a distinctive voice derived from supplied examples or brand guidance. Use when the user wants polished written content longer than a paragraph, especially when voice consistency, structure, and credibility matter.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Article Writing, When to Activate, Core Rules, Voice Handling, Banned Patterns. Resources: has_agents_metadata.
- Notability: Included from selected repository structure reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Assigned benchmark scenarios:
  - `skill-proof-affaan-m-everything-claude-code-agents-skills-article-writing-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/article-writing/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## brand-voice - affaan-m/everything-claude-code `.agents/skills/brand-voice/SKILL.md`

- Skill page: [affaan-m-everything-claude-code-agents-skills-brand-voice](../skills/by-category/creative-media-design/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-brand-voice.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-brand-voice`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-brand-voice/SKILL.md`
- Source: [affaan-m/everything-claude-code `.agents/skills/brand-voice/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/brand-voice/SKILL.md)
- Selected ref: `v1.10.0`; commit `846ffb75da9a`
- What it covers: Source description: Build a source-derived writing style profile from real posts, essays, launch notes, docs, or site copy, then reuse that profile across content, outreach, and social workflows. Use when the user wants voice consistency without generic AI writing tropes.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Brand Voice, When to Activate, Source Priority, Collection Workflow, What to Extract. Resources: has_references.
- Notability: Included from selected repository structure reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-affaan-m-everything-claude-code-agents-skills-brand-voice-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/brand-voice/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## fal-ai-media - affaan-m/everything-claude-code `.agents/skills/fal-ai-media/SKILL.md`

- Skill page: [affaan-m-everything-claude-code-agents-skills-fal-ai-media](../skills/by-category/creative-media-design/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-fal-ai-media.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-fal-ai-media`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-fal-ai-media/SKILL.md`
- Source: [affaan-m/everything-claude-code `.agents/skills/fal-ai-media/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/fal-ai-media/SKILL.md)
- Selected ref: `v1.10.0`; commit `846ffb75da9a`
- What it covers: Source description: Unified media generation via fal.ai MCP — image, video, and audio. Covers text-to-image (Nano Banana), text/image-to-video (Seedance, Kling, Veo 3), text-to-speech (CSM-1B), and video-to-audio (ThinkSound). Use when the user wants to generate images, videos, or audio with AI.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: fal.ai Media Generation, When to Activate, MCP Requirement, MCP Tools, Image Generation. Resources: has_agents_metadata.
- Notability: Included from selected repository structure reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Assigned benchmark scenarios:
  - `skill-proof-affaan-m-everything-claude-code-agents-skills-fal-ai-media-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/fal-ai-media/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## algorithmic-art - anthropics/skills `skills/algorithmic-art/SKILL.md`

- Skill page: [anthropics-skills-skills-algorithmic-art](../skills/by-category/creative-media-design/official-reference/anthropics-skills-skills-algorithmic-art.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/official-reference/anthropics-skills-skills-algorithmic-art`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/official-reference/anthropics-skills-skills-algorithmic-art/SKILL.md`
- Source: [anthropics/skills `skills/algorithmic-art/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/algorithmic-art/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`
- What it covers: Source description: Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use this when users request creating art using code, generative art, algorithmic art, flow fields, or particle systems. Create original algorithmic art rather than copying existing artists' work to avoid copyright violations.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: ALGORITHMIC PHILOSOPHY CREATION, THE CRITICAL UNDERSTANDING, HOW TO GENERATE AN ALGORITHMIC PHILOSOPHY, PHILOSOPHY EXAMPLES, ESSENTIAL PRINCIPLES. Resources: none observed.
- Notability: Included from official skill reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-anthropics-skills-skills-algorithmic-art-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/algorithmic-art/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## brand-guidelines - anthropics/skills `skills/brand-guidelines/SKILL.md`

- Skill page: [anthropics-skills-skills-brand-guidelines](../skills/by-category/creative-media-design/official-reference/anthropics-skills-skills-brand-guidelines.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/official-reference/anthropics-skills-skills-brand-guidelines`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/official-reference/anthropics-skills-skills-brand-guidelines/SKILL.md`
- Source: [anthropics/skills `skills/brand-guidelines/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/brand-guidelines/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`
- What it covers: Source description: Applies Anthropic's official brand colors and typography to any sort of artifact that may benefit from having Anthropic's look-and-feel. Use it when brand colors or style guidelines, visual formatting, or company design standards apply.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Anthropic Brand Styling, Overview, Brand Guidelines, Colors, Typography. Resources: none observed.
- Notability: Included from official skill reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-anthropics-skills-skills-brand-guidelines-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/brand-guidelines/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## slack-gif-creator - anthropics/skills `skills/slack-gif-creator/SKILL.md`

- Skill page: [anthropics-skills-skills-slack-gif-creator](../skills/by-category/creative-media-design/official-reference/anthropics-skills-skills-slack-gif-creator.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/official-reference/anthropics-skills-skills-slack-gif-creator`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/official-reference/anthropics-skills-skills-slack-gif-creator/SKILL.md`
- Source: [anthropics/skills `skills/slack-gif-creator/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/slack-gif-creator/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`
- What it covers: Source description: Knowledge and utilities for creating animated GIFs optimized for Slack. Provides constraints, validation tools, and animation concepts. Use when users request animated GIFs for Slack like "make me a GIF of X doing Y for Slack."
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Slack GIF Creator, Slack Requirements, Core Workflow, 1. Create builder, 2. Generate frames. Resources: none observed.
- Notability: Included from official skill reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-anthropics-skills-skills-slack-gif-creator-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/slack-gif-creator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## amazon-product-api-skill - browser-act/skills `amazon-product-api-skill/SKILL.md`

- Skill page: [browser-act-skills-amazon-product-api-skill](../skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-amazon-product-api-skill.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-amazon-product-api-skill`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/browser-automation-reference/browser-act-skills-amazon-product-api-skill/SKILL.md`
- Source: [browser-act/skills `amazon-product-api-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/amazon-product-api-skill/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `749ed52133b8`
- What it covers: Source description: This skill helps users extract structured product listings from Amazon, including titles, ASINs, prices, ratings, and specifications. Use this skill when users want to search for products on Amazon, find the best selling brand products, track price changes for items, get a list of categories with high ratings, compare different brand products on Amazon, extract Amazon product data for market research, look for.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Amazon Product Search Skill, 📖 Introduction, ✨ Features, 🔑 API Key Setup, 🛠️ Input Parameters. Resources: has_scripts.
- Notability: Included from browser and web automation skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-browser-act-skills-amazon-product-api-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/amazon-product-api-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## google-image-api-skill - browser-act/skills `google-image-api-skill/SKILL.md`

- Skill page: [browser-act-skills-google-image-api-skill](../skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-google-image-api-skill.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-google-image-api-skill`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/browser-automation-reference/browser-act-skills-google-image-api-skill/SKILL.md`
- Source: [browser-act/skills `google-image-api-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/google-image-api-skill/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `749ed52133b8`
- What it covers: Source description: This skill helps users automatically extract structured image data from Google Images via BrowserAct API. Agent should proactively apply this skill when users express needs like finding images for specific keywords, gathering product style images for competitors, building visual datasets at scale, scanning visual search results for market research, tracking localized image trends by country, compiling related image.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Google Image API Automation Skill, 📖 Introduction, ✨ Features, 🔑 API Key Guide, 🛠️ Input Parameters. Resources: has_scripts.
- Notability: Included from browser and web automation skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-browser-act-skills-google-image-api-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/google-image-api-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## social-media-finder-skill - browser-act/skills `social-media-finder-skill/SKILL.md`

- Skill page: [browser-act-skills-social-media-finder-skill](../skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-social-media-finder-skill.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-social-media-finder-skill`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/browser-automation-reference/browser-act-skills-social-media-finder-skill/SKILL.md`
- Source: [browser-act/skills `social-media-finder-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/social-media-finder-skill/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `749ed52133b8`
- What it covers: Source description: This skill helps users automatically find social media profiles across platforms like Facebook, Twitter, Instagram, LinkedIn, etc. using the BrowserAct API. Agent should proactively apply this skill when users express needs like finding someone's social media accounts, discovering a brand's social media presence, tracking down social profiles of job candidates, finding contact info for sales prospects, researching.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Social Media Finder Skill, 📖 Brief, ✨ Features, 🔑 API Key Setup, 🛠️ Input Parameters. Resources: has_scripts.
- Notability: Included from browser and web automation skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-browser-act-skills-social-media-finder-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/social-media-finder-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## youtube-batch-transcript-extractor-api-skill - browser-act/skills `youtube-batch-transcript-extractor-api-skill/SKILL.md`

- Skill page: [browser-act-skills-youtube-batch-transcript-extractor-api-skill](../skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-batch-transcript-extractor-api-skill.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-batch-transcript-extractor-api-skill`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-batch-transcript-extractor-api-skill/SKILL.md`
- Source: [browser-act/skills `youtube-batch-transcript-extractor-api-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-batch-transcript-extractor-api-skill/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `749ed52133b8`
- What it covers: Source description: This skill helps users automatically extract YouTube video transcripts and metadata in batch via the BrowserAct API. The Agent should proactively apply this skill when users express needs like batch extract full transcripts from YouTube videos for specific keywords, scrape YouTube subtitles for a list of videos, get batch video metadata and likes counts for analysis, automate YouTube search and subtitle extraction,.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: YouTube Batch Transcript Extractor API Skill, 📖 Introduction, ✨ Features, 🔑 API Key Guide Process, 🛠️ Input Parameters. Resources: has_scripts.
- Notability: Included from browser and web automation skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-browser-act-skills-youtube-batch-transcript-extractor-api-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-batch-transcript-extractor-api-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## youtube-comments-api-skill - browser-act/skills `youtube-comments-api-skill/SKILL.md`

- Skill page: [browser-act-skills-youtube-comments-api-skill](../skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-comments-api-skill.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-comments-api-skill`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-comments-api-skill/SKILL.md`
- Source: [browser-act/skills `youtube-comments-api-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-comments-api-skill/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `749ed52133b8`
- What it covers: Source description: This skill helps users extract structured video list data and comment data from YouTube using the BrowserAct API. The Agent should proactively apply this skill when users request searching for YouTube videos and their comments, analyzing viewer sentiment for a specific video topic, gathering audience feedback on AI or automation, extracting a list of top videos and their viewer reactions, compiling YouTube video.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: YouTube Comments API Automation Skill, 📖 Introduction, ✨ Features, 🔑 API Key Guidance Process, 🛠️ Input Parameters. Resources: has_scripts.
- Notability: Included from browser and web automation skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-browser-act-skills-youtube-comments-api-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-comments-api-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## youtube-transcript-analysis-api-skill - browser-act/skills `youtube-transcript-analysis-api-skill/SKILL.md`

- Skill page: [browser-act-skills-youtube-transcript-analysis-api-skill](../skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-transcript-analysis-api-skill.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-transcript-analysis-api-skill`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-transcript-analysis-api-skill/SKILL.md`
- Source: [browser-act/skills `youtube-transcript-analysis-api-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-transcript-analysis-api-skill/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `749ed52133b8`
- What it covers: Source description: This skill helps users extract YouTube video transcripts and perform deep competitive analysis on the content. Agent should proactively apply this skill when users express needs like analyze YouTube video content strategy, perform competitive video content analysis, extract and analyze YouTube subtitles for marketing insights, understand competitor value propositions from their videos, identify target audience from.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: YouTube Transcript Analysis API Skill, 📖 Brief, ✨ Features, 🔑 API Key Guide, 🛠️ Input Parameters. Resources: has_scripts.
- Notability: Included from browser and web automation skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-browser-act-skills-youtube-transcript-analysis-api-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-transcript-analysis-api-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## youtube-transcript-extractor-api-skill - browser-act/skills `youtube-transcript-extractor-api-skill/SKILL.md`

- Skill page: [browser-act-skills-youtube-transcript-extractor-api-skill](../skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-transcript-extractor-api-skill.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-transcript-extractor-api-skill`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-transcript-extractor-api-skill/SKILL.md`
- Source: [browser-act/skills `youtube-transcript-extractor-api-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-transcript-extractor-api-skill/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `749ed52133b8`
- What it covers: Source description: This skill helps users automatically extract YouTube video transcripts and metadata via the BrowserAct API. The Agent should proactively apply this skill when users express needs like extracting full transcript from a specific YouTube video, getting subtitles and metadata for video content analysis, gathering video titles and likes counts, summarizing YouTube videos without watching them, collecting channel details.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: YouTube Transcript Extractor API Skill, 📖 Introduction, ✨ Features, 🔑 API Key Setup, 🛠️ Input Parameters. Resources: has_scripts.
- Notability: Included from browser and web automation skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-browser-act-skills-youtube-transcript-extractor-api-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-transcript-extractor-api-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## youtube-video-api-skill - browser-act/skills `youtube-video-api-skill/SKILL.md`

- Skill page: [browser-act-skills-youtube-video-api-skill](../skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-video-api-skill.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-video-api-skill`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-video-api-skill/SKILL.md`
- Source: [browser-act/skills `youtube-video-api-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-video-api-skill/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `749ed52133b8`
- What it covers: Source description: This skill helps users automatically extract channel-level and video detail data from a specific YouTube channel via BrowserAct API. Agent should proactively apply this skill when users express needs like extracting channel video data, getting latest or popular videos from a YouTube channel, tracking competitor channel content, extracting video metrics such as views likes comments, retrieving subscriber count and.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: YouTube Video API Skill, 📖 Introduction, ✨ Features, 🔑 API Key Guidance Flow, 🛠️ Input Parameters. Resources: has_scripts.
- Notability: Included from browser and web automation skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-browser-act-skills-youtube-video-api-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-video-api-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## ai-graphic-design - designrique/ai-graphic-design-skill `SKILL.md`

- Skill page: [designrique-ai-graphic-design-skill](../skills/by-category/creative-media-design/creative-reference/designrique-ai-graphic-design-skill.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/creative-reference/designrique-ai-graphic-design-skill`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/creative-reference/designrique-ai-graphic-design-skill/SKILL.md`
- Source: [designrique/ai-graphic-design-skill `SKILL.md`](https://github.com/designrique/ai-graphic-design-skill/blob/7d9d03b290f076e51d0b574659cda2ca9347651e/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `7d9d03b290f0`
- What it covers: Source description: Guide for creating logos, brand identities, and visual assets using AI tools — covers tool selection, prompt engineering, vectorization pipelines, mockups, automation, and IP safety.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: AI Graphic Design — Logomarcas e Identidades Visuais com IA, When to Trigger, 1. Tool Selection Matrix, 2. Briefing Frameworks, Framework RCAO (para prompts de LLM). Resources: none observed.
- Notability: Included from creative media skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-designrique-ai-graphic-design-skill-skill-md`: Use the immutable source file https://github.com/designrique/ai-graphic-design-skill/blob/7d9d03b290f076e51d0b574659cda2ca9347651e/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## marketing-designer - fruteroclub/marketing-designer `SKILL.md`

- Skill page: [fruteroclub-marketing-designer](../skills/by-category/creative-media-design/creative-reference/fruteroclub-marketing-designer.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/creative-reference/fruteroclub-marketing-designer`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/creative-reference/fruteroclub-marketing-designer/SKILL.md`
- Source: [fruteroclub/marketing-designer `SKILL.md`](https://github.com/fruteroclub/marketing-designer/blob/c8f65f94fc3a1b99bafcfe334d3fae3347d94433/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `c8f65f94fc3a`
- What it covers: Source description: Expert marketing creative-strategic skill combining Peggy Olson's bold creative intuition with modern data-driven precision. Use for: (1) Campaign development and creative concepting, (2) Copy and messaging optimization, (3) Proposal and pitch deck improvement, (4) Brand voice and positioning, (5) Marketing strategy and measurement design, (6) Creative brief writing and review. Triggers on: "improve copy",.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Marketing Designer, Core Workflow: Insight-to-Impact Loop, 1. DISCOVER, 2. DEFINE, 3. IDEATE. Resources: has_references.
- Notability: Included from creative media skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-fruteroclub-marketing-designer-skill-md`: Use the immutable source file https://github.com/fruteroclub/marketing-designer/blob/c8f65f94fc3a1b99bafcfe334d3fae3347d94433/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## image-generation - guinacio/claude-image-gen `skills/image-generation/SKILL.md`

- Skill page: [guinacio-claude-image-gen-skills-image-generation](../skills/by-category/creative-media-design/latest-release-creative/guinacio-claude-image-gen-skills-image-generation.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/guinacio-claude-image-gen-skills-image-generation`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/guinacio-claude-image-gen-skills-image-generation/SKILL.md`
- Source: [guinacio/claude-image-gen `skills/image-generation/SKILL.md`](https://github.com/guinacio/claude-image-gen/blob/6f25d226f906db0420b2ceaa51f32de253eb2f22/skills/image-generation/SKILL.md)
- Selected ref: `1.0.2`; commit `6f25d226f906`
- What it covers: Source description: Generates professional AI images using Google Gemini. ALWAYS invoke this skill when building websites, landing pages, slide decks, presentations, or any task needing visual content. Invoke IMMEDIATELY when you detect image needs - don't wait for the user to ask. This skill handles prompt optimization and aspect ratio selection.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Image Generation Skill, When to Invoke This Skill, Using the CLI, Parameters, Output. Resources: has_references.
- Notability: Included from latest release image generation skill with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-guinacio-claude-image-gen-skills-image-generation-skill-md`: Use the immutable source file https://github.com/guinacio/claude-image-gen/blob/6f25d226f906db0420b2ceaa51f32de253eb2f22/skills/image-generation/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## ckm:banner-design - nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/banner-design/SKILL.md`

- Skill page: [nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-banner-design](../skills/by-category/creative-media-design/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-banner-design.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-banner-design`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-banner-design/SKILL.md`
- Source: [nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/banner-design/SKILL.md`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/banner-design/SKILL.md)
- Selected ref: `v2.5.0`; commit `07f4ef3ac256`
- What it covers: Source description: Design banners for social media, ads, website heroes, creative assets, and print. Multiple art direction options with AI-generated visuals. Actions: design, create, generate banner. Platforms: Facebook, Twitter/X, LinkedIn, YouTube, Instagram, Google Display, website hero, print. Styles: minimalist, gradient, bold typography, photo-based, illustrated, geometric, retro, glassmorphism, 3D, neon, duotone, editorial,.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Banner Design - Multi-Format Creative Banner System, When to Activate, Workflow, Step 1: Gather Requirements (AskUserQuestion), Step 2: Research & Art Direction. Resources: has_references.
- Notability: Included from latest release UI/UX skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-banner-design-skill-md`: Use the immutable source file https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/banner-design/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## ckm:design-system - nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/design-system/SKILL.md`

- Skill page: [nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design-system](../skills/by-category/creative-media-design/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design-system.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design-system`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design-system/SKILL.md`
- Source: [nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/design-system/SKILL.md`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/design-system/SKILL.md)
- Selected ref: `v2.5.0`; commit `07f4ef3ac256`
- What it covers: Source description: Token architecture, component specifications, and slide generation. Three-layer tokens (primitive→semantic→component), CSS variables, spacing/typography scales, component specs, strategic slide creation. Use for design tokens, systematic design, brand-compliant presentations.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Design System, When to Use, Token Architecture, Three-Layer Structure, Quick Start. Resources: has_scripts, has_references.
- Notability: Included from latest release UI/UX skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design-system-skill-md`: Use the immutable source file https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/design-system/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## ckm:ui-styling - nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/ui-styling/SKILL.md`

- Skill page: [nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-ui-styling](../skills/by-category/creative-media-design/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-ui-styling.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-ui-styling`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-ui-styling/SKILL.md`
- Source: [nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/ui-styling/SKILL.md`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/ui-styling/SKILL.md)
- Selected ref: `v2.5.0`; commit `07f4ef3ac256`
- What it covers: Source description: Create beautiful, accessible user interfaces with shadcn/ui components (built on Radix UI + Tailwind), Tailwind CSS utility-first styling, and canvas-based visual designs. Use when building user interfaces, implementing design systems, creating responsive layouts, adding accessible components (dialogs, dropdowns, forms, tables), customizing themes and colors, implementing dark mode, generating visual designs and.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: UI Styling Skill, Reference, When to Use This Skill, Core Stack, Component Layer: shadcn/ui. Resources: has_scripts, has_references.
- Notability: Included from latest release UI/UX skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-ui-styling-skill-md`: Use the immutable source file https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/ui-styling/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## svg-animations - supermemoryai/skills `svg-animations/SKILL.md`

- Skill page: [supermemoryai-skills-svg-animations](../skills/by-category/creative-media-design/reddit-verified-creative-skill/supermemoryai-skills-svg-animations.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/reddit-verified-creative-skill/supermemoryai-skills-svg-animations`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/reddit-verified-creative-skill/supermemoryai-skills-svg-animations/SKILL.md`
- Source: [supermemoryai/skills `svg-animations/SKILL.md`](https://github.com/supermemoryai/skills/blob/10d5e16780b446c5ce58968bcde528766699cdf2/svg-animations/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `10d5e16780b4`
- What it covers: Source description: Create beautiful, performant SVG animations and illustrations. Use this skill when the user asks to create SVG graphics, icons, illustrations, animated logos, path animations, morphing shapes, loading spinners, or any animated SVG content. Covers SMIL animations, CSS-driven SVG animation, path drawing effects, shape morphing, motion paths, gradients, masks, and filters.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: SVG Fundamentals, Coordinate System, Shape Primitives, The `<path>` Element — The Power Tool, Grouping and Transforms. Resources: none observed.
- Notability: Included from Reddit r/codex linked skill; GitHub SKILL.md verified with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-supermemoryai-skills-svg-animations-skill-md`: Use the immutable source file https://github.com/supermemoryai/skills/blob/10d5e16780b446c5ce58968bcde528766699cdf2/svg-animations/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

## agent-media - yuvalsuede/agent-media-skill `SKILL.md`

- Skill page: [yuvalsuede-agent-media-skill](../skills/by-category/creative-media-design/creative-reference/yuvalsuede-agent-media-skill.md)
- Mirrored skill: `included/skills/by-category/creative-media-design/creative-reference/yuvalsuede-agent-media-skill`
- Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/creative-reference/yuvalsuede-agent-media-skill/SKILL.md`
- Source: [yuvalsuede/agent-media-skill `SKILL.md`](https://github.com/yuvalsuede/agent-media-skill/blob/c37c209942bad44588f4d93b744473d733f95e6d/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `c37c209942ba`
- What it covers: Source description: AI UGC video production from the terminal using the `agent-media` CLI.
- Agent use: Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: agent-media — AI UGC Video Production & Media Generation, MANDATORY RULES — READ BEFORE EVERY COMMAND, Rule 1: ALWAYS use `--actor` — PICK A RANDOM ONE, Rule 2: ALWAYS count words — 2.5 words per second, Rule 3: SaaS reviews MUST have screenshots. Resources: none observed.
- Notability: Included from creative media skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-yuvalsuede-agent-media-skill-skill-md`: Use the immutable source file https://github.com/yuvalsuede/agent-media-skill/blob/c37c209942bad44588f4d93b744473d733f95e6d/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
  - `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
  - `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

<p align="center">
  <img src="./assets/logo.svg" alt="AI Video Editing Skill Logo" width="140" />
</p>

<h1 align="center">AI Video Editing Skill</h1>

<p align="center">
  Token-efficient rough cuts for talking-head videos
</p>

<p align="center">
  <a href="#english">English</a> · <a href="#中文说明">中文说明</a>
</p>

<p align="center">
  <img alt="workflow" src="https://img.shields.io/badge/workflow-speech--to--text%20first-0f766e">
  <img alt="focus" src="https://img.shields.io/badge/focus-token%20efficient-c2410c">
  <img alt="best for" src="https://img.shields.io/badge/best%20for-talking--head%20editing-1d4ed8">
  <img alt="model" src="https://img.shields.io/badge/recommended-GPT5.4-111827">
</p>

## English

`AI Video Editing Skill` is an automatic rough-cut workflow built for talking-head videos such as commentary, explainers, educational clips, and creator monologues.

> Recommended model: `GPT5.4`

Its goal is not full visual understanding. The goal is to solve the highest-value editing problems for spoken videos while keeping token usage low:

- repeated takes
- immediate restarts
- unnecessary pauses and breathing gaps
- subtitle regeneration after editing
- script comparison when a prepared script is available

### Design Focus

This skill deliberately avoids heavy visual analysis. It does not rely on frame-by-frame video understanding.

Instead, it uses a lightweight workflow:

1. transcribe the video into subtitles and text
2. detect semantic repetition, restarts, and likely rehearsal takes
3. create a rough cut based on the chosen editing intensity
4. re-transcribe the edited video
5. compare the edited transcript against the provided script if one exists
6. flag long likely NG / rehearsal / improvised sections for user confirmation

### Quick Start

```bash
bash scripts/run_ai_video_edit.sh "/path/to/video.mp4" --intensity normal
```

With a script:

```bash
bash scripts/run_ai_video_edit.sh "/path/to/video.mp4" --script "/path/to/script.docx" --intensity normal
```

### Installation

1. Clone or download this repository.
2. Make sure `python3` is installed.
3. Install `ffmpeg` and `ffprobe`:
   - macOS: `brew install ffmpeg`
   - Windows: `winget install Gyan.FFmpeg`
   - or Windows with Chocolatey: `choco install ffmpeg`
4. Place the skill folder in your local skills directory, or load it from this repository in your agent environment.
5. On first run, the script will automatically create a local `.venv` and install `faster-whisper`.

Minimal command example:

```bash
bash scripts/run_ai_video_edit.sh "/path/to/video.mp4" --intensity normal
```

### How To Use

The most common workflow is to give the agent the video path first, then provide two more pieces of information:

1. whether a prepared script is available
2. whether the pause-cutting intensity should be `normal` or `more`

Typical workflow:

1. provide the video file path
2. if available, provide the script as `txt / md / docx` or paste the text directly
3. choose the editing intensity:
   - `normal`
   - `more`
4. let the agent generate the rough cut
5. review the exported video, subtitles, and report
6. if the system finds long likely NG / rehearsal / improvised sections, confirm whether they should also be removed

### English Trigger Phrases

Common English prompts:

- `AI video editing`
- `auto edit this video`
- `video edit`
- `rough cut`
- `rough cut this talking-head video`
- `remove repeated takes`
- `trim pauses`
- `turn this video into subtitles`
- `compare the video against the script`
- `edit this video using the script`
- `clean up this monologue video`

### Why this approach

- Token-efficient: avoids costly vision-first multimodal processing
- Better fit for talking-head editing: most issues are verbal, not visual
- Easy to scale: suitable for batch processing similar creator videos
- Better with a script: when a script is provided, the system can more reliably keep the better take and detect suspicious cuts

### Best Use Cases

- rough cuts for talking-head videos
- explainer content
- educational creator videos
- commentary and voice-led short videos
- teams that need fast first-pass editing plus subtitle verification

### Not ideal for direct automatic cutting

- multi-person interviews
- vlogs or documentaries that depend heavily on visuals
- cinematic edits requiring facial, gesture, and shot-language judgment

### Compatible Tools / Runtime Environments

This skill is essentially a `SKILL.md + local scripts` workflow, so it fits best in agent environments that can execute local shell, Python, and ffmpeg commands.

Reasonable compatibility notes:

- Codex / Codex Desktop
- OpenCode
- Claude Code
- Antigravity
- local agent environments that support Skills or `SKILL.md`-based workflows

About `OpenClaw`:

If `OpenClaw` can:

- read `SKILL.md`
- execute local `bash / python / ffmpeg`
- pass user-provided file paths into the workflow

then this skill should be adaptable to `OpenClaw`.

More precisely:

- `Codex / Codex Desktop`: direct fit or very small adjustments
- `Claude Code`: direct fit or very small adjustments
- `OpenCode`: usually adaptable if local script execution and file path passing are supported
- `Antigravity`: usually adaptable if it supports skill-style instructions plus local command execution
- `OpenClaw`: likely compatible, but whether it works out of the box depends on its support for skill packaging and local script execution

As a practical rule, an agent environment is a good fit for this skill if it can do all of the following:

- read a skill instruction file such as `SKILL.md`
- run local `bash`
- run local `python`
- access local `ffmpeg / ffprobe`
- pass user-provided video and script paths into the workflow

### First-run Dependencies

- Automatically creates a local `.venv`
- Automatically installs `faster-whisper`
- Does not auto-install system-level `ffmpeg / ffprobe`
- If `ffmpeg` or `ffprobe` is missing, the script now prints install guidance instead of failing silently
- Built-in install hints:
  - macOS: `brew install ffmpeg`
  - Windows: `winget install Gyan.FFmpeg` or `choco install ffmpeg`

### Outputs

- raw transcript: `.raw.txt`
- cleaned transcript: `.txt`
- raw subtitles: `.raw.srt`
- rough-cut video: `.roughcut.mp4`
- re-transcribed rough-cut text: `.roughcut.raw.txt`
- cleaned rough-cut transcript: `.roughcut.txt`
- rough-cut subtitles: `.roughcut.srt`
- edit report: `.roughcut.json`

## 中文说明

`AI Video Editing Skill` 是一个面向口播视频的自动初剪技能，重点场景是单人口播、讲解、解说、知识分享类视频。

> 推荐模型：`GPT5.4`

它的核心目标不是做复杂视频理解，而是在尽量少消耗 token 的前提下，把真正影响口播节奏的问题先解决掉：

- 重复重说
- 临时重讲
- 多余气口和停顿
- 剪后字幕复核
- 与口播稿比对

### 设计重点

这个技能刻意不依赖视觉识别，不走“逐帧看视频”的重型路线。

它主要基于以下工作流：

1. 先把视频转成字幕和转写文本
2. 基于语义相似度识别相邻重复、重说和试讲
3. 按用户选择的剪辑强度进行口播初剪
4. 初剪后重新转字幕
5. 如果用户提供了口播稿，再把剪后字幕和口播稿重新比对
6. 标出疑似大段 NG / 试讲 / 临场发挥，交给用户确认是否继续删

### 快速开始

```bash
bash scripts/run_ai_video_edit.sh "/path/to/video.mp4" --intensity normal
```

如果有口播稿：

```bash
bash scripts/run_ai_video_edit.sh "/path/to/video.mp4" --script "/path/to/script.docx" --intensity normal
```

### 安装方式

1. 克隆或下载这个仓库。
2. 确保机器上已经安装 `python3`。
3. 安装 `ffmpeg` 和 `ffprobe`：
   - macOS：`brew install ffmpeg`
   - Windows：`winget install Gyan.FFmpeg`
   - 或 Windows + Chocolatey：`choco install ffmpeg`
4. 把这个 skill 目录放到你的本地 skills 目录里，或者在你的 agent 环境中直接从这个仓库加载。
5. 首次运行时，脚本会自动创建本地 `.venv` 并安装 `faster-whisper`。

最小运行示例：

```bash
bash scripts/run_ai_video_edit.sh "/path/to/video.mp4" --intensity normal
```

### 怎么使用

最常见的使用方式是，先把视频路径发给智能体，再补两个信息：

1. 有没有口播稿
2. 气口剪辑强度选 `一般` 还是 `多点`

典型使用流程：

1. 提供视频文件路径
2. 如有口播稿，再提供 `txt / md / docx` 或直接粘贴文本
3. 选择剪辑强度：
   - `一般`
   - `多点`
4. 智能体执行初剪
5. 输出初剪视频、字幕、报告
6. 如果检测到大段疑似 NG / 试讲 / 临场发挥，再由用户确认是否继续删

### 中文唤醒词

可直接触发这类技能的常见说法：

- `AI剪辑`
- `自动剪辑`
- `初剪`
- `口播初剪`
- `去气口`
- `剪掉重复`
- `视频转字幕`
- `对稿`
- `按口播稿剪辑`
- `帮我粗剪这个口播视频`

### 为什么这样做

- 更省 token：不依赖视觉识别，不做高成本多模态逐帧分析
- 更适合口播：口播问题大多出在“说法重复、节奏拖沓、重讲、气口”而不是画面内容
- 更容易批量化：同类口播视频可以快速统一处理
- 有稿效果更好：如果提供口播稿，系统能更稳地判断该保留哪一句、哪里可能误剪

### 适用场景

- 口播视频初剪
- 自媒体讲解视频
- 知识分享短视频
- 解说类出镜素材
- 需要快速做粗剪和字幕复核的内容团队

### 不适合直接硬剪的场景

- 多人物访谈
- 强依赖画面信息的 vlog / 纪录片 / 剧情内容
- 需要镜头语言、表情和动作判断的复杂剪辑

### 适用软件 / 兼容环境

这个技能本质上是一个 `SKILL.md + 本地脚本` 的工作流，因此最适合能直接调用本地 shell / Python / ffmpeg 的智能体环境。

当前可写进说明的适用范围：

- Codex / Codex Desktop
- OpenCode
- Claude Code
- Antigravity
- 支持 Skills / SKILL.md 机制的本地 AI Agent 工作流

关于 `OpenClaw`：

- 如果 `OpenClaw` 支持读取 `SKILL.md`
- 并且可以调用本地 `bash / python / ffmpeg`
- 也支持把用户文件路径传给技能脚本

那么这套技能理论上可以接入 `OpenClaw`。

更准确地说：

- `Codex / Codex Desktop`：可直接使用或少量调整后使用
- `Claude Code`：可直接使用或少量调整后使用
- `OpenCode`：如果支持本地脚本调用和文件路径传递，通常可以适配
- `Antigravity`：如果支持技能说明文件和本地命令执行，通常可以适配
- `OpenClaw`：大概率可以适配，但是否“开箱即用”取决于它对技能包格式和本地脚本执行的支持程度

判断一个智能体环境是否适合接入这套技能，可以看它是否满足这几个条件：

- 能读取技能说明文件，例如 `SKILL.md`
- 能执行本地 `bash`
- 能执行本地 `python`
- 本机可用 `ffmpeg / ffprobe`
- 能把用户提供的视频路径和口播稿路径传给脚本

### 首次运行依赖

- 会自动创建本地 `.venv`
- 会自动安装 `faster-whisper`
- 不会自动安装系统级 `ffmpeg / ffprobe`
- 如果缺少 `ffmpeg` 或 `ffprobe`，脚本会直接给出安装提示，不会无提示失败
- 当前内置安装提示：
  - macOS：`brew install ffmpeg`
  - Windows：`winget install Gyan.FFmpeg` 或 `choco install ffmpeg`

### 输出内容

- 原始转写：`.raw.txt`
- 校对稿：`.txt`
- 原始字幕：`.raw.srt`
- 初剪视频：`.roughcut.mp4`
- 初剪后重新转写：`.roughcut.raw.txt`
- 初剪后校对稿：`.roughcut.txt`
- 初剪后字幕：`.roughcut.srt`
- 剪辑报告：`.roughcut.json`

---

## 支持作者

如果这个技能对你有帮助，欢迎随手支持一下：

![支持作者](./assets/support-author-banner.jpg)

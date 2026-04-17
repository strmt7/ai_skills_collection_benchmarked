from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import subprocess
import zipfile
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable


PUNCT_RE = re.compile(r"[，。！？、；：“”‘’（）()《》【】\[\]\-—…,.!?:;\"'\s]+")
FILLER_RE = re.compile(r"(就是|然后|那个|这个|呃|嗯|啊)")
SUPPORTED_UI_LOCALES = {"zh", "en"}
I18N = {
    "zh": {
        "argparse_description": "AI 口播视频自动剪辑",
        "arg_video": "视频路径",
        "arg_script": "可选口播稿路径：txt/md/docx",
        "arg_ui_locale": "界面语言：auto/zh/en，默认按电脑语言自动切换",
        "missing_module": "缺少 faster-whisper，请先安装。",
        "unsupported_script": "不支持的口播稿格式: {suffix}",
        "script_compare_notice": "视频内容与口播稿存在明显偏差，建议人工复核是否拿错稿件或是否存在大段临场发挥。",
        "ng_reason": "这一大段与口播稿匹配度偏低，可能是临场发挥、试讲或废段，建议先问用户是否保留。",
        "repeat_reason": "相邻两段语义高度接近，疑似重讲/NG 后重说。",
        "review_question": "如果 large_ng_candidates 不为空，先问用户这些大段疑似 NG / 试讲 / 临场发挥是否要剪掉。",
        "keep_later": "later",
        "keep_review": "review",
        "keep_ask_user": "ask_user",
    },
    "en": {
        "argparse_description": "AI video editing for talking-head videos",
        "arg_video": "Video path",
        "arg_script": "Optional script path: txt/md/docx",
        "arg_ui_locale": "UI locale: auto/zh/en. Defaults to the system language.",
        "missing_module": "faster-whisper is missing. Install it first.",
        "unsupported_script": "Unsupported script format: {suffix}",
        "script_compare_notice": "The video content differs noticeably from the provided script. Please verify whether the script is correct or whether there is a large improvised section.",
        "ng_reason": "This long section has a low match with the provided script. It may be an improvised take, rehearsal, or discardable NG section. Ask the user before removing it.",
        "repeat_reason": "Two adjacent sections are semantically very close, likely a restart or repeated take.",
        "review_question": "If large_ng_candidates is not empty, ask the user whether these likely NG / rehearsal / improvised sections should also be removed.",
        "keep_later": "later",
        "keep_review": "review",
        "keep_ask_user": "ask_user",
    },
}


@dataclass
class Segment:
    start: float
    end: float
    text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=I18N["en"]["argparse_description"])
    parser.add_argument("video", help=I18N["en"]["arg_video"])
    parser.add_argument("--script", default="", help=I18N["en"]["arg_script"])
    parser.add_argument("--language", default="zh")
    parser.add_argument("--model", default="tiny")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--intensity", choices=["normal", "more"], default="normal")
    parser.add_argument("--ui-locale", choices=["auto", "zh", "en"], default="auto", help=I18N["en"]["arg_ui_locale"])
    return parser.parse_args()


def resolve_ui_locale(requested: str) -> str:
    if requested in SUPPORTED_UI_LOCALES:
        return requested
    locale_value = (
        os.environ.get("LC_ALL")
        or os.environ.get("LC_MESSAGES")
        or os.environ.get("LANG")
        or ""
    ).lower()
    if locale_value.startswith("zh"):
        return "zh"
    return "en"


def tr(ui_locale: str, key: str, **kwargs: object) -> str:
    template = I18N[ui_locale][key]
    return template.format(**kwargs)


def load_whisper_model_class():
    try:
        module = importlib.import_module("faster_whisper")
        return module.WhisperModel
    except ModuleNotFoundError as exc:
        raise RuntimeError(tr("en", "missing_module")) from exc


def read_script(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".docx":
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml").decode("utf-8", "ignore")
        return "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml))
    raise ValueError(I18N["en"]["unsupported_script"].format(suffix=path.suffix))


def normalize_text(text: str) -> str:
    t = PUNCT_RE.sub("", text)
    t = FILLER_RE.sub("", t)
    return t.strip().lower()


def tokenize_text(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    return [token for token in re.split(r"[^0-9a-zA-Z\u4e00-\u9fff]+", normalized) if token]


def char_ngrams(text: str, n: int = 2) -> set[str]:
    normalized = normalize_text(text)
    if len(normalized) <= n:
        return {normalized} if normalized else set()
    return {normalized[i : i + n] for i in range(len(normalized) - n + 1)}


def semantic_similarity(left: str, right: str) -> float:
    left_norm = normalize_text(left)
    right_norm = normalize_text(right)
    if not left_norm or not right_norm:
        return 0.0
    seq = SequenceMatcher(None, left_norm, right_norm).ratio()
    left_tokens = set(tokenize_text(left_norm))
    right_tokens = set(tokenize_text(right_norm))
    token_jaccard = len(left_tokens & right_tokens) / len(left_tokens | right_tokens) if left_tokens and right_tokens else 0.0
    left_ngrams = char_ngrams(left_norm)
    right_ngrams = char_ngrams(right_norm)
    ngram_jaccard = len(left_ngrams & right_ngrams) / len(left_ngrams | right_ngrams) if left_ngrams and right_ngrams else 0.0
    return round(max(seq, (seq * 0.5 + token_jaccard * 0.3 + ngram_jaccard * 0.2)), 4)


def proofread_zh(text: str) -> str:
    pairs = [
        ("github", "GitHub"),
        ("codex", "Codex"),
        ("gpt", "GPT"),
        ("skill", "Skill"),
        ("skills", "Skills"),
        ("token", "Token"),
        ("agent", "agent"),
    ]
    fixed = text
    for wrong, correct in pairs:
        fixed = re.sub(wrong, correct, fixed, flags=re.IGNORECASE)
    fixed = re.sub(r"\b(呃|嗯|啊)\b", "", fixed)
    fixed = re.sub(r"[ \t]+", "", fixed)
    lines = [line.strip(" ，。！？；") for line in fixed.splitlines() if line.strip()]
    return "\n\n".join(line if re.search(r"[。！？]$", line) else line + "。" for line in lines).strip()


def write_srt(path: Path, segments: Iterable[Segment]) -> None:
    def fmt_time(seconds: float) -> str:
        ms = int(round(seconds * 1000))
        h, rem = divmod(ms, 3600000)
        m, rem = divmod(rem, 60000)
        s, ms = divmod(rem, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    blocks: list[str] = []
    for idx, seg in enumerate(segments, start=1):
        blocks.append(f"{idx}\n{fmt_time(seg.start)} --> {fmt_time(seg.end)}\n{seg.text.strip()}\n")
    path.write_text("\n".join(blocks).strip() + "\n", encoding="utf-8")


def transcribe(video: Path, model_name: str, language: str, device: str, compute_type: str) -> list[Segment]:
    whisper_model_class = load_whisper_model_class()
    model = whisper_model_class(model_name, device=device, compute_type=compute_type)
    raw_segments, _ = model.transcribe(str(video), language=language, vad_filter=True, beam_size=5)
    return [
        Segment(start=float(seg.start), end=float(seg.end), text=seg.text.strip())
        for seg in raw_segments
        if seg.text.strip()
    ]


def probe_duration(video: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def is_restart(current: Segment, nxt: Segment, gap: float) -> bool:
    cur = normalize_text(current.text)
    nxt_text = normalize_text(nxt.text)
    if not cur or not nxt_text or gap > 1.5:
        return False
    if nxt_text.startswith(cur) and len(nxt_text) >= len(cur):
        return True
    shorter, longer = sorted((cur, nxt_text), key=len)
    if len(shorter) >= 6 and shorter in longer:
        return True
    return semantic_similarity(cur, nxt_text) >= 0.88


def window_text(segments: list[Segment], start: int, length: int) -> str:
    return "".join(normalize_text(seg.text) for seg in segments[start : start + length])


def detect_adjacent_repeat_windows(segments: list[Segment]) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    used: list[tuple[float, float]] = []

    def overlaps(start: float, end: float) -> bool:
        return any(not (end <= a or start >= b) for a, b in used)

    for i in range(len(segments) - 1):
        for left_len in range(3, 0, -1):
            if i + left_len >= len(segments):
                continue
            left_text = window_text(segments, i, left_len)
            if len(left_text) < 8:
                continue
            left_start = segments[i].start
            left_end = segments[i + left_len - 1].end
            if overlaps(left_start, left_end):
                continue
            for right_len in range(3, 0, -1):
                right_start_idx = i + left_len
                right_end_idx = right_start_idx + right_len - 1
                if right_end_idx >= len(segments):
                    continue
                if segments[right_start_idx].start - left_end > 1.6:
                    continue
                right_text = window_text(segments, right_start_idx, right_len)
                if len(right_text) < 8:
                    continue
                ratio = semantic_similarity(left_text, right_text)
                shorter, longer = sorted((left_text, right_text), key=len)
                contains = len(shorter) >= 8 and shorter in longer
                if ratio < 0.72 and not contains:
                    continue
                if len(right_text) + 2 < len(left_text):
                    continue
                found.append(
                    {
                        "type": "adjacent_repeat",
                        "start": round(left_start, 3),
                        "end": round(left_end, 3),
                        "text": " / ".join(seg.text for seg in segments[i : i + left_len]),
                        "next_text": " / ".join(
                            seg.text for seg in segments[right_start_idx : right_start_idx + right_len]
                        ),
                    }
                )
                used.append((left_start, left_end))
                break
            else:
                continue
            break
    return found


def split_script_blocks(text: str) -> list[str]:
    lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line:
            if current:
                blocks.append("".join(current))
                current = []
            continue
        current.append(line)
    if current:
        blocks.append("".join(current))
    return [block for block in blocks if normalize_text(block)]


def best_script_matches(script_text: str, transcript_text: str, label: str, ui_locale: str) -> dict[str, object]:
    if not script_text or not transcript_text:
        return {
            f"{label}_script_similarity": None,
            f"{label}_script_missing_blocks": [],
            f"{label}_script_extra_notice": None,
        }

    script_norm = normalize_text(script_text)
    transcript_norm = normalize_text(transcript_text)
    overall = round(semantic_similarity(script_norm, transcript_norm), 4)

    missing_blocks: list[dict[str, object]] = []
    for idx, block in enumerate(split_script_blocks(script_text), start=1):
        score = semantic_similarity(block, transcript_text)
        if score < 0.6:
            missing_blocks.append(
                {
                    "index": idx,
                    "score": round(score, 4),
                    "text": block[:80],
                }
            )

    extra_notice = None
    if overall < 0.55:
        extra_notice = tr(ui_locale, "script_compare_notice")

    return {
        f"{label}_script_similarity": overall,
        f"{label}_script_missing_blocks": missing_blocks[:10],
        f"{label}_script_extra_notice": extra_notice,
    }


def detect_large_ng_candidates(segments: list[Segment], script_text: str, ui_locale: str) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    if len(segments) < 2:
        return candidates

    script_reference = script_text or ""
    for idx in range(len(segments) - 1):
        left = segments[idx]
        right = segments[idx + 1]
        gap = right.start - left.end
        left_text = left.text.strip()
        right_text = right.text.strip()
        left_norm = normalize_text(left_text)
        right_norm = normalize_text(right_text)
        if not left_norm or not right_norm or gap > 2.0:
            continue

        sim = semantic_similarity(left_text, right_text)
        left_script = semantic_similarity(left_text, script_reference) if script_reference else 0.0
        right_script = semantic_similarity(right_text, script_reference) if script_reference else 0.0
        duration = right.end - left.start

        if sim >= 0.6 and duration >= 5.0 and len(right_norm) >= max(10, len(left_norm) - 6):
            keep_hint = tr(ui_locale, "keep_later") if right_script >= left_script else tr(ui_locale, "keep_review")
            reason = tr(ui_locale, "repeat_reason")
            candidates.append(
                {
                    "start": round(left.start, 3),
                    "end": round(right.end, 3),
                    "left_text": left_text,
                    "right_text": right_text,
                    "similarity": sim,
                    "keep_hint": keep_hint,
                    "reason": reason,
                }
            )
            continue

        if script_reference and duration >= 6.0 and max(left_script, right_script) < 0.35:
            candidates.append(
                {
                    "start": round(left.start, 3),
                    "end": round(right.end, 3),
                    "left_text": left_text,
                    "right_text": right_text,
                    "similarity": round(max(left_script, right_script), 4),
                    "keep_hint": tr(ui_locale, "keep_ask_user"),
                    "reason": tr(ui_locale, "ng_reason"),
                }
            )
    return candidates[:8]


def detect_silences(video_path: Path, min_duration: float, noise: str, duration: float) -> list[tuple[float, float]]:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(video_path),
            "-af",
            f"silencedetect=noise={noise}:d={min_duration}",
            "-f",
            "null",
            "-",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", proc.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+) \| silence_duration:", proc.stderr)]
    silences = []
    for start, end in zip(starts, ends):
        if end > start:
            silences.append((max(0.0, start), min(duration, end)))
    return silences


def cuts_from_silences(silences: list[tuple[float, float]], desired_gap: float, duration: float) -> list[tuple[float, float]]:
    cuts: list[tuple[float, float]] = []
    keep_side = desired_gap / 2
    for start, end in silences:
        if end - start <= desired_gap:
            continue
        cut_start = max(0.0, start + keep_side)
        cut_end = min(duration, end - keep_side)
        if cut_end - cut_start >= 0.06:
            cuts.append((cut_start, cut_end))
    return cuts


def invert_ranges(ranges: list[tuple[float, float]], duration: float) -> list[tuple[float, float]]:
    if not ranges:
        return [(0.0, duration)]
    merged: list[list[float]] = []
    for start, end in sorted(ranges):
        if end <= start:
            continue
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    keep: list[tuple[float, float]] = []
    cursor = 0.0
    for start, end in merged:
        if start - cursor >= 0.12:
            keep.append((cursor, start))
        cursor = end
    if duration - cursor >= 0.12:
        keep.append((cursor, duration))
    return keep


def build_filter(intervals: list[tuple[float, float]]) -> str:
    parts: list[str] = []
    refs: list[str] = []
    for idx, (start, end) in enumerate(intervals):
        parts.append(f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[v{idx}]")
        parts.append(f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a{idx}]")
        refs.extend([f"[v{idx}]", f"[a{idx}]"])
    parts.append("".join(refs) + f"concat=n={len(intervals)}:v=1:a=1[outv][outa]")
    return ";".join(parts)


def export_video(video: Path, out_path: Path, intervals: list[tuple[float, float]]) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-filter_complex",
            build_filter(intervals),
            "-map",
            "[outv]",
            "-map",
            "[outa]",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(out_path),
        ],
        check=True,
    )


def main() -> int:
    args = parse_args()
    ui_locale = resolve_ui_locale(args.ui_locale)
    video = Path(args.video).expanduser().resolve()
    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video}")

    script_text = ""
    if args.script:
        script_text = read_script(Path(args.script).expanduser().resolve())

    cfg = {
        "normal": {"desired_gap": 0.18, "silence_duration": 0.45, "noise": "-35dB"},
        "more": {"desired_gap": 0.08, "silence_duration": 0.22, "noise": "-33dB"},
    }[args.intensity]

    duration = probe_duration(video)
    segments = transcribe(video, args.model, args.language, args.device, args.compute_type)

    raw_txt = video.with_suffix(".raw.txt")
    final_txt = video.with_suffix(".txt")
    raw_srt = video.with_suffix(".raw.srt")
    roughcut_mp4 = video.with_name(f"{video.stem}.roughcut.mp4")
    roughcut_json = video.with_name(f"{video.stem}.roughcut.json")
    roughcut_raw_txt = video.with_name(f"{video.stem}.roughcut.raw.txt")
    roughcut_txt = video.with_name(f"{video.stem}.roughcut.txt")
    roughcut_srt = video.with_name(f"{video.stem}.roughcut.srt")

    transcript = "\n".join(seg.text for seg in segments)
    raw_txt.write_text(transcript, encoding="utf-8")
    final_txt.write_text(proofread_zh(transcript), encoding="utf-8")
    write_srt(raw_srt, segments)

    removed: list[dict[str, object]] = []
    cut_ranges: list[tuple[float, float]] = []
    for idx, seg in enumerate(segments[:-1]):
        nxt = segments[idx + 1]
        if is_restart(seg, nxt, nxt.start - seg.end):
            cut_ranges.append((seg.start, seg.end))
            removed.append(
                {
                    "type": "restart",
                    "start": round(seg.start, 3),
                    "end": round(seg.end, 3),
                    "text": seg.text,
                    "next_text": nxt.text,
                }
            )
    for item in detect_adjacent_repeat_windows(segments):
        cut_ranges.append((float(item["start"]), float(item["end"])))
        removed.append(item)

    large_ng_candidates = detect_large_ng_candidates(segments, script_text, ui_locale)

    silences = detect_silences(video, cfg["silence_duration"], cfg["noise"], duration)
    cut_ranges.extend(cuts_from_silences(silences, cfg["desired_gap"], duration))
    intervals = invert_ranges(cut_ranges, duration)

    export_video(video, roughcut_mp4, intervals)

    roughcut_segments = transcribe(roughcut_mp4, args.model, args.language, args.device, args.compute_type)
    roughcut_transcript = "\n".join(seg.text for seg in roughcut_segments)
    roughcut_raw_txt.write_text(roughcut_transcript, encoding="utf-8")
    roughcut_txt.write_text(proofread_zh(roughcut_transcript), encoding="utf-8")
    write_srt(roughcut_srt, roughcut_segments)

    compare_before = best_script_matches(script_text, transcript, "before", ui_locale)
    compare_after = best_script_matches(script_text, roughcut_transcript, "after", ui_locale)

    report = {
        "source": str(video),
        "output": str(roughcut_mp4),
        "duration_before": round(duration, 3),
        "duration_after": round(sum(end - start for start, end in intervals), 3),
        "intensity": args.intensity,
        "ui_locale": ui_locale,
        "script_provided": bool(script_text),
        "script_similarity": compare_before["before_script_similarity"],
        "roughcut_script_similarity": compare_after["after_script_similarity"],
        "script_missing_blocks_before": compare_before["before_script_missing_blocks"],
        "script_missing_blocks_after": compare_after["after_script_missing_blocks"],
        "script_compare_notice_before": compare_before["before_script_extra_notice"],
        "script_compare_notice_after": compare_after["after_script_extra_notice"],
        "segments_detected": len(segments),
        "roughcut_segments_detected": len(roughcut_segments),
        "intervals_kept": len(intervals),
        "removed_count": len(removed),
        "removed_examples": removed[:20],
        "large_ng_candidates": large_ng_candidates,
        "review_questions": [
            tr(ui_locale, "review_question")
        ]
        if large_ng_candidates
        else [],
        "outputs": {
            "raw_txt": str(raw_txt),
            "txt": str(final_txt),
            "raw_srt": str(raw_srt),
            "roughcut_raw_txt": str(roughcut_raw_txt),
            "roughcut_txt": str(roughcut_txt),
            "roughcut_srt": str(roughcut_srt),
            "roughcut_mp4": str(roughcut_mp4),
            "roughcut_json": str(roughcut_json),
        },
        "intervals": [{"start": round(start, 3), "end": round(end, 3)} for start, end in intervals],
        "transcript_preview": [
            {"start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text}
            for seg in segments[:30]
        ],
        "roughcut_transcript_preview": [
            {"start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text}
            for seg in roughcut_segments[:30]
        ],
    }
    roughcut_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

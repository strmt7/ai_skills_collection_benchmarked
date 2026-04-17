---
name: android-visual-qa
description: Use when validating Project Air Defense with screenshots, OCR, template matching, or live emulator navigation, especially when libGDX SurfaceView content is not visible in the Android accessibility tree.
---

# Android Visual QA

Use this skill when the question is "what is actually on screen?" rather than only "did the process survive?"

## Read next

- [`docs/android-visual-qa.md`](../../../docs/android-visual-qa.md)
- [`docs/reference/android-visual-qa-sources.md`](../../../docs/reference/android-visual-qa-sources.md)

## Workflow

1. Probe the toolchain first.
   - `py -3 tools/android_visual_qa/visual_qa.py probe`
2. Verify emulator health before making claims.
   - `adb devices`
   - `adb shell getprop sys.boot_completed`
3. Resolve and launch the exact installed app variant when package names are uncertain.
   - default smoke lane after `:android:installDebug`: `py -3 tools/android_visual_qa/visual_qa.py launch --device emulator-5554 --package com.airdefense.game.debug`
   - benchmark package only when the benchmark build is actually installed: `com.airdefense.game.benchmark`
4. Use the Android UI tree only for native surfaces.
   - system dialogs
   - permission prompts
   - launcher chrome
5. Use screenshot-driven checks for libGDX gameplay surfaces.
   - `find-text` or `tap-text` for readable buttons or HUD labels
   - `match-template` or `tap-template` when OCR is too weak
6. Save hard proof.
   - screenshot
   - OCR or template JSON
   - logcat when the flow matters
7. Distinguish the outcomes.
   - installed
   - process alive
   - correct screen visible
   - correct target tapped

## Rules

- Do not guess tap coordinates from memory when the toolchain can read the screen.
- Do not treat process survival or logcat alone as proof of a usable flow.
- Prefer OCR over template matching when the control has strong text.
- Prefer template matching over OCR when the target is icon-heavy or stylized.
- Keep one active automation stack in this repo: `adbutils` + `OpenCV` + `Tesseract` + `Pillow`, with `scrcpy` for live confirmation.
- Treat Appium, Maestro, Airtest, and SikuliX as evaluated references unless a future task needs them explicitly.
- On fresh Android emulator boots, clear any Android full-screen education overlay before claiming OCR-based menu state.

## Validation

- `py -3 tools/android_visual_qa/test_visual_qa.py`
- `py -3 tools/android_visual_qa/visual_qa.py selftest`
- `py -3 tools/android_visual_qa/visual_qa.py launch --device emulator-5554 --package com.airdefense.game.debug`
- `py -3 tools/android_visual_qa/visual_qa.py find-text "ENTER AIRSPACE" --device emulator-5554`

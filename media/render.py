"""Render a motion-graphics timeline of ``media/commercial/index.html`` to video, frame by frame.

The page exposes ``renderAt(t, timeline)``: every frame is a pure function of time, so the capture is
deterministic and independent of the machine's speed. Frames are piped to ffmpeg (H.264), then
the soundtrack synthesised from the timeline's cues (``media/soundtrack.py``) is muxed in.

    python media/render.py commercial                      # media/out/vigie_commercial.mp4
    python media/render.py commercial --preview 0.6 12 39  # PNG stills in media/out/preview/
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

MEDIA = Path(__file__).resolve().parent
OUT = MEDIA / "out"
PAGE = (MEDIA / "commercial" / "index.html").as_uri()
CHROMIUM = "/usr/bin/chromium"
FPS = 30


def open_page(playwright, timeline: str):
    browser = playwright.chromium.launch(executable_path=CHROMIUM, args=["--force-color-profile=srgb", "--hide-scrollbars"])
    page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    page.goto(f"{PAGE}?timeline={timeline}#0")
    page.evaluate("document.fonts.ready")
    return browser, page


def capture_frames(timeline: str, video: Path, start: float = 0.0, end: float | None = None) -> dict:
    """Pipe every frame of ``timeline`` into ffmpeg; returns the timeline info (duration, cues)."""
    with sync_playwright() as p:
        browser, page = open_page(p, timeline)
        info = page.evaluate(f"timelineInfo({json.dumps(timeline)})")
        end = info["duration"] if end is None else end
        frames = round((end - start) * FPS)
        ffmpeg = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
             "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)],
            stdin=subprocess.PIPE)
        for k in range(frames):
            page.evaluate(f"renderAt({start + k / FPS:.6f}, {json.dumps(timeline)})")
            ffmpeg.stdin.write(page.screenshot(type="png"))
            if k % 60 == 0:
                print(f"\r{timeline}: frame {k}/{frames}", end="", file=sys.stderr, flush=True)
        ffmpeg.stdin.close()
        ffmpeg.wait()
        browser.close()
        print(file=sys.stderr)
        return info


def preview(timeline: str, times: list[float]) -> None:
    folder = OUT / "preview"
    folder.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = open_page(p, timeline)
        for t in times:
            page.evaluate(f"renderAt({t}, {json.dumps(timeline)})")
            page.screenshot(path=str(folder / f"{timeline}_{t:06.2f}.png"))
        browser.close()


def mux(video: Path, audio: Path, output: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio), "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(output)], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("timeline", help="commercial, demo_intro or demo_outro")
    parser.add_argument("--preview", nargs="*", type=float, help="write PNG stills at these times instead of a video")
    parser.add_argument("--output", type=Path, help="video path (default: media/out/vigie_<timeline>.mp4)")
    parser.add_argument("--silent", action="store_true", help="no soundtrack (cards that are muxed later)")
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.preview is not None:
        preview(args.timeline, args.preview)
        return
    output = args.output or OUT / f"vigie_{args.timeline}.mp4"
    silent = output.with_suffix(".video.mp4")
    info = capture_frames(args.timeline, silent)
    (OUT / f"{args.timeline}_cues.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    if args.silent:
        silent.replace(output)
        return
    from soundtrack import render_soundtrack

    audio = output.with_suffix(".wav")
    render_soundtrack(info["cues"], info["duration"], audio)
    mux(silent, audio, output)
    silent.unlink()
    audio.unlink()
    print(output)


if __name__ == "__main__":
    main()

"""Record the Vigie MVP demo: a real session driven by Playwright, captured frame by frame.

The running app (``mise run mvp``) is driven like an analyst would: triage of an incident report,
investigation with the local LLM, CTI pivot in the graph, detection rule, assistant security,
metrics and the incident record. Frames are written on a *virtual* timeline: waiting for the API or
the LLM is not recorded (the spinner is shown briefly, then the result), every result on screen is
the application's real output. Captions and a cursor orb are overlaid in the commercial's style;
intro and end cards come from ``media/commercial`` (timelines ``demo_intro`` / ``demo_outro``).

    mise run mvp                                   # in another terminal
    python media/demo/record_demo.py               # → media/out/vigie_demo_mvp.mp4
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import Locator, Page, sync_playwright

MEDIA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MEDIA))
from render import capture_frames
from soundtrack import render_soundtrack

OUT = MEDIA / "out"
UI = "http://localhost:8501"
FPS = 30
VIEW = {"width": 1536, "height": 864}  # × 1.25 device scale = 1920 × 1080 frames, larger UI text
OVERLAY = (Path(__file__).with_name("overlay.js")).read_text(encoding="utf-8")


class Recorder:
    """Writes frames to ffmpeg on a virtual clock; records sound cues at the same clock."""

    def __init__(self, page: Page, video: Path) -> None:
        self.page, self.frames, self.cues = page, 0, []
        self.last: bytes | None = None
        self.fade_next = False
        self.orb = (VIEW["width"] * 0.62, VIEW["height"] * 0.7)
        self.ffmpeg = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
             "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", str(video)], stdin=subprocess.PIPE)

    @property
    def t(self) -> float:
        return self.frames / FPS

    def _write(self, png: bytes, count: int) -> None:
        if self.fade_next and self.last is not None:  # 8-frame crossfade over a cut
            a, b = Image.open(io.BytesIO(self.last)).convert("RGB"), Image.open(io.BytesIO(png)).convert("RGB")
            for k in range(1, 9):
                buf = io.BytesIO()
                Image.blend(a, b, k / 8).save(buf, "PNG", compress_level=1)
                self.ffmpeg.stdin.write(buf.getvalue())
            self.frames += 8
            count = max(0, count - 8)
            self.fade_next = False
        for _ in range(count):
            self.ffmpeg.stdin.write(png)
        self.frames += count
        self.last = png

    def grab(self) -> bytes:
        self.page.evaluate(OVERLAY)
        return self.page.screenshot(type="png")

    def hold(self, seconds: float) -> None:
        self._write(self.grab(), round(seconds * FPS))

    def live(self, seconds: float, step=None, every: int = 2) -> None:
        """Capture a moving sequence: ``step(k)`` poses the page before each capture (every 2 frames)."""
        n = max(1, round(seconds * FPS / every))
        for k in range(n):
            if step:
                step(k / max(1, n - 1))
            self._write(self.grab(), every)

    def cut(self) -> None:
        self.fade_next = True

    # ---------------------------------------------------------------- overlay helpers
    def caption(self, step: str, text: str) -> None:
        self.page.evaluate(OVERLAY)
        self.page.evaluate("([s, t]) => window.__demo.caption(s, t)", [step, text])

    def move_orb(self, x: float, y: float, seconds: float = 0.45) -> None:
        x0, y0 = self.orb

        def step(k: float) -> None:
            e = 1 - (1 - k) ** 3
            self.page.evaluate("([x, y]) => window.__demo.orb(x, y, false)", [x0 + (x - x0) * e, y0 + (y - y0) * e])

        self.live(seconds, step)
        self.orb = (x, y)

    def click(self, locator: Locator, seconds: float = 0.45) -> None:
        locator.scroll_into_view_if_needed()
        box = locator.bounding_box()
        x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        self.move_orb(x, y, seconds)
        self.page.evaluate("([x, y]) => window.__demo.orb(x, y, true)", [x, y])
        self.cues.append({"t": self.t, "type": "click"})
        self.live(0.15)
        locator.click()
        self.page.evaluate("([x, y]) => window.__demo.orb(x, y, false)", [x, y])

    def type_into(self, locator: Locator, text: str) -> None:
        self.click(locator, 0.4)
        self.cues.append({"t": self.t, "type": "type", "dur": len(text) * 2 / FPS})
        for ch in text:
            locator.press_sequentially(ch)
            self._write(self.grab(), 2)

    def scroll(self, to: float | str, seconds: float = 0.9) -> None:
        """Smooth scroll of the main pane to a pixel offset or to the element containing ``to``."""
        start = self.page.evaluate("() => window.__demo.scrollTop()")
        target = self.page.evaluate("(q) => window.__demo.offsetOf(q)", to) if isinstance(to, str) else to

        def step(k: float) -> None:
            e = k * k * (3 - 2 * k)
            self.page.evaluate("(y) => window.__demo.scrollTo(y)", start + (target - start) * e)

        self.live(seconds, step)

    def close(self) -> None:
        self.ffmpeg.stdin.close()
        self.ffmpeg.wait()


def settle(page: Page, condition: str, timeout: float = 120) -> None:
    """Wait (unrecorded) until ``condition`` holds and Streamlit has finished its rerun."""
    page.wait_for_function(condition, timeout=timeout * 1000)
    page.wait_for_function("() => document.querySelector('[data-testid=stApp]')?.dataset.testScriptState !== 'running'",
                           timeout=timeout * 1000)
    page.wait_for_timeout(700)


def has_text(text: str) -> str:
    return f"() => document.body.innerText.includes({json.dumps(text)})"


def nav(rec: Recorder, title: str) -> None:
    rec.click(rec.page.locator('[data-testid="stSidebarNav"] a').filter(has_text=title).first)
    settle(rec.page, has_text(title))


def session(rec: Recorder) -> None:
    page = rec.page
    page.goto(UI)
    settle(page, has_text("Poste analyste"))

    # 01 — analyst desk
    rec.caption("01 · Poste analyste", "Le point d'entrée du SOC : file de travail et <b>accès rapides</b> aux outils.")
    rec.hold(2.6)

    # 02 — triage of a real-looking incident report
    nav(rec, "Triage")
    rec.cut()
    rec.caption("02 · Triage", "Un signalement : <b>rançongiciel LockBit</b> sur le serveur d'un hôpital.")
    rec.hold(2.2)
    rec.click(page.get_by_role("button", name="Qualifier"))
    rec.live(0.5)
    settle(page, has_text("Investiguer avec l'assistant"))
    rec.cut()
    rec.caption("02 · Triage", "Priorité, catégorie et <b>TTP MITRE ATT&CK</b> suggérées, avec leurs raisons.")
    rec.scroll(260, 1.0)
    rec.hold(2.6)
    rec.caption("02 · Triage", "Chaque IOC reçoit un <b>verdict</b> : l'adresse interne 10.0.0.5 n'est pas exportable.")
    rec.scroll("Indicateurs", 1.0)
    rec.hold(2.6)
    rec.caption("02 · Triage", "Playbook <b>NIST SP 800-61</b> : confinement, éradication, rétablissement.")
    rec.scroll("Playbook", 1.0)
    rec.hold(2.4)

    # 03 — investigation with the local LLM (question pre-filled from the triage)
    button = page.get_by_role("button", name="🔎 Investiguer avec l'assistant")
    rec.click(button)
    rec.live(0.5)
    settle(page, "() => document.querySelectorAll('[data-testid=stChatMessage]').length >= 2"
                 " && !document.body.innerText.includes('Recherche des sources et rédaction')")
    rec.cut()
    rec.caption("03 · Investigation", "Question reprise du triage : réponse du <b>LLM local</b>, sources <b>[S#]</b> citées.")
    rec.hold(3.2)
    rec.scroll(340, 1.0)
    rec.caption("03 · Investigation", "Chaque phrase est <b>vérifiée</b> contre les preuves : documents et faits du graphe.")
    rec.hold(2.8)
    rec.caption("03 · Investigation", "")  # the caption would cover the chat input while typing
    rec.type_into(page.get_by_placeholder("Question d'investigation (français ou anglais)…"), "Et quels IOC faut-il bloquer ?")
    page.keyboard.press("Enter")
    rec.live(0.5)
    settle(page, "() => document.querySelectorAll('[data-testid=stChatMessage]').length >= 4"
                 " && !document.body.innerText.includes('Recherche des sources et rédaction')")
    rec.cut()
    rec.caption("03 · Investigation", "Question de suivi : le <b>contexte</b> de la conversation est conservé.")
    rec.scroll(100000, 1.0)
    rec.hold(3.0)

    # 04 — CTI pivot: question → Cypher on the STIX graph
    nav(rec, "Pivot CTI")
    rec.cut()
    rec.caption("04 · Pivot CTI", "Une question en langage naturel devient une <b>requête Cypher</b> sur le graphe STIX 2.1.")
    rec.hold(1.6)
    rec.click(page.get_by_role("button", name="Pivoter"))
    settle(page, has_text("MATCH"))
    rec.cut()
    rec.caption("04 · Pivot CTI", "Résultats du graphe, chacun avec sa <b>provenance</b> (documents sources).")
    rec.hold(2.2)
    rec.scroll(320, 1.0)
    rec.hold(2.2)

    # 05 — detection rule from the case's IOCs
    nav(rec, "Règles de détection")
    rec.cut()
    rec.caption("05 · Détection", "Les IOC du dossier pré-remplissent la règle : seuls les <b>indicateurs valides</b> passent.")
    rec.hold(2.0)
    rec.click(page.get_by_role("button", name="Générer la règle"))
    settle(page, has_text("Splunk SPL"))
    rec.cut()
    rec.scroll("Splunk SPL", 1.0)
    rec.caption("05 · Détection", "Règle <b>Splunk SPL</b> et <b>Microsoft Sentinel KQL</b> prête à déployer.")
    rec.hold(2.2)
    rec.click(page.get_by_role("tab", name="Microsoft Sentinel KQL"))
    rec.hold(2.0)

    # 06 — security of the assistant
    nav(rec, "Sécurité de l'assistant")
    rec.cut()
    rec.caption("06 · Sécurité", "Garde-fou <b>anti-injection de prompt</b> (OWASP LLM01) testé en direct.")
    rec.hold(1.2)
    rec.click(page.get_by_role("button", name="Vérifier"))
    settle(page, "() => true")
    rec.hold(2.0)
    rec.caption("06 · Sécurité", "Audit d'<b>empoisonnement du graphe</b> (GragPoison) à la demande.")
    rec.click(page.get_by_role("button", name="Lancer l'audit"))
    settle(page, "() => true")
    rec.cut()
    rec.scroll(320, 0.9)
    rec.hold(2.4)

    # 07 — metrics
    nav(rec, "Pilotage")
    rec.cut()
    rec.caption("07 · Pilotage", "Les métriques <b>mesurées</b> dans les notebooks, consultables par l'équipe SOC.")
    rec.hold(2.2)
    rec.click(page.get_by_role("tab", name="HybridRAG"))
    rec.hold(2.2)
    rec.click(page.get_by_role("tab", name="Sécurité & agent"))
    rec.hold(2.2)

    # 08 — incident record
    nav(rec, "Dossier d'incident")
    rec.cut()
    rec.caption("08 · Dossier d'incident", "Toute l'analyse est tracée dans la <b>main courante</b>, exportable pour le ticket.")
    rec.hold(2.4)
    rec.scroll(100000, 1.2)
    rec.hold(2.4)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    capture, intro, outro = OUT / "demo_capture.mp4", OUT / "demo_intro.mp4", OUT / "demo_outro.mp4"
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--force-color-profile=srgb"])
        page = browser.new_page(viewport=VIEW, device_scale_factor=1.25, locale="fr-FR")
        rec = Recorder(page, capture)
        try:
            session(rec)
        finally:
            rec.close()
            browser.close()
    intro_info = capture_frames("demo_intro", intro)
    outro_info = capture_frames("demo_outro", outro)
    t_intro, t_main = intro_info["duration"], rec.t
    total = t_intro + t_main + outro_info["duration"]
    cues = [*intro_info["cues"], {"t": t_intro, "type": "whoosh"},
            *({**c, "t": c["t"] + t_intro} for c in rec.cues),
            {"t": t_intro + t_main, "type": "whoosh"}, *({**c, "t": c["t"] + t_intro + t_main} for c in outro_info["cues"])]
    audio = OUT / "demo.wav"
    render_soundtrack(cues, total, audio, music_gain=0.55)
    final = OUT / "vigie_demo_mvp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(intro), "-i", str(capture), "-i", str(outro), "-i", str(audio),
                    "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]", "-map", "[v]", "-map", "3:a",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", str(final)], check=True)
    for tmp in (capture, intro, outro, audio):
        tmp.unlink()
    print(f"{final} · {total:.1f} s")


if __name__ == "__main__":
    main()

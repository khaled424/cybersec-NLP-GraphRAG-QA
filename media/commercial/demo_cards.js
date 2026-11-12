/* Intro and end cards of the MVP demo video (same locked style as the commercial). */
"use strict";

// Intro: aurora hero + title of the demo (4 s)
shot("demo_intro", 0, 4, (st) => {
  const arc = el(st, "abs", { left: "-120px", top: "-260px", width: "2400px", height: "1900px", borderRadius: "50%",
    border: "150px solid transparent", borderTopColor: C.teal, borderLeftColor: C.slate, filter: "blur(70px)", opacity: 0.9 });
  aurora(st, [{ x: 960, y: 1150, w: 1900, h: 560, c: C.navy, o: 1 }]);
  const logo = centered(st, "logo", 330, "✦ Vigie", { fontSize: "54px" });
  const head = centered(st, "headline", 410, "Démo du MVP", { fontSize: "150px", lineHeight: "170px" });
  const sub = centered(st, "tagline", 610, "L'assistant IA du <span class=\"cyan\">Centre d'Opérations de Sécurité</span>", { fontSize: "40px" });
  const note = centered(st, "label", 690, "Capture réelle de l'application · temps d'attente du LLM coupés", { fontSize: "26px", color: C.muted });
  const s1 = makeStar(st, 150), s2 = makeStar(st, 90);
  return { arc, logo, head, sub, note, s1, s2 };
}, (lt, d, r) => {
  camera(r.stage, { y: tween(lt, 0, d, 30, -10), s: tween(lt, 0, d, 0.97, 1.04) });
  r.arc.style.transform = `rotate(${tween(lt, 0, d, -26, 6)}deg)`;
  wipe(r.logo, lt, 0.1, 0.4); wipe(r.head, lt, 0.25, 0.6); wipe(r.sub, lt, 0.9, 0.5); wipe(r.note, lt, 1.4, 0.5);
  poseStar(r.s1, { x: 330 + lt * 25, y: tween(lt, 0, 1.2, 1100, 760), ry: lt * 140, rz: -15 + lt * 20 });
  poseStar(r.s2, { x: 1600 - lt * 20, y: tween(lt, 0.2, 1.4, 1150, 300), ry: 60 + lt * 180, rz: 20 - lt * 30 });
});
cue("demo_intro", 0.25, "swell");

// End card: aurora ring + how to launch it (4 s)
endCard("demo_outro", 0, 4, "Vigie", "✦ mise run mvp · github.com/khaled424/cybersec-NLP-GraphRAG-QA");

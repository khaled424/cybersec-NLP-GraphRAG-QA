/* Reusable shot builders of the master prompt's shot library (S3 button, S8/S9 star bridge,
 * S10 end card) and small UI pieces (icons, glass cards). Used by the commercial and the demo cards. */
"use strict";

const ICONS = {
  book: '<path d="M10 18c14-6 26-6 38 4v52c-12-10-24-10-38-4z M86 18c-14-6-26-6-38 4v52c12-10 24-10 38-4z"/>',
  tag: '<path d="M14 14h34l36 36-34 34-36-36z"/><circle cx="32" cy="32" r="6"/>',
  graph: '<circle cx="22" cy="24" r="9"/><circle cx="74" cy="20" r="9"/><circle cx="48" cy="54" r="10"/><circle cx="20" cy="78" r="8"/><circle cx="78" cy="76" r="8"/><path d="M29 29l12 18M66 25L55 46M42 61L26 72M55 61l16 10"/>',
  layers: '<path d="M48 12l38 18-38 18-38-18z"/><path d="M10 48l38 18 38-18"/><path d="M10 66l38 18 38-18"/>',
  db: '<ellipse cx="48" cy="20" rx="32" ry="10"/><path d="M16 20v56c0 6 14 10 32 10s32-4 32-10V20"/><path d="M16 48c0 6 14 10 32 10s32-4 32-10"/>',
  chip: '<rect x="24" y="24" width="48" height="48" rx="8"/><rect x="38" y="38" width="20" height="20" rx="3"/><path d="M36 10v12M48 10v12M60 10v12M36 74v12M48 74v12M60 74v12M10 36h12M10 48h12M10 60h12M74 36h12M74 48h12M74 60h12"/>',
  target: '<circle cx="48" cy="48" r="34"/><circle cx="48" cy="48" r="20"/><circle cx="48" cy="48" r="5"/><path d="M48 4v14M48 78v14M4 48h14M78 48h14"/>',
  bolt: '<path d="M54 8L20 54h24l-6 34 36-48H50z"/>',
  shield: '<path d="M48 8l32 12v24c0 22-14 36-32 44C30 80 16 66 16 44V20z"/><path d="M34 48l10 10 18-20"/>',
  user: '<circle cx="48" cy="34" r="16"/><path d="M16 84c4-18 16-26 32-26s28 8 32 26"/>',
  refresh: '<path d="M78 40a32 32 0 1 0 2 22"/><path d="M80 14v26H54"/>',
};
function icon(name, color = C.cyan, size = 84, width = 6) {
  return `<svg viewBox="0 0 96 96" width="${size}" height="${size}" fill="none" stroke="${color}" stroke-width="${width}"
    stroke-linecap="round" stroke-linejoin="round">${ICONS[name]}</svg>`;
}

/** Glass card at (x, y) of size (w, h). */
function glass(parent, x, y, w, h, extraCls = "", style = {}) {
  return el(parent, `glass ${extraCls}`, { left: `${x}px`, top: `${y}px`, width: `${w}px`, height: `${h}px`, ...style });
}
/** Horizontally centred absolutely positioned text block. */
function centered(parent, cls, y, html, style = {}) {
  return el(parent, `abs ${cls}`, { top: `${y}px`, width: "1920px", textAlign: "center", ...style }, html);
}
/** Pop-in with overshoot (tiles, badges, cards). */
function pop(node, t, start, dur = 0.32, baseExtra = "") {
  const k = prog(t, start, start + dur);
  node.style.opacity = clamp(k * 3);
  node.style.transform = `${baseExtra} scale(${k === 0 ? 0.001 : eBack(k)})`;
}
/** Left-to-right wipe reveal. */
function wipe(node, t, start, dur = 0.3) {
  const k = eOut(prog(t, start, start + dur));
  node.style.clipPath = `inset(-20px ${100 - k * 100}% -20px -20px)`;
  node.style.opacity = k > 0 ? 1 : 0;
}

// ---------------------------------------------------------------- S3 button press
function buttonShot(tl, a, b, label) {
  const click = (b - a) * 0.55;
  cue(tl, a + click, "click");
  shot(tl, a, b, (stage) => {
    aurora(stage, [{ x: 960, y: 980, w: 1600, h: 600, c: C.navy, o: 0.9 }, { x: 1500, y: 200, w: 700, h: 500, c: C.slate, o: 0.35 }]);
    const halo = el(stage, "abs", { left: "960px", top: "540px", width: "10px", height: "10px", borderRadius: "50%",
      border: `3px solid ${C.cyan}`, boxShadow: `0 0 40px ${C.cyan}` });
    const btn = el(stage, "pill", { left: "960px", top: "540px", height: "170px", fontSize: "64px", padding: "0 70px",
      borderWidth: "3px", fontWeight: "600", boxShadow: "0 0 50px rgba(39,210,230,.35)" }, label);
    const orb = el(stage, "cursor-orb");
    return { btn, orb, halo };
  }, (lt, dur, r) => {
    camera(r.stage, { s: tween(lt, 0, dur, 1.0, 1.16, eOut) });
    const pressed = lt >= click;
    const k = prog(lt, click, click + 0.12);
    r.btn.style.transform = `translate(-50%, -50%) scale(${pressed ? lerp(1, 1.1, eBack(k)) : 1})`;
    r.btn.style.background = pressed ? C.chead : "rgba(21,24,31,.85)";
    r.btn.style.color = pressed ? "#06202A" : C.text;
    const ox = tween(lt, 0, click, 1500, 1060, eOut), oy = tween(lt, 0, click, 900, 575, eOut);
    r.orb.style.transform = `translate(${ox}px, ${oy}px) scale(${pressed ? 1 - 0.25 * Math.sin(Math.PI * k) : 1})`;
    const hk = prog(lt, click, dur);
    const size = lerp(560, 1500, eOut(hk));
    Object.assign(r.halo.style, { width: `${size}px`, height: `${size * 0.42}px`, borderRadius: "999px",
      transform: "translate(-50%, -50%)", opacity: pressed ? (1 - hk) * 0.9 : 0, borderWidth: `${lerp(4, 1, hk)}px` });
  });
}

// ---------------------------------------------------------------- S8 + S9 star bridge
/**
 * The hero star spins to a sliver, shrinks and becomes the typing cursor; `lines` are typed one
 * after the other (each [partA, partB, highlighted = "A" | "B"]), the star parking in the gap between
 * the parts; the highlighted part is cyan, the other white.
 */
function bridgeShot(tl, a, b, lines, { spin = 0.4, cps = 24, size = 58, holdEnd = 0.25 } = {}) {
  cue(tl, a, "swell");
  // schedule: spin, then for each line: type A, type B, hold, wipe out (except the last line)
  const plan = [];
  let t = spin + 0.05;
  lines.forEach(([A, B, hl = "A"], i) => {
    const tA = t, tB = tA + A.length / cps, end = tB + B.length / cps;
    const last = i === lines.length - 1;
    const out = last ? b - a + 1 : Math.max(end + 0.35, end);
    plan.push({ A, B, hl, tA, tB, end, out });
    cue(tl, a + tA, "type", { dur: end - tA });
    t = last ? end : out + 0.2;
  });
  shot(tl, a, b, (stage) => {
    aurora(stage, [{ x: 960, y: 1120, w: 1900, h: 520, c: C.navy, o: 1 }, { x: 960, y: 1060, w: 900, h: 260, c: C.slate, o: 0.35 }]);
    const hero = makeStar(stage, 460);
    const lineNodes = plan.map((p) => {
      const line = centered(stage, "tagline", 500, "", { fontSize: `${size}px`, lineHeight: "80px", height: "80px" });
      const spanA = document.createElement("span"), spanB = document.createElement("span");
      (p.hl === "B" ? spanB : spanA).className = "cyan";
      const slot = document.createElement("span");
      Object.assign(slot.style, { display: "inline-block", width: `${size * 1.4}px`, height: "10px", position: "relative" });
      line.append(spanA, slot, spanB);
      const small = makeStar(slot, size * 1.15);
      Object.assign(small.style, { left: "50%", top: "-14px" });
      return { line, spanA, spanB, slot, small };
    });
    return { hero, lineNodes };
  }, (lt, dur, r) => {
    camera(r.stage, { s: tween(lt, 0, dur, 1.0, 1.04, eInOut) });
    const ks = prog(lt, 0, spin);
    const heroOn = lt < spin;
    poseStar(r.hero, { x: 960, y: tween(lt, 0, spin, 520, 520), s: lerp(1, 0.14, eInOut(ks)), ry: lerp(0, 450, eOut(ks)),
      o: heroOn ? 1 : 0, blur: heroOn ? 1.5 * Math.sin(Math.PI * ks) : 0 });
    plan.forEach((p, i) => {
      const n = r.lineNodes[i];
      const visible = lt >= (i === 0 ? spin : p.tA) && lt < p.out + 0.18;
      n.line.style.display = visible ? "block" : "none";
      const nA = clamp((lt - p.tA) * cps, 0, p.A.length), nB = clamp((lt - p.tB) * cps, 0, p.B.length);
      n.spanA.textContent = p.A.slice(0, Math.floor(nA));
      n.spanB.textContent = p.B.slice(0, Math.floor(nB));
      poseStar(n.small, { x: 0, y: 0, ry: lt * 420, s: 1 });
      const ko = prog(lt, p.out, p.out + 0.18);  // wipe the line out
      n.line.style.clipPath = ko > 0 ? `inset(0 0 0 ${ko * 100}%)` : "none";
    });
  });
}

// ---------------------------------------------------------------- S10 aurora end card
function endCard(tl, a, b, logo, cta) {
  cue(tl, a, "chime");
  shot(tl, a, b, (stage) => {
    aurora(stage, [{ x: 960, y: 540, w: 900, h: 700, c: C.navy, o: 0.7 }]);
    const ring = el(stage, "abs", { left: "960px", top: "540px", width: "1240px", height: "1240px", borderRadius: "50%",
      background: `conic-gradient(from 0deg, ${C.slate} 0deg, ${C.slate} 110deg, ${C.teal} 165deg, ${C.cyan} 220deg, #9FF3FF 232deg, ${C.teal} 280deg, ${C.slate} 330deg, ${C.slate} 360deg)`,
      WebkitMaskImage: "radial-gradient(circle, transparent 47%, #000 54%, #000 60%, transparent 69%)",
      maskImage: "radial-gradient(circle, transparent 47%, #000 54%, #000 60%, transparent 69%)", filter: "blur(26px)" });
    const ring2 = el(stage, "abs", { left: "960px", top: "540px", width: "1240px", height: "1240px", borderRadius: "50%",
      background: `conic-gradient(from 0deg, transparent 150deg, ${C.cyan} 222deg, transparent 290deg)`,
      WebkitMaskImage: "radial-gradient(circle, transparent 52%, #000 55%, #000 57%, transparent 61%)",
      maskImage: "radial-gradient(circle, transparent 52%, #000 55%, #000 57%, transparent 61%)", filter: "blur(6px)" });
    const logoNode = centered(stage, "logo", 468, logo, { fontSize: "124px", lineHeight: "130px", textShadow: "0 0 40px rgba(39,210,230,.45)" });
    const ctaNode = centered(stage, "label", 622, cta, { fontSize: "34px", fontWeight: "500", color: C.text });
    return { ring, ring2, logoNode, ctaNode };
  }, (lt, dur, r) => {
    const breathe = 1 + 0.02 * Math.sin(lt * 2.2);
    const kIn = eOut(prog(lt, 0, 0.6));
    for (const ring of [r.ring, r.ring2]) {
      ring.style.transform = `translate(-50%, -50%) scale(${lerp(0.86, 1, kIn) * breathe})`;
      ring.style.opacity = kIn * (0.86 + 0.14 * Math.sin(lt * 2.2));
    }
    r.logoNode.style.opacity = eOut(prog(lt, 0.05, 0.45));
    r.logoNode.style.transform = `scale(${lerp(0.94, 1, eOut(prog(lt, 0.05, 0.6)))})`;
    wipe(r.ctaNode, lt, 0.45, 0.45);
  });
}

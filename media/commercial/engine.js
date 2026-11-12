/* Deterministic motion-graphics engine: a timeline of shots rendered as a pure function of time.
 *
 * renderAt(t) shows the shot active at time t (hard cuts) and lets it pose its elements for its
 * local time. Nothing depends on wall-clock time, so frame k is always identical and the video
 * can be captured frame by frame (media/render.py). Shared by the commercial and the demo cards.
 */
"use strict";

const W = 1920, H = 1080;
const C = {
  bg: "#0C111C", navy: "#0B2347", cyan: "#27D2E6", teal: "#62B0BC", slate: "#3D5A8A",
  lblue: "#7FB0F0", chead: "#1CCDE6", peri: "#6B7FD0", card: "#15181F", text: "#E6EAF0",
  muted: "#7A8394", coral: "#FF6B7A", green: "#3DDC97", blue2: "#5AA8F0",
};
/** 96 BPM: one 10-s beat = 4 bars exactly; cuts land on half-beats. */
const BPM = 96, HB = 60 / BPM / 2;

// ---------------------------------------------------------------- maths & easing
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const eOut = (k) => 1 - Math.pow(1 - k, 3);
const eInOut = (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
const eBack = (k) => { const c1 = 1.1, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); };
const tween = (t, a, b, from, to, ease = eOut) => lerp(from, to, ease(prog(t, a, b)));
const nf = (x, digits = 0) => x.toFixed(digits).replace(".", ",").replace(/\B(?=(\d{3})+(?!\d))/g, " ");

// ---------------------------------------------------------------- DOM helpers
function el(parent, cls = "", style = {}, html = "") {
  const node = document.createElement("div");
  if (cls) node.className = cls;
  Object.assign(node.style, style);
  if (html) node.innerHTML = html;
  if (parent) parent.appendChild(node);
  return node;
}
const put = (node, x, y, extra = "") => { node.style.transform = `translate(${x}px, ${y}px) ${extra}`; };
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/** Typewriter over styled segments: [{t: "text", c: "css class or ''"}]. Returns HTML of the first n chars. */
function typeRich(segments, n, caret = false) {
  let out = "", left = Math.max(0, Math.floor(n));
  for (const seg of segments) {
    if (left <= 0) break;
    const part = seg.t.slice(0, left);
    left -= part.length;
    out += seg.c ? `<span class="${seg.c}">${esc(part)}</span>` : esc(part);
  }
  return out + (caret ? '<span class="caret"></span>' : "");
}
const segLen = (segments) => segments.reduce((s, x) => s + x.t.length, 0);

// ---------------------------------------------------------------- the chrome star
let starCount = 0;
const STAR_PATH = "M0,-100 C10,-14 14,-10 100,0 C14,10 10,14 0,100 C-10,14 -14,10 -100,0 C-14,-10 -10,-14 0,-100 Z";
function makeStar(parent, size) {
  const id = `sg${starCount++}`;
  const wrap = el(parent, "star", { width: `${size}px`, height: `${size}px`, marginLeft: `${-size / 2}px`, marginTop: `${-size / 2}px` });
  wrap.innerHTML = `<svg viewBox="-110 -110 220 220" width="${size}" height="${size}">
    <defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#F4FFFF"/><stop offset=".22" stop-color="#8FEFF8"/>
      <stop offset=".45" stop-color="#27D2E6"/><stop offset=".68" stop-color="#3D5A8A"/>
      <stop offset=".86" stop-color="#9FE7F2"/><stop offset="1" stop-color="#E9FDFF"/></linearGradient>
      <radialGradient id="${id}h" cx=".35" cy=".3" r=".35"><stop offset="0" stop-color="#fff" stop-opacity=".95"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>
    <path d="${STAR_PATH}" fill="url(#${id})"/>
    <path d="${STAR_PATH}" fill="url(#${id}h)"/>
    <path d="${STAR_PATH}" fill="none" stroke="#DFFBFF" stroke-opacity=".7" stroke-width="2.2"/></svg>`;
  wrap.grad = wrap.querySelector(`#${id}`);
  return wrap;
}
/** Pose a star: position, scale, Y spin (degrees), Z roll, motion blur, opacity. */
function poseStar(star, { x, y, s = 1, ry = 0, rz = 0, blur = 0, o = 1 }) {
  star.style.transform = `translate(${x}px, ${y}px) rotateZ(${rz}deg) rotateY(${ry}deg) scale(${s})`;
  star.style.filter = `drop-shadow(0 0 ${18 * s}px rgba(39,210,230,.55)) ${blur ? `blur(${blur}px)` : ""}`;
  star.style.opacity = o;
  star.grad.setAttribute("gradientTransform", `rotate(${(ry * 0.6) % 360} .5 .5)`);  // iridescent shift
}

// ---------------------------------------------------------------- backgrounds
function aurora(parent, blobs) {
  return blobs.map((b) => el(parent, "blob", {
    left: `${b.x - b.w / 2}px`, top: `${b.y - b.h / 2}px`, width: `${b.w}px`, height: `${b.h}px`,
    background: `radial-gradient(ellipse at center, ${b.c} 0%, transparent 68%)`, opacity: b.o ?? 0.8,
  }));
}
function blueprint(parent) { return el(parent, "blueprint"); }

// ---------------------------------------------------------------- shots & timeline
const timelines = {};
let active = null;

/** Register a shot spanning [a, b) seconds. build(root) returns refs; render(lt, dur, refs). */
function shot(timeline, a, b, build, render, opts = {}) {
  const frame = document.getElementById("frame");
  const root = el(frame, "shot");
  const stage = el(root, "stage");
  const refs = build(stage, root) || {};
  refs.stage = stage;
  (timelines[timeline] ||= { shots: [], cues: [], duration: 0 }).shots.push({ a, b, root, refs, render, opts });
  timelines[timeline].duration = Math.max(timelines[timeline].duration, b);
}
const cue = (timeline, t, type, extra = {}) => (timelines[timeline] ||= { shots: [], cues: [], duration: 0 }).cues.push({ t, type, ...extra });

/** Camera = transform of the stage: continuous move within a shot. */
function camera(stage, { x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, s = 1, blur = 0 }) {
  stage.style.transform = `translate3d(${x}px, ${y}px, ${z}px) rotateX(${rx}deg) rotateY(${ry}deg) rotateZ(${rz}deg) scale(${s})`;
  stage.style.filter = blur ? `blur(${blur}px)` : "";
}

window.renderAt = function (t, name = "commercial") {
  const tl = timelines[name];
  for (const [key, other] of Object.entries(timelines)) if (key !== name) other.shots.forEach((s) => (s.root.style.display = "none"));
  let current = null;
  for (const s of tl.shots) {
    const on = t >= s.a && (t < s.b || (s === tl.shots[tl.shots.length - 1] && t <= s.b + 1e-6));
    s.root.style.display = on ? "block" : "none";
    if (on) current = s;
  }
  if (current) current.render(t - current.a, current.b - current.a, current.refs);
  active = current;
};
window.timelineInfo = (name) => ({ duration: timelines[name].duration, cues: timelines[name].cues });

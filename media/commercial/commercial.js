/* Vigie commercial — 40 s = 4 beats of 10 s (media/MASTER_PROMPT.md, Part 2).
 * Shot times are in half-beats (HB = 0.3125 s at 96 BPM) so every hard cut lands on the music.
 * Every figure on screen comes from the project's notebooks (reports/metrics). */
"use strict";

const TL = "commercial";
const at = (n) => n * HB;
/** Register a content shot on the half-beat grid; every hard cut gets a whoosh. */
function S(from, to, build, render) {
  if (from > 0) cue(TL, at(from), "whoosh");
  shot(TL, at(from), at(to), build, render);
}

// ====================================================================== BEAT 1 — hook & reveal
// S1 aurora hero
S(0, 4, (st) => {
  const arc = el(st, "abs", { left: "-120px", top: "-260px", width: "2400px", height: "1900px", borderRadius: "50%",
    border: "150px solid transparent", borderTopColor: C.teal, borderLeftColor: C.slate, filter: "blur(70px)", opacity: 0.9,
    transformOrigin: "50% 50%" });
  aurora(st, [{ x: 960, y: 1150, w: 1900, h: 560, c: C.navy, o: 1 }, { x: 1650, y: 120, w: 700, h: 420, c: C.slate, o: 0.3 }]);
  const logo = centered(st, "logo", 168, "✦ Vigie", { fontSize: "46px" });
  const head = centered(st, "headline", 238, "L'analyste SOC, augmenté", { fontSize: "132px", lineHeight: "150px" });
  const panel = glass(st, 470, 520, 980, 470, "", { transformOrigin: "50% 100%" });
  panel.innerHTML = `<div class="row" style="padding:28px 34px;gap:16px;border-bottom:1px solid rgba(127,176,240,.16)">
      <div class="badge" style="position:static;width:48px;height:48px;background:#E6EAF0;color:${C.cyan};font-size:26px">✦</div>
      <div class="label" style="font-size:28px">Vigie · assistant SOC</div><div style="flex:1"></div>
      <div class="muted" style="font-size:22px">● en ligne</div></div>
    <div class="bubble" style="left:34px;top:120px;background:#252B36;color:${C.text}">Quels IOC pour cette alerte ?</div>
    <div class="bubble" style="right:34px;top:210px;background:rgba(39,210,230,.16);border:1px solid rgba(39,210,230,.5)">89.62.172.13 · serveur C2 <span class="cyan">[S1]</span></div>
    <div class="abs" style="left:34px;top:320px;width:520px;height:18px;border-radius:9px;background:#232934"></div>
    <div class="abs" style="left:34px;top:356px;width:380px;height:18px;border-radius:9px;background:#1E242E"></div>`;
  const s1 = makeStar(st, 170), s2 = makeStar(st, 100);
  return { arc, logo, head, panel, s1, s2 };
}, (lt, d, r) => {
  camera(r.stage, { y: tween(lt, 0, d, 50, -10), s: tween(lt, 0, d, 0.95, 1.06) });
  r.arc.style.transform = `rotate(${tween(lt, 0, d, -30, 4)}deg)`;
  wipe(r.logo, lt, 0.0, 0.35);
  wipe(r.head, lt, 0.08, 0.5);
  r.panel.style.transform = `translateY(${tween(lt, 0.05, 0.9, 520, 0)}px) rotateX(${tween(lt, 0.05, 1.2, 46, 30)}deg)`;
  poseStar(r.s1, { x: 360 + lt * 40, y: tween(lt, 0, 0.9, 1100, 690), ry: lt * 160, rz: -18 + lt * 30 });
  poseStar(r.s2, { x: 1590 - lt * 30, y: tween(lt, 0.1, 1.0, 1150, 620), ry: 40 + lt * 200, rz: 22 - lt * 40 });
});

// S7 data — the SOC challenge
S(4, 8, (st) => {
  aurora(st, [{ x: 300, y: 120, w: 900, h: 600, c: C.slate, o: 0.35 }, { x: 960, y: 1150, w: 1900, h: 500, c: C.navy, o: 1 }]);
  const head = centered(st, "section", 230, "Le défi du SOC", { fontSize: "30px" });
  const data = [[2411, "rapports bruts"], [379, "entités de menace"], [5277, "relations dans le graphe"]];
  const cards = data.map(([n, label], i) => {
    const c = glass(st, 210 + i * 520, 360, 460, 300);
    c.innerHTML = `<div class="headline num" style="position:absolute;top:58px;width:100%;text-align:center;font-size:112px;line-height:120px"></div>
      <div class="label" style="position:absolute;top:196px;width:100%;text-align:center;font-size:30px;color:${C.muted}">${label}</div>`;
    c.num = c.querySelector(".num"); c.value = n;
    return c;
  });
  const sub = centered(st, "tagline", 742, 'Trop de signaux pour une lecture <span class="cyan">manuelle</span>.', { fontSize: "36px" });
  return { head, cards, sub };
}, (lt, d, r) => {
  camera(r.stage, { ry: tween(lt, 0, d, 9, -5), s: tween(lt, 0, d, 1.0, 1.05) });
  wipe(r.head, lt, 0, 0.3);
  r.cards.forEach((c, i) => {
    pop(c, lt, 0.08 + i * 0.09, 0.3);
    c.num.textContent = nf(Math.round(c.value * eOut(prog(lt, 0.12 + i * 0.09, 0.75 + i * 0.09))));
  });
  wipe(r.sub, lt, 0.7, 0.35);
});

// S2 card deck — the assistant
S(8, 12, (st) => {
  aurora(st, [{ x: 1700, y: 600, w: 600, h: 700, c: C.slate, o: 0.35 }, { x: 960, y: 1180, w: 1900, h: 500, c: C.navy, o: 1 }]);
  const orbs = [0, 1, 2, 3].map((i) => el(st, "abs", { left: `${1560 + (i % 2) * 140}px`, top: `${300 + i * 150}px`,
    width: `${60 + i * 26}px`, height: `${60 + i * 26}px`, borderRadius: "50%", background: "rgba(90,168,240,.18)",
    border: "1px solid rgba(127,176,240,.35)", filter: "blur(5px)" }));
  const search = glass(st, 410, 100, 1100, 96, "", { borderRadius: "48px" });
  search.innerHTML = `<div class="row" style="height:100%;padding:0 18px 0 34px;gap:18px">
    <span class="cyan" style="font-size:30px">✦</span><span class="muted" style="font-size:30px">Interroger la base de menaces…</span>
    <div style="flex:1"></div><div class="pill" style="position:static;height:62px;font-size:26px">✦ Analyser</div></div>`;
  const header = (bg, title, dark) => `<div class="row" style="height:84px;padding:0 26px;gap:16px;background:${bg};border-radius:26px 26px 0 0">
    <div class="badge" style="position:static;width:48px;height:48px;background:#F2F5F9;color:${C.cyan};font-size:24px">✦</div>
    <div class="label" style="font-size:27px;color:${dark ? C.text : "#0B1520"}">${title}</div><div style="flex:1"></div>
    ${icon("refresh", dark ? C.muted : "#0B1520", 30, 8)}</div>`;
  const back1 = glass(st, 510, 300, 900, 450, "soft"); back1.innerHTML = header(C.lblue, "Triage");
  const back2 = glass(st, 510, 300, 900, 450, "soft"); back2.innerHTML = header(C.chead, "Pivot CTI");
  const front = glass(st, 510, 300, 900, 450);
  const bullet = (name, n) => `<div class="row" style="margin:14px 0"><span class="sparkle">✦</span>
    <span class="label" style="font-size:28px;font-weight:600">${name}</span><span class="muted" style="font-size:24px">&nbsp;· ${n} documents</span></div>`;
  front.innerHTML = header("#1B212B", "Vigie Bot", true) + `<div style="padding:26px 40px">
    <div class="row" style="gap:16px;margin-bottom:18px">${icon("user", C.muted, 34, 7)}
      <span class="label" style="font-size:28px">Quels malwares ciblent le secteur bancaire ?</span></div>
    ${bullet("dridex", 4)}${bullet("emotet", 3)}${bullet("trickbot", 2)}
    <div class="muted" style="font-size:21px;margin-top:20px">Graphe STIX · relation TARGETS → banking · sources HF-01128, HF-02321…</div></div>`;
  const star = makeStar(st, 120);
  return { search, back1, back2, front, orbs, star };
}, (lt, d, r) => {
  camera(r.stage, { s: tween(lt, 0, d, 1.13, 1.0), y: tween(lt, 0, d, 40, 0) });
  wipe(r.search, lt, 0, 0.3);
  r.back1.style.transform = `translate(${tween(lt, 0, 0.5, 0, -70)}px, ${tween(lt, 0, 0.5, 0, -34)}px) rotate(${tween(lt, 0, 0.5, 0, -7)}deg)`;
  r.back2.style.transform = `translate(${tween(lt, 0, 0.5, 0, 40)}px, ${tween(lt, 0, 0.5, 0, -46)}px) rotate(${tween(lt, 0, 0.5, 0, 3)}deg)`;
  r.front.style.transform = `translateY(${tween(lt, 0, 0.4, 60, 0)}px)`;
  r.front.style.opacity = eOut(prog(lt, 0, 0.25));
  r.orbs.forEach((o, i) => (o.style.transform = `translateY(${Math.sin(lt * 2 + i) * 18}px)`));
  poseStar(r.star, { x: tween(lt, 0.2, d, -200, 2100, (k) => k), y: 900 - lt * 60, ry: lt * 300, rz: 20, s: 1.2, blur: 7 });
});

// S3 button press
buttonShot(TL, at(12), at(14), "✦ Analyser");
cue(TL, at(12), "whoosh");

// S4 blueprint typing — question → cited answer → Cypher
{
  const q = "Quelle CVE affecte log4j ?";
  const a1 = [{ t: "CVE-2021-44228 affecte log4j ", c: "" }, { t: "[S1]", c: "cyan" }];
  const code = "MATCH (x:Vulnerability)-[:AFFECTS]->(a:Software {name: 'log4j'})\nRETURN DISTINCT x.name";
  cue(TL, at(14) + 0.35, "type", { dur: 0.6 });
  cue(TL, at(14) + 1.3, "type", { dur: 0.8 });
  S(14, 21, (st) => {
    blueprint(st);
    aurora(st, [{ x: 960, y: 1150, w: 1900, h: 500, c: C.navy, o: 0.9 }]);
    const input = el(st, "abs", { left: "960px", top: "250px", borderRadius: "50px", border: `1px solid ${C.cyan}` });
    const avatar = el(st, "badge", { left: "392px", top: "262px", width: "76px", height: "76px", background: "#1B2230",
      border: "1px solid rgba(127,176,240,.4)" }, icon("user", C.lblue, 44, 7));
    const qText = el(st, "abs label", { left: "500px", top: "276px", fontSize: "36px" });
    const ai = el(st, "badge", { left: "392px", top: "430px", width: "76px", height: "76px", background: "linear-gradient(135deg,#27D2E6,#5AA8F0)",
      color: "#06202A", font: "800 28px var(--display)" }, "AI");
    const card = glass(st, 500, 420, 1040, 330, "", { overflow: "hidden" });
    card.innerHTML = `<div class="label a1" style="position:absolute;left:40px;top:36px;font-size:36px"></div>
      <div class="muted src" style="position:absolute;left:40px;top:96px;font-size:23px">Source : document HF-01308 · relation AFFECTS du graphe STIX</div>
      <pre class="mono code" style="position:absolute;left:40px;top:150px;width:960px;height:140px;margin:0;padding:22px 26px;border-radius:16px;
        background:#0B0F16;border:1px solid rgba(127,176,240,.2);color:${C.lblue};font-size:25px;line-height:1.5;white-space:pre-wrap"></pre>`;
    return { input, avatar, qText, ai, card, a1: card.querySelector(".a1"), src: card.querySelector(".src"), code: card.querySelector(".code") };
  }, (lt, d, r) => {
    camera(r.stage, { rx: tween(lt, 0, d, 0, 9), y: tween(lt, 0, d, 30, -30), s: tween(lt, 0, d, 1.03, 1.0) });
    const km = eOut(prog(lt, 0, 0.32));
    Object.assign(r.input.style, { width: `${lerp(420, 1160, km)}px`, height: `${lerp(10, 100, km)}px`,
      transform: "translate(-50%, 0)", background: km < 1 ? `linear-gradient(90deg, ${C.blue2}, ${C.peri})` : "rgba(21,24,31,.92)",
      boxShadow: `0 0 ${lerp(60, 30, km)}px rgba(90,168,240,.5)`, borderColor: km < 1 ? "transparent" : C.cyan });
    pop(r.avatar, lt, 0.3, 0.25);
    r.qText.innerHTML = typeRich([{ t: q, c: "" }], (lt - 0.35) * 42, lt > 0.3 && lt < 1.1);
    pop(r.ai, lt, 1.0, 0.25);
    const kc = eOut(prog(lt, 1.05, 1.3));
    r.card.style.height = `${330 * kc}px`; r.card.style.opacity = kc > 0 ? 1 : 0;
    r.a1.innerHTML = typeRich(a1, (lt - 1.3) * 80);
    r.src.style.opacity = eOut(prog(lt, 1.6, 1.8));
    r.code.textContent = code.slice(0, Math.max(0, Math.floor((lt - 1.65) * 190)));
  });
}

// S5 screen arc — the three workspaces of Vigie
S(21, 26, (st) => {
  aurora(st, [{ x: 960, y: 1150, w: 1900, h: 520, c: C.navy, o: 1 }, { x: 960, y: 120, w: 1200, h: 360, c: C.slate, o: 0.3 }]);
  const arc = el(st, "abs", { left: "0", top: "0", width: "1920px", height: "1080px", transformStyle: "preserve-3d" });
  const screen = (x, ry, z, headerBg, title, body, tag, dark) => {
    const s = glass(arc, x, 230, 400, 730, "", { borderRadius: "46px", overflow: "hidden",
      transform: `translateZ(${z}px) rotateY(${ry}deg)` });
    s.innerHTML = `<div class="row" style="height:96px;padding:0 26px;gap:14px;background:${headerBg}">
      <div class="badge" style="position:static;width:44px;height:44px;background:#F2F5F9;color:${C.cyan};font-size:22px">✦</div>
      <span class="label" style="font-size:26px;color:${dark ? C.text : "#0B1520"}">${title}</span></div>${body}`;
    const t = el(arc, "tag", { left: `${x + 200}px`, top: "170px", transform: `translateX(-50%) translateZ(${z}px) rotateY(${ry}deg)` }, tag);
    return { s, t };
  };
  const chip = (txt, col) => `<span class="chip" style="background:${col}22;color:${col};border:1px solid ${col}66;margin:0 8px 10px 0">${txt}</span>`;
  screen(250, 26, -160, C.chead, "Triage", `<div style="padding:28px 26px">
      <div class="pill" style="position:static;height:52px;font-size:24px;border-color:${C.coral};color:${C.coral}">Priorité suggérée</div>
      <div class="label" style="font-size:24px;margin:26px 0 14px">Entités extraites</div>
      ${chip("LockBit", C.coral)}${chip("CVE-2023-4966", C.cyan)}${chip("Citrix", C.lblue)}${chip("hospitals", C.teal)}
      <div class="label" style="font-size:24px;margin:26px 0 12px">Playbook NIST SP 800-61</div>
      <div class="muted" style="font-size:21px;line-height:1.8">① Confinement<br>② Éradication<br>③ Rétablissement</div>
      <div class="muted" style="font-size:21px;margin-top:18px">TTP ATT&CK · IOC · escalade</div></div>`, "Triage");
  screen(760, 0, 0, C.lblue, "Vigie", `<div class="bubble" style="left:24px;top:130px;width:300px;background:#2A303C">Bonjour, quelle alerte analysons-nous ?</div>
      <div class="bubble" style="right:24px;top:300px;width:260px;background:#3E6FD8;color:#fff">Quels IOC pour cette alerte ?</div>
      <div class="bubble" style="left:24px;top:430px;width:310px;background:#2A303C">89.62.172.13 · serveur C2 <span class="cyan">[S1]</span></div>`,
    "Investigation");
  screen(1270, -26, -160, "#1B212B", "Détection", `<div style="padding:28px 26px">
      ${chip("Splunk SPL", C.cyan)}${chip("Sentinel KQL", C.lblue)}
      <pre class="mono" style="margin:20px 0;font-size:18px;line-height:1.55;color:${C.lblue};white-space:pre-wrap">search index=*\n(src_ip IN\n ("89.62.172.13"))</pre>
      <pre class="mono" style="margin:0 0 20px;font-size:18px;line-height:1.55;color:${C.lblue};white-space:pre-wrap">CommonSecurityLog
| where SourceIP in
 ("89.62.172.13")</pre>
      <div class="label" style="font-size:22px;color:${C.green}">✓ IOC validés · règle prête</div></div>`, "Détection", true);
  return { arc };
}, (lt, d, r) => {
  const whip = prog(lt, d - 0.2, d);
  r.arc.style.transform = `rotateY(${tween(lt, 0, d - 0.2, 14, -12, eInOut)}deg) translateX(${lerp(0, -1400, eInOut(whip))}px)`;
  camera(r.stage, { s: tween(lt, 0, d, 1.06, 1.0), blur: whip * 22 });
});

// S8 + S9 star bridge → beat 2
cue(TL, at(26), "whoosh");
bridgeShot(TL, at(26), at(32), [["Du rapport brut", "au graphe de menaces"]], { cps: 26 });

// ====================================================================== BEAT 2 — how it works
// S4 variant: NER on an incoming report
{
  const ENT = { MALWARE: C.coral, VECTOR: C.peri, CVE: C.cyan, SOFTWARE: C.lblue, TARGET: C.teal, IP: C.chead };
  const segs = [["The ", ""], ["LockBit", "MALWARE"], [" ", ""], ["ransomware", "VECTOR"], [" gang exploited ", ""],
    ["CVE-2023-4966", "CVE"], [" in ", ""], ["Citrix", "SOFTWARE"], [" NetScaler to target ", ""], ["hospitals", "TARGET"],
    [" from ", ""], ["89.62.172.13", "IP"], [".", ""]];
  const total = segs.reduce((s, x) => s + x[0].length, 0);
  cue(TL, at(32) + 0.05, "type", { dur: 0.7 });
  segs.filter((x) => x[1]).forEach((_, i) => cue(TL, at(32) + 0.82 + i * 0.09, "pop"));
  S(32, 37, (st) => {
    aurora(st, [{ x: 200, y: 150, w: 900, h: 600, c: C.slate, o: 0.35 }, { x: 960, y: 1150, w: 1900, h: 500, c: C.navy, o: 1 }]);
    const card = glass(st, 230, 300, 1460, 430);
    card.innerHTML = `<div class="row" style="padding:30px 44px 0;gap:18px"><span class="section" style="font-size:22px">Signalement entrant</span>
      <div style="flex:1"></div><span class="muted" style="font-size:22px">NER cyber · STIX 2.1</span></div>
      <div class="txt label" style="position:absolute;left:44px;top:130px;width:1370px;font-size:42px;line-height:96px;font-weight:400;white-space:normal"></div>`;
    const txt = card.querySelector(".txt");
    const spans = segs.map(([t, lab]) => {
      const s = document.createElement("span");
      if (lab) {
        Object.assign(s.style, { position: "relative", borderRadius: "8px", padding: "2px 6px", margin: "0 -6px" });
        const chipNode = document.createElement("span");
        chipNode.className = "chip";
        Object.assign(chipNode.style, { position: "absolute", left: "50%", top: "-44px", fontSize: "15px", lineHeight: "20px",
          background: `${ENT[lab]}26`, color: ENT[lab], border: `1px solid ${ENT[lab]}88`, whiteSpace: "nowrap" });
        chipNode.textContent = lab;
        s.chipNode = chipNode;
      }
      s.full = t; s.lab = lab;
      txt.appendChild(s);
      return s;
    });
    return { card, spans };
  }, (lt, d, r) => {
    camera(r.stage, { s: tween(lt, 0, d, 1.0, 1.06), ry: tween(lt, 0, d, -5, 4) });
    pop(r.card, lt, 0, 0.2);
    let left = Math.floor((lt - 0.05) * (total / 0.7)), k = 0;
    r.spans.forEach((s) => {
      const n = clamp(left, 0, s.full.length); left -= s.full.length;
      s.textContent = s.full.slice(0, n);
      if (s.lab) {
        const kp = prog(lt, 0.82 + k * 0.09, 1.1 + k * 0.09); k++;
        const col = ENT[s.lab];
        s.style.background = kp > 0 ? `${col}${Math.round(kp * 40).toString(16).padStart(2, "0")}` : "transparent";
        s.style.boxShadow = kp > 0 ? `inset 0 -3px 0 ${col}` : "none";
        if (kp > 0 && n === s.full.length) {
          s.appendChild(s.chipNode);
          s.chipNode.style.transform = `translateX(-50%) scale(${eBack(kp)})`;
          s.chipNode.style.opacity = clamp(kp * 3);
        }
      }
    });
  });
}

// S7 graph — the report becomes STIX 2.1 facts
{
  const nodes = [["LockBit", "Malware", 960, 520, C.coral], ["CVE-2023-4966", "Vulnerability", 600, 320, C.cyan],
    ["Citrix", "Software", 360, 590, C.lblue], ["hospitals", "Target", 1320, 320, C.teal],
    ["ransomware", "AttackPattern", 1360, 720, C.peri], ["89.62.172.13", "Indicator", 680, 800, C.chead]];
  const edges = [[0, 1, "EXPLOITS"], [1, 2, "AFFECTS"], [0, 3, "TARGETS"], [0, 4, "USES"], [5, 0, "INDICATES"]];
  nodes.forEach((_, i) => cue(TL, at(37) + 0.05 + i * 0.07, "pop"));
  S(37, 43, (st) => {
    aurora(st, [{ x: 960, y: 540, w: 1400, h: 900, c: C.navy, o: 0.9 }]);
    let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const bg = Array.from({ length: 46 }, () => [rnd() * 1920, rnd() * 1080]);
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("width", 1920); svg.setAttribute("height", 1080); svg.setAttribute("class", "abs");
    let far = "";
    bg.forEach(([x, y], i) => {
      const [x2, y2] = bg[(i * 7 + 3) % bg.length];
      far += `<line x1="${x}" y1="${y}" x2="${x2}" y2="${y2}" stroke="#3D5A8A" stroke-opacity=".25" stroke-width="1.5"/><circle cx="${x}" cy="${y}" r="5" fill="#62B0BC" fill-opacity=".35"/>`;
    });
    svg.innerHTML = `<g style="filter:blur(3px)">${far}</g>` + edges.map(([a, b, rel], i) => {
      const [, , x1, y1] = nodes[a], [, , x2, y2] = nodes[b];
      return `<line class="e" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${C.cyan}" stroke-width="3" stroke-opacity=".8"/>
        <text class="el" x="${(x1 + x2) / 2}" y="${(y1 + y2) / 2 - 14}" text-anchor="middle" fill="${C.teal}" font-family="Adwaita Sans" font-size="20" letter-spacing="3">${rel}</text>`;
    }).join("");
    st.appendChild(svg);
    const nodeEls = nodes.map(([name, type, x, y, col]) => {
      const n = el(st, "abs", { left: `${x}px`, top: `${y}px` });
      n.innerHTML = `<div style="position:absolute;left:-30px;top:-30px;width:60px;height:60px;border-radius:50%;background:${col}33;border:2px solid ${col};box-shadow:0 0 30px ${col}88"></div>
        <div class="muted" style="position:absolute;left:-150px;width:300px;top:-64px;text-align:center;font-size:18px;letter-spacing:.12em">${type.toUpperCase()}</div>
        <div class="label" style="position:absolute;left:-150px;width:300px;top:40px;text-align:center;font-size:27px">${name}</div>`;
      return n;
    });
    const counter = centered(st, "tagline", 950, 'Graphe STIX 2.1 · <span class="cyan">2 573 nœuds · 5 277 arêtes</span> · provenance sur chaque arête', { fontSize: "30px" });
    return { svg, nodeEls, counter, lines: [...svg.querySelectorAll(".e")], labels: [...svg.querySelectorAll(".el")] };
  }, (lt, d, r) => {
    camera(r.stage, { ry: tween(lt, 0, d, -12, 9, eInOut), rx: 5, s: tween(lt, 0, d, 0.96, 1.03) });
    r.nodeEls.forEach((n, i) => pop(n, lt, 0.05 + i * 0.07, 0.3));
    r.lines.forEach((l, i) => {
      const len = Math.hypot(l.x2.baseVal.value - l.x1.baseVal.value, l.y2.baseVal.value - l.y1.baseVal.value);
      const k = eOut(prog(lt, 0.4 + i * 0.12, 0.75 + i * 0.12));
      l.setAttribute("stroke-dasharray", `${len}`); l.setAttribute("stroke-dashoffset", `${len * (1 - k)}`);
      r.labels[i].setAttribute("opacity", eOut(prog(lt, 0.7 + i * 0.12, 0.9 + i * 0.12)));
    });
    wipe(r.counter, lt, 1.25, 0.4);
  });
}

// S6 tile grid — the building blocks
{
  const tiles = [["book", C.green, "Corpus CTI"], ["tag", C.coral, "NER cyber"], ["graph", C.lblue, "Graphe STIX"],
    ["layers", C.cyan, "FAISS · E5"], ["db", C.lblue, "Neo4j"], ["chip", C.teal, "Qwen local"],
    ["target", C.green, "MITRE ATT&CK"], ["bolt", "#F5C451", "SIEM"]];
  tiles.forEach((_, i) => cue(TL, at(43) + 0.32 + i * 0.07, "pop"));
  S(43, 49, (st) => {
    aurora(st, [{ x: 960, y: 1150, w: 1900, h: 520, c: C.navy, o: 1 }, { x: 1700, y: 200, w: 600, h: 500, c: C.slate, o: 0.3 }]);
    const top = el(st, "abs", { left: "0", top: "0", width: "1920px", height: "400px" });
    const head = centered(top, "section", 112, "Connectez vos sources", { fontSize: "30px" });
    const hs = makeStar(top, 50);
    const panel = el(top, "abs", { left: "460px", top: "190px", width: "1000px", height: "130px" });
    panel.innerHTML = `<svg width="1000" height="130" style="position:absolute;inset:0"><polygon points="40,2 960,2 998,128 2,128"
      fill="#15181F" stroke="${C.cyan}" stroke-opacity=".75" stroke-width="1.5" style="filter:drop-shadow(0 0 14px rgba(39,210,230,.4))"/></svg>
      <div class="label" style="position:absolute;width:100%;top:34px;text-align:center;font:700 50px var(--display)">Du texte au <i class="cyan">graphe</i> de menaces</div>`;
    const grid = el(st, "abs", { left: "0", top: "0", width: "1920px", height: "1080px", transformStyle: "preserve-3d" });
    const tileEls = tiles.map(([ic, col, name], i) => {
      const t = el(grid, "tile", { left: `${500 + (i % 4) * 240}px`, top: `${400 + Math.floor(i / 4) * 250}px` },
        `${icon(ic, col, 84, 6)}<div class="name">${name}</div>`);
      return t;
    });
    return { top, head, hs, panel, tileEls };
  }, (lt, d, r) => {
    const fly = eInOut(prog(lt, 0.95, d));
    camera(r.stage, { s: tween(lt, 0, 0.95, 1.0, 1.07) * lerp(1, 1.08, fly), rx: lerp(0, 34, fly), rz: lerp(0, -16, fly), y: lerp(0, -110, fly) });
    r.top.style.filter = `blur(${fly * 6}px)`;
    wipe(r.head, lt, 0, 0.3);
    poseStar(r.hs, { x: 960 - 290, y: 128, s: 1, ry: lt * 260 });
    r.panel.style.opacity = eOut(prog(lt, 0.1, 0.35));
    r.panel.style.transform = `translateY(${tween(lt, 0.1, 0.4, 20, 0)}px)`;
    r.tileEls.forEach((t, i) => pop(t, lt, 0.32 + i * 0.07, 0.3));
  });
}

// S7 fusion — HybridRAG: vectors + graph → re-ranking → cited evidence
{
  [0, 1, 2].forEach((i) => cue(TL, at(49) + 1.0 + i * 0.13, "pop"));
  S(49, 55, (st) => {
    aurora(st, [{ x: 960, y: 520, w: 900, h: 700, c: C.navy, o: 0.9 }]);
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("width", 1920); svg.setAttribute("height", 1080); svg.setAttribute("class", "abs");
    const paths = ["M720 375 C 820 375, 840 520, 860 530", "M720 635 C 820 635, 840 545, 860 545", "M1060 540 C 1110 540, 1130 520, 1180 520"];
    svg.innerHTML = paths.map((d) => `<path d="${d}" fill="none" stroke="${C.slate}" stroke-width="3" stroke-dasharray="6 10"/>`).join("") +
      Array.from({ length: 12 }, () => `<circle r="7" fill="${C.cyan}" style="filter:drop-shadow(0 0 8px #27D2E6)"/>`).join("");
    st.appendChild(svg);
    const src1 = glass(st, 190, 300, 530, 150); src1.innerHTML = `<div style="padding:30px 34px"><div class="label" style="font-size:32px">Recherche vectorielle</div><div class="muted" style="font-size:24px;margin-top:10px">E5 multilingue · FAISS</div></div>`;
    const src2 = glass(st, 190, 560, 530, 150); src2.innerHTML = `<div style="padding:30px 34px"><div class="label" style="font-size:32px">Faits du graphe</div><div class="muted" style="font-size:24px;margin-top:10px">STIX 2.1 · provenance</div></div>`;
    const core = el(st, "badge", { left: "860px", top: "440px", width: "200px", height: "200px", background: "radial-gradient(circle at 40% 35%, #1D3A55, #0E1622)",
      border: `2px solid ${C.cyan}`, flexDirection: "column", gap: "6px" },
    `<span class="label" style="font-size:26px">Re-ranking</span><span class="muted" style="font-size:19px">cross-encodeur</span>`);
    const ev = glass(st, 1180, 300, 560, 440);
    const row = (s, txt) => `<div class="evr row" style="margin:20px 0;gap:14px"><span class="chip" style="background:rgba(39,210,230,.15);color:${C.cyan};border:1px solid rgba(39,210,230,.5)">${s}</span><span class="label" style="font-size:24px;white-space:normal">${txt}</span></div>`;
    ev.innerHTML = `<div style="padding:30px 32px"><div class="section" style="font-size:22px">Preuves citées</div>
      ${row("S1", "Fait du graphe · CVE-2021-44228 → log4j")}${row("S2", "Extrait · document HF-01308")}${row("S3", "Extrait · document voisin")}</div>`;
    const pill = el(st, "pill", { left: "960px", top: "880px", height: "70px", fontSize: "28px", background: "rgba(21,24,31,.9)" },
      'Recall@4 <span class="cyan">0,857</span> · MRR <span class="cyan">0,789</span> · 300 questions');
    return { svg, paths: [...svg.querySelectorAll("path")], dots: [...svg.querySelectorAll("circle")], src1, src2, core, ev, rows: [...ev.querySelectorAll(".evr")], pill };
  }, (lt, d, r) => {
    camera(r.stage, { x: tween(lt, 0, d, 40, -40), s: 1.02 });
    pop(r.src1, lt, 0, 0.25); pop(r.src2, lt, 0.06, 0.25); pop(r.core, lt, 0.25, 0.3); pop(r.ev, lt, 0.75, 0.3);
    r.core.style.boxShadow = `0 0 ${40 + 25 * Math.sin(lt * 9)}px rgba(39,210,230,.55)`;
    r.dots.forEach((dot, i) => {
      const p = r.paths[i < 8 ? i % 2 : 2], L = p.getTotalLength();
      const start = i < 8 ? 0.2 + Math.floor(i / 2) * 0.12 : 0.85 + (i - 8) * 0.1;
      const k = prog(lt, start, start + 0.35);
      const pt = p.getPointAtLength(L * eInOut(k));
      dot.setAttribute("cx", pt.x); dot.setAttribute("cy", pt.y);
      dot.setAttribute("opacity", k > 0 && k < 1 ? 1 : 0);
    });
    r.rows.forEach((row, i) => wipe(row, lt, 1.0 + i * 0.13, 0.28));
    pop(r.pill, lt, 1.4, 0.3, "translate(-50%, 0)");
  });
}

// S4 code variant — Text-to-Cypher with ReAct repair
{
  const bad = [{ t: "MATCH (c:", c: "" }, { t: "CVE", c: "bad" }, { t: ")-[:AFFECTS]->(s:Software {name: 'log4j'})", c: "" }];
  const good = [{ t: "MATCH (c:", c: "" }, { t: "Vulnerability", c: "cyan" }, { t: ")-[:AFFECTS]->(s:Software {name: 'log4j'})", c: "" }];
  cue(TL, at(55) + 0.05, "type", { dur: 0.35 });
  cue(TL, at(55) + 0.8, "type", { dur: 0.3 });
  cue(TL, at(55) + 1.25, "pop");
  S(55, 60, (st) => {
    blueprint(st);
    aurora(st, [{ x: 960, y: 1150, w: 1900, h: 500, c: C.navy, o: 0.9 }]);
    const card = glass(st, 260, 220, 1400, 560);
    card.innerHTML = `<div class="row" style="padding:30px 44px;gap:16px;border-bottom:1px solid rgba(127,176,240,.16)">
        <span class="label" style="font-size:30px">Text-to-Cypher · agent ReAct</span><div style="flex:1"></div>
        <span class="muted" style="font-size:22px">gabarits guidés par le schéma + Qwen2.5-1.5B</span></div>
      <div style="padding:26px 44px;font-size:27px" class="mono">
        <div class="l1" style="height:44px"></div>
        <div class="err coral" style="height:44px;font-size:22px">✗ Unknown label \`CVE\`. Known labels: [AttackPattern, …, Vulnerability]</div>
        <div class="fix muted" style="height:50px;font-size:22px;font-family:var(--ui)">↻ Réparation guidée par le schéma : CVE → Vulnerability</div>
        <div class="l2" style="height:44px"></div>
        <div class="res" style="height:50px;font-size:24px;color:${C.green}">✓ CVE-2021-44228</div></div>`;
    const badge = el(st, "pill", { left: "960px", top: "830px", height: "70px", fontSize: "28px", background: "rgba(21,24,31,.9)" },
      '<span class="cyan">✓ 100 %</span> de réponses exactes · jeu de validation');
    const q = (s) => card.querySelector(s);
    return { card, badge, l1: q(".l1"), err: q(".err"), fix: q(".fix"), l2: q(".l2"), res: q(".res") };
  }, (lt, d, r) => {
    camera(r.stage, { s: tween(lt, 0, d, 1.0, 1.06), rx: tween(lt, 0, d, 5, 0) });
    pop(r.card, lt, 0, 0.18);
    r.l1.innerHTML = typeRich(bad, (lt - 0.05) * 150).replace('class="bad"', `style="text-decoration:${lt > 0.42 ? "underline wavy " + C.coral : "none"};text-underline-offset:6px"`);
    wipe(r.err, lt, 0.45, 0.2); wipe(r.fix, lt, 0.65, 0.2);
    r.l2.innerHTML = typeRich(good, (lt - 0.8) * 190);
    wipe(r.res, lt, 1.12, 0.15);
    pop(r.badge, lt, 1.25, 0.3, "translate(-50%, 0)");
  });
}

cue(TL, at(60), "whoosh");
bridgeShot(TL, at(60), at(64), [["Des réponses", "prouvées"]], { cps: 24 });

// ====================================================================== BEAT 3 — trust & security
// S7 grounding — every sentence must be backed by evidence
{
  const sentences = ["CVE-2021-44228 (Log4Shell) affecte la bibliothèque log4j.", "Appliquer le correctif et vérifier la version installée.",
    "La faille a été découverte en 2019."];
  [0, 1].forEach((i) => cue(TL, at(64) + 0.7 + i * 0.08, "pop"));
  S(64, 69, (st) => {
    aurora(st, [{ x: 1700, y: 200, w: 700, h: 500, c: C.slate, o: 0.3 }, { x: 960, y: 1150, w: 1900, h: 500, c: C.navy, o: 1 }]);
    const card = glass(st, 300, 230, 1320, 520);
    card.innerHTML = `<div class="row" style="padding:30px 44px;gap:16px;border-bottom:1px solid rgba(127,176,240,.16)">
      <div class="badge" style="position:static;width:46px;height:46px;background:#F2F5F9;color:${C.cyan};font-size:24px">✦</div>
      <span class="label" style="font-size:30px">Réponse de Vigie</span><div style="flex:1"></div>
      <span class="muted" style="font-size:22px">contrôle de fidélité phrase par phrase</span></div>
      <div style="padding:20px 44px">${sentences.map((s, i) => `<div class="srow row" style="height:96px;gap:18px;position:relative">
        <span class="stxt label" style="font-size:31px;font-weight:400">${s}</span>
        <span class="sb chip" style="${i < 2 ? `background:rgba(39,210,230,.15);color:${C.cyan};border:1px solid rgba(39,210,230,.5)` : `background:rgba(255,107,122,.15);color:${C.coral};border:1px solid rgba(255,107,122,.5)`}">${i < 2 ? `S${i + 1}` : "non étayée · retirée"}</span>
        ${i === 2 ? `<div class="strike" style="position:absolute;left:0;top:47px;height:3px;background:${C.coral}"></div>` : ""}</div>`).join("")}</div>`;
    const pill = el(st, "pill", { left: "960px", top: "820px", height: "70px", fontSize: "28px", background: "rgba(21,24,31,.9)" },
      '<span class="cyan">100 %</span> des phrases conservées sont étayées');
    return { card, pill, rows: [...card.querySelectorAll(".srow")], badges: [...card.querySelectorAll(".sb")], strike: card.querySelector(".strike") };
  }, (lt, d, r) => {
    camera(r.stage, { s: tween(lt, 0, d, 1.0, 1.05), ry: tween(lt, 0, d, 4, -3) });
    pop(r.card, lt, 0, 0.18);
    r.rows.forEach((row, i) => wipe(row.querySelector(".stxt"), lt, 0.08 + i * 0.14, 0.3));
    r.badges.forEach((b, i) => pop(b, lt, i < 2 ? 0.7 + i * 0.08 : 0.95, 0.25));
    r.strike.style.width = `${tween(lt, 0.75, 0.95, 0, 600)}px`;
    const fade = prog(lt, 1.05, 1.3);
    r.rows[2].style.opacity = lerp(1, 0.22, fade);
    pop(r.pill, lt, 1.2, 0.3, "translate(-50%, 0)");
  });
}

// S7 graph audit — GragPoison detection and quarantine
{
  cue(TL, at(69) + 0.95, "pop");
  S(69, 75, (st) => {
    aurora(st, [{ x: 960, y: 1150, w: 1900, h: 500, c: C.navy, o: 1 }]);
    const head = centered(st, "section", 120, "Audit d'empoisonnement du graphe", { fontSize: "28px" });
    let seed = 11; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const pts = Array.from({ length: 22 }, (_, i) => [260 + (i % 6) * 250 + rnd() * 110, 260 + Math.floor(i / 6) * 170 + rnd() * 80]);
    const hub = [1180, 520];
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("width", 1920); svg.setAttribute("height", 1080); svg.setAttribute("class", "abs");
    let g = "";
    pts.forEach(([x, y], i) => { const [x2, y2] = pts[(i + 1) % pts.length], [x3, y3] = pts[(i + 6) % pts.length];
      g += `<line x1="${x}" y1="${y}" x2="${x2}" y2="${y2}" stroke="${C.teal}" stroke-opacity=".35" stroke-width="2"/>
            <line x1="${x}" y1="${y}" x2="${x3}" y2="${y3}" stroke="${C.teal}" stroke-opacity=".22" stroke-width="2"/>`; });
    const poisoned = [0, 2, 3, 5, 7, 9, 12, 14, 16, 19, 21];
    g += poisoned.map((i) => `<line class="pe" x1="${hub[0]}" y1="${hub[1]}" x2="${pts[i][0]}" y2="${pts[i][1]}" stroke="${C.coral}" stroke-width="2.5"/>`).join("");
    g += pts.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="11" fill="#15181F" stroke="${C.teal}" stroke-width="3"/>`).join("");
    svg.innerHTML = g;
    st.appendChild(svg);
    const hubEl = el(st, "abs", { left: `${hub[0]}px`, top: `${hub[1]}px` });
    hubEl.innerHTML = `<div style="position:absolute;left:-34px;top:-34px;width:68px;height:68px;border-radius:50%;background:${C.coral}33;border:3px solid ${C.coral};box-shadow:0 0 40px ${C.coral}"></div>
      <div class="label" style="position:absolute;left:-160px;width:320px;top:44px;text-align:center;font-size:26px;color:${C.coral}">updatehelper</div>
      <div class="muted" style="position:absolute;left:-160px;width:320px;top:80px;text-align:center;font-size:19px">source : pastebin · non approuvée</div>`;
    const scan = el(st, "abs", { left: "0", top: "180px", width: "6px", height: "780px", background: C.cyan, boxShadow: `0 0 40px 10px rgba(39,210,230,.55)` });
    const quarantine = glass(st, 1430, 800, 380, 120, "", { borderColor: "rgba(255,107,122,.7)" });
    quarantine.innerHTML = `<div style="padding:24px 28px"><div class="label coral" style="font-size:28px">Quarantaine</div><div class="muted" style="font-size:20px;margin-top:6px">34 arêtes injectées · 32 retirées</div></div>`;
    const pill = el(st, "pill", { left: "960px", top: "960px", height: "70px", fontSize: "28px", background: "rgba(21,24,31,.9)" },
      'Précision <span class="cyan">1,00</span> · Rappel <span class="cyan">0,94</span> · <span class="cyan">0</span> faux positif');
    return { head, svg, pe: [...svg.querySelectorAll(".pe")], hubEl, scan, quarantine, pill };
  }, (lt, d, r) => {
    camera(r.stage, { ry: tween(lt, 0, d, 7, -6), s: tween(lt, 0, d, 1.0, 1.04) });
    wipe(r.head, lt, 0, 0.3);
    const sx = tween(lt, 0.15, 0.95, 120, 1800, (k) => k);
    r.scan.style.transform = `translateX(${sx}px)`; r.scan.style.opacity = lt > 0.12 && lt < 1.0 ? 1 : 0;
    const flagged = sx > 1180;
    const dissolve = prog(lt, 0.95, 1.35);
    r.pe.forEach((l) => l.setAttribute("stroke-opacity", flagged ? (1 - dissolve) * (0.6 + 0.4 * Math.sin(lt * 40)) : 0.85));
    const kq = eInOut(prog(lt, 0.95, 1.35));
    r.hubEl.style.transform = `translate(${lerp(0, 440, kq)}px, ${lerp(0, 330, kq)}px) scale(${lerp(1, 0.5, kq)})`;
    r.hubEl.style.opacity = lerp(1, 0, prog(lt, 1.2, 1.4));
    pop(r.quarantine, lt, 0.95, 0.3);
    pop(r.pill, lt, 1.35, 0.3, "translate(-50%, 0)");
  });
}

// S3 button press → export the rule
buttonShot(TL, at(75), at(77), "✦ Exporter la règle");
cue(TL, at(75), "whoosh");

// S4 code variant — SIEM rules from validated IOCs only
{
  const spl = 'search index=* earliest=-24h ((src_ip IN ("89.62.172.13") OR dest_ip IN ("89.62.172.13")))';
  const kql = 'CommonSecurityLog\n| where TimeGenerated > ago(24h)\n| where SourceIP in ("89.62.172.13") or DestinationIP in ("89.62.172.13")';
  const iocs = [["✓", "89.62.172.13", "retenu · serveur C2", C.green], ["✗", "10.0.0.5", "adresse non routable", C.coral],
    ["✗", "192.0.2.10", "plage de documentation", C.coral], ["✗", "8.8.8.8", "résolveur DNS public", C.coral]];
  iocs.forEach((_, i) => cue(TL, at(77) + 0.1 + i * 0.13, "pop"));
  cue(TL, at(77) + 0.55, "type", { dur: 1.0 });
  S(77, 83, (st) => {
    aurora(st, [{ x: 300, y: 200, w: 800, h: 600, c: C.slate, o: 0.3 }, { x: 960, y: 1150, w: 1900, h: 500, c: C.navy, o: 1 }]);
    const left = glass(st, 120, 230, 660, 560);
    left.innerHTML = `<div style="padding:30px 36px"><div class="section" style="font-size:22px">Validation des IOC</div>
      ${iocs.map(([m, v, why, col]) => `<div class="ioc row" style="height:104px;gap:20px;border-bottom:1px solid rgba(127,176,240,.1)">
        <span style="font-size:34px;color:${col};width:34px">${m}</span>
        <div><div class="mono" style="font-size:28px;color:${C.text}">${v}</div><div style="font-size:21px;color:${col}">${why}</div></div></div>`).join("")}</div>`;
    const codeCard = (y, title, col) => {
      const c = glass(st, 840, y, 960, y === 230 ? 230 : 300);
      c.innerHTML = `<div style="padding:26px 32px"><span class="chip" style="background:${col}22;color:${col};border:1px solid ${col}66">${title}</span>
        <pre class="mono code" style="margin:18px 0 0;font-size:23px;line-height:1.55;color:${C.lblue};white-space:pre-wrap"></pre></div>`;
      c.code = c.querySelector(".code");
      return c;
    };
    const c1 = codeCard(230, "Splunk SPL", C.cyan), c2 = codeCard(490, "Microsoft Sentinel KQL", C.lblue);
    return { left, rows: [...left.querySelectorAll(".ioc")], c1, c2 };
  }, (lt, d, r) => {
    camera(r.stage, { ry: tween(lt, 0, d, -7, 6), s: tween(lt, 0, d, 1.0, 1.04) });
    pop(r.left, lt, 0, 0.2);
    r.rows.forEach((row, i) => wipe(row, lt, 0.1 + i * 0.13, 0.25));
    pop(r.c1, lt, 0.4, 0.22); pop(r.c2, lt, 0.5, 0.22);
    r.c1.code.textContent = spl.slice(0, Math.max(0, Math.floor((lt - 0.55) * 170)));
    r.c2.code.textContent = kql.slice(0, Math.max(0, Math.floor((lt - 0.95) * 190)));
  });
}

// S6/S7 measured results
{
  const M = [[0.857, 3, "", "Recherche hybride", "Recall@4 · 300 questions"], [100, 0, " %", "Text-to-Cypher", "réponses exactes (validation)"],
    [100, 0, " %", "Abstention hors domaine", "12 questions sur 12"], [0.91, 2, "", "NER SecBERT", "micro-F1"],
    [10, 0, "/10", "Garde-fou anti-injection", "attaques bloquées · 0 faux positif"], [15, 0, "/15", "Critères d'acceptation", "atteints"]];
  M.forEach((_, i) => cue(TL, at(83) + 0.15 + i * 0.08, "pop"));
  S(83, 90, (st) => {
    aurora(st, [{ x: 960, y: 1150, w: 1900, h: 520, c: C.navy, o: 1 }, { x: 200, y: 150, w: 800, h: 500, c: C.slate, o: 0.3 }]);
    const top = el(st, "abs", { left: "0", top: "0", width: "1920px", height: "220px" });
    const head = centered(top, "section", 120, "✦ Résultats mesurés", { fontSize: "30px" });
    const cards = M.map(([v, dec, suf, title, sub], i) => {
      const c = glass(st, 170 + (i % 3) * 540, 230 + Math.floor(i / 3) * 270, 500, 230);
      c.innerHTML = `<div class="headline val" style="position:absolute;left:36px;top:30px;font-size:84px;line-height:96px"></div>
        <div class="label" style="position:absolute;left:38px;top:132px;font-size:28px">${title}</div>
        <div class="muted" style="position:absolute;left:38px;top:174px;font-size:21px">${sub}</div>`;
      Object.assign(c, { val: c.querySelector(".val"), v, dec, suf });
      return c;
    });
    return { top, head, cards };
  }, (lt, d, r) => {
    const fly = eInOut(prog(lt, 1.05, d));
    camera(r.stage, { s: tween(lt, 0, 1.05, 1.0, 1.05) * lerp(1, 1.06, fly), rx: lerp(0, 26, fly), rz: lerp(0, -11, fly), y: lerp(0, -80, fly) });
    r.top.style.filter = `blur(${fly * 6}px)`;
    wipe(r.head, lt, 0, 0.3);
    r.cards.forEach((c, i) => {
      pop(c, lt, 0.15 + i * 0.08, 0.3);
      const k = eOut(prog(lt, 0.2 + i * 0.08, 0.85 + i * 0.08));
      c.val.textContent = nf(c.v * k, c.dec) + c.suf;
    });
  });
}

cue(TL, at(90), "whoosh");
bridgeShot(TL, at(90), at(96), [["Local, traçable", "sécurisé"]], { cps: 24 });

// ====================================================================== BEAT 4 — close
// S5 screen arc — the MVP stack
S(96, 101, (st) => {
  aurora(st, [{ x: 960, y: 1150, w: 1900, h: 520, c: C.navy, o: 1 }, { x: 960, y: 100, w: 1300, h: 380, c: C.slate, o: 0.28 }]);
  const arc = el(st, "abs", { left: "0", top: "0", width: "1920px", height: "1080px", transformStyle: "preserve-3d" });
  const panel = (x, ry, z, tag, body) => {
    const p = glass(arc, x, 220, 460, 600, "", { transform: `translateZ(${z}px) rotateY(${ry}deg)` });
    p.innerHTML = `<div style="padding:34px 34px">${body}</div>`;
    el(arc, "tag", { left: `${x + 230}px`, top: "160px", transform: `translateX(-50%) translateZ(${z}px) rotateY(${ry}deg)` }, tag);
  };
  const rows = (items, mono) => items.map((t) => `<div class="${mono ? "mono" : "label"}" style="font-size:${mono ? 23 : 25}px;height:62px;line-height:62px;border-bottom:1px solid rgba(127,176,240,.1);${mono ? `color:${C.lblue}` : ""}">${t}</div>`).join("");
  panel(220, 24, -150, "API FastAPI", rows(["POST /analyze", "POST /ask", "POST /cypher", "POST /siem/rules", "POST /audit/graph", "GET  /metrics", "POST /cases/export"], true));
  panel(730, 0, 0, "Interface Streamlit", `<div class="section" style="font-size:19px;margin-bottom:8px">Opérations</div>${rows(["Triage", "Investigation", "Pivot CTI", "Dossier d'incident"])}
    <div class="section" style="font-size:19px;margin:22px 0 8px">Détection · Supervision</div>${rows(["Règles de détection", "Pilotage"])}`);
  panel(1240, -24, -150, "Moteur SOCEngine", rows(["HybridRAG + re-ranking", "Agent ReAct · Cypher", "Contrôle de fidélité", "Audit GragPoison", "Garde-fou LLM01", "Export SIEM", "Triage P1 – P4"]));
  const pill = el(st, "pill", { left: "960px", top: "880px", height: "70px", fontSize: "27px", background: "rgba(21,24,31,.9)" },
    '<span class="cyan">Qwen2.5-1.5B en local</span> · ~3 s par réponse · aucune donnée ne sort');
  return { arc, pill };
}, (lt, d, r) => {
  r.arc.style.transform = `rotateY(${tween(lt, 0, d, -12, 12, eInOut)}deg)`;
  camera(r.stage, { s: tween(lt, 0, d, 1.05, 0.99) });
  pop(r.pill, lt, 0.5, 0.3, "translate(-50%, 0)");
});

// S2 variant — the team
{
  const team = [["Walid Fehry", "NER & graphe STIX"], ["Emna Trabelsi", "GNN · GCN / GAT"], ["Hejer Mnejja", "HGT & clustering Leiden"],
    ["Khaled Gannoun", "LLM, prompting & LoRA"], ["Ines Trabelsi", "HybridRAG"], ["Adrian Salvador Ekomo Mesi Obono", "Agent, sécurité & SIEM"]];
  team.forEach((_, i) => cue(TL, at(101) + 0.12 + i * 0.08, "pop"));
  S(101, 106, (st) => {
    aurora(st, [{ x: 960, y: 1150, w: 1900, h: 520, c: C.navy, o: 1 }, { x: 1600, y: 160, w: 700, h: 460, c: C.slate, o: 0.3 }]);
    const head = centered(st, "section", 200, "Une équipe · six expertises", { fontSize: "30px" });
    const cards = team.map(([name, role], i) => {
      const c = glass(st, 120 + (i % 3) * 570, 310 + Math.floor(i / 3) * 190, 540, 150, "soft");
      c.innerHTML = `<div class="row" style="height:100%;padding:0 30px;gap:22px">
        <div class="badge" style="position:static;width:56px;height:56px;background:rgba(39,210,230,.14);border:1px solid rgba(39,210,230,.5);color:${C.cyan};font-size:26px;flex:none">✦</div>
        <div><div class="label" style="font-size:${name.length > 20 ? 25 : 30}px;font-weight:600">${name}</div>
        <div class="muted" style="font-size:22px;margin-top:6px">${role}</div></div></div>`;
      return c;
    });
    const foot = centered(st, "tagline", 760, 'Projet TAL & cybersécurité · méthode <span class="cyan">TDSP</span>', { fontSize: "30px" });
    return { head, cards, foot };
  }, (lt, d, r) => {
    camera(r.stage, { s: tween(lt, 0, d, 1.0, 1.05), y: tween(lt, 0, d, 10, -10) });
    wipe(r.head, lt, 0, 0.3);
    r.cards.forEach((c, i) => pop(c, lt, 0.12 + i * 0.08, 0.3));
    wipe(r.foot, lt, 0.75, 0.35);
  });
}

// S8 + S9 close: tagline, then "avec ✦ Vigie"
cue(TL, at(106), "whoosh");
bridgeShot(TL, at(106), at(118), [["L'avenir du SOC", "est ici"], ["avec", "Vigie", "B"]], { cps: 20 });

// S10 aurora end card
cue(TL, at(118), "whoosh");
endCard(TL, at(118), at(128), "Vigie", "✦ Lancer une investigation");

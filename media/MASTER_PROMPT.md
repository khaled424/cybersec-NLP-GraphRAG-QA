# Universal master prompt — premium dark SaaS motion-graphics explainer

A reusable prompt that turns **any text or script** (product pitch, feature list, report, release
notes, voice-over script) into a sequence of **10-second motion-graphics beats** that all share one
locked visual language. It generalises a single 10-second "AI chatbot" brief into a system:
the style, palette, typography, motion grammar, transitions and sound are fixed; only the
content of each beat changes.

Part 1 is the master prompt (copy it as is, then fill the `{{…}}` inputs). Part 2 applies it to
this project: the 40-second commercial for **Vigie**, rendered by `media/commercial/`.

---

## Part 1 — The master prompt

```text
ROLE
You are a motion-graphics director. Turn the INPUT SCRIPT into a sequence of 10-second beats for a
premium dark SaaS explainer. Every beat obeys the LOCKED STYLE SYSTEM below; only the content changes.

INPUTS
- INPUT SCRIPT: {{script — any text: pitch, feature list, report, VO script}}
- BRAND: {{brand name}}            - ON-SCREEN LANGUAGE: {{language}}
- TOTAL DURATION: {{N × 10 s}}     - CALL TO ACTION: {{e.g. "✦ Get started"}}
- PROOF POINTS (optional): {{numbers, results, customer facts — never invent any}}

STEP 1 — ANALYSE THE SCRIPT (write this out before any prompt)
1. One-line promise: what changes for the viewer, in ≤ 8 words.
2. Audience and tone (e.g. SOC analysts, technical, confident, calm).
3. Extract and rank: the problem, the product moment (the core interaction), 3–8 capabilities,
   the proof points (exact figures only, copied verbatim from the script), the tagline, the CTA.
4. Compress every idea to on-screen copy: headlines ≤ 5 words, UI labels ≤ 4 words,
   typed sentences ≤ 60 characters. Keep real names, identifiers and numbers unchanged.

STEP 2 — SPLIT INTO BEATS (number of beats = total duration / 10 s)
Assign one role per beat, in this order (merge or repeat middle roles as needed):
  B1 HOOK & REVEAL   — brand, promise, the product UI appearing, first interaction.
  B2…Bn-1 SYSTEM / PROOF — how it works (inputs → processing → output), then why it can be
                       trusted (results, safeguards). One idea per shot.
  Bn CLOSE           — tagline typed by the star cursor, "with ✦ BRAND", aurora-ring end card.
A non-final beat ends with a STAR BRIDGE (hero star spin + typed title of the next beat);
only the final beat has the end card.

STEP 3 — BUILD EACH BEAT FROM THE SHOT LIBRARY (5–8 shots per beat, 0.4–2.4 s each)
  S1 AURORA HERO      blurred aurora arc sweeps a corner; small cyan logo over a huge gradient
                      headline; a dark rounded chat/UI panel with cyan rim rises from frame
                      bottom in low-angle perspective; two chrome stars tumble; crane down + push in.
  S2 CARD DECK        front-on glass capsule search bar with glowing stroke + outlined "✦ action"
                      pill; three stacked cards fanned like a deck (light-blue, cyan, dark headers),
                      round logo badge left, icon right; front card shows a question line and a
                      sparkle-tile bulleted answer; motion-blurred stars cross; slow pull-back.
  S3 BUTTON PRESS     extreme close-up push on a "✦" button; translucent blue orb cursor glides in
                      and clicks; button fills solid cyan, scales 1.1×, halo pulse.
  S4 BLUEPRINT TYPING dark blueprint grid (1px lines, small blue diamonds at intersections); a
                      glowing blue→periwinkle rectangle morphs into an input; avatar; typed
                      question; "AI" badge; cyan-outlined answer card expands and types the answer,
                      then one monospace line (code, query, command); parallax tilt down.
  S5 SCREEN ARC       three phone/app screens in a 3D arc, camera orbits; small dark pill tags
                      name each screen; side screens tilted 25° and cropped; ends on a whip-pan.
  S6 TILE GRID        star icon + wide-tracked section header; trapezoid cyan-rimmed panel with one
                      cyan italic keyword; 4×2 grid of dark rounded tiles popping in staggered with
                      overshoot; dolly in, Dutch tilt 20°, fly-over with depth of field.
  S7 DATA / PROOF     glass metric cards or a node graph that builds itself; numbers count up;
                      one accent colour per state (cyan = valid, coral #FF6B7A = rejected/threat).
  S8 HERO STAR        empty frame, navy glow at bottom; one large chrome star spins on Y to an
                      edge-on sliver and shrinks.
  S9 STAR TYPEWRITER  the small spinning star is the cursor; centred text types behind it; the
                      first words in cyan, the rest white; the star parks in the gap, still flipping.
  S10 AURORA END CARD huge soft aurora ring (bright cyan lower-left → slate-blue right) around a
                      dark centre, breathing glow; bold cyan logo dead centre (~9 % frame height);
                      small white CTA fades in beneath; hold still.
Shots S1–S7 carry content; S8–S10 are the bridge / close. Never invent a new shot type: re-skin one.

LOCKED STYLE SYSTEM (identical in every beat — paste it into every beat prompt)
STYLE: premium dark SaaS motion-graphics explainer; moody deep-navy space lit by soft neon-cyan rim
light and blurred aurora glows; cool teal-and-slate grade with lifted blacks; glassmorphic floating
UI cards with 1px glowing cyan strokes; iridescent teal chrome 4-point stars with specular
highlights; smooth virtual-camera dollies / orbits / Dutch tilts with ease-out motion; shallow depth
of field on background elements; crisp vector UI; clean high-end 3D render finish; no people, no
photography.
SPECS: 1920×1080, 16:9, 30 fps, 10 s per beat, hard cuts on music hits, continuous camera motion
within each shot.
PALETTE: background #0C111C, navy glow #0B2347, primary cyan #27D2E6, muted teal #62B0BC,
slate-blue aurora #3D5A8A, light-blue header #7FB0F0, cyan header #1CCDE6, periwinkle #6B7FD0,
card body #15181F, text #E6EAF0, muted text #7A8394 (+ one alert accent #FF6B7A, used sparingly).
TYPOGRAPHY: headline & logo heavy geometric sans (Poppins / Montserrat ExtraBold), tight tracking,
cyan or cyan→blue gradient; UI and chat text neo-grotesk (Inter Regular / Medium) #E6EAF0 and
#7A8394; section headers wide-tracked Regular #62B0BC; code monospace; tagline small Regular with
one cyan keyword; text animates only by left-to-right typewriter or wipe, never bounce.
MOTION PRINCIPLES: ease-out (cubic) on every move, overshoot only on tile/badge pop-ins (≤ 8 %);
one camera move per shot that never stops; staggered entrances 60–90 ms apart; foreground stars
with motion blur; depth: background blurred, UI sharp; no element enters without a reason.
TRANSITIONS: hard cut + whoosh between shots on music hits, on the beat grid (tempo near 92 BPM chosen so
that 10 s = whole bars: 96 BPM = 4 bars, cuts on half-beats of 0.3125 s);
whip-pan allowed once per beat; beats chain through the star bridge; the chrome star is the
recurring object that links all beats.
PACING: 5–8 shots per beat; dense info shots 1.2–2.4 s, accent shots 0.4–0.7 s; leave ≥ 0.8 s of
readable hold on any text longer than 4 words.
SOUND: one continuous tech-electronic bed ~92 BPM (crisp hi-hats, soft synth pads), no voice-over;
whoosh on every hard cut; soft UI click + shimmer on every button press; keyboard ticks during
typing; glassy pop per tile or card; airy reverse swell into each hero star; final beat: warm rising
chime + low sub hit on the end card, music resolves and rings out.

STEP 4 — OUTPUT FORMAT (one block per beat, same order every time)
BEAT k/N — {{role}} — {{start}}–{{end}} s (global)
STYLE / SPECS / PALETTE / TYPOGRAPHY: "locked — see style system" (or pasted in full when each
beat is sent to a video model on its own)
TIMELINE: one line per shot, local time "0.0–1.2s — [shot type] …", exact on-screen copy in
quotes, camera move, end transition ("Hard cut." / "Whip-pan." / "Star bridge.")
SOUND: cue list with local times.
FINAL FRAME: the exact last frame, so the next beat can continue from it.

QUALITY CHECKLIST (run before returning)
- Every number and name on screen exists in the INPUT SCRIPT; nothing is invented.
- Each beat uses only library shots, the locked palette and the locked typography.
- Copy limits respected; each text has its readable hold; one idea per shot.
- Hard cuts land on the beat grid (half-beats of 0.3125 s at 96 BPM); whoosh listed for each cut.
- The star appears in every beat; the last beat ends on the aurora-ring end card with the CTA.
```

---

## Part 2 — Applied: the Vigie commercial (40 s = 4 beats)

**Analysis.** Promise: *« L'analyste SOC, augmenté »*. Audience: SOC analysts and the teaching staff;
technical and calm in tone. Product moment: an analyst asks a question and gets an answer that
cites its sources, plus the Cypher query behind it. Capabilities: triage, NER, STIX graph,
HybridRAG, Text-to-Cypher, poisoning audit, SIEM export. Proof points, all measured in the
notebooks: Recall@4 0,857 · MRR 0,789 · Text-to-Cypher 100 % (validation) · abstention hors domaine
100 % · NER micro-F1 0,91 · quarantaine précision 1,00 / rappel 0,94 · 15/15 critères. Tagline:
*« L'avenir du SOC ✦ est ici »*. CTA: *« ✦ Lancer une investigation »*. Language: French.

STYLE, SPECS, PALETTE, TYPOGRAPHY and SOUND are locked (Part 1). Brand = **Vigie**. Rendered at 96 BPM: shot
times below are rounded; `media/commercial/commercial.js` holds the exact half-beat grid.

### BEAT 1/4 — Hook & reveal — 0–10 s
TIMELINE:
- 0.0–1.2s — S1 aurora hero: cyan "✦ Vigie" logo over a gradient headline "L'analyste SOC, augmenté"; chat panel rises from the bottom with two tumbling stars; crane down + push in. Hard cut.
- 1.2–2.6s — S7 data: wide-tracked header "LE DÉFI DU SOC"; three glass cards count up "2 411 rapports bruts", "379 entités de menace", "5 277 relations"; slow dolly. Hard cut.
- 2.6–3.8s — S2 card deck: search bar "Interroger la base de menaces…" + "✦ Analyser" pill; deck of three "Vigie" cards; the front card shows "Quels malwares ciblent le secteur bancaire ?" and sparkle bullets "dridex", "emotet", "trickbot" with sources "HF-01128"; pull-back. Hard cut.
- 3.8–4.4s — S3 button press on "✦ Analyser". Hard cut.
- 4.4–6.6s — S4 blueprint typing: "Quelle CVE affecte log4j ?" → answer "CVE-2021-44228 affecte log4j [S1]" → monospace "MATCH (x:Vulnerability)-[:AFFECTS]->(a:Software {name: 'log4j'})". Hard cut.
- 6.6–8.0s — S5 screen arc: "Triage" (badge "P1 · Critique"), "Investigation" (bot "Bonjour, quelle alerte analysons-nous ?"), "Détection" (rule card "SPL · KQL"); orbit left. Whip-pan.
- 8.0–10.0s — S8 + S9 star bridge: the star types "Du rapport brut ✦ au graphe de menaces".
SOUND: whooshes at every cut; click + shimmer at 4.1 s; ticks 4.6–6.4 s and 8.4–9.8 s; reverse swell at 8.0 s.
FINAL FRAME: centred line "Du rapport brut ✦ au graphe de menaces" on #0C111C.

### BEAT 2/4 — How it works — 10–20 s
- 0.0–1.6s — S4 variant: a raw report types "The LockBit ransomware gang exploited CVE-2023-4966 in Citrix NetScaler to target hospitals from 89.62.172.13."; NER highlights pop with chips MALWARE, VECTOR, CVE, SOFTWARE, TARGET, IP. Hard cut.
- 1.6–3.4s — S7 graph: the chips fly into a STIX 2.1 graph whose edges draw themselves (USES, EXPLOITS, AFFECTS, TARGETS); counter "2 573 nœuds · 5 277 arêtes"; orbit. Hard cut.
- 3.4–5.2s — S6 tile grid: header "CONNECTEZ VOS SOURCES"; panel "Du texte au *graphe* de menaces"; tiles: Corpus CTI, NER cyber, Graphe STIX, FAISS, Neo4j, Qwen local, MITRE ATT&CK, SIEM; Dutch-tilt fly-over. Hard cut.
- 5.2–7.0s — S7 fusion: two streams "Recherche vectorielle E5" and "Faits du graphe" merge through "Re-ranking" into evidence chips [S1] [S2] [S3]; pill "Recall@4 0,857 · MRR 0,789". Hard cut.
- 7.0–8.6s — S4 code variant: the LLM's query `MATCH (c:CVE)…` is underlined in coral with "Unknown label `CVE`", the agent repairs it to `Vulnerability`, and a cyan check "✓ 100 % de réponses exactes (validation)" appears. Hard cut.
- 8.6–10.0s — S8 + S9 star bridge: "Des réponses ✦ prouvées".

### BEAT 3/4 — Trust & security — 20–30 s
- 0.0–1.6s — S7 grounding: three answer sentences; two get "[S1]" / "[S2]" badges, the third is struck through "non étayée" and removed; pill "100 % des phrases étayées". Hard cut.
- 1.6–3.4s — S7 graph audit: a coral hub "updatehelper" wired to many nodes; a scan line passes; the coral edges dissolve into quarantine; "Précision 1,00 · Rappel 0,94 · 0 faux positif". Hard cut.
- 3.4–4.0s — S3 button press on "✦ Exporter la règle". Hard cut.
- 4.0–5.8s — S4 code variant: SPL and KQL cards type; IOC list: "89.62.172.13 ✓ retenu", "10.0.0.5 ✗ non routable", "192.0.2.10 ✗ documentation", "8.8.8.8 ✗ bénin". Hard cut.
- 5.8–8.2s — S6/S7 metric grid: six glass cards pop in with overshoot and count up: "Recherche hybride · Recall@4 0,857", "Text-to-Cypher · 100 %", "Abstention hors domaine · 100 %", "NER SecBERT · F1 0,91", "Garde-fou · 10/10", "Critères d'acceptation · 15/15"; Dutch-tilt fly-over. Hard cut.
- 8.2–10.0s — S8 + S9 star bridge: "Local, traçable ✦ sécurisé".

### BEAT 4/4 — Close — 30–40 s
- 0.0–1.6s — S5 screen arc: "API FastAPI", "Interface Streamlit", "Moteur SOCEngine"; pill "Qwen2.5-1.5B en local · ~3 s par réponse". Hard cut.
- 1.6–3.0s — S2 variant: header "UNE ÉQUIPE · SIX EXPERTISES"; six name pills: Walid Fehry, Emna Trabelsi, Hejer Mnejja, Khaled Gannoun, Ines Trabelsi, Adrian Salvador Ekomo Mesi Obono. Hard cut.
- 3.0–3.4s — S8 hero star spins to a sliver.
- 3.4–5.6s — S9: "L'avenir du SOC ✦ est ici" ("L'avenir du SOC" cyan).
- 5.6–6.8s — S9: "avec ✦ Vigie".
- 6.8–10.0s — S10 end card: aurora ring, "Vigie" logo, "✦ Lancer une investigation"; hold.
SOUND: warm rising chime + sub hit at 36.8 s; drums stop, the pad resolves and rings out by 40 s.
FINAL FRAME: dark #0C111C centre inside a soft aurora ring (cyan lower-left → slate-blue right), bold cyan "Vigie" at ~9 % frame height, small white "✦ Lancer une investigation" beneath, held still.

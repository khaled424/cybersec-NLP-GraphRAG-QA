/* Demo overlay injected into the Streamlit page: step captions and a cursor orb in the commercial's
 * style, plus helpers to scroll the main pane. Idempotent: evaluated before every capture. */
(() => {
  if (window.__demo && document.getElementById("demo-cap")) return;
  const css = document.createElement("style");
  css.textContent = `
    [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { visibility: hidden !important; }
    #demo-cap { position: fixed; left: 50%; bottom: 26px; transform: translateX(-50%); z-index: 2147483000;
      max-width: 1180px; padding: 14px 26px 16px; border-radius: 18px; pointer-events: none;
      background: linear-gradient(180deg, rgba(27,32,42,.96), rgba(16,19,26,.96)); border: 1px solid rgba(39,210,230,.65);
      box-shadow: 0 0 26px rgba(39,210,230,.28), 0 18px 50px rgba(0,0,0,.55); font-family: "Adwaita Sans", "Inter", sans-serif; }
    #demo-cap .step { color: #62B0BC; font-size: 12.5px; letter-spacing: .3em; text-transform: uppercase; margin-bottom: 4px; }
    #demo-cap .text { color: #E6EAF0; font-size: 20px; line-height: 1.35; white-space: nowrap; }
    #demo-cap .text b { color: #27D2E6; font-weight: 600; }
    #demo-cap .brand { position: absolute; right: 18px; top: 12px; color: #27D2E6; font-size: 12.5px; font-weight: 700; letter-spacing: .08em; }
    #demo-orb { position: fixed; left: 0; top: 0; width: 34px; height: 34px; margin: -17px 0 0 -17px; border-radius: 50%;
      z-index: 2147483001; pointer-events: none; transition: none;
      background: radial-gradient(circle at 35% 30%, rgba(220,240,255,.95), rgba(90,168,240,.6) 45%, rgba(61,90,138,.15) 75%);
      box-shadow: 0 0 22px rgba(90,168,240,.8); }
    #demo-orb.down { transform: scale(.78); box-shadow: 0 0 0 10px rgba(39,210,230,.25), 0 0 30px rgba(39,210,230,.9); }`;
  document.head.appendChild(css);
  const cap = document.createElement("div");
  cap.id = "demo-cap";
  cap.innerHTML = '<div class="brand">✦ VIGIE</div><div class="step"></div><div class="text"></div>';
  const orb = document.createElement("div");
  orb.id = "demo-orb";
  document.body.append(cap, orb);
  const state = window.__demoState || { step: "", text: "", x: -100, y: -100, down: false };
  window.__demoState = state;
  const pane = () => {
    const main = document.querySelector('[data-testid="stMain"]') || document.querySelector("section.main");
    const candidates = [main, ...document.querySelectorAll("section, div")].filter(Boolean);
    return candidates.find((e) => e.scrollHeight > e.clientHeight + 10 && /(auto|scroll)/.test(getComputedStyle(e).overflowY)
      && e.clientHeight > 400 && !e.closest('[data-testid="stSidebar"]')) || document.scrollingElement;
  };
  const apply = () => {
    cap.querySelector(".step").textContent = state.step;
    cap.querySelector(".text").innerHTML = state.text;
    cap.style.display = state.text ? "block" : "none";
    orb.style.left = `${state.x}px`; orb.style.top = `${state.y}px`;
    orb.classList.toggle("down", state.down);
  };
  window.__demo = {
    caption(step, text) { state.step = step; state.text = text; apply(); },
    orb(x, y, down) { state.x = x; state.y = y; state.down = down; apply(); },
    scrollTop() { return pane().scrollTop; },
    scrollTo(y) { const p = pane(); p.scrollTop = Math.max(0, Math.min(y, p.scrollHeight - p.clientHeight)); },
    offsetOf(text) {
      const p = pane();
      const walker = document.createTreeWalker(p, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        if (walker.currentNode.textContent.includes(text)) {
          const r = walker.currentNode.parentElement.getBoundingClientRect();
          return p.scrollTop + r.top - p.getBoundingClientRect().top - 90;
        }
      }
      return p.scrollTop;
    },
  };
  apply();
})();

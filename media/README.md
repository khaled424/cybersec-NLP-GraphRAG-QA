# Vidéos de Vigie

| Vidéo | Durée | Source |
| --- | --- | --- |
| `out/vigie_commercial.mp4` | 40 s (4 temps de 10 s) | `commercial/` : moteur de motion design déterministe (HTML/CSS/JS), bande-son synthétisée |
| `out/vigie_demo_mvp.mp4` | ~82 s | `demo/record_demo.py` : session réelle de Vigie pilotée par Playwright, sous-titres et cartes au même style |

[`MASTER_PROMPT.md`](./MASTER_PROMPT.md) : le prompt maître universel (n'importe quel texte → temps de 10 s au style
verrouillé) et son application à la publicité de Vigie.

```bash
python -m venv .venv-media && .venv-media/bin/pip install -r media/requirements.txt   # ffmpeg + chromium requis
.venv-media/bin/python media/render.py commercial                  # → media/out/vigie_commercial.mp4 (~3 min)
.venv-media/bin/python media/render.py commercial --preview 4 12   # images fixes pour vérifier un plan
mise run mvp   # dans un autre terminal, puis :
.venv-media/bin/python media/demo/record_demo.py                   # → media/out/vigie_demo_mvp.mp4 (~2 min)
```

- **Déterminisme** : chaque image est une fonction pure du temps (`renderAt(t)`) ; la capture image par image ne
  dépend pas de la vitesse de la machine. `commercial/index.html#12.5` affiche l'image à 12,5 s, `#play` la joue.
- **Démo** : les attentes de l'API et du LLM ne sont pas enregistrées (le spinner apparaît, puis le résultat) ;
  tout ce qui est affiché est la sortie réelle de l'application.
- **Son** : `soundtrack.py` génère tout (pads, basse, kick, hi-hats à 96 BPM, whooshes, clics, frappe, pops, swell,
  carillon final) à partir des repères (`cue`) de la timeline : aucun échantillon, aucune licence.
- **Polices** : Poppins / Montserrat / Inter si installées, sinon Adwaita Sans (dérivée d'Inter) et JetBrains Mono.

## Logo

`brand/` : logo de Vigie en PNG haute définition, généré depuis `brand/logo.html` (`python media/brand/render_logo.py`).

| Fichier | Taille | Usage |
| --- | --- | --- |
| `vigie_logo.png` | 3800 × 1280, fond transparent | documents, slides, README |
| `vigie_logo_dark.png` | 3800 × 1280, fond #0C111C | bannière, couverture du rapport |
| `vigie_icon.png` | 1024 × 1024, coins transparents | icône d'application, favicon |
| `vigie_mark.png` | 2048 × 2048, fond transparent | symbole seul |

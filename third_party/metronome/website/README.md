# Metronome — paper explainer website

An interactive single-page explainer for the paper *"Metronome: Bound the Cache, Keep the Beat
for Real-Time Interaction Model Serving"* (Meng & Li).

Built with React + Vite. All charts are hand-rolled SVG (no chart library); animations are
CSS/SMIL/requestAnimationFrame. Chart palette and series labels follow the paper's figure
conventions (`paper/figures/nstyle.py`): vermillion `#D55E00` = unbounded KV (failure), blue
`#0072B2` = Metronome windowed KV (fix); CVD-validated.

## Develop

```bash
cd website
npm install
npm run dev        # dev server
npm run build      # production build -> dist/
npm run preview    # serve the production build
```

## Structure

- `src/data.js` — every chart's data; headline numbers match the paper's measurements, traces
  are reconstructed at the paper's reported resolution for the animated recreations.
- `src/chart/` — shared SVG chart frame (grid/axes/crosshair-tooltip) and scales/playback hooks.
- `src/components/` — one component per section: animated metronome, workload contrast,
  latency-cliff replay, KV-pool simulation, collapse properties, first-order-model charts,
  architecture animation, sliding-window animation, admission trace, quality boundary,
  four-model capacity, beyond-voice, footer.

The site is fully static; deploy `dist/` anywhere (GitHub Pages works — `base: './'` is set).

## Deploy

The site is served at <https://01.me/research/metronome/> (ring0.me redirects there) from the
icourse server. To redeploy after a change:

```bash
npm run build
rsync -az --delete dist/ icourse:/var/www/ring0.me/research/metronome/
```

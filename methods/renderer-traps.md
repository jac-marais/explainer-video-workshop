# Renderer traps

These are route-specific acceptance traps learned from local runs, for the route chosen in step 5 of `methods/prepare-explainer-video.md`. A production agent applies the traps for its route before it accepts a check or a render. `library/renderers.md` holds the evidence for each route.

## HyperFrames preflight traps

Use these checks when the route is HyperFrames. They are route-specific acceptance traps, not general claims about every HTML renderer (S-HF-001–S-HF-005):

- Require a standalone composition HTML file; do not assume a template scaffold supplies the accepted source.
- Require the root `data-composition-id` to match the paused timeline key that the renderer seeks.
- Require every referenced audio ID to resolve to an intended asset before timing or render acceptance.
- Run the lint/check path and treat any lint error that disables layout or contrast audits as a failure requiring repair.
- Require positive layout/contrast samples. A report with zero samples or `0-of-0` checks is not a pass.
- Set `HYPERFRAMES_NO_UPDATE_CHECK=1` and `HYPERFRAMES_NO_AUTO_INSTALL=1` for `check`. `scripts/film/render.py` sets both for its render, but it never runs `check`. In a local 0.8.57 run, the CLI's background self-update installed 0.8.99 during a render, deleted files in `dist/`, and failed the render with "Missing manifest".
- Colour depends on where the render runs. A Docker render image built on ffmpeg 5.1 writes BT.601 pixels under a BT.709 tag. A host render with ffmpeg 9.0.2 writes true BT.709. Tags cannot show which matrix the pixels use, so measure a known brand colour. `scripts/film/render.py --relabel-601` does the relabel, but it does not detect the matrix. Pass it only for a Docker render built on ffmpeg 5.1, and never for a host render.
- `check` does not test elements marked `data-layout-allow-overlap`, so an overlap they cause can pass. The per-sentence frame sweep in M6 of the production prompt covers them.
- Persist Studio caption/timing changes into source files and refresh the preview before accepting them (S-HF-005).

These local HyperFrames runs show that the route works in this environment; they do not validate the renderer in general.

## Live-app capture traps

- The screencast sends a frame only when the screen changes. Hold each frame until the next one arrives to build constant-rate video. Use high-quality JPEG screencast frames, because Playwright's built-in video recording blurs code text.
- Load lazy components, such as an embedded code editor, in every frame before the take. A first load can freeze the stage for seconds.
- Freeze the app's source during a take. A hot reload, for example from a concurrent edit, glitches the take and can bring back hidden developer overlays.
- In the per-sentence frame sweep, check the edges of scrolled regions. Rows cut in half at a scroll edge can pass a quick still review.

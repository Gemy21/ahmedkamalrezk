# Ahmed Kamal — GitHub profile README

Terminal-style profile: an animated real-data contribution graph, an ASCII
portrait, and a streak/stats card that refreshes itself every day.

## How it works

1. `scripts/fetch_contributions.py` scrapes the public GitHub contributions
   page (no token needed) and writes `data/contributions.json` with the daily
   counts plus streaks, best day and monthly totals.
2. `scripts/generate_streak_svg.py` renders `contrib-heatmap.svg` from that
   snapshot — every cell pops in and flashes, like GitHub's own graph.
3. `scripts/render_stats_svg.py` renders `stats.svg`: six stat tiles that count
   up and a monthly bar chart that grows in.
4. `.github/workflows/update-profile-art.yml` runs all three every day at
   06:17 UTC, on every push to `main`, and on demand, then commits the result.

All animation is CSS/SMIL inside the SVG, because GitHub only renders SVG
images and never runs JavaScript inside them.

## Install it

1. The repository must be **public** and named exactly `ahmedkamalrezk` so
   GitHub shows its README on the profile.
2. Upload everything to the repository root, including the hidden `.github`
   folder.
3. Make `main` the default branch.
4. Open **Settings → Actions → General → Workflow permissions** and allow
   read/write permissions so the workflow can push.
5. Run **Actions → Update profile art → Run workflow** once; it refreshes daily
   after that. The built-in `GITHUB_TOKEN` is enough — no personal token.

## Files

- `README.md` — profile layout.
- `contrib-heatmap.svg` — animated contribution calendar (generated).
- `stats.svg` — animated streak / numbers card (generated).
- `ahmed-ascii.svg` — animated ASCII portrait (generated).
- `data/contributions.json` — daily contribution snapshot (generated).
- `source-photo.png` / `source-prepped.png` — portrait source and its prepared
  grayscale version.
- `scripts/fetch_contributions.py` — scrapes GitHub's public calendar.
- `scripts/generate_streak_svg.py` — renders the heatmap.
- `scripts/render_stats_svg.py` — renders the stats card.
- `scripts/prep_photo.py` — crops/smooths a new photo into `source-prepped.png`.
- `scripts/make_ascii_svg.py` — turns `source-prepped.png` into ASCII art.

## Using a different photo

```bash
python scripts/prep_photo.py path/to/photo.png
python scripts/make_ascii_svg.py
```

`prep_photo.py` crops a square around the head using the `CROP` constant. For a
clean cut-out background, install `rembg` and run with `USE_REMBG=1` (the small
`u2netp` model downloads on first use); otherwise the ASCII script's elliptical
vignette fades the edges instead.

## Local run

```bash
python -m pip install -r scripts/requirements.txt
python scripts/fetch_contributions.py
python scripts/generate_streak_svg.py ahmedkamalrezk contrib-heatmap.svg
python scripts/render_stats_svg.py
```

If the contribution endpoint is unavailable, `generate_streak_svg.py` falls
back to the public `github-contributions-api.jogruber.de` API.

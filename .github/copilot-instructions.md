# Copilot instructions – rozvrh-mladez

Static GitHub Pages site (custom domain in `CNAME`) with the training schedule and match results of TJ Sokol Vratimov. The UI and comments are in Czech.

## Architecture
- `index.html`: the whole frontend (HTML, CSS and JS in one file, no build step). It shows a static training schedule. It also loads `current.json` with `fetch` and renders two sections: "Aktuální a budoucí zápasy" and "Odehrané zápasy".
- `current.json`: generated data, **do not edit by hand**. Schema: `updated`, `days[]` (today + 8 days, empty days kept) and `past_days[]` (last 8 days, only days that have matches). Each match has `skupina`, `cislo`, `tymy`, `stav`, `badge` and `href`.
- `scripts/fetch_current.py`: standard library only, no dependencies. It scrapes `https://ezapis.cvf.cz/online/?search=YYYY-MM-DD` with a custom `HTMLParser` (`table.match-table`, `tr[data-href]`). It keeps only rows whose teams cell contains `FILTER = "Sokol Vratimov"`. It uses the Europe/Prague timezone. If a day fails to download, it keeps that day's old data. It rewrites the file only when the matches change, which avoids needless commits.
- `.github/workflows/current.yml`: GitHub Actions workflow that runs the scraper every 5 minutes (and manually via `workflow_dispatch`). It commits and pushes `current.json` only when it changed.
- `sitemap.xml`, `robots.txt` and `_config.yml` are SEO and Pages config.

## Commands
- Run the scraper: `python3 scripts/fetch_current.py`. It needs network access and writes `current.json`.
- Preview the site: `python3 -m http.server`. `fetch` of `current.json` does not work from `file://`.

## Conventions
- Keep the Python script free of external dependencies.
- Constants `DAYS_AHEAD` and `DAYS_BACK` control the date window. If you change them, update the README and the section titles in `index.html`.
- If you change the JSON schema, update the scraper, `index.html` and the README together.
- Write user-facing text and comments in Czech.
- Today's matches show the result and sets. Later matches show only the teams. Past matches always show results.


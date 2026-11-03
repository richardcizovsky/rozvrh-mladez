#!/usr/bin/env python3
"""Stáhne data týmů klubu za minulé sezóny (stejně jako team.json) do souborů historyYYYYYY.json.

Příklad: sezóna 2025/26 -> history202526.json.
Bez argumentů stáhne sezóny 2025/26 až 2022/23 (starší sezóny API nemá);
lze zadat i konkrétní sezóny:
    python3 scripts/fetch_history.py 2024/25 2023/24
Přihlašovací údaje se berou z proměnných prostředí API_USERNAME a API_PASSWORD.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_team import die, fetch_season, login  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIRST_YEAR = 2022  # sezóna 2022/23 – starší sezóny CVF API nevrací (prázdná data)
LAST_YEAR = 2025   # sezóna 2025/26

# Týmy, které se do historie neukládají – jejich soutěže se nakonec nehrály
EXCLUDE_TEAMS = {
    "2025/26": {91768},  # U18Z-B – okresní přebor kategorie U18Z
    "2024/25": {88894},  # U14M – Letní pohár ing. Lumíra Hajduška
}


def season_name(year):
    return f"{year}/{(year + 1) % 100:02d}"


def out_path(season):
    start, end = season.split("/")
    return ROOT / f"history{start}{end}.json"


def main():
    seasons = sys.argv[1:] or [season_name(y) for y in range(LAST_YEAR, FIRST_YEAR - 1, -1)]
    for s in seasons:
        if len(s) != 7 or s[4] != "/" or not (s[:4] + s[5:]).isdigit():
            die(f"neplatná sezóna '{s}', očekávaný formát RRRR/RR")
    token = login()
    for season in seasons:
        print(f"Sezóna {season}")
        fetch_season(season, out_path(season), token, EXCLUDE_TEAMS.get(season, set()))


if __name__ == "__main__":
    main()




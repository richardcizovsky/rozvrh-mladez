#!/usr/bin/env python3
"""Stáhne zápasy z eZapis na dnešek a 7 dní dopředu a uloží řádky se 'Sokol Vratimov' do current.json."""
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

FILTER = "Sokol Vratimov"
DAYS_AHEAD = 0  # jen dnešek (např. 7 = týden dopředu)
OUT = Path(__file__).resolve().parent.parent / "current.json"


class MatchParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.in_table = False
        self.row = None
        self.cell = None
        self.in_badge = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table" and "match-table" in (a.get("class") or ""):
            self.in_table = True
        elif self.in_table and tag == "tr" and a.get("data-href"):
            self.row = {"href": a["data-href"], "cells": [], "badge": ""}
        elif self.row is not None and tag == "td":
            self.cell = []
        elif self.cell is not None and tag == "span" and "badge-status" in (a.get("class") or ""):
            self.in_badge = True

    def handle_endtag(self, tag):
        if tag == "span" and self.in_badge:
            self.in_badge = False
        elif tag == "td" and self.cell is not None:
            self.row["cells"].append(re.sub(r"\s+", " ", "".join(self.cell)).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        elif tag == "table":
            self.in_table = False

    def handle_data(self, data):
        if self.in_badge:
            self.row["badge"] += data.strip()
        elif self.cell is not None:
            self.cell.append(data)


def fetch_day(date):
    url = f"https://ezapis.cvf.cz/online/?search={date}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rozvrh-mladez bot)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", errors="replace")

    p = MatchParser()
    p.feed(html)

    matches = []
    for row in p.rows:
        c = row["cells"]
        if len(c) >= 4 and FILTER in c[2]:
            matches.append({
                "skupina": c[0],
                "cislo": c[1],
                "tymy": c[2],
                "stav": c[3],
                "badge": row["badge"],
                "href": "https://ezapis.cvf.cz/online/" + row["href"],
            })
    return matches


def main():
    now = datetime.now(ZoneInfo("Europe/Prague"))
    old = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {}
    old_days = {d["date"]: d["matches"] for d in old.get("days", [])}

    days = []
    for i in range(DAYS_AHEAD + 1):
        date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            matches = fetch_day(date)
        except Exception as e:  # při výpadku ponechat stará data pro daný den
            print(f"Chyba {date}: {e}", file=sys.stderr)
            matches = old_days.get(date, [])
        days.append({"date": date, "matches": matches})

    # Neměnit soubor, pokud se změnil jen čas aktualizace (méně commitů)
    if old.get("days") == days:
        print("Beze změny")
        return
    data = {"updated": now.strftime("%Y-%m-%d %H:%M"), "days": days}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"Uloženo {sum(len(d['matches']) for d in days)} zápasů ({days[0]['date']} – {days[-1]['date']})")


if __name__ == "__main__":
    sys.exit(main())


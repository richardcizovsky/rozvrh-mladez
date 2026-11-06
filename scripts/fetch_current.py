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
DAYS_AHEAD = 8  # jen dnešek (např. 7 = týden dopředu)
DAYS_BACK = 8  # minulé zápasy - 8 dní zpět
OUT = Path(__file__).resolve().parent.parent / "current.json"


def clean(parts):
    return re.sub(r"\s+", " ", "".join(parts)).strip()


class MatchParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.headers = []  # názvy sloupců aktuální tabulky (web občas přidá sloupec, např. „Čas“)
        self.in_table = False
        self.th = None
        self.row = None
        self.cell = None
        self.in_badge = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table" and "match-table" in (a.get("class") or ""):
            self.in_table = True
            self.headers = []
        elif self.in_table and tag == "th":
            self.th = []
        elif self.in_table and tag == "tr" and a.get("data-href"):
            self.row = {"href": a["data-href"], "cells": [], "badge": "", "headers": self.headers}
        elif self.row is not None and tag == "td":
            self.cell = []
        elif self.cell is not None and tag == "span" and "badge-status" in (a.get("class") or ""):
            self.in_badge = True

    def handle_endtag(self, tag):
        if tag == "span" and self.in_badge:
            self.in_badge = False
        elif tag == "th" and self.th is not None:
            self.headers.append(clean(self.th))
            self.th = None
        elif tag == "td" and self.cell is not None:
            self.row["cells"].append(clean(self.cell))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        elif tag == "table":
            self.in_table = False

    def handle_data(self, data):
        if self.th is not None:
            self.th.append(data)
        elif self.in_badge:
            self.row["badge"] += data.strip()
        elif self.cell is not None:
            self.cell.append(data)


def column_index(headers, name, default):
    """Index sloupce podle názvu v hlavičce; když chybí, použije výchozí pozici."""
    for i, h in enumerate(headers):
        if h.lower().startswith(name):
            return i
    return default


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
        h = row["headers"]
        i_skupina = column_index(h, "skupina", 0)
        i_cislo = column_index(h, "číslo", 1)
        i_tymy = column_index(h, "týmy", 2)
        i_stav = column_index(h, "stav", 3)
        i_cas = column_index(h, "čas", -1)  # čas začátku (HH:MM), nemusí být k dispozici
        if len(c) > max(i_skupina, i_cislo, i_tymy, i_stav) and FILTER in c[i_tymy]:
            matches.append({
                "skupina": c[i_skupina],
                "cas": c[i_cas] if 0 <= i_cas < len(c) else "",
                "cislo": c[i_cislo],
                "tymy": c[i_tymy],
                "stav": c[i_stav],
                "badge": row["badge"],
                "href": "https://ezapis.cvf.cz/online/" + row["href"],
            })
    return matches


def main():
    now = datetime.now(ZoneInfo("Europe/Prague"))
    old = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {}
    old_future_days = {d["date"]: d["matches"] for d in old.get("days", [])}
    old_past_days = {d["date"]: d["matches"] for d in old.get("past_days", [])}

    # Stahuj budoucí zápasy
    future_days = []
    for i in range(DAYS_AHEAD + 1):
        date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            matches = fetch_day(date)
        except Exception as e:  # při výpadku ponechat stará data pro daný den
            print(f"Chyba {date}: {e}", file=sys.stderr)
            matches = old_future_days.get(date, [])
        future_days.append({"date": date, "matches": matches})

    # Stahuj minulé zápasy
    past_days = []
    for i in range(1, DAYS_BACK + 1):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            matches = fetch_day(date)
        except Exception as e:  # při výpadku ponechat stará data pro daný den
            print(f"Chyba {date}: {e}", file=sys.stderr)
            matches = old_past_days.get(date, [])
        if matches:  # jen dny se zápasy
            past_days.append({"date": date, "matches": matches})

    # Seřaď minulé zápasy od nejnovějšího
    past_days.sort(key=lambda x: x["date"], reverse=True)

    # Neměnit soubor, pokud se změnil jen čas aktualizace (méně commitů)
    if old.get("days") == future_days and old.get("past_days") == past_days:
        print("Beze změny")
        return
    data = {
        "updated": now.strftime("%Y-%m-%d %H:%M"),
        "days": future_days,
        "past_days": past_days
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    future_count = sum(len(d['matches']) for d in future_days)
    past_count = sum(len(d['matches']) for d in past_days)
    print(f"Uloženo {future_count} budoucích + {past_count} minulých zápasů")


if __name__ == "__main__":
    sys.exit(main())


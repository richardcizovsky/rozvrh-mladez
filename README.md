# Rozvrh tréninků TJ Sokol Vratimov

Stránka se rozvrhem tréninků a zápasy z eZapis.

## Struktura projektu

```
rozvrh-mladez/
├── index.html              # Hlavní stránka
├── fotogalerie.html        # Fotogalerie (samostatná stránka, fotky se nestahují s rozpisem)
├── foto/                   # Fotky ve WebP (1920 px), náhledy v foto/nahled/ (720 px)
├── logo.png                # Logo klubu
├── current.json            # Zápasy z eZapis (generuje se automaticky)
├── sitemap.xml             # Mapa webu pro SEO
├── robots.txt              # Pravidla pro roboty
├── _config.yml             # GitHub Pages config
├── CNAME                   # Vlastní doména pro GitHub Pages
├── .github/
│   ├── copilot-instructions.md  # Instrukce pro Copilota
│   └── workflows/
│       └── current.yml     # GitHub Actions – aktualizace current.json každých 5 minut
└── scripts/
    └── fetch_current.py    # Script na stažení zápasů z eZapis
```

## Lokální náhled stránky

`index.html` načítá `current.json` přes `fetch`, což nefunguje z `file://`. Spusť lokální server:

```bash
python3 -m http.server
```

a otevři `http://localhost:8000`.

Pokud hlásí `OSError: [Errno 48] Address already in use`, server už běží (zjistíš přes `lsof -nP -iTCP:8000 -sTCP:LISTEN`). Buď použij běžící server, ukonči ho (`kill <PID>`), nebo spusť jiný port: `python3 -m http.server 8001`.

Mobilní zobrazení otestuješ v prohlížeči přes vývojářské nástroje (Chrome: `Cmd+Opt+I` a pak `Cmd+Shift+M`).

## Lokální testování `fetch_current.py`

### Instalace závislostí

Script nemá externí závislosti, používá jen standardní Python knihovny.

### Spuštění

V kořenovém adresáři projektu spusť script (vyžaduje přístup k internetu):

```bash
python3 scripts/fetch_current.py
```

### Co se stane

- Script stáhne zápasy na dnešek a 8 dní dopředu (budoucí zápasy)
- Script stáhne zápasy z posledních 8 dní zpět (minulé zápasy)
- Filtruje zápasy, kde hraje "Sokol Vratimov"
- Pokud se některý den nepodaří stáhnout, ponechá se jeho předchozí obsah
- Uloží data do `current.json` (jen pokud se zápasy změnily)
- Pro minulé zápasy se zobrazují jen dny se skutečnými zápasy
- Vypíše počet načtených budoucích a minulých zápasů

### Výstup

Příklad úspěšného běhu:
```
Uloženo 6 budoucích + 13 minulých zápasů
```

Pokud se nic nezmění:
```
Beze změny
```

Při chybě:
```
Chyba 2026-10-08: [popis chyby]
```

## Automatizace

Script je spouštěn automaticky prostřednictvím GitHub Actions každých 5 minut (`.github/workflows/current.yml`, lze spustit i ručně přes `workflow_dispatch`). Pokud se `current.json` změní, workflow ho commitne a pushne.

`current.json` needituj ručně, generuje ho script.

## Data v `current.json`

```json
{
  "updated": "2026-10-12 12:44",
  "days": [
    {
      "date": "2026-10-12",
      "matches": []
    },
    {
      "date": "2026-10-14",
      "matches": [
        {
          "skupina": "OV-Z",
          "cislo": "(10)",
          "tymy": "TJ Hlučín - TJ Sokol Vratimov",
          "stav": "-",
          "badge": "",
          "href": "https://ezapis.cvf.cz/online/view.php?match=943013"
        }
      ]
    }
  ],
  "past_days": [
    {
      "date": "2026-10-11",
      "matches": [
        {
          "skupina": "MS-U16Z-T1D",
          "cislo": "(1)",
          "tymy": "TJ Sokol Vratimov \"A\" - TJ Frenštát p. R. \"B\"",
          "stav": "3:1 (23,-18,21,18)",
          "badge": "PLAY",
          "href": "https://ezapis.cvf.cz/online/view.php?match=953188"
        }
      ]
    }
  ]
}
```

### Pole v JSON

- **updated**: Čas poslední aktualizace
- **days**: Budoucí zápasy od dnešního dne až na 8 dní dopředu (včetně prázdných dní)
- **past_days**: Minulé zápasy z posledních 8 dní (jen dny se zápasy)

## Zobrazení na webu

Stránka `index.html`:
- Zobrazuje statický rozvrh tréninků
- Zobrazuje sekci **"Aktuální a budoucí zápasy"** (8 dní dopředu) - plánované zápasy od dnešího dne
  - Dnešní zápasy zobrazují řádek s výsledky a sety
  - Budoucí zápasy (ne dnešní) zobrazují jen týmy bez výsledků
- Zobrazuje sekci **"Odehrané zápasy - Minulý týden"** (8 dní zpět) - minulé zápasy od včerejška zpět
  - Zobrazují jen dny se skutečnými zápasy
  - Vždy zobrazují výsledky a jednotlivé sety
- Obě sekce dynamicky načítají data z `current.json`
- Dny bez zápasů se nezobrazují (v sekci aktuálních se dnešní den vždy zobrazí)
- Zápasy jsou seřazeny od nejnověji odehrané (minulé) a od dnešního dne (budoucí)

### Mobilní zobrazení

`index.html` i `tym.html` mají na malých displejích menší písmo:
- do šířky 768 px je základní velikost písma `14px`, do 420 px `13px` (na desktopu výchozích 16 px)
- většina velikostí je v `em`, takže se nadpisy, tabulky i štítky zmenší úměrně
- na mobilu jsou také menší odsazení v tabulkách, tlačítkách a záhlavích panelů
- `text-size-adjust: 100%` brání tomu, aby si mobilní prohlížeč (hlavně iOS Safari) písmo sám zvětšoval

Při úpravách stylů zadávej velikosti písma v `em`, aby se na mobilu správně zmenšily.

## Fotogalerie

`fotogalerie.html` je samostatná stránka (odkaz z `index.html`), takže se fotky nestahují při každém načtení rozpisu.
Mřížka načítá jen malé náhledy (`loading="lazy"`), plná fotka se stáhne až po kliknutí.

Přidání fotky (ImageMagick, odstraní EXIF/GPS metadata):

```bash
magick FOTKA.jpg -auto-orient -strip -resize '1920x1920>' -quality 78 foto/nazev.webp
magick FOTKA.jpg -auto-orient -strip -resize '720x720>' -quality 70 foto/nahled/nazev.webp
```

Pak přidej položku `{ file: "nazev", title: "Popisek" }` do pole `PHOTOS` ve `fotogalerie.html`.

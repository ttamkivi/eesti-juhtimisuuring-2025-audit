# Eesti Juhtimisvaldkonna Uuring 2025 — sõltumatu analüüs ja andmelekke audit

> Sõltumatu analüüs ja audit Eesti Juhtimisvaldkonna Uuringu 2025 avalikust Power BI andmelauast.

**Tellija:** Ettevõtluse ja Innovatsiooni Sihtasutus (EIS, Hange nr 291688)
**Teostajad:** Tartu Ülikooli majandusteaduskond + OÜ LevelLab
**Analüüsi autor:** Taavi Tamkivi (sõltumatu, mai 2026)

## Mida see repo sisaldab

| Fail | Mis see on |
|---|---|
| **`index.html`** / **`analysis.html`** | 📊 Interaktiivne analüüs, 5 filtrit, 14 küsimust, 41,592 vastust manustatud failis. Internet pole vajalik. **Ava brauseris ja vaata.** |
| **`AUDIT_REPORT.md`** | 📋 Auditi-aruanne andmelekkest: mis on lekkinud, kuidas, GDPR-risk, soovitused tellijale. |
| **`extract.html`** | 🛠 Reprodutseeritav andmestiku ekstraktor — avab Power BI avalikku lõpp-punkti, laadib alla 7 tabelit ZIP-ina. |
| **`start.command`** | ▶️ Mac-i topelt-klõpsatav helper, mis käivitab kohaliku veebiserveri. |
| **`build_offline.py`** | 🐍 Python-skript, mis CSV-de põhjal genereerib `analysis.html` koos manustatud andmetega. |

## Põhileid

Power BI „Publish to Web" embed avaldab **tervet andmemudelit**, mitte ainult agregaate, mida visualiseeringud kuvavad:

- **`FactSurvey`** — 55,840 vastaja-tasemel rida (436 organisatsiooni × 30 küsimust × kõik vastusvariandid)
- **`FactFinance`** — 3,643 finantskirjet (2022–2024 müügitulu, tööjõukulud, puhaskasum vastaja kohta)
- **`DimRespondent`** — 436 organisatsiooni segmenteerimistunnustega (Sektor, Liik, Töötajaid, Piirkond, Edukus)

Kombineerides need tunnused ja finantsandmed (käive 537M €, 250+ töötajat, Tallinn) saab paljud ettevõtted **triviaalselt re-identifitseerida**. Sama vastaja vastused küsimustele 21 (töökiusamine!), 22 (sisemised väited) on samuti taastatavad.

Vt täpsemalt: [`AUDIT_REPORT.md`](AUDIT_REPORT.md).

## Viis analüüsi peamist leidu

1. **„Edukas" = 2024. aasta kasumlikkus** — kategooria pole sõltumatu skoor vaid finantsmõõdik
2. **Avalik sektor teatab töökiusamist 8× sagedamini** kui tootmissektor (78% vs 47% vähemalt korra)
3. **Suurettevõtete re-identifitseerimine on triviaalne** — €537M käibega Tallinna teenusettevõte = 1–3 kandidaati
4. **15 organisatsiooni ei oma ühtegi plaani** — sealhulgas mitmed „edukad"
5. **„Moodne juhtimine" on enamasti loosung** — AI 6-10%, avalikus sektoris 0%

## Kuidas käivitada

### Lihtsaim viis (analüüs)

Lae alla `index.html` ja ava brauseris (Chrome / Safari / Firefox). Andmed on failis sees — internet pole vajalik. Saad filtreerida Liigi, Sektori, Töötajate arvu, Piirkonna ja Edukuse järgi.

### Andmete uuesti tõmbamine

Kui tahad andmeid otse Power BI-st uuesti ekstraktida (et veenduda, et leke on alles olemas):

```bash
# Topelt-klõpsa Mac-is:
./start.command

# VÕI ava extract.html otse brauseris ja klõpsa „Extract all tables" —
# kõik 7 CSV-d laaditakse ZIP-ina su Downloads kausta.
```

### Offline-analüüsi uuesti ehitamine

Kui sul on raw CSV-failid (samad mis `extract.html` toodab):

```bash
python3 build_offline.py
```

See loeb CSV-d kaustast `raw/` ja ehitab uue `analysis.html` koos manustatud andmetega.

## Soovitused tellijale (EIS) ja teostajatele

1. **Vaadake andmelaua avaldamist üle.** Power BI „Publish to Web" annab juurdepääsu kõigile 7 tabelile sealhulgas vastaja-tasemel `FactSurvey` ja `FactFinance`.
2. **Selgitage „Edukas" kategooria definitsiooni.** Kui see on tuletatud kasumimarginaalist, tuleks see selgesõnaliselt välja öelda.
3. **Avaliku sektori kiusamise näitajad väärivad järelteemat.** 78% „vähemalt korra" on uudisväärtuslik info, kuid valim on väike (n=23).
4. **Lisage Q5 selgitused.** 15 vastajat valisid „Plaan puudub" kõikide plaaniliikide kohta — tõenäoliselt mõisteti küsimust valesti.

## Eetiline märkus

See repo **ei sisalda raw andmeid** (FactSurvey ja FactFinance CSV-d) eesmärgiga **mitte amplifitseerida** sama lekke, mille audit kirjeldab. Kõik analüüsi- ja statistilised numbrid on agregaadid; ühegi konkreetse vastaja andmeid ei ole publitseeritud.

Kui siiski soovid raw andmeid auditeerida või kontrollida — mine [Power BI avaliku andmelauaga](https://app.powerbi.com/view?r=eyJrIjoiMzM0MTE5OGUtZjIwZC00NjQxLTgyMTItMjZjYmNlMTNlZThiIiwidCI6ImZiZmFiM2UwLTljNjUtNDFhZi05OWMwLTZmZmI5NTBmZDgzZCIsImMiOjl9) ja käivita `extract.html`. Andmed on nagunii avalikud (mis ongi probleem).

## Litsents

MIT litsents — vaba kasutamine, modifitseerimine, levitamine. Andmed kuuluvad EIS-ile ja teostajatele.

## Kontakt

Taavi Tamkivi · [taavi.tamkivi@gmail.com](mailto:taavi.tamkivi@gmail.com)

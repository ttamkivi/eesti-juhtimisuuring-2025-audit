# Power BI Public Embed — Data Exposure Audit

**Asset:** Eesti Juhtimisvaldkonna Uuring 2025 — interaktiivne andmelaud
**URL:** `https://app.powerbi.com/view?r=eyJrIjoiMzM0MTE5OGUtZjIwZC00NjQxLTgyMTItMjZjYmNlMTNlZThiIiwidCI6ImZiZmFiM2UwLTljNjUtNDFhZi05OWMwLTZmZmI5NTBmZDgzZCIsImMiOjl9`
**Publisher:** Tartu Ülikool majandusteaduskond + OÜ LevelLab, on behalf of Ettevõtluse ja Innovatsiooni Sihtasutus (EIS)
**Procurement:** Hange nr 291688
**Audit date:** 4 May 2026
**Auditor:** Taavi Tamkivi

---

## Headline finding

The Power BI "Publish to web" embed used to share the dashboard's aggregated visuals **also exposes the entire underlying dataset, including respondent-level rows**, via an unauthenticated HTTPS endpoint. Anyone who has the report URL can pull the raw data — not just the cross-tabs shown in the dashboard.

This is the standard, documented behaviour of Power BI's public publish-to-web feature when the dataset model is reachable from the report. The dashboard authors almost certainly did not intend for the respondent-level table to be public. It is, today.

---

## What's exposed

The report's data model contains seven tables (full schema and CSVs attached). Counts as of audit date:

| Table                  | Rows   | What it contains                                                  |
|------------------------|-------:|-------------------------------------------------------------------|
| `DimRespondent`        |    436 | One row per surveyed organisation: Vastuse ID, Edukas, Edukas_tase, Sektor, Liik, Töötajaid, Piirkond |
| `DimQuestion`          |     30 | Question metadata (label, scale code, panel)                      |
| `DimScale`             |     66 | Answer scale lookups (Skaala 1..14, Jah-Ei)                       |
| `DimOption_Base`       |    200 | Option labels per question                                        |
| `FactFinance`          |  3,643 | Per-respondent financials: Vastuse ID × Year × Metric × Amount    |
| `FactSurvey`           | 55,840 | **Respondent-level answer matrix:** Vastuse ID × QuestionID × OptionLabel × Answer_Raw × SelectedFlag × ScaleCode × HasScale |
| `FactSurvey_PreOption` | 55,840 | Pre-option respondent-level answers including raw question text   |

The two `FactSurvey*` tables are the sensitive ones. They are joinable on `Vastuse ID` to `DimRespondent`, which gives a complete per-organisation answer file across all 30 questions plus three years of financial data. Effectively, **the original survey export is reconstructable in full**.

---

## How the exposure works (technical detail)

The Power BI embed loads JavaScript that issues unauthenticated POSTs to:

```
https://wabi-west-europe-e-primary-api.analysis.windows.net/public/reports/querydata?synchronous=true
```

Authentication consists solely of an `X-PowerBI-ResourceKey` header containing the GUID `3341198e-f20d-4641-8212-26cbce13ee8b` — **the same GUID embedded in the public URL**.

The endpoint accepts arbitrary `SemanticQueryDataShapeCommand` queries against the model. There is a per-query row cap of ~30,000, but it can be paginated trivially (e.g., by `QuestionID`). The full extraction takes ~30 HTTP requests and finishes in under a minute.

A schema map is also publicly exposed at `/public/reports/conceptualschema`, which lists every entity, column, and relationship without auth.

**Reproduction:** open the included `extract.html` in any browser and click *Extract all tables*. CSVs land in your Downloads folder.

---

## Risk assessment

### Re-identification
The respondent-level table contains no direct identifiers (no organisation name, no e-mail). However, the combination of fields per row is highly identifying:

- `Sektor` (Primaarne / Sekundaar / Tertsiaar)
- `Liik` (e.g., "Erasektor - Tootmine")
- `Töötajaid` (size band: <10, 10–49, 50–249, 250+)
- `Piirkond` (e.g., "Tallinn ja Harjumaa")
- `Edukas` / `Edukas_tase` (success classification)
- 30 question answers, including ones describing strategic plans, internal practices, problems with workplace harassment, and three years of `Müügitulu` / `Tööjõukulud` figures (`FactFinance`)

For organisations that are unique on the demographic dimensions — which will be many at the upper size bands and in smaller regions — this enables re-identification by anyone who knows roughly which companies were sampled.

### GDPR / personal data
The dataset does not appear to contain personal data of natural persons directly. However:
- `FactFinance` is sensitive commercial information (revenue, labour cost) that organisations did not consent to publish.
- Question 21 records whether the organisation has experienced workplace bullying / harassment / discrimination — re-identifiable disclosure of a "yes" answer here could be reputationally damaging.
- If any respondents are sole proprietors, their data is personal data under GDPR.

### Procurement / contractual
The procurement (Hange nr 291688) almost certainly specified that the dashboard would publish aggregate results only. Publishing the underlying respondent data — even unintentionally — likely breaches the data-handling clause of that procurement. Worth checking the contract.

---

## Remediation options

In rough order of effort:

1. **Republish with row-level security or pre-aggregated dataset** *(recommended).*
   Publish a Power BI report whose backing dataset contains only the cross-tabs the dashboard actually shows — not the row-level fact tables. Visuals look identical; the underlying model contains nothing private to leak. This is the only fix that addresses the root cause.

2. **Take the public link down and re-share via Power BI Service** with named-user access.
   Removes the leak entirely but loses the convenience of public access.

3. **"Publish to web" is the wrong feature for this dataset.**
   Microsoft's documentation explicitly warns that publish-to-web exposes the entire model. Switch off publish-to-web (Settings → Tenant settings → Publish to web → restrict to specific groups, or disable).

4. **Retain the link, redact the data model.**
   Strip `FactSurvey`, `FactSurvey_PreOption`, `FactFinance`, and the joinable keys from the model before publishing. Keep only pre-aggregated measures. This is option 1 with less rebuilding.

Whatever path is chosen, the existing public link should be revoked first — Power BI publish-to-web links cannot be retroactively redacted, and the data has been live since at least the dashboard launch date.

---

## Suggested communication to publisher

Suggested wording (Estonian or English, as you prefer) to TÜ / LevelLab / EIS:

> Tere — märkasime, et avaliku Power BI andmelaua taga olev andmemudel on tervikuna avalikult kättesaadav, sealhulgas vastaja-tasemel `FactSurvey` tabel (436 organisatsiooni × 30 küsimust × kõik vastusvariandid) ja `FactFinance` tabel (3 aasta müügitulu ja tööjõukulud organisatsiooni kohta). See ei nõua autentimist — piisab avaliku lingi GUID-st.
>
> Lisame demonstratsiooni (üks HTML-fail, mille saab brauseris avada — see laadib alla kõik 7 tabelit CSV-formaadis ~1 minutiga) ja lühikese auditiraporti.
>
> See on Power BI "Publish to web" funktsiooni dokumenteeritud käitumine, mitte rünnak — kuid on tugev oletus, et seda ei olnud kavandatud. Soovitame: (1) avaliku lingi sulgeda, (2) avaldada uuesti andmemudeliga, mis sisaldab ainult agregaate, mida visualiseeringud kuvavad. Hea meelega aitame, kui kasulik.

---

## Audit artefacts

Saved to `~/Desktop/Brain/powerbi_audit/`:

- `AUDIT_REPORT.md` — this document
- `extract.html` — self-contained reproducible extractor (open in browser)
- `raw/DimRespondent.csv`, `raw/DimQuestion.csv`, `raw/DimScale.csv`, `raw/DimOption_Base.csv` — already extracted dimension tables
- `raw/FactFinance.csv`, `raw/FactSurvey.csv`, `raw/FactSurvey_PreOption.csv` — generated when you run `extract.html`

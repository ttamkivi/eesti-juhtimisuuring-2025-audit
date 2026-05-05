#!/usr/bin/env python3
"""
v2: rekonstrueerin lisandväärtus per töötaja FactFinance-st ja teen
korraliku 33/33/33 tertsiili. Siis võrdlen sektor- vs mgt-praktika-driverit.

Metoodika:
  Lisandväärtus = Tööjõukulud + Puhaskasum + Kulum
  Aga FactFinance-s pole Kulum (depreciation) eraldi. Approximatsioon:
  - Lisandväärtuse proxy = Tööjõukulud + Puhaskasum  (ignore depreciation)
  - Müügitulu/töötaja  (revenue per FTE) — ka oluline mõõdik
  - Tööjõukulud/töötaja (avg salary) — kõrge palk = kõrge VA

  Töötajate arv kategoorias -> midpoint:
    "vähem kui 10"     -> 5
    "10 kuni 49"       -> 30
    "50 kuni 249"      -> 150
    "250+"             -> 400

  3 aasta keskmine (2022-2024) iga vastaja kohta, kus andmed olemas.
"""
import csv
from collections import defaultdict, Counter
from pathlib import Path
import statistics

RAW = Path("/sessions/nice-confident-einstein/mnt/Brain/powerbi_audit/raw")

# Töötajate keskmine ühikute järgi
EMP_MIDPOINT = {
    "vähem kui 10 töötajat": 5,
    "10 kuni 49 töötajat": 30,
    "50 kuni 249 töötajat": 150,
    "250 töötajat või enam": 400,
}

# 1. Lae respondents
respondents = {}
with (RAW / "DimRespondent.csv").open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rid = row["Vastuse ID"]
        respondents[rid] = {
            "sektor": row["Sektor"] or "tundmatu",
            "edukas_orig": row["Edukas"] or "",
            "edukas_tase_orig": row["Edukas_tase"] or "",
            "suurus_kategooria": row["Töötajaid"],
            "töötajaid_midpoint": EMP_MIDPOINT.get(row["Töötajaid"], None),
            "liik": row["Liik"],
        }

# 2. Lae FactFinance ja arvuta per-respondent 3-aasta keskmised
finance_raw = defaultdict(lambda: defaultdict(dict))  # rid -> year -> {metric: amount}
with (RAW / "FactFinance.csv").open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r["HasAmount"] != "1":
            continue
        try:
            amount = float(r["Amount"])
            year = int(r["Year"])
        except (ValueError, TypeError):
            continue
        finance_raw[r["Vastuse ID"]][year][r["Metric"]] = amount

# Per respondent 3-aasta keskmised
for rid in respondents:
    years_data = finance_raw.get(rid, {})
    if not years_data:
        respondents[rid]["müügitulu_avg"] = None
        respondents[rid]["tööjõukulud_avg"] = None
        respondents[rid]["puhaskasum_avg"] = None
        respondents[rid]["lisandväärtus_avg"] = None
        continue

    mt = []  # müügitulu
    tk = []  # tööjõukulud
    pk = []  # puhaskasum
    for year in (2022, 2023, 2024):
        yd = years_data.get(year, {})
        if "Müügitulu" in yd:
            mt.append(yd["Müügitulu"])
        if "Tööjõukulud" in yd:
            tk.append(yd["Tööjõukulud"])
        if "Puhaskasum" in yd:
            pk.append(yd["Puhaskasum"])

    respondents[rid]["müügitulu_avg"] = sum(mt)/len(mt) if mt else None
    respondents[rid]["tööjõukulud_avg"] = sum(tk)/len(tk) if tk else None
    respondents[rid]["puhaskasum_avg"] = sum(pk)/len(pk) if pk else None

    # Lisandväärtus proxy = tööjõukulud + puhaskasum (ignore Kulum)
    if respondents[rid]["tööjõukulud_avg"] is not None and respondents[rid]["puhaskasum_avg"] is not None:
        respondents[rid]["lisandväärtus_avg"] = (
            respondents[rid]["tööjõukulud_avg"] + respondents[rid]["puhaskasum_avg"]
        )
    else:
        respondents[rid]["lisandväärtus_avg"] = None

# Per töötaja
for rid, r in respondents.items():
    mp = r["töötajaid_midpoint"]
    if mp is None:
        r["la_per_tootaja"] = None
        r["mt_per_tootaja"] = None
        r["tk_per_tootaja"] = None
        continue
    r["la_per_tootaja"] = r["lisandväärtus_avg"] / mp if r["lisandväärtus_avg"] else None
    r["mt_per_tootaja"] = r["müügitulu_avg"] / mp if r["müügitulu_avg"] else None
    r["tk_per_tootaja"] = r["tööjõukulud_avg"] / mp if r["tööjõukulud_avg"] else None

# Statistika
print("=" * 75)
print("LISANDVÄÄRTUS PER TÖÖTAJA — STATISTIKA")
print("=" * 75)

with_la = [(rid, r) for rid, r in respondents.items() if r["la_per_tootaja"] is not None]
print(f"\nVastajaid lisandväärtuse arvestuses: {len(with_la)} / 436")

la_values = [r["la_per_tootaja"] for _, r in with_la]
print(f"  Min:    {min(la_values):>12,.0f} EUR")
print(f"  P25:    {statistics.quantiles(la_values, n=4)[0]:>12,.0f} EUR")
print(f"  Median: {statistics.median(la_values):>12,.0f} EUR")
print(f"  P75:    {statistics.quantiles(la_values, n=4)[2]:>12,.0f} EUR")
print(f"  Max:    {max(la_values):>12,.0f} EUR")
print(f"  Mean:   {statistics.mean(la_values):>12,.0f} EUR")

# Filter: ainult realistlikud (välistame extrema mis tulevad väikese valimi suuruse-midpointide tõttu)
# Anomaaliad: kui müügitulu = 0 või negatiivne, või lisandväärtus < 0 (kahjum).
# Aga kahjum on legitimate, las jääb.

# Tertsiilid (33/33/33 lisandväärtuse järgi, ainult erasektor)
era_with_la = [(rid, r) for rid, r in with_la if r["liik"] != "Avalik sektor"]
print(f"\nEraSektoris: {len(era_with_la)}")

if era_with_la:
    sorted_era = sorted(era_with_la, key=lambda x: x[1]["la_per_tootaja"])
    n = len(sorted_era)
    t1_idx = n // 3
    t2_idx = 2 * n // 3
    t1_threshold = sorted_era[t1_idx][1]["la_per_tootaja"]
    t2_threshold = sorted_era[t2_idx][1]["la_per_tootaja"]

    print(f"\nKorrektne 33/33/33 tertsiil:")
    print(f"  madal:    < {t1_threshold:>12,.0f} EUR ({t1_idx} vastajat)")
    print(f"  keskmine: {t1_threshold:>12,.0f} - {t2_threshold:,.0f} EUR ({t2_idx-t1_idx} vastajat)")
    print(f"  kõrge:    > {t2_threshold:>12,.0f} EUR ({n-t2_idx} vastajat)")

    # Märgi tertsiil iga era-respondendi külge
    for i, (rid, r) in enumerate(sorted_era):
        if i < t1_idx:
            r["la_tertsiil"] = "madal"
        elif i < t2_idx:
            r["la_tertsiil"] = "keskmine"
        else:
            r["la_tertsiil"] = "kõrge"

    # Sektorite jaotus tertsiilides
    print("\n" + "=" * 75)
    print("TEST 1 v2: Sektor × KORREKTNE lisandväärtuse tertsiil (ainult erasektor)")
    print("=" * 75)

    sectors = ["Kvaternaar", "Tertsiaar", "Sekundaar", "Primaar"]
    ct = defaultdict(lambda: Counter())
    for rid, r in era_with_la:
        ct[r["sektor"]][r["la_tertsiil"]] += 1

    print(f"\n{'Sektor':<12} {'n':>4} | {'kõrge':>14} {'keskmine':>14} {'madal':>14}")
    print("-" * 70)
    for sektor in sectors:
        if sektor not in ct:
            continue
        dist = ct[sektor]
        total = sum(dist.values())
        if total == 0:
            continue
        parts = []
        for tase in ["kõrge", "keskmine", "madal"]:
            n = dist.get(tase, 0)
            pct = 100*n/total
            parts.append(f"{n:>3} ({pct:>3.0f}%)")
        print(f"{sektor:<12} {total:>4} | " + " ".join(f"{p:>14}" for p in parts))

    # Test 3 v2: P(kõrge | sektor)
    print("\n" + "=" * 75)
    print("TEST 3 v2: P(kõrge lisandväärtus | sektor) vs muu sektor")
    print("=" * 75)

    print(f"\n{'Sektor':<12} {'P(kõrge | sektor)':>18} {'P(kõrge | muu)':>18} {'ratio':>8}")
    print("-" * 65)
    for sektor in sectors:
        in_s = ct.get(sektor, Counter())
        out_s = Counter()
        for s, c in ct.items():
            if s != sektor:
                for k, v in c.items():
                    out_s[k] += v
        n_in = sum(in_s.values())
        n_out = sum(out_s.values())
        if n_in == 0 or n_out == 0:
            continue
        p_in = in_s.get("kõrge", 0) / n_in
        p_out = out_s.get("kõrge", 0) / n_out
        ratio = p_in / p_out if p_out > 0 else float("inf")
        print(f"{sektor:<12} {p_in:>17.1%} {p_out:>17.1%} {ratio:>7.2f}x")

    # Mgt-skoor
    modern_methods = [
        "Lean", "Tehisaru", "Andmepõhine", "Agiilne", "Klienditeekonna",
        "CRM", "Kliendisuhete", "Disainmõtlemine", "Innovatsioonijuhtimine",
        "Jätkusuutlik", "ESG", "Õppiv", "Coaching",
    ]
    mgt_use_count = defaultdict(int)
    with (RAW / "FactSurvey.csv").open(encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for r in reader:
            try:
                qid = int(r[1])
            except (ValueError, IndexError):
                continue
            if qid != 18:
                continue
            rid = r[0]
            opt = r[3] if len(r) > 3 else ""
            val = r[4] if len(r) > 4 else ""
            if not any(m.lower() in opt.lower() for m in modern_methods):
                continue
            if val.strip() == "3":  # Kasutame
                mgt_use_count[rid] += 1

    # TEST 2 v2: Mgt-skoor sektor × tertsiili kaupa
    print("\n" + "=" * 75)
    print("TEST 2 v2: Mgt-skoor sektor × KORREKTNE tertsiil")
    print("=" * 75)

    groups = defaultdict(list)
    for rid, r in era_with_la:
        score = mgt_use_count.get(rid, 0)
        groups[(r["sektor"], r["la_tertsiil"])].append(score)

    print(f"\n{'Sektor':<12} {'Tase':<10} {'n':>4} {'mgt-skoor avg':>14}")
    print("-" * 50)
    for sektor in sectors:
        for tase in ["kõrge", "keskmine", "madal"]:
            scores = groups.get((sektor, tase), [])
            if not scores:
                continue
            avg = sum(scores) / len(scores)
            print(f"{sektor:<12} {tase:<10} {len(scores):>4} {avg:>14.2f}")

    # WITHIN-SECTOR DELTA
    print("\n" + "=" * 75)
    print("TEST 2B v2: WITHIN-SECTOR delta (kõrge - madal mgt-skoor)")
    print("=" * 75)

    within_deltas = {}
    print(f"\n{'Sektor':<12} {'kõrge avg':>10} {'madal avg':>10} {'delta':>8} {'n_kõrge':>8} {'n_madal':>8}")
    print("-" * 70)
    for sektor in sectors:
        high = groups.get((sektor, "kõrge"), [])
        low = groups.get((sektor, "madal"), [])
        if len(high) < 3 or len(low) < 3:
            continue
        h_avg = sum(high) / len(high)
        l_avg = sum(low) / len(low)
        delta = h_avg - l_avg
        within_deltas[sektor] = delta
        print(f"{sektor:<12} {h_avg:>10.2f} {l_avg:>10.2f} {delta:>+8.2f} {len(high):>8} {len(low):>8}")

    # CROSS-SECTOR DELTA
    print("\n" + "=" * 75)
    print("TEST 2C v2: CROSS-SECTOR mgt-skoor (eri sektorite vahel kogu valim)")
    print("=" * 75)

    sektor_means = {}
    for sektor in sectors:
        all_in = []
        for tase in ["kõrge", "keskmine", "madal"]:
            all_in.extend(groups.get((sektor, tase), []))
        if all_in:
            sektor_means[sektor] = (sum(all_in)/len(all_in), len(all_in))

    print(f"\n{'Sektor':<12} {'mgt-skoor avg':>14} {'n':>5}")
    print("-" * 40)
    for sektor in sectors:
        if sektor in sektor_means:
            avg, n = sektor_means[sektor]
            print(f"{sektor:<12} {avg:>14.2f} {n:>5}")

    if "Kvaternaar" in sektor_means and "Sekundaar" in sektor_means:
        cross = sektor_means["Kvaternaar"][0] - sektor_means["Sekundaar"][0]
        avg_within = sum(within_deltas.values()) / max(len(within_deltas), 1) if within_deltas else 0
        print(f"\nCross-sector delta (Kvaternaar - Sekundaar): {cross:+.2f}")
        print(f"Within-sector delta keskmine:                 {avg_within:+.2f}")

    # ÜLDINE LISANDVÄÄRTUSE KESKMINE SEKTORITE KAUPA
    print("\n" + "=" * 75)
    print("LISANDVÄÄRTUS PER TÖÖTAJA SEKTORITE KAUPA (EUR/aasta)")
    print("=" * 75)

    by_sector = defaultdict(list)
    for rid, r in era_with_la:
        by_sector[r["sektor"]].append(r["la_per_tootaja"])

    print(f"\n{'Sektor':<12} {'n':>4} {'median':>14} {'mean':>14} {'p25':>14} {'p75':>14}")
    print("-" * 80)
    for sektor in sectors:
        vals = by_sector.get(sektor, [])
        if len(vals) < 3:
            continue
        med = statistics.median(vals)
        mn = statistics.mean(vals)
        if len(vals) >= 4:
            p25, _, p75 = statistics.quantiles(vals, n=4)
        else:
            p25 = min(vals); p75 = max(vals)
        print(f"{sektor:<12} {len(vals):>4} {med:>14,.0f} {mn:>14,.0f} {p25:>14,.0f} {p75:>14,.0f}")

    # KORRELATSIOON-ANALÜÜS: kas lisandväärtus vs mgt-skoor on tugevam korrelatsioon kui sektor vs lisandväärtus?
    print("\n" + "=" * 75)
    print("KORRELATSIOON: lisandväärtus vs (a) sektor, (b) mgt-skoor")
    print("=" * 75)

    # Sektor → lisandväärtuse seletusvõime: between-group variance / total variance
    all_la = [r["la_per_tootaja"] for _, r in era_with_la]
    overall_mean = statistics.mean(all_la)
    total_ss = sum((x - overall_mean) ** 2 for x in all_la)

    between_ss_sector = 0
    for sektor in sectors:
        vals = by_sector.get(sektor, [])
        if not vals:
            continue
        sec_mean = statistics.mean(vals)
        between_ss_sector += len(vals) * (sec_mean - overall_mean) ** 2
    eta_sq_sector = between_ss_sector / total_ss if total_ss > 0 else 0

    # Mgt-skoor → lisandväärtuse seletusvõime (paaride korrelatsioon)
    pairs = [(r["la_per_tootaja"], mgt_use_count.get(rid, 0)) for rid, r in era_with_la]
    n_pairs = len(pairs)
    mean_la = sum(p[0] for p in pairs) / n_pairs
    mean_mgt = sum(p[1] for p in pairs) / n_pairs
    cov = sum((p[0] - mean_la) * (p[1] - mean_mgt) for p in pairs) / n_pairs
    var_la = sum((p[0] - mean_la) ** 2 for p in pairs) / n_pairs
    var_mgt = sum((p[1] - mean_mgt) ** 2 for p in pairs) / n_pairs
    if var_la > 0 and var_mgt > 0:
        pearson_r = cov / (var_la * var_mgt) ** 0.5
    else:
        pearson_r = 0
    r_sq_mgt = pearson_r ** 2

    print(f"\n  η² (sektor seletab) = {eta_sq_sector:.3f}  ({eta_sq_sector*100:.1f}% lisandväärtuse variatsioonist)")
    print(f"  R² (mgt-skoor seletab) = {r_sq_mgt:.3f}  ({r_sq_mgt*100:.1f}% lisandväärtuse variatsioonist)")
    print(f"  Pearson r (mgt-skoor, lisandväärtus) = {pearson_r:+.3f}")

    print("\n  Tõlgendus:")
    if eta_sq_sector > r_sq_mgt:
        print(f"  → SEKTOR seletab rohkem ({eta_sq_sector*100:.1f}% vs {r_sq_mgt*100:.1f}%) — Taavi hüpotees toetatud")
    else:
        print(f"  → MGT-SKOOR seletab rohkem ({r_sq_mgt*100:.1f}% vs {eta_sq_sector*100:.1f}%) — Taavi hüpotees ei pea")

    # KOKKUVÕTE
    print("\n" + "=" * 75)
    print("LÕPPKOKKUVÕTE")
    print("=" * 75)
    if "Kvaternaar" in sektor_means and "Sekundaar" in sektor_means:
        kv_la_med = statistics.median(by_sector.get("Kvaternaar", [0]))
        sek_la_med = statistics.median(by_sector.get("Sekundaar", [0]))
        print(f"\n  Lisandväärtus per töötaja median:")
        print(f"    Kvaternaar (IT, finants): {kv_la_med:>12,.0f} EUR")
        print(f"    Sekundaar (tootmine):     {sek_la_med:>12,.0f} EUR")
        print(f"    Suhe: {kv_la_med/sek_la_med if sek_la_med > 0 else 0:.2f}x")

    print()

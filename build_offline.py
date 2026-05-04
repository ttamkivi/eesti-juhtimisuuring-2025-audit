#!/usr/bin/env python3
"""Build a fully offline analysis HTML from CSVs in powerbi_audit/raw/ + historical data."""
import csv, json, gzip, base64, re
from pathlib import Path

RAW = Path("/sessions/nice-confident-einstein/mnt/Brain/powerbi_audit/raw")
HIST = Path("/sessions/nice-confident-einstein/mnt/outputs/historical_data.json")
OUT = Path("/sessions/nice-confident-einstein/mnt/Brain/powerbi_audit/analysis_offline.html")
TEMPLATE = Path("/sessions/nice-confident-einstein/mnt/Brain/powerbi_audit/analysis.html")

QIDS = {4,5,6,7,13,14,15,16,17,18,21,22,24,25}

def load_csv(name):
    with (RAW / f"{name}.csv").open(encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        return list(reader)

print("Loading DimRespondent...")
dr_raw = load_csv("DimRespondent")
respondents = [[r[0], r[6], r[4], r[3], r[5], r[2]] for r in dr_raw]
print(f"  {len(respondents)} respondents")

print("Loading FactFinance...")
finance = load_csv("FactFinance")
print(f"  {len(finance)} rows")

print("Loading FactSurvey (filtering to needed questions)...")
qd = {qid: [] for qid in QIDS}
with (RAW / "FactSurvey.csv").open(encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for r in reader:
        try:
            qid = int(r[1])
        except (ValueError, IndexError):
            continue
        if qid in QIDS:
            qd[qid].append([r[0], r[3], r[4]])
total_fs = sum(len(v) for v in qd.values())
print(f"  Filtered to {total_fs} rows across {len(QIDS)} questions")

# Load historical data
print("Loading historical data...")
hist = json.loads(HIST.read_text(encoding="utf-8"))
print(f"  Loaded {len(hist)} historical sections")

data = {
    "respondents": respondents,
    "finance": finance,
    "qd": {str(k): v for k, v in qd.items()},
    "hist": hist,
}
json_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
print(f"  Combined JSON size: {len(json_str):,} chars")

gz = gzip.compress(json_str.encode("utf-8"), compresslevel=9)
b64 = base64.b64encode(gz).decode("ascii")
print(f"  Gzipped + base64: {len(b64):,} chars ({len(gz):,} bytes gzipped)")

# Read template
template = TEMPLATE.read_text(encoding="utf-8")

# Inject embed block BEFORE the existing <script> (which contains init())
embed_block = f'''
<script id="embedded-data" type="application/octet-stream">{b64}</script>
<script>
window.__OFFLINE_MODE = true;
async function loadEmbeddedData() {{
  const b64 = document.getElementById("embedded-data").textContent.trim();
  const bin = atob(b64);
  const u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  const ds = new DecompressionStream("gzip");
  const stream = new Blob([u8]).stream().pipeThrough(ds);
  const text = await new Response(stream).text();
  const data = JSON.parse(text);
  const qd = {{}};
  for (const k in data.qd) qd[parseInt(k)] = data.qd[k];
  return {{ respondents: data.respondents, finance: data.finance, qd, hist: data.hist }};
}}
</script>
'''

# Replace the init() function to use embedded data instead of fetch
new_init = '''async function init() {
  const status = document.getElementById("status");
  const progress = document.getElementById("progress");
  try {
    status.textContent = "Dekodeerin manustatud andmeid...";
    progress.textContent = "(loen ~1 MB pakitud andmeid)";
    const data = await loadEmbeddedData();
    STATE.respondents = data.respondents;
    STATE.finance = data.finance;
    STATE.qd = data.qd;
    STATE.hist = data.hist;
    populateFilters();
    applyFilters();
    status.className = "done";
    let totalAns = 0; for (const k in STATE.qd) totalAns += STATE.qd[k].length;
    status.innerHTML = "✓ Andmed laaditud manustatud allikast: " + STATE.respondents.length + " vastajat, " + STATE.finance.length + " finantskirjet, " + totalAns + " vastust + 15 aasta võrdlusandmed. <div class='progress'>Internet pole vajalik. Kasuta filtreid.</div>";
  } catch (e) {
    status.className = "error";
    status.innerHTML = '<span class="big">Viga manustatud andmete dekodeerimisel: ' + e.message + '</span>';
    console.error(e);
  }
}'''

pattern = re.compile(r"async function init\(\) \{.*?^init\(\);", re.DOTALL | re.MULTILINE)
match = pattern.search(template)
if not match:
    print("ERROR: could not find init() function in template")
    exit(1)

patched = template[:match.start()] + new_init + "\ninit();" + template[match.end():]

# Inject embed block BEFORE the existing <script>
script_marker = "<script>\nconst RESOURCE_KEY"
patched = patched.replace(script_marker, embed_block + "\n" + script_marker)

# Mark as offline in title
patched = patched.replace(
    "<title>Eesti Juhtimisuuring 2025 — sõltumatu analüüs ja kontekst</title>",
    "<title>Eesti Juhtimisuuring 2025 — sõltumatu analüüs (OFFLINE)</title>"
)
patched = patched.replace(
    "<h1>Eesti Juhtimisvaldkonna Uuring 2025 — sõltumatu analüüs ja kontekst</h1>",
    "<h1>Eesti Juhtimisvaldkonna Uuring 2025 — sõltumatu analüüs (OFFLINE)</h1>"
)

OUT.write_text(patched, encoding="utf-8")
print(f"\n✓ Wrote {OUT}")
print(f"  Final HTML size: {len(patched):,} chars ({len(patched)/1024:.1f} KB)")

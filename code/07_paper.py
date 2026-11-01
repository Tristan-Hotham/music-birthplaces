"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). Facts stated in words are checked here
(and those on the page, by importing 05_build_site.py). The DOI stays as a 10.5281/zenodo.23850287 placeholder for the publisher."""
import subprocess, importlib.util
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "05_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Where_The_Worlds_Music_Comes_From"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# ---------- facts stated in words in the paper ----------
A = R["areas"]
assert [p["name"] for p in R["places"]["top"][:3]] == ["Vienna", "New York City", "London"]
assert [a["name"] for a in A["top"][:7]] == ["New York", "London", "Paris", "Vienna", "Tokyo", "Berlin", "Prague"]
assert [a["name"] for a in A["per_capita"][:4]] == ["Tallinn", "Prague", "Brno", "Erfurt"] and A["per_capita"][3]["per100k"] > 230
FC = {r["k"]: r for r in R["contrast"]["fam_cont"]}
assert max(FC.values(), key=lambda r: r["Europe"])["k"] == "conductor" and {k for k in FC if FC[k]["Europe"] > 65} == {"conductor", "instr", "composer"}
assert FC["rap"]["North America"] >= FC["rap"]["Europe"] - 2 and abs(FC["songwriter"]["North America"] - FC["songwriter"]["Europe"]) < 2
assert max(FC.values(), key=lambda r: r["Asia"])["k"] == "singer"
SG = R["signature"]["by"]
assert SG["cantopop"]["city"] == "Hong Kong" and SG["dancehall"]["city"] == "Kingston"
big = sorted([s for s in R["signature"]["rows"] if s["n"] >= 20], key=lambda s: -s["pct"])
assert [s["genre"] for s in big[:6]] == ["cantopop", "samba", "grime", "tango", "K-pop", "fado"], [s["genre"] for s in big[:6]]
assert SG["country music"]["pct"] < 6
assert [r["name"] for r in R["genre_cities"]["rnb"]["lq"][:2]] == ["Lagos", "Detroit"]
C = R["countries"]
assert [c["iso"] for c in C["per_m"][:3]] == ["EST", "CZE", "AUT"]
d = R["decades"]
assert d["ita"]["late_pct"] < d["ita"]["early_pct"] and d["usa"]["late_pct"] > 2 * d["usa"]["early_pct"]
assert [r["iso"] for r in R["women"]["top"][:4]] == ["IDN", "CHN", "KOR", "JPN"] and R["women"]["top"][3]["pct"] > 40
assert {"DEU", "CZE", "ITA"} <= {r["iso"] for r in R["women"]["bottom"]}
cf = {r["k"]: r["iso_pct"] for r in R["coverage"]["by_fam"] if r["k"] != "other"}
assert min(cf, key=cf.get) == "dj" and max(cf, key=cf.get) == "conductor"
assert R["coverage"]["by_fam"][4]["k"] == "dj" and R["coverage"]["by_fam"][5]["k"] == "conductor"
assert FC["conductor"] == R["contrast"]["fam_cont"][5] and R["contrast"]["fam_cont"][3]["k"] == "rap" and R["contrast"]["fam_cont"][1]["k"] == "singer"
assert R["women"]["by_genre"][12]["k"] == "metal"


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    return tex(str(v))


s = R["source"]
TP = ("\\begin{table}[tbp]\\centering\\small\\caption{From query to data.}\\label{tab:pipe}"
      "\\begin{tabular}{p{10.5cm}r}\\toprule Step & Count\\\\\\midrule\n"
      f"Rows returned by the musician query & {s['n_rows']:,}\\\\\n"
      f"Musicians & {s['n']:,}\\\\\n"
      f"\\quad with a birthplace & {s['n_bp']:,}\\\\\n"
      f"\\quad with a birth country & {s['n_iso']:,}\\\\\n"
      f"\\quad with a birthplace point (on the map) & {s['n_pt']:,}\\\\\n"
      f"\\quad\\quad of which in a city area & {s['n_in_area']:,}\\\\\n"
      f"\\quad with a year of birth & {s['n_dob']:,}\\\\\n"
      f"\\quad with a recorded gender & {s['n_gender']:,}\\\\\n"
      f"\\quad with a genre & {s['n_genre']:,}\\\\\n"
      f"\\quad notable ({NOTABLE}+ sitelinks) & {s['n_notable']:,}\\\\\n"
      f"Musical groups & {s['g_n']:,}\\\\\n"
      f"\\quad with a country & {s['g_iso']:,}\\\\\n"
      f"\\quad with a formation place & {s['g_loc']:,}\\\\\n"
      f"\\quad with a formation point (on the map) & {s['g_pt']:,}\\\\\n"
      f"\\quad with a year of formation & {s['g_inc']:,}\\\\\n"
      f"\\quad with a genre & {s['g_genre']:,}\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for a, p, b in zip(A["top"][:15], A["per_capita"][:15], A["top_b"][:15]):
    rows += f"{tex(a['name'])} & {a['n']:,} & {a['notable']:,} & {tex(p['name'])} & {p['per100k']:.1f} & {tex(b['name'])} & {b['b']:,}\\\\\n"
TCI = ("\\begin{table}[tbp]\\centering\\small\\caption{City areas: most musicians born (with notable musicians), most musicians per 100,000 present-day residents (cities with " + str(A["per_capita_min_n"]) + "+ musicians), and most bands formed.}\\label{tab:cities}\\setlength{\\tabcolsep}{5pt}"
       "\\begin{tabular}{lrr@{\\hspace{14pt}}lr@{\\hspace{14pt}}lr}\\toprule City & Musicians & Notable & City & Per 100,000 & City & Bands\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for f, c in zip(R["families"]["rows"], R["contrast"]["fam_cont"]):
    rows += f"{tex(f['name'])} & {f['n']:,} & {f['w_pct']:.1f}\\% & {c['Europe']:.1f}\\% & {c['North America']:.1f}\\% & {c['Asia']:.1f}\\% & {c['South America']:.1f}\\% & {c['Africa']:.1f}\\%\\\\\n"
TF = ("\\begin{table}[tbp]\\centering\\small\\caption{Kinds of musician: people in each family (a person can be in several), women's share, and continent of birth.}\\label{tab:fam}\\setlength{\\tabcolsep}{4pt}"
      "\\begin{tabular}{lrrrrrrr}\\toprule Family & People & Women & Europe & N. America & Asia & S. America & Africa\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for x in sorted(R["signature"]["rows"], key=lambda x: -x["pct"]):
    rows += f"{tex(x['genre'])} & {tex(x['city'])} & {x['n']:,} & {x['of']:,} & {x['pct']:.1f}\\% & {tex(x['second'])} & {x['second_n']:,}\\\\\n"
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Home towns of named genres: the city area with most acts (musicians born and groups formed) tagged with the genre, the number of such acts on the map, the city's share, and the runner-up.}\\label{tab:sig}\\setlength{\\tabcolsep}{5pt}"
      "\\begin{tabular}{llrrrlr}\\toprule Genre & City & Acts & Of & Share & Next & Acts\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
cov = {c["dec"]: c for c in R["coverage"]["by_dec"]}
for w in R["women"]["by_dec"]:
    if w["n"] < 300: continue
    rows += f"{tex(decname(w['dec']))} & {w['n']:,} & {w['w']:,} & {w['pct']:.1f}\\% & {w['n_notable']:,} & {(str(round(w['pct_notable'], 1)) + chr(92) + '%') if w['n_notable'] >= 30 else 'n/a'} & {cov[w['dec']]['iso_pct']:.0f}\\%\\\\\n"
TW = ("\\begin{table}[tbp]\\centering\\small\\caption{By decade of birth: musicians with a recorded gender, women, women's share among all and among notable musicians (where 30 or more), and the share of all musicians with a birth country.}\\label{tab:women}"
      "\\begin{tabular}{lrrrrrr}\\toprule Born & With gender & Women & Share & Notable & Share & Birth country known\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
t = t.replace("{{TABLE_PIPELINE}}", TP).replace("{{TABLE_CITIES}}", TCI).replace("{{TABLE_FAM}}", TF).replace("{{TABLE_SIG}}", TS).replace("{{TABLE_WOMEN}}", TW)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t, [l for l in t.splitlines() if "{{" in l or "--" in l][:3]
for bad in ("DSIT", "DCMS"):
    assert bad not in t
# the DOI placeholder stays literal for the publisher; LaTeX needs its braces escaped
t = t.replace("DOIPLACEHOLDER", "\\{\\{DOI\\_URL\\}\\}")
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))

"""All results (data/results.json), reusable tables (data/*.csv, *.csv.gz) and page data (data/site.json, data/map/*).

Definitions
- Musician: a Wikidata human with an occupation that is musician or a subclass. Group: an item that is a musical group
  or a subclass ('bands' in the text, including orchestras and choirs unless the type filter says otherwise).
- Act: a musician or a group. Place: a musician's place of birth or a group's location of formation (P740).
- Decade: decade of birth for musicians, of formation (P571) for groups; before 1800 pooled.
- Notable: {NOTABLE}+ sitelinks (Wikipedia articles and other Wikimedia pages, in any language).
- Women's share: women / (women + men + another gender), among musicians whose gender Wikidata records.
- City area: points within 25 km of a Natural Earth place of 200,000 people or more (code/03_geo.py). Per-head rates use
  that place's present-day population (Natural Earth pop_max); countries use Natural Earth POP_EST.
- Genre families and occupation families: code/01_mappings.py. Location quotient of a genre in a city: the genre's share
  of the city's genre-tagged acts divided by its share of all genre-tagged acts.
"""
import csv, gzip, math, struct
from collections import Counter, defaultdict
from common import *

M0 = jload(f"{WORK}/musicians_geo.json"); M = M0["people"]
G0 = jload(f"{WORK}/groups_geo.json"); B = G0["groups"]
GEOJ = jload(f"{WORK}/geo.json"); META, QID, BIG = GEOJ["meta"], GEOJ["qid"], GEOJ["big"]
CN = lambda i: META[i]["name"] if i in META else i
RENAME = {"København": "Copenhagen", "Montréal": "Montreal", "Washington, D.C.": "Washington", "Wien": "Vienna", "Köln": "Cologne",
          "Tel Aviv-Yafo": "Tel Aviv", "Bombay": "Mumbai", "Ürümqi": "Urumqi", "Turin": "Turin", "Den Haag": "The Hague", "s-Gravenhage": "The Hague",
          "Kyiv": "Kyiv", "Kiev": "Kyiv", "Bogota": "Bogotá", "Sao Paulo": "São Paulo"}
cityname = lambda i: RENAME.get(re.sub(r"\s+", " ", BIG[i][0]), re.sub(r"\s+", " ", BIG[i][0]))
CONTS = ["Europe", "North America", "Asia", "South America", "Africa", "Oceania"]
pc = lambda a, b: round(100 * a / b, 1) if b else None
NOTE = lambda d: d["sl"] >= NOTABLE
FK = [k for k, _ in FAMS]; GK = [k for k, _ in GENS]
FN, GN = dict(FAMS), dict(GENS)

for d in M:
    d["dec"] = dec_of(d["by"]); d["kind"] = "m"
for d in B:
    d["dec"] = dec_of(d["by"]); d["kind"] = "b"; d["fam"] = [d["bt"]]
MI = [d for d in M if d["iso"]]; MP = [d for d in M if d["pt"]]
BI = [d for d in B if d["iso"]]; BP = [d for d in B if d["pt"]]
gk = [d for d in M if d["g"] in "wmo"]


def wshare(ds):
    g = [d for d in ds if d["g"] in "wmo"]
    return pc(sum(1 for d in g if d["g"] == "w"), len(g)), len(g)


R = {"meta": {"slug": SLUG, "page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "retrieved": RETRIEVED, "notable": NOTABLE}}
N = len(M)
src = {"n_rows": M0["n_rows"], "n_line_repairs": M0["n_line_repairs"], "n": N, "n_bp": sum(1 for d in M if d["bp"]),
       "n_iso": len(MI), "n_pt": len(MP), "n_country_bp": sum(1 for d in M if d["bp"] in QID), "n_multi_bp": sum(1 for d in M if d["nbp"] > 1),
       "agree_pct": pc(M0["agree"]["same"], M0["agree"]["same"] + M0["agree"]["different"]), "n_agree_checked": M0["agree"]["same"] + M0["agree"]["different"],
       "n_dob": sum(1 for d in M if d["by"]), "n_gender": len(gk), "n_w": sum(1 for d in M if d["g"] == "w"), "n_m": sum(1 for d in M if d["g"] == "m"),
       "n_o": sum(1 for d in M if d["g"] == "o"), "n_u": sum(1 for d in M if d["g"] == "u"), "n_nolabel": sum(1 for d in M if not d["n"]),
       "n_notable": sum(1 for d in M if NOTE(d)), "median_sl": sorted(d["sl"] for d in M)[N // 2], "n_genre": sum(1 for d in M if d["ngen"]),
       "n_places": len({d["bp"] for d in MP}), "n_countries": len({d["iso"] for d in MI}), "n_in_area": sum(1 for d in MP if d["area"] is not None),
       "n_occ_values": len(M0["occ_people"]), "n_multi_fam": sum(1 for d in M if len(d["fam"]) > 1),
       "g_rows": G0["n_rows"], "g_n": len(B), "g_loc": sum(1 for d in B if d["bp"]), "g_pt": len(BP), "g_iso": len(BI), "g_inc": sum(1 for d in B if d["by"]),
       "g_genre": sum(1 for d in B if d["ngen"]), "g_notable": sum(1 for d in B if NOTE(d)), "g_ens": sum(1 for d in B if d["bt"] == "ens"),
       "g_places": len({d["bp"] for d in BP}), "g_iso_origin": G0["how"].get("country of origin", 0), "g_in_area": sum(1 for d in BP if d["area"] is not None)}
for k in ("bp", "iso", "pt", "dob", "gender", "genre", "notable"):
    src[k + "_pct"] = pc(src["n_" + k], N)
for k in ("pt", "iso", "inc", "genre", "loc"):
    src["g_" + k + "_pct"] = pc(src["g_" + k], len(B))
src["in_area_pct"] = pc(src["n_in_area"], src["n_pt"])
src["notable_bp_pct"] = pc(sum(1 for d in M if NOTE(d) and d["iso"]), src["n_notable"])
src["sl1_bp_pct"] = pc(sum(1 for d in M if d["sl"] <= 1 and d["iso"]), sum(1 for d in M if d["sl"] <= 1))
src["n_sl1"] = sum(1 for d in M if d["sl"] <= 1); src["sl1_pct"] = pc(src["n_sl1"], N)
src["g_notable_pt_pct"] = pc(sum(1 for d in B if NOTE(d) and d["pt"]), src["g_notable"])
src["n_acts_pt"] = src["n_pt"] + src["g_pt"]
R["source"] = src

# coverage by sitelinks band and by decade
bands_sl = [(0, 1, "0 to 1"), (2, 4, "2 to 4"), (5, 9, "5 to 9"), (10, 19, "10 to 19"), (20, 49, "20 to 49"), (50, 10**6, "50 or more")]
R["coverage"] = {"by_sl": [{"lab": l, "n": sum(1 for d in M if a <= d["sl"] <= b), "iso_pct": pc(sum(1 for d in M if a <= d["sl"] <= b and d["iso"]), sum(1 for d in M if a <= d["sl"] <= b)),
                            "g_n": sum(1 for d in B if a <= d["sl"] <= b), "g_pt_pct": pc(sum(1 for d in B if a <= d["sl"] <= b and d["pt"]), sum(1 for d in B if a <= d["sl"] <= b))} for a, b, l in bands_sl]}
R["coverage"]["by_fam"] = [{"k": k, "name": FN[k], "n": sum(1 for d in M if k in d["fam"]), "iso_pct": pc(sum(1 for d in M if k in d["fam"] and d["iso"]), sum(1 for d in M if k in d["fam"]))} for k in FK]
R["coverage"]["by_dec"] = [{"dec": k, "n": sum(1 for d in M if d["dec"] == k), "iso_pct": pc(sum(1 for d in M if d["dec"] == k and d["iso"]), sum(1 for d in M if d["dec"] == k))} for k in DECS]
R["coverage"]["no_dob_iso_pct"] = pc(sum(1 for d in M if not d["by"] and d["iso"]), sum(1 for d in M if not d["by"]))

# ---------- families ----------
fam = []
for k in FK:
    L = [d for d in M if k in d["fam"]]
    ws, ng = wshare(L)
    fam.append({"k": k, "name": FN[k], "n": len(L), "pct": pc(len(L), N), "notable": sum(1 for d in L if NOTE(d)), "w_pct": ws, "n_g": ng,
                "n_pt": sum(1 for d in L if d["pt"]),
                "w_since1960": wshare([d for d in L if d["by"] and d["by"] >= 1960])[0], "w_before1900": wshare([d for d in L if d["by"] and d["by"] < 1900])[0],
                "top": [{"n": d["n"], "q": d["q"], "sl": d["sl"], "iso": d["iso"], "place": d["bpl"]} for d in sorted(L, key=lambda d: -d["sl"])[:8]]})
R["families"] = {"rows": fam, "by": {f["k"]: f for f in fam}}

# ---------- genres ----------
def genre_links(path):
    Gl = defaultdict(set)
    for p in open(path, encoding="utf-8").read().split("\n")[1:]:
        p = p.split("\t")
        if len(p) == 2 and p[0].startswith("Q") and p[1].startswith("Q"):
            Gl[p[0]].add(p[1])
    return Gl


MGl, BGl = genre_links(f"{RAW}/musician_genres.tsv"), genre_links(f"{RAW}/band_genres.tsv")
for d in M: d["gq"] = MGl.get(d["q"], set())
for d in B: d["gq"] = BGl.get(d["q"], set())
ACTS = M + B; AP = MP + BP
tagged = [d for d in AP if d["gen"] and d["gen"] != ["other"]]
gen = []
for k in GK:
    Lm = [d for d in M if k in d["gen"]]; Lb = [d for d in B if k in d["gen"]]
    gen.append({"k": k, "name": GN[k], "m": len(Lm), "b": len(Lb), "n": len(Lm) + len(Lb), "w_pct": wshare(Lm)[0],
                "m_pt": sum(1 for d in Lm if d["pt"]), "b_pt": sum(1 for d in Lb if d["pt"])})
R["genres"] = {"rows": gen, "by": {g["k"]: g for g in gen}, "n_tagged_pt": len(tagged), "n_genre_values": len({g for d in ACTS for g in d["gq"]})}

# ---------- city areas ----------
def area_rows(ds, min_n=1):
    c = Counter(d["area"] for d in ds if d["area"] is not None)
    return c


def area_row(i, n, ds=None):
    r = {"i": i, "name": cityname(i), "iso": BIG[i][4], "n": n, "pop": BIG[i][3], "per100k": round(n / BIG[i][3] * 1e5, 1)}
    return r


byarea_m = defaultdict(list); byarea_b = defaultdict(list)
for d in MP:
    if d["area"] is not None: byarea_m[d["area"]].append(d)
for d in BP:
    if d["area"] is not None: byarea_b[d["area"]].append(d)
am = Counter({i: len(v) for i, v in byarea_m.items()}); ab = Counter({i: len(v) for i, v in byarea_b.items()})


def full_area(i):
    Lm, Lb = byarea_m.get(i, []), byarea_b.get(i, [])
    r = area_row(i, len(Lm)); r["b"] = len(Lb); r["b_per100k"] = round(len(Lb) / BIG[i][3] * 1e5, 1)
    r["notable"] = sum(1 for d in Lm if NOTE(d)); r["w_pct"] = wshare(Lm)[0]
    r["fam"] = {k: sum(1 for d in Lm if k in d["fam"]) for k in FK}
    r["gen"] = {k: sum(1 for d in Lm + Lb if k in d["gen"]) for k in GK}
    r["top"] = [[dash(d["n"]), d["q"], d["sl"]] for d in sorted(Lm, key=lambda d: -d["sl"])[:6]]
    r["topb"] = [[dash(d["n"]), d["q"], d["sl"]] for d in sorted(Lb, key=lambda d: -d["sl"])[:6]]
    return r


AREA = {i: full_area(i) for i in set(am) | set(ab)}
BYNAME = {}
for i, r in AREA.items():
    if r["name"] not in BYNAME or r["n"] + r["b"] > BYNAME[r["name"]]["n"] + BYNAME[r["name"]]["b"]:
        BYNAME[r["name"]] = r
slim = lambda r: {k: r[k] for k in ("name", "iso", "n", "b", "pop", "per100k", "b_per100k", "notable", "w_pct")}
MINP = 150
per_m = sorted([AREA[i] for i in am if am[i] >= MINP], key=lambda r: -r["per100k"])
per_b = sorted([AREA[i] for i in ab if ab[i] >= 60], key=lambda r: -r["b_per100k"])
acn = Counter(d["area"] for d in MP if d["area"] is not None and NOTE(d))
R["areas"] = {"top": [slim(AREA[i]) for i, _ in am.most_common(30)], "per_capita": [slim(r) for r in per_m[:20]], "per_capita_min_n": MINP,
              "top_b": [slim(AREA[i]) for i, _ in ab.most_common(30)], "per_capita_b": [slim(r) for r in per_b[:20]], "per_capita_b_min_n": 60,
              "top_notable": [{"name": cityname(i), "iso": BIG[i][4], "n": n} for i, n in acn.most_common(15)],
              "n_big": len(BIG), "n_with": len(am), "top10_pct": pc(sum(n for _, n in am.most_common(10)), len(MP)),
              "top10_b_pct": pc(sum(n for _, n in ab.most_common(10)), len(BP))}
for nm in ("London", "Paris", "New York", "Los Angeles", "Vienna", "Leipzig", "Tokyo", "Seoul", "Stockholm", "Nashville", "Kingston", "Lagos",
           "Liverpool", "Manchester", "Sheffield", "Birmingham", "Glasgow", "Leeds", "Bristol", "Newcastle", "Edinburgh", "Cardiff", "Belfast",
           "Detroit", "Chicago", "Memphis", "New Orleans", "Bergen", "Oslo", "Helsinki", "Rio de Janeiro", "Buenos Aires", "Havana", "Mumbai",
           "Shanghai", "Beijing", "Moscow", "Berlin", "Rome", "Naples", "Milan", "Prague", "Budapest", "Istanbul", "Cairo", "Atlanta", "Houston", "Kolkata", "Lisbon", "Madrid",
           "Barcelona", "Copenhagen", "Amsterdam", "Gothenburg", "Osaka", "Dublin", "Toronto", "Montreal", "Sydney", "Melbourne", "Tampere", "Turku", "Seattle", "San Francisco"):
    if nm in BYNAME:
        R["areas"][norm(nm).replace(" ", "_")] = slim(BYNAME[nm])
UK = ["London", "Manchester", "Liverpool", "Birmingham", "Glasgow", "Sheffield", "Leeds", "Bristol", "Newcastle", "Edinburgh", "Cardiff", "Belfast"]
R["uk"] = {"rows": sorted([slim(BYNAME[n]) for n in UK if n in BYNAME], key=lambda r: -r["b_per100k"])}

# composers' Europe versus the pop and rock map
def tops(ds, n=12):
    c = Counter(d["area"] for d in ds if d["area"] is not None)
    tot = len([d for d in ds if d["pt"]])
    return [{"name": cityname(i), "iso": BIG[i][4], "n": m, "pct": pc(m, tot)} for i, m in c.most_common(n)], tot


comp_old = [d for d in MP if "composer" in d["fam"] and d["by"] and d["by"] < 1900]
poprock = [d for d in MP if ({"pop", "rock", "metal"} & set(d["gen"])) and d["by"] and d["by"] >= 1940]
hip = [d for d in AP if "hiphop" in d["gen"]]
ct, cn_ = tops(comp_old); pt_, pn_ = tops(poprock); ht, hn = tops(hip)
R["contrast"] = {"composers_pre1900": ct, "n_composers_pre1900": cn_, "poprock_post1940": pt_, "n_poprock_post1940": pn_, "hiphop": ht, "n_hiphop": hn,
                 "comp_europe_pct": pc(sum(1 for d in comp_old if d["cont"] == "Europe"), len(comp_old)),
                 "poprock_europe_pct": pc(sum(1 for d in poprock if d["cont"] == "Europe"), len(poprock)),
                 "poprock_na_pct": pc(sum(1 for d in poprock if d["cont"] == "North America"), len(poprock))}
cont_rows = []
for k in FK:
    L = [d for d in MI if k in d["fam"]]
    cont_rows.append({"k": k, "name": FN[k], "n": len(L), **{c: pc(sum(1 for d in L if d["cont"] == c), len(L)) for c in CONTS}})
R["contrast"]["fam_cont"] = cont_rows

# music city by genre: genre families and signature genres
def leaders(sel, min_n=25, k=8):
    c = Counter(d["area"] for d in AP if d["area"] is not None and sel(d))
    tot_sel = sum(1 for d in tagged if sel(d)); tot = len(tagged)
    tag_area = Counter(d["area"] for d in tagged if d["area"] is not None)
    out = []
    for i, n in c.items():
        if n >= min_n and tag_area[i] >= 40:
            lq = (n / tag_area[i]) / (tot_sel / tot) if tot_sel else 0
            out.append({"name": cityname(i), "iso": BIG[i][4], "n": n, "share": pc(n, tag_area[i]), "lq": round(lq, 1)})
    top = [{"name": cityname(i), "iso": BIG[i][4], "n": n, "lon": BIG[i][1], "lat": BIG[i][2]} for i, n in c.most_common(k)]
    return top, sorted(out, key=lambda r: -r["lq"])[:k], sum(c.values())


gcity = {}
for k in GK[:-1]:
    top, lq, n = leaders(lambda d, k=k: k in d["gen"])
    gcity[k] = {"name": GN[k], "top": top, "lq": lq, "n_in_areas": n}
R["genre_cities"] = gcity
SIG = [("Q83440", "country music"), ("Q9794", "reggae"), ("Q213665", "K-pop"), ("Q131578", "J-pop"), ("Q25099840", "Afrobeats"), ("Q963061", "highlife"),
       ("Q132438", "black metal"), ("Q483251", "death metal"), ("Q38848", "heavy metal"), ("Q338450", "tango"), ("Q11403", "samba"), ("Q486263", "bossa nova"),
       ("Q9764", "flamenco"), ("Q185676", "fado"), ("Q170611", "techno"), ("Q20502", "house music"), ("Q1166726", "grime"), ("Q2913982", "trap music"),
       ("Q189825", "salsa"), ("Q202930", "reggaeton"), ("Q1413570", "sardana"), ("Q8341", "jazz"), ("Q9759", "blues"), ("Q1344", "opera"),
       ("Q11365", "grunge"), ("Q189045", "Britpop"), ("Q485915", "trot"), ("Q853873", "cantopop"), ("Q956883", "Carnatic music"), ("Q1958273", "sertanejo"),
       ("Q959583", "schlager"), ("Q1062328", "chanson"), ("Q474027", "dancehall"), ("Q213714", "bluegrass")]
GLAB = defaultdict(set)                       # a few genres have two items with the same English label: use both
for p in open(f"{RAW}/genre_labels.tsv", encoding="utf-8").read().split("\n")[1:]:
    p = p.split("\t")
    if len(p) == 2 and p[0].startswith("Q"):
        GLAB[p[1].strip('"').lower()].add(p[0])
GFAM = {r["genre_wikidata"]: r["family"] for r in csv.DictReader(open(f"{DATA}/genre_families.csv", encoding="utf-8"))}
sig = []
for q, lab in SIG:
    qs = {q} | GLAB.get(next((k for k in GLAB if q in GLAB[k]), ""), set())
    top, lq, n = leaders(lambda d, qs=qs: bool(qs & d["gq"]), min_n=8, k=5)
    tot = sum(1 for d in AP if qs & d["gq"])
    if top:
        sig.append({"q": q, "genre": lab, "gfam": GFAM.get(q, "other"), "lon": top[0]["lon"], "lat": top[0]["lat"], "city": top[0]["name"], "iso": top[0]["iso"], "n": top[0]["n"], "of": tot, "pct": pc(top[0]["n"], tot),
                    "second": top[1]["name"] if len(top) > 1 else "", "second_n": top[1]["n"] if len(top) > 1 else 0, "lq_top": lq[0]["name"] if lq else ""})
R["signature"] = {"rows": sig, "by": {s["genre"]: s for s in sig}, "n_genres": len(sig)}

# ---------- countries ----------
cc = Counter(d["iso"] for d in MI); ccn = Counter(d["iso"] for d in MI if NOTE(d)); bc = Counter(d["iso"] for d in BI)
byc = defaultdict(list)
for d in MI: byc[d["iso"]].append(d)
bybc = defaultdict(list)
for d in BI: bybc[d["iso"]].append(d)
popc = lambda i: META[i]["pop"] or 0
def crow(i):
    ws, _ = wshare(byc[i])
    return {"iso": i, "name": CN(i), "n": cc[i], "pct": pc(cc[i], len(MI)), "notable": ccn[i], "w_pct": ws, "b": bc[i],
            "per_m": round(cc[i] / popc(i) * 1e6, 1) if popc(i) else None, "b_per_m": round(bc[i] / popc(i) * 1e6, 1) if popc(i) else None,
            "metal_b": sum(1 for d in bybc[i] if "metal" in d["gen"]), "metal_per_m": round(sum(1 for d in bybc[i] if "metal" in d["gen"]) / popc(i) * 1e6, 1) if popc(i) else None}
CROW = {i: crow(i) for i in set(cc) | set(bc)}
big = [r for r in CROW.values() if popc(r["iso"]) >= 1_000_000]
R["countries"] = {"top": [CROW[i] for i, _ in cc.most_common(30)], "top_b": [CROW[i] for i, _ in bc.most_common(20)],
                  "top_notable": [{"iso": i, "name": CN(i), "n": n, "pct": pc(n, sum(ccn.values()))} for i, n in ccn.most_common(20)],
                  "per_m": sorted([r for r in big if r["n"] >= 200], key=lambda r: -r["per_m"])[:20],
                  "b_per_m": sorted([r for r in big if r["b"] >= 100], key=lambda r: -r["b_per_m"])[:20],
                  "metal_per_m": sorted([r for r in big if r["metal_b"] >= 30], key=lambda r: -r["metal_per_m"])[:15],
                  "us_pct": pc(cc["USA"], len(MI)), "us_notable_pct": pc(ccn["USA"], sum(ccn.values())),
                  "us_b_pct": pc(bc["USA"], len(BI)), "n_notable_iso": sum(ccn.values()),
                  "by_cont": [{"cont": k, "n": sum(1 for d in MI if d["cont"] == k), "pct": pc(sum(1 for d in MI if d["cont"] == k), len(MI))} for k in CONTS],
                  "by_cont_b": [{"cont": k, "n": sum(1 for d in BI if d["cont"] == k), "pct": pc(sum(1 for d in BI if d["cont"] == k), len(BI))} for k in CONTS]}
for i in ("USA", "DEU", "GBR", "FRA", "ITA", "JPN", "IND", "NGA", "FIN", "SWE", "NOR", "KOR", "CHN", "BRA", "JAM", "ISL", "IRL", "AUT", "CZE", "RUS"):
    if i in CROW: R["countries"][i.lower()] = CROW[i]
R["countries"]["europe_pct"] = R["countries"]["by_cont"][0]["pct"]; R["countries"]["africa_pct"] = R["countries"]["by_cont"][4]["pct"]
R["countries"]["africa_b_pct"] = R["countries"]["by_cont_b"][4]["pct"]

# ---------- decades ----------
WATCH = ["USA", "DEU", "GBR", "FRA", "ITA", "RUS", "JPN", "KOR", "IND", "BRA", "ESP", "SWE", "NGA", "CHN", "AUT", "CZE", "MEX", "ARG", "CAN", "AUS"]
def decrows(ds_iso, ds_all):
    out = []
    for k in DECS:
        L = [d for d in ds_iso if d["dec"] == k]; A = [d for d in ds_all if d["dec"] == k]; n = len(L)
        row = {"dec": k, "n": n, "n_all": len(A), "iso_pct": pc(n, len(A))}
        for c in CONTS: row[c + "_pct"] = pc(sum(1 for d in L if d["cont"] == c), n)
        row["c_pct"] = {i: pc(sum(1 for d in L if d["iso"] == i), n) for i in WATCH}
        row["top"] = [{"iso": i, "name": CN(i), "n": m, "pct": pc(m, n)} for i, m in Counter(d["iso"] for d in L).most_common(5)]
        out.append(row)
    return out


DM = decrows(MI, M); DB = decrows(BI, B)
R["decades"] = {"rows": DM, "rows_b": DB, "by": {str(r["dec"]): r for r in DM}, "by_b": {str(r["dec"]): r for r in DB}}
early = [d for d in MI if d["by"] and d["by"] < 1900]; late = [d for d in MI if d["by"] and d["by"] >= 1970]
R["decades"].update({"n_early": len(early), "n_late": len(late),
                     **{f"{c.lower().replace(' ', '_')}_early_pct": pc(sum(1 for d in early if d["cont"] == c), len(early)) for c in CONTS},
                     **{f"{c.lower().replace(' ', '_')}_late_pct": pc(sum(1 for d in late if d["cont"] == c), len(late)) for c in CONTS}})
ce, cl = Counter(d["iso"] for d in early), Counter(d["iso"] for d in late)
R["decades"]["rise"] = sorted([{"iso": i, "name": CN(i), "early_pct": pc(ce[i], len(early)), "late_pct": pc(cl[i], len(late)), "late_n": cl[i]} for i in cl if cl[i] >= 1500],
                              key=lambda r: -(r["late_pct"] / max(r["early_pct"], .05)))[:12]
for i in ("USA", "DEU", "ITA", "FRA", "GBR", "KOR", "JPN", "IND", "NGA", "BRA", "AUT", "RUS", "SWE", "FIN"):
    R["decades"][i.lower()] = {"early_pct": pc(ce[i], len(early)), "late_pct": pc(cl[i], len(late))}
# group formation peaks
bdec = Counter(d["dec"] for d in B if d["dec"])
R["decades"]["b_peak"] = max((k for k in DECS if k < 2020), key=lambda k: bdec[k]); R["decades"]["b_peak_n"] = bdec[R["decades"]["b_peak"]]
R["decades"]["b_since1960_pct"] = pc(sum(1 for d in B if d["by"] and d["by"] >= 1960), sum(1 for d in B if d["by"]))

# ---------- women ----------
wdec = []
for k in DECS:
    L = [d for d in M if d["dec"] == k and d["g"] in "wmo"]; Ln = [d for d in L if NOTE(d)]
    row = {"dec": k, "n": len(L), "w": sum(1 for d in L if d["g"] == "w"), "pct": pc(sum(1 for d in L if d["g"] == "w"), len(L)),
           "n_notable": len(Ln), "pct_notable": pc(sum(1 for d in Ln if d["g"] == "w"), len(Ln))}
    for f in ("composer", "singer", "instr", "rap", "dj", "conductor"):
        Lf = [d for d in L if f in d["fam"]]
        row[f] = pc(sum(1 for d in Lf if d["g"] == "w"), len(Lf)) if len(Lf) >= 100 else None
    wdec.append(row)
WD_ = {r["dec"]: r for r in wdec}
wc = []
for i, L in byc.items():
    ws, ng = wshare(L)
    if ng >= 1000: wc.append({"iso": i, "name": CN(i), "n": ng, "pct": ws})
wc.sort(key=lambda r: -r["pct"])
wg = []
for k in GK[:-1]:
    ws, ng = wshare([d for d in M if k in d["gen"]]); wg.append({"k": k, "name": GN[k], "pct": ws, "n": ng})
wg.sort(key=lambda r: -r["pct"])
R["women"] = {"pct": wshare(M)[0], "notable_pct": wshare([d for d in M if NOTE(d)])[0], "by_dec": wdec, "by": {str(k): v for k, v in WD_.items()},
              "by_country": wc, "top": wc[:10], "bottom": wc[-8:], "by_genre": wg, "u_pct": pc(src["n_u"], N), "o_n": src["n_o"],
              "fam": sorted([{"k": f["k"], "name": f["name"], "pct": f["w_pct"], "since1960": f["w_since1960"]} for f in fam], key=lambda r: -r["pct"]),
              "min_n": 1000, "famous": [{"n": d["n"], "q": d["q"], "sl": d["sl"], "iso": d["iso"]} for d in sorted([d for d in M if d["g"] == "w"], key=lambda d: -d["sl"])[:15]]}

# ---------- famous ----------
R["famous"] = {"top": [{"n": d["n"] or d["q"], "q": d["q"], "sl": d["sl"], "iso": d["iso"], "place": d["bpl"], "by": d["by"]} for d in sorted(M, key=lambda d: -d["sl"])[:25]],
               "top_b": [{"n": d["n"], "q": d["q"], "sl": d["sl"], "iso": d["iso"], "place": d["bpl"], "by": d["by"]} for d in sorted(B, key=lambda d: -d["sl"])[:25]]}
R["notable"] = {"n": src["n_notable"], "europe_pct": pc(sum(1 for d in MI if NOTE(d) and d["cont"] == "Europe"), R["countries"]["n_notable_iso"]),
                "top_places": [{"name": cityname(i), "n": n} for i, n in acn.most_common(10)]}
bpc_ = Counter(d["bp"] for d in MP); bpl = {d["bp"]: d["bpl"] for d in MP}
R["places"] = {"top": [{"q": q, "name": bpl[q] or q, "n": n} for q, n in bpc_.most_common(20)]}

# ---------- CSV ----------
GL = {"w": "woman", "m": "man", "o": "another gender", "u": ""}
with gzip.open(f"{DATA}/musicians.csv.gz", "wt", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["wikidata", "name", "birth_year", "gender", "families", "genre_families", "birthplace_wikidata", "birthplace", "lon", "lat", "birth_country", "city_area", "sitelinks"])
    for d in sorted(M, key=lambda d: (d["iso"] or "~", d["bp"] or "~", -d["sl"])):     # by country and place: compresses far better
        w.writerow([d["q"], dash(d["n"]), d["by"] or "", GL[d["g"]], ";".join(d["fam"]), ";".join(d["gen"]), d["bp"] or "", dash(d["bpl"]),
                    d["pt"][0] if d["pt"] else "", d["pt"][1] if d["pt"] else "", d["iso"] or "", cityname(d["area"]) if d["area"] is not None else "", d["sl"]])
with gzip.open(f"{DATA}/groups.csv.gz", "wt", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["wikidata", "name", "formed", "dissolved", "group_type", "types", "genre_families", "formation_place_wikidata", "formation_place", "lon", "lat", "country", "city_area", "sitelinks"])
    for d in sorted(B, key=lambda d: (d["iso"] or "~", d["bp"] or "~", -d["sl"])):
        w.writerow([d["q"], dash(d["n"]), d["by"] or "", d["dis"] or "", d["bt"], ";".join(dash(d["types"])), ";".join(d["gen"]), d["bp"] or "", dash(d["bpl"]),
                    d["pt"][0] if d["pt"] else "", d["pt"][1] if d["pt"] else "", d["iso"] or "", cityname(d["area"]) if d["area"] is not None else "", d["sl"]])
with open(f"{DATA}/countries.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["iso3", "country", "continent", "musicians_born", "notable_born", "women_pct", "musicians_per_million", "groups_formed", "groups_per_million", "metal_groups", "metal_groups_per_million", "population_ne"])
    for i in sorted(CROW, key=lambda i: -CROW[i]["n"]):
        if i not in META: continue
        r = CROW[i]; ws, ngk = wshare(byc.get(i, []))
        w.writerow([i, CN(i), META[i]["cont"], r["n"], r["notable"], ws if ngk >= 30 else "", r["per_m"] or "", r["b"], r["b_per_m"] or "", r["metal_b"], r["metal_per_m"] or "", META[i]["pop"]])
with open(f"{DATA}/city_areas.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["city", "iso3", "lon", "lat", "population_ne", "musicians_born", "musicians_per_100k", "notable_born", "women_pct", "groups_formed", "groups_per_100k"] + [f"musicians_{k}" for k in FK] + [f"acts_{k}" for k in GK])
    for i in sorted(AREA, key=lambda i: -(AREA[i]["n"] + AREA[i]["b"])):
        r = AREA[i]
        w.writerow([r["name"], r["iso"], BIG[i][1], BIG[i][2], r["pop"], r["n"], r["per100k"], r["notable"], r["w_pct"] if r["n"] >= 30 else "", r["b"], r["b_per100k"]] + [r["fam"][k] for k in FK] + [r["gen"][k] for k in GK])
with open(f"{DATA}/decades.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["decade", "musicians_born", "with_birth_country", "birth_country_pct"] + [f"musicians_{c}_pct" for c in CONTS] + ["women_pct", "groups_formed", "groups_with_country"] + [f"groups_{c}_pct" for c in CONTS])
    for r, rb in zip(DM, DB):
        w.writerow([decname(r["dec"]), r["n_all"], r["n"], r["iso_pct"]] + [r[c + "_pct"] for c in CONTS] + [WD_[r["dec"]]["pct"], rb["n_all"], rb["n"]] + [rb[c + "_pct"] for c in CONTS])
with open(f"{DATA}/genre_cities.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["genre_wikidata", "genre", "top_city_area", "acts_there", "acts_with_genre", "pct", "second_city", "second_n"])
    for s in sig: w.writerow([s["q"], s["genre"], s["city"], s["n"], s["of"], s["pct"], s["second"], s["second_n"]])

# ---------- page data ----------
# places: musician birthplaces and group formation places, ordered geographically (5-degree cells) so that one map
# hexagon needs few detail chunks; acts: two 32-bit words each, sorted by place then sitelinks.
places, pidx = [], {}
def pkey(d): return d["bp"]
allp = {}
for d in AP:
    if d["bp"] not in allp:
        allp[d["bp"]] = [d["pt"][0], d["pt"][1], dash(d["bpl"]) or "", d["iso"] or "", d["bp"]]
cell = lambda p: (int((p[1] + 90) // 5), int((p[0] + 180) // 5) if int((p[1] + 90) // 5) % 2 == 0 else -int((p[0] + 180) // 5))
order = sorted(allp, key=lambda q: (cell(allp[q]), allp[q][0]))
for q in order:
    pidx[q] = len(places); places.append(allp[q])
assert len(places) < 2 ** 18
GI = {"m": 0, "w": 1, "o": 2, "u": 3}
acts = sorted(AP, key=lambda d: (pidx[d["bp"]], -d["sl"]))
words = []
famI = {k: i for i, k in enumerate(FK)}; famB = {"band": 0, "ens": 1}; genI = {k: i for i, k in enumerate(GK)}
for d in acts:
    fm = sum(1 << (famI[f] if d["kind"] == "m" else famB[f]) for f in d["fam"])
    gm = sum(1 << genI[g] for g in d["gen"])
    di = DECS.index(d["dec"]) + 1 if d["dec"] else 0                  # 0 = no date
    a = pidx[d["bp"]] | (di << 18) | ((GI[d["g"]] if d["kind"] == "m" else 3) << 23) | ((1 if d["kind"] == "b" else 0) << 25)
    b = fm | (gm << 8) | (min(d["sl"], 1023) << 22)
    words += [a, b]
MAPD = os.path.join(DATA, "map"); os.makedirs(MAPD, exist_ok=True)
for f in os.listdir(MAPD): os.remove(os.path.join(MAPD, f))
with open(f"{MAPD}/acts.bin", "wb") as fh:
    fh.write(struct.pack(f"<{len(words)}I", *words))
jsave({"cols": ["lon", "lat", "name", "iso", "wikidata"], "places": places}, f"{MAPD}/places.json")
# detail chunks: contiguous runs of acts, cut at place boundaries, about 3,000 acts each
chunks, start = [], 0
CH = 3000
while start < len(acts):
    end = min(len(acts), start + CH)
    while end < len(acts) and pidx[acts[end]["bp"]] == pidx[acts[end - 1]["bp"]]:
        end += 1
    chunks.append([start, end]); start = end
for k, (s0, e0) in enumerate(chunks):
    jsave([[dash(d["n"]), d["q"], d["by"] or 0] for d in acts[s0:e0]], f"{MAPD}/d{k:03d}.json")
# search index: acts with 3+ sitelinks (name, act index), plus all places in places.json
SMIN = 3
srch = [[dash(d["n"]), k] for k, d in enumerate(acts) if d["sl"] >= SMIN and d["n"]]
jsave({"min_sl": SMIN, "rows": srch}, f"{MAPD}/search.json")
R["source"]["search_min_sl"] = SMIN; R["source"]["n_search"] = len(srch)

def cfam(L): return {k: sum(1 for d in L if k in d["fam"]) for k in FK}
SITE = {"cname": {i: m["name"] for i, m in META.items()}, "cont": {i: m["cont"] for i, m in META.items()},
        "cpos": {i: [m["lx"], m["ly"], m["pop"]] for i, m in META.items()},
        "c": {i: {"n": cc.get(i, 0), "nn": ccn.get(i, 0), "w": wshare(byc.get(i, []))[0], "g": wshare(byc.get(i, []))[1], "b": bc.get(i, 0),
                  "pm": CROW[i]["per_m"], "bpm": CROW[i]["b_per_m"], "mpm": CROW[i]["metal_per_m"],
                  "dec": [sum(1 for d in byc.get(i, []) if d["dec"] == k) for k in DECS], "decb": [sum(1 for d in bybc.get(i, []) if d["dec"] == k) for k in DECS],
                  "fam": [sum(1 for d in byc.get(i, []) if k in d["fam"]) for k in FK],
                  "gen": [sum(1 for d in byc.get(i, []) + bybc.get(i, []) if k in d["gen"]) for k in GK],
                  "top": [[dash(d["n"]), d["q"], d["sl"]] for d in sorted(byc.get(i, []), key=lambda d: -d["sl"])[:8]],
                  "topb": [[dash(d["n"]), d["q"], d["sl"]] for d in sorted(bybc.get(i, []), key=lambda d: -d["sl"])[:5]]} for i in CROW if i in META},
        "areas": [[AREA[i]["name"], BIG[i][1], BIG[i][2], BIG[i][3], AREA[i]["n"], AREA[i]["b"], BIG[i][4]] for i in sorted(AREA, key=lambda i: -(AREA[i]["n"] + AREA[i]["b"]))[:200]],
        "decs": DECS, "fams": FAMS, "gens": GENS, "btypes": BTYPES, "chunks": chunks, "n_acts": len(acts), "n_m": len(MP), "n_b": len(BP)}
jsave(SITE, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)

# ---------- report ----------
print(json.dumps(R["source"], indent=0)[:2500])
print("fam", [(f["k"], f["n"], f["w_pct"], f["n_pt"]) for f in fam])
print("gen", [(g["k"], g["m"], g["b"]) for g in gen])
print("areas", [(a["name"], a["n"], a["b"], a["per100k"]) for a in R["areas"]["top"][:15]])
print("per cap", [(a["name"], a["n"], a["per100k"]) for a in R["areas"]["per_capita"][:12]])
print("bands", [(a["name"], a["b"], a["b_per100k"]) for a in R["areas"]["top_b"][:15]])
print("bands per cap", [(a["name"], a["b"], a["b_per100k"]) for a in R["areas"]["per_capita_b"][:12]])
print("composers<1900", [(a["name"], a["n"]) for a in ct[:10]], R["contrast"]["comp_europe_pct"])
print("poprock", [(a["name"], a["n"]) for a in pt_[:10]], R["contrast"]["poprock_europe_pct"], R["contrast"]["poprock_na_pct"])
print("hiphop", [(a["name"], a["n"]) for a in ht[:8]])
for k, v in gcity.items(): print("G", k, [(t["name"], t["n"]) for t in v["top"][:4]], "LQ", [(t["name"], t["n"], t["lq"]) for t in v["lq"][:5]])
for s in sig: print("S", s["genre"], s["city"], s["n"], s["of"], s["pct"], s["second"], s["second_n"], s["lq_top"])
print("countries", [(c["iso"], c["n"], c["pct"], c["per_m"], c["b"]) for c in R["countries"]["top"][:12]])
print("per m", [(c["iso"], c["n"], c["per_m"]) for c in R["countries"]["per_m"][:12]])
print("b per m", [(c["iso"], c["b"], c["b_per_m"]) for c in R["countries"]["b_per_m"][:12]])
print("metal per m", [(c["iso"], c["metal_b"], c["metal_per_m"]) for c in R["countries"]["metal_per_m"][:12]])
print("dec", [(r["dec"], r["n_all"], r["n"], r["Europe_pct"], r["North America_pct"], r["Asia_pct"]) for r in DM])
print("decb", [(r["dec"], r["n_all"], r["n"]) for r in DB], R["decades"]["b_peak"])
print("women", R["women"]["pct"], [(r["dec"], r["n"], r["pct"]) for r in wdec])
print("wfam", R["women"]["fam"]); print("wgen", wg); print("wc", [(r["iso"], r["pct"]) for r in wc[:8]], [(r["iso"], r["pct"]) for r in wc[-6:]])
print("uk", [(r["name"], r["n"], r["per100k"], r["b"], r["b_per100k"]) for r in R["uk"]["rows"]])
print("cov", R["coverage"]["by_sl"], R["coverage"]["by_fam"])
print("famous", [(f["n"], f["sl"]) for f in R["famous"]["top"][:12]], [(f["n"], f["sl"]) for f in R["famous"]["top_b"][:8]])
for f in os.listdir(DATA) + ["map/" + x for x in os.listdir(MAPD)[:3]]:
    p = os.path.join(DATA, f)
    if os.path.isfile(p): print(f, os.path.getsize(p) // 1024, "KB")
print("chunks", len(chunks), "search", len(srch), "acts", len(acts), "places", len(places))

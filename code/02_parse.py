"""Parse the QLever exports into one record per musician and one per musical group.

Rules
- One record per Wikidata item. Blank nodes (Wikidata 'unknown value') are dropped wherever they appear.
- Six lines of musicians.tsv lack their line break (the sitelinks value runs into the next Q-id); they are split here.
- Birthplace: the first named place of birth (P19) in the export; people with two or more different birthplaces are
  counted and keep the first. Point: the coordinates of that place (the first if it has several).
- Birth year: the earliest parsable year of P569 from 800 to 2020; formation year of a group: earliest P571, 800 to 2026.
- Gender: woman (female, trans woman), man (male, trans man), another gender (non-binary and other values), unknown.
- Occupation families and genre families: code/01_mappings.py (data/occupation_families.csv, data/genre_families.csv).
  A person or group belongs to every family of any of its occupations or genres.
- Group type: orchestras, choirs and ensembles (type label matches orchestra, choir, chorus, ensemble, military or
  marching or brass band, quartet, consort, philharmonic) or bands and groups (everything else).
"""
import csv, sys, importlib.util
from collections import Counter, defaultdict
from common import *

spec = importlib.util.spec_from_file_location("mp", os.path.join(ROOT, "code", "01_mappings.py")); MP = importlib.util.module_from_spec(spec); spec.loader.exec_module(MP)
OM = MP.occupations(); GM = MP.genres()
POINT = re.compile(r"POINT\(([-\d.eE+]+) ([-\d.eE+]+)\)")
YEAR = re.compile(r'^"?(-?\d{1,4})-\d\d-\d\dT')
WOMAN = {"Q6581072", "Q1052281", "Q43445"}
MAN = {"Q6581097", "Q2449503", "Q44148"}


def val(v):
    v = (v or "").strip()
    if "/.well-known/genid/" in v:
        return ""
    if v.startswith("<" + WD):
        return v[len(WD) + 1:-1]
    m = re.match(r'^"(.*)"(@[\w-]+|\^\^<[^>]+>)?$', v, re.S)
    if m:
        return m.group(1).replace('\\"', '"').replace("\\\\", "\\")
    return v


def year(v, lo, hi):
    m = YEAR.match(v or "")
    if not m:
        return None
    y = int(m.group(1))
    return y if lo <= y <= hi else None


def point(v):
    m = POINT.search(v or "")
    if not m:
        return None
    lon, lat = float(m.group(1)), float(m.group(2))
    return (round(lon, 4), round(lat, 4)) if -180 <= lon <= 180 and -90 <= lat <= 90 else None


def lines(path, nf):
    txt = open(path, encoding="utf-8").read()
    out, fixed = [], 0
    for ln in txt.split("\n"):
        p = ln.split("\t")
        if len(p) == 2 * nf - 1:              # sitelinks of one row glued to the Q-id of the next
            m = re.match(r"^(\d*)(Q\d+)$", p[nf - 1])
            if m:
                out.append(p[:nf - 1] + [m.group(1)]); out.append([m.group(2)] + p[nf:]); fixed += 1
                continue
        if len(p) >= 2:
            out.append(p + [""] * (nf - len(p)))
    return out[0], out[1:], fixed


# ---------- genres ----------
def genre_links(path):
    G = defaultdict(set)
    for p in open(path, encoding="utf-8").read().split("\n")[1:]:
        p = p.split("\t")
        if len(p) == 2 and p[0].startswith("Q") and p[1].startswith("Q"):
            G[p[0]].add(p[1])
    return G


MG, BG = genre_links(f"{RAW}/musician_genres.tsv"), genre_links(f"{RAW}/band_genres.tsv")
gfam = lambda gs: sorted({GM.get(g, ("", "other"))[1] for g in gs})

# ---------- musicians ----------
head, rows, nfix = lines(f"{RAW}/musicians.tsv", 10)
head = [h.lstrip("?") for h in head]
P = {}
n_blank = 0
for r in rows:
    if "/.well-known/genid/" in r[0] or not r[0].startswith("Q"):
        n_blank += 1
        continue
    r = dict(zip(head, [val(x) for x in r]))
    d = P.setdefault(r["p"], {"q": r["p"], "n": "", "occ": set(), "bps": [], "bpl": {}, "pt": {}, "bpc": set(), "dob": [], "sl": 0, "g": set()})
    if r["pL"] and not d["n"]:
        d["n"] = r["pL"]
    if r["occ"]:
        d["occ"].add(r["occ"])
    if r["bp"]:
        if r["bp"] not in d["bps"]:
            d["bps"].append(r["bp"])
        if r["bpL"]:
            d["bpl"].setdefault(r["bp"], r["bpL"])
        pt = point(r["coord"])
        if pt and r["bp"] not in d["pt"]:
            d["pt"][r["bp"]] = pt
        if r["bpc"]:
            d["bpc"].add((r["bp"], r["bpc"]))
    y = year(r["dob"], 800, 2020)
    if y:
        d["dob"].append(y)
    if r["sl"].isdigit():
        d["sl"] = max(d["sl"], int(r["sl"]))
    if r["g"]:
        d["g"].add(r["g"])
print("musician rows", len(rows), "repaired", nfix, "blank-node rows", n_blank, "people", len(P))

out, gc, occ_people = [], Counter(), Counter()
for q, d in P.items():
    bp = d["bps"][0] if d["bps"] else None
    g = "w" if d["g"] & WOMAN and not d["g"] & MAN else "m" if d["g"] & MAN and not d["g"] & WOMAN else ("o" if d["g"] else "u")
    gc[g] += 1
    fams = sorted({OM.get(o, ("", "other"))[1] for o in d["occ"]}) or ["other"]
    for o in d["occ"]:
        occ_people[o] += 1
    out.append({"q": q, "n": d["n"], "bp": bp, "bpl": d["bpl"].get(bp, "") if bp else "", "pt": d["pt"].get(bp) if bp else None,
                "bpc": sorted({c for b, c in d["bpc"] if b == bp}), "nbp": len(d["bps"]), "by": min(d["dob"]) if d["dob"] else None,
                "sl": d["sl"], "g": g, "fam": fams, "occ": sorted(d["occ"]), "gen": gfam(MG.get(q, ())), "ngen": len(MG.get(q, ()))})
print("gender", dict(gc))
jsave({"n_rows": len(rows), "n_blank_rows": n_blank, "n_line_repairs": nfix, "people": out,
       "occ_people": dict(occ_people)}, f"{WORK}/musicians_raw.json")

# ---------- groups ----------
TYL = {}
for p in open(f"{RAW}/band_types.tsv", encoding="utf-8").read().split("\n")[1:]:
    p = p.split("\t")
    if p[0].startswith("Q"):
        TYL[p[0]] = val(p[1]) if len(p) > 1 else ""
ENS = re.compile(r"orchestr|choir|chorus|choral|ensemble|military|marching|brass band|quartet|quintet|consort|philharmon|symphon|"
                 r"kapelle|cappella|schola|glee club|sinfonia|harmonie|wind band|concert band|big band|chapel|cantor", re.I)
head, rows, nfix_b = lines(f"{RAW}/bands.tsv", 11)
head = [h.lstrip("?") for h in head]
B = {}
for r in rows:
    if "/.well-known/genid/" in r[0] or not r[0].startswith("Q"):
        continue
    r = dict(zip(head, [val(x) for x in r]))
    d = B.setdefault(r["b"], {"q": r["b"], "n": "", "type": set(), "locs": [], "locl": {}, "pt": {}, "lc": set(), "inc": [], "dis": [], "co": set(), "sl": 0})
    if r["bL"] and not d["n"]:
        d["n"] = r["bL"]
    if r["type"]:
        d["type"].add(r["type"])
    if r["loc"]:
        if r["loc"] not in d["locs"]:
            d["locs"].append(r["loc"])
        if r["locL"]:
            d["locl"].setdefault(r["loc"], r["locL"])
        pt = point(r["coord"])
        if pt and r["loc"] not in d["pt"]:
            d["pt"][r["loc"]] = pt
        if r["lc"]:
            d["lc"].add((r["loc"], r["lc"]))
    y = year(r["inc"], 800, 2026)
    if y: d["inc"].append(y)
    y = year(r["dis"], 800, 2026)
    if y: d["dis"].append(y)
    if r["country"]:
        d["co"].add(r["country"])
    if r["sl"].isdigit():
        d["sl"] = max(d["sl"], int(r["sl"]))
bout, tc = [], Counter()
for q, d in B.items():
    loc = d["locs"][0] if d["locs"] else None
    labs = " ".join(TYL.get(t, "") for t in d["type"])
    bt = "ens" if ENS.search(labs) else "band"
    tc[bt] += 1
    bout.append({"q": q, "n": d["n"], "bp": loc, "bpl": d["locl"].get(loc, "") if loc else "", "pt": d["pt"].get(loc) if loc else None,
                 "bpc": sorted({c for b, c in d["lc"] if b == loc}), "co": sorted(d["co"]), "nbp": len(d["locs"]),
                 "by": min(d["inc"]) if d["inc"] else None, "dis": max(d["dis"]) if d["dis"] else None, "sl": d["sl"], "bt": bt,
                 "types": sorted(TYL.get(t, "") or t for t in d["type"]), "gen": gfam(BG.get(q, ())), "ngen": len(BG.get(q, ()))})
print("group rows", len(rows), "groups", len(B), "types", dict(tc))
jsave({"n_rows": len(rows), "n_line_repairs": nfix_b, "groups": bout}, f"{WORK}/groups_raw.json")

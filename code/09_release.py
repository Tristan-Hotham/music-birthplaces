"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
https://doi.org/10.5281/zenodo.23850287 and https://blog.tristanhotham.com/2026/10/31/music-birthplaces/ stay as placeholders for the publisher."""
import csv, gzip, json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Where_The_Worlds_Music_Comes_From"
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "05_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))

# facts stated in words in the blog (alt text included); the page build checks the rest
A = R["areas"]; C = R["countries"]; SG = R["signature"]["by"]
assert [(a["name"], a["n"]) for a in A["top"][:4]] == [("New York", 6124), ("London", 4627), ("Paris", 4466), ("Vienna", 4102)]
assert [a["name"] for a in A["top"][4:10]] == ["Tokyo", "Berlin", "Prague", "Los Angeles", "Budapest", "Buenos Aires"]
assert [(a["name"], a["b"]) for a in A["top_b"][:3]] == [("Los Angeles", 1454), ("New York", 1380), ("London", 1023)]
assert [a["name"] for a in A["top_b"][3:8]] == ["Tokyo", "San Francisco", "Seoul", "Jakarta", "Seattle"]
big = sorted([s for s in R["signature"]["rows"] if s["n"] >= 20], key=lambda s: -s["pct"])
assert [(s["genre"], s["city"]) for s in big[:17]] == [("cantopop", "Hong Kong"), ("samba", "Rio de Janeiro"), ("grime", "London"), ("tango", "Buenos Aires"), ("K-pop", "Seoul"), ("fado", "Lisbon"),
    ("sardana", "Barcelona"), ("bossa nova", "Rio de Janeiro"), ("trot", "Seoul"), ("chanson", "Paris"), ("J-pop", "Tokyo"), ("reggae", "Kingston"), ("flamenco", "Cádiz"),
    ("Carnatic music", "Chennai"), ("grunge", "Seattle"), ("Afrobeats", "Lagos"), ("dancehall", "Kingston")], [(s["genre"], s["city"]) for s in big]
assert [round(s["pct"]) for s in big[:6]] == [74, 57, 56, 52, 52, 49]
assert [c["iso"] for c in C["b_per_m"][:5]] == ["EST", "FIN", "SVN", "NOR", "SWE"]
assert [(c["iso"], c["metal_per_m"]) for c in C["metal_per_m"][:5]] == [("FIN", 84.8), ("SWE", 56.2), ("NOR", 55.5), ("SVN", 44.1), ("NLD", 28.0)]
assert [c["iso"] for c in C["metal_per_m"][5:8]] == ["DNK", "AUT", "DEU"]
assert round(R["women"]["by"]["1700"]["pct"]) == 8 and round(R["women"]["by"]["1990"]["pct"]) == 42
assert [round(f["pct"]) for f in R["women"]["fam"]] == [46, 27, 20, 17, 12, 11, 9, 7] and [f["k"] for f in R["women"]["fam"]] == ["singer", "songwriter", "other", "instr", "composer", "rap", "dj", "conductor"]
W = R["women"]["by_dec"]
assert all(w["pct_notable"] > w["pct"] for w in W if w["dec"] in (1970, 1980, 1990, 2000))   # dashed line 'rising above it'
cv = R["coverage"]["by_sl"]
assert round(cv[0]["iso_pct"]) == 46 and round(cv[-1]["iso_pct"]) == 100 and round(cv[0]["g_pt_pct"]) == 18 and round(cv[-1]["g_pt_pct"]) == 94
GC = R["genre_cities"]
assert GC["jazz"]["lq"][0]["name"] == "New Orleans" and GC["hiphop"]["lq"][0]["name"] == "Atlanta" and "Detroit" in [r["name"] for r in GC["rnb"]["lq"][:2]]
FC = {r["k"]: r for r in R["contrast"]["fam_cont"]}
assert FC["rap"]["North America"] > FC["rap"]["Europe"] - 2
lviv = [r for r in csv.DictReader(gzip.open(f"{DATA}/musicians.csv.gz", "rt", encoding="utf-8")) if r["birthplace"] == "Lviv" and r["birth_year"] and int(r["birth_year"]) < 1900 and "composer" in r["families"]]
assert lviv and all(r["birth_country"] == "UKR" for r in lviv), len(lviv)
pc_ = {r["name"]: r for r in R["uk"]["rows"]}
assert max(pc_.values(), key=lambda r: r["per100k"])["name"] == "Liverpool" and max(pc_.values(), key=lambda r: r["b_per100k"])["name"] == "Liverpool"
assert {"Liverpool"} <= {a["name"] for a in A["per_capita_b"][:9]}

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL\}\}|BLOG_URL\}\}|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
for ln in post.splitlines():
    if "{{IMG|" in ln:
        assert ln.startswith("{{IMG|") and ln.endswith("}}"), ln[:60]
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s = R["source"]
meta = {"title": "Where the world's music comes from",
        "slug": "music-birthplaces",
        "excerpt": f"I mapped the birthplaces of {s['n_pt']:,} musicians and the home towns of {s['g_pt']:,} bands in Wikidata: New York, London, Paris and Vienna lead, every genre has a home town from Kingston to Seoul, Finland has the most metal bands per head, and women went from {R['women']['by']['1700']['pct']:.0f}% of musicians born before 1800 to {R['women']['by']['1990']['pct']:.0f}% of those born in the 1990s.",
        "seo_description": "A map of where musicians were born and bands formed: top cities, the home town of each genre, Nordic metal, and women's share over time.",
        "tags": ["music", "musicians", "bands", "maps", "data visualisation", "Wikidata", "music history", "genres", "women in music"],
        "header_alt": f"Title card reading 'Where the world's music comes from' in black, red and gold on cream, beside a world map of hexagons shaded from pale yellow to deep plum by the number of musicians born there, darkest in central Europe, the eastern United States and Japan. Text: the birthplaces of {s['n_pt']:,} musicians and the home towns of {s['g_pt']:,} bands in Wikidata."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/music-birthplaces_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d_ in ("code", "code/queries", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d_))):
            p = os.path.join(ROOT, d_, fn)
            if fn.endswith(".pyc") or not os.path.isfile(p) or fn in ("site.json", "world.json", "cities.json"):   # page-only data, rebuilt by the scripts
                continue
            z.write(p, f"music-birthplaces/{d_}/{fn}")
    for fn in ("README.md", "LICENSE", "reddit/collage.py"):
        z.write(os.path.join(ROOT, fn), f"music-birthplaces/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": "Where the World's Music Comes From: The Birthplaces of Musicians and the Home Towns of Bands in Wikidata, by City, Genre, Decade and Gender",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["musicians", "bands", "music geography", "music scenes", "genres", "gender", "Wikidata", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
st = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in st, bad
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")

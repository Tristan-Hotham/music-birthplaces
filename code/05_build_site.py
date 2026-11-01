"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page summaries (site.json, world.json, cities) are embedded; data/map/* is loaded by the page.
Facts stated in words on the page are checked here (the blog, paper and collage builds import this module).
https://doi.org/10.5281/zenodo.23850287 and https://blog.tristanhotham.com/2026/10/31/music-birthplaces/ stay as placeholders for the publisher. The full-screen map snippet is pasted before </body>."""
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
A = R["areas"]; C = R["countries"]; SG = R["signature"]["by"]; GC = R["genre_cities"]; F = R["families"]["by"]

# ---------- facts stated in words ----------
assert [a["name"] for a in A["top"][:4]] == ["New York", "London", "Paris", "Vienna"], [a["name"] for a in A["top"][:4]]
assert R["places"]["top"][0]["name"] == "Vienna"
first_out = next(a for a in A["top"] if SITE["cont"][a["iso"]] not in ("Europe", "North America", "South America"))
assert first_out["name"] == "Tokyo"
big = [a for a in A["top"] if a["pop"] >= 1_000_000]
assert [a["name"] for a in sorted(big, key=lambda a: -a["per100k"])[:2]] == ["Prague", "Vienna"]   # 'Prague and Vienna have the most per head'
assert [a["name"] for a in A["per_capita"][:3]] == ["Tallinn", "Prague", "Brno"]
assert A["vienna"]["per100k"] > 5 * A["new_york"]["per100k"]
assert [a["name"] for a in A["top_b"][:5]] == ["Los Angeles", "New York", "London", "Tokyo", "San Francisco"] or [a["name"] for a in A["top_b"][:3]] == ["Los Angeles", "New York", "London"]
assert {"San Francisco", "Seattle"} <= {a["name"] for a in A["top_b"][:8]}
assert [a["name"] for a in A["per_capita_b"][:4]] == ["Ljubljana", "Bergen", "Malmö", "Oslo"]
assert {"Liverpool", "Nashville"} <= {a["name"] for a in A["per_capita_b"][:9]}
cp = [a["name"] for a in R["contrast"]["composers_pre1900"]]
assert cp[:7] == ["Vienna", "Paris", "London", "Prague", "Berlin", "Naples", "Barcelona"], cp
pp = [a["name"] for a in R["contrast"]["poprock_post1940"]]
assert pp[:3] == ["London", "New York", "Los Angeles"] and {"Tokyo", "Stockholm", "Jakarta"} <= set(pp[:10])
assert SG["country music"]["city"] == "Nashville" and GC["country"]["lq"][0]["name"] == "Nashville"
for g, c in (("reggae", "Kingston"), ("K-pop", "Seoul"), ("samba", "Rio de Janeiro"), ("tango", "Buenos Aires"), ("fado", "Lisbon"),
             ("black metal", "Oslo"), ("grunge", "Seattle"), ("grime", "London"), ("Afrobeats", "Lagos")):
    assert SG[g]["city"] == c, (g, SG[g]["city"])
assert SG["black metal"]["second"] == "Bergen"
assert GC["reggae"]["lq"][0]["name"] == "Kingston" and GC["jazz"]["lq"][0]["name"] == "New Orleans"
assert GC["rnb"]["lq"][1]["name"] == "Detroit" and GC["hiphop"]["lq"][0]["name"] == "Atlanta"
assert R["decades"]["b_peak"] == 2000
assert [c["iso"] for c in C["b_per_m"] if c["iso"] in ("FIN", "NOR", "SWE")] == ["FIN", "NOR", "SWE"]
assert [c["iso"] for c in C["metal_per_m"][:3]] == ["FIN", "SWE", "NOR"]
assert C["deu"]["metal_per_m"] < 15 and C["usa"]["metal_per_m"] < 10
d = R["decades"]
assert d["asia_late_pct"] > 9 * d["asia_early_pct"] and d["deu"]["late_pct"] < d["deu"]["early_pct"] / 2 and d["kor"]["early_pct"] < 0.05
assert d["jpn"]["late_pct"] > 10 * d["jpn"]["early_pct"]
W = R["women"]["by"]
assert all(18 <= W[str(k)]["pct"] <= 24 for k in range(1850, 1960, 10)), [W[str(k)]["pct"] for k in range(1850, 1960, 10)]  # 'about a fifth'
assert W["1700"]["pct"] < 10 and W["1970"]["pct"] < W["1980"]["pct"] < W["1990"]["pct"]
assert R["women"]["by_genre"][0]["k"] == "eapop" and R["women"]["by_genre"][0]["pct"] > 50 and all(r["pct"] < 50 for r in R["women"]["by_genre"][1:])
assert R["women"]["by_genre"][-1]["k"] == "metal"
assert [c["iso"] for c in C["top"][:6]] == ["USA", "DEU", "GBR", "ITA", "FRA", "JPN"] and C["top"][6]["iso"] == "CZE"
assert [c["iso"] for c in C["top"][7:9]] == ["ESP", "RUS"]
assert C["us_notable_pct"] > 2 * C["us_pct"] and C["top_notable"][1]["iso"] == "GBR"
uk = {r["name"]: r for r in R["uk"]["rows"]}
assert max(uk.values(), key=lambda r: r["per100k"])["name"] == "Liverpool" and max(uk.values(), key=lambda r: r["b_per100k"])["name"] == "Liverpool"
assert uk["Manchester"]["b"] > uk["Liverpool"]["b"]
big_uk = [r for r in uk.values() if r["pop"] >= 500_000]
assert min(big_uk, key=lambda r: r["per100k"])["name"] == "Sheffield" and min(big_uk, key=lambda r: r["b_per100k"])["name"] == "Sheffield"
top_names = [f["n"] for f in R["famous"]["top"][:12]]
for nm in ("Leonardo da Vinci", "Johann Wolfgang von Goethe", "Martin Luther", "Friedrich Nietzsche", "Michael Jackson", "Wolfgang Amadeus Mozart", "Ludwig van Beethoven"):
    assert nm in top_names, nm
assert R["source"]["n"] == 478552            # matches the coordinator's separate QLever count (478,552)


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI_URL\}\}|BLOG_URL\}\}|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    assert "{{" not in html.replace("https://doi.org/10.5281/zenodo.23850287", "").replace("https://blog.tristanhotham.com/2026/10/31/music-birthplaces/", "").replace("10.5281/zenodo.23850287", "")
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()

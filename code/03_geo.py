"""Geography (adapted from the director-birthplaces study).
- world.json: light world outlines for the page and figures (Natural Earth 1:50m, simplified).
- Birth country: the present-day country (Natural Earth 1:10m) that the birthplace point falls in; if the birthplace has
  no point, the birthplace's Wikidata country (P17) matched to Natural Earth by Wikidata ID.
- Former states recorded as the country of a place (FORMER below: Soviet Union, Czechoslovakia, Yugoslavia, the German
  states, British India...) count for their principal present-day successor when a place has no point.
- Groups: the country of the location of formation (point first, then its Wikidata country), else the group's country
  of origin (P495).
- City areas: every birthplace or formation point within 25 km of a Natural Earth populated place of 200,000 people or
  more is given to the nearest such place (a place within 25 km of a bigger one is merged into it), so that Brooklyn
  counts with New York and Hollywood with Los Angeles, while Liverpool and Manchester stay apart.
- cities.json: place names for map labels.
"""
import math
from collections import Counter
from shapely.geometry import shape, mapping, Point
from shapely.strtree import STRtree
from common import *

SOV = ["RUS", "UKR", "BLR", "KAZ", "UZB", "TKM", "KGZ", "TJK", "GEO", "ARM", "AZE", "MDA", "LTU", "LVA", "EST"]
YUG = ["SRB", "HRV", "SVN", "BIH", "MKD", "MNE", "KOS"]
REICH = ["DEU", "POL", "AUT", "CZE"]
# former state Q-id: (name, successor set, principal successor). Identified from Wikidata and checked against the
# birth countries of the directors who made films there.
FORMER = {
    "Q15180": ("Soviet Union", SOV, "RUS"), "Q34266": ("Russian Empire", SOV + ["POL", "FIN"], "RUS"), "Q2305208": ("Russian Empire", SOV + ["POL", "FIN"], "RUS"),
    "Q130229": ("Georgian SSR", ["GEO"], "GEO"), "Q131337": ("Azerbaijan SSR", ["AZE"], "AZE"), "Q2895": ("Byelorussian SSR", ["BLR"], "BLR"),
    "Q133356": ("Ukrainian SSR", ["UKR"], "UKR"),
    "Q33946": ("Czechoslovakia", ["CZE", "SVK"], "CZE"), "Q853348": ("Czechoslovakia", ["CZE", "SVK"], "CZE"), "Q152750": ("Protectorate of Bohemia and Moravia", ["CZE"], "CZE"),
    "Q36704": ("Yugoslavia", YUG, "SRB"), "Q83286": ("Yugoslavia", YUG, "SRB"), "Q838261": ("Federal Republic of Yugoslavia", ["SRB", "MNE", "KOS"], "SRB"),
    "Q37024": ("Serbia and Montenegro", ["SRB", "MNE", "KOS"], "SRB"), "Q211092": ("Socialist Republic of Slovenia", ["SVN"], "SVN"),
    "Q16957": ("East Germany", ["DEU"], "DEU"), "Q713750": ("West Germany", ["DEU"], "DEU"), "Q1206012": ("German Reich", REICH, "DEU"),
    "Q43287": ("German Empire", REICH, "DEU"), "Q41304": ("Weimar Republic", REICH, "DEU"), "Q7318": ("Nazi Germany", REICH, "DEU"),
    "Q28513": ("Austria-Hungary", ["AUT", "HUN", "CZE", "SVK", "HRV", "SVN", "POL", "UKR", "ROU", "BIH", "SRB", "ITA"], "AUT"),
    "Q129286": ("British India", ["IND", "PAK", "BGD", "MMR"], "IND"), "Q1054923": ("British Hong Kong", ["HKG"], "HKG"),
    "Q121932": ("People's Republic of Bulgaria", ["BGR"], "BGR"), "Q147909": ("Bulgaria", ["BGR"], "BGR"),
    "Q211274": ("Polish People's Republic", ["POL"], "POL"), "Q207272": ("Second Polish Republic", ["POL"], "POL"),
    "Q842794": ("Socialist Republic of Romania", ["ROU"], "ROU"), "Q172579": ("Kingdom of Italy", ["ITA"], "ITA"),
    "Q124943": ("Kingdom of Egypt", ["EGY"], "EGY"), "Q170468": ("United Arab Republic", ["EGY", "SYR"], "EGY"),
    "Q212056": ("Mongolian People's Republic", ["MNG"], "MNG"), "Q13426199": ("Republic of China (1912 to 1949)", ["CHN", "TWN"], "CHN"),
    "Q19188": ("Mainland China", ["CHN"], "CHN"), "Q188712": ("Empire of Japan", ["JPN"], "JPN"), "Q188161": ("Dutch East Indies", ["IDN"], "IDN"),
    "Q29999": ("Kingdom of the Netherlands", ["NLD"], "NLD"), "Q193714": ("Mandatory Palestine", ["ISR", "PSE"], "ISR"),
    "Q219060": ("State of Palestine", ["PSE"], "PSE"), "Q21": ("England", ["GBR"], "GBR"), "Q25": ("Wales", ["GBR"], "GBR"),
    "Q22": ("Scotland", ["GBR"], "GBR"), "Q26": ("Northern Ireland", ["GBR"], "GBR"), "Q22890": ("Ireland", ["IRL"], "IRL"), "Q176": ("Quebec", ["CAN"], "CAN"),
}
FIX = {"CNM": "CYP", "ESB": "CYP", "WSB": "CYP", "PSX": "PSE", "SAH": "ESH", "KAS": "IND"}


def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


iso_of = lambda p: FIX.get(p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"], p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"])
W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats, meta = [], {}
for f in W50["features"]:
    p = f["properties"]; iso = iso_of(p)
    g = shape(f["geometry"]).simplify(0.05, preserve_topology=True)
    if g.is_empty or iso == "ATA":
        continue
    gm = mapping(g)
    feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
W10 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
QID, geoms = {}, []
for f in W10["features"]:
    p = f["properties"]; iso = iso_of(p)
    if p.get("WIKIDATAID") and iso not in ("-99",):
        QID.setdefault(p["WIKIDATAID"], iso)
    g = shape(f["geometry"]).buffer(0)
    geoms.append((iso, g))
    if iso in meta and (meta[iso]["pop"] or 0) >= (p["POP_EST"] or 0):
        continue
    nm = (p["NAME_EN"] or p["NAME"]).replace("People's Republic of China", "China").replace("United States of America", "United States")
    nm = {"KOS": "Kosovo", "PSE": "Palestine", "CYP": "Cyprus", "TWN": "Taiwan", "HKG": "Hong Kong", "MAC": "Macau", "CZE": "Czech Republic",
          "MKD": "North Macedonia", "COD": "DR Congo", "COG": "Republic of the Congo", "GBR": "United Kingdom", "KOR": "South Korea", "PRK": "North Korea",
          "RUS": "Russia", "IRN": "Iran", "SYR": "Syria", "VNM": "Vietnam", "LAO": "Laos", "BHS": "Bahamas", "GMB": "Gambia", "NLD": "Netherlands",
          "PHL": "Philippines", "CIV": "Ivory Coast", "TZA": "Tanzania", "BOL": "Bolivia", "VEN": "Venezuela", "MDA": "Moldova"}.get(iso, nm)
    meta[iso] = {"name": nm, "cont": p["CONTINENT"], "sub": p["SUBREGION"], "pop": p["POP_EST"], "lx": round(p["LABEL_X"], 2), "ly": round(p["LABEL_Y"], 2)}
for k in meta:
    if meta[k]["cont"] == "Seven seas (open ocean)":
        meta[k]["cont"] = "Africa" if meta[k]["sub"] in ("Eastern Africa", "Southern Africa") else "Asia" if "Asia" in meta[k]["sub"] else "Oceania"
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
tree = STRtree([g for _, g in geoms])


def at(lon, lat):
    pt = Point(lon, lat)
    hit = [geoms[i][0] for i in tree.query(pt) if geoms[i][1].covers(pt)]
    if hit:
        return hit[0]
    near = [(geoms[i][1].distance(pt), geoms[i][0]) for i in tree.query(pt.buffer(0.15))]
    near = [x for x in near if x[0] < 0.15]
    return min(near)[1] if near else None


# city areas
def km(lon1, lat1, lon2, lat2):
    a = math.sin(math.radians(lat2 - lat1) / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(min(1, a)))


RAD, MINPOP = 25, 200_000
P = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")["features"]
BIG = [(p["properties"]["name"], p["properties"]["longitude"], p["properties"]["latitude"], int(p["properties"]["pop_max"]), iso_of({"ISO_A3_EH": p["properties"]["adm0_a3"], "ADM0_A3": p["properties"]["adm0_a3"]}))
       for p in P if (p["properties"]["pop_max"] or 0) >= MINPOP]
BIG.sort(key=lambda c: -c[3])
# a place within 25 km of a bigger one is part of that city's area (Howrah with Kolkata, Yokohama with Tokyo)
keep = []
for c in BIG:
    if not any(km(c[1], c[2], k[1], k[2]) <= RAD for k in keep):
        keep.append(c)
BIG = keep
btree = STRtree([Point(c[1], c[2]) for c in BIG])


def area_of(lon, lat):
    best = None
    for i in btree.query(Point(lon, lat).buffer(0.5)):
        c = BIG[i]; d = km(lon, lat, c[1], c[2])
        if d <= RAD and (best is None or d < best[0]):
            best = (d, int(i))
    return best[1] if best else None



def assign(d, extra=()):
    wd = [QID[q] for q in list(d["bpc"]) + list(extra) if q in QID] + [FORMER[q][2] for q in list(d["bpc"]) + list(extra) if q in FORMER]
    if d["bp"] in QID or (d["bp"] in FORMER and d["bp"] != "Q1054923"):   # the place is itself a country or a former state: country, no point
        d["pt"] = None
    iso = at(*d["pt"]) if d["pt"] else None
    how = "point" if iso else ("wikidata country" if wd else ("place, no country" if d["bp"] else "none"))
    agree = None
    if iso and wd:
        agree = iso in wd
    if not iso and wd:
        iso = wd[0]
    if iso and iso not in meta:
        how = "no outline"; iso = None
    d["iso"] = iso; d["cont"] = meta[iso]["cont"] if iso else None
    d["area"] = area_of(*d["pt"]) if d["pt"] else None
    return how, agree


M = jload(f"{WORK}/musicians_raw.json")
how, agree = Counter(), Counter()
for d in M["people"]:
    h, a = assign(d); how[h] += 1
    if a is not None: agree[a] += 1
M["how"] = dict(how); M["agree"] = {"same": agree[True], "different": agree[False]}
print("musicians: country from", dict(how), "agree", dict(agree))
jsave(M, f"{WORK}/musicians_geo.json")
G = jload(f"{WORK}/groups_raw.json")
how, agree = Counter(), Counter()
for d in G["groups"]:
    h, a = assign(d)
    if not d["iso"]:
        co = [QID[q] for q in d["co"] if q in QID] + [FORMER[q][2] for q in d["co"] if q in FORMER]
        if co and co[0] in meta:
            d["iso"] = co[0]; d["cont"] = meta[co[0]]["cont"]; h = "country of origin"
    how[h] += 1
    if a is not None: agree[a] += 1
G["how"] = dict(how); G["agree"] = {"same": agree[True], "different": agree[False]}
print("groups: country from", dict(how), "agree", dict(agree))
jsave(G, f"{WORK}/groups_geo.json")
jsave({"qid": QID, "former": FORMER, "meta": meta, "big": BIG}, f"{WORK}/geo.json")

cities = []
for f in P:
    p = f["properties"]; pop = p.get("pop_max") or 0
    if pop >= 150000 or p.get("adm0cap") == 1:
        cities.append({"name": re.sub(r"\s+", " ", p["name"]), "lat": round(p["latitude"], 3), "lon": round(p["longitude"], 3), "pop": int(pop)})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")
print("cities", len(cities), "big", len(BIG), "countries", len(meta), "world", os.path.getsize(f"{DATA}/world.json") // 1024, "KB")

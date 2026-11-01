"""Shared paths and helpers for the music-birthplaces project.

Raw inputs (read in place, never modified). QLever query results on Wikidata (CC0), retrieved 2026:
  /home/claude/newdata/raw4/musicians.tsv   every human (P31 Q5) with an occupation (P106) that is musician (Q639669)
      or any subclass of it: ?p person, ?pL English label, ?occ occupation, ?bp place of birth (P19), ?bpL its English
      label, ?coord its coordinates (P625), ?bpc its country (P17), ?dob date of birth (P569), ?g sex or gender (P21),
      ?sl number of sitelinks. One row per combination of values, so a person repeats. Exported in pages; six lines lack
      a line break and are repaired in 02_parse.py. Blank nodes (Wikidata 'unknown value') appear as .well-known/genid
      IRIs and are dropped.
  /home/claude/newdata/raw4/bands.tsv   every musical group (P31 Q215380 or a subclass): ?b, ?bL label, ?type, ?loc
      location of formation (P740), ?locL, ?coord, ?lc its country, ?inc inception (P571), ?dis dissolved (P576),
      ?country country of origin (P495), ?sl sitelinks.
  /home/claude/newdata/raw4/band_types.tsv, music_occupations.tsv, genre_labels.tsv: labels of types, occupations, genres.
  /home/claude/newdata/raw4/musician_genres.tsv, band_genres.tsv: genre (P136) links.
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson, ne_50m_admin_0_countries.geojson, ne_50m_land.geojson,
      ne_10m_populated_places_simple.geojson (Natural Earth, public domain)
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("MUS_RAW", "/home/claude/newdata/raw4")
GEO = os.environ.get("MUS_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("MUS_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("MUSTMP", "/dev/shm/music"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "music-birthplaces"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23850287"            # filled in by the publisher
DOI_URL = "https://doi.org/10.5281/zenodo.23850287"    # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/music-birthplaces/"      # filled in by the publisher
RETRIEVED = "2026"
NOTABLE = 20               # sitelinks threshold for the 'notable' view
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
WD = "http://www.wikidata.org/entity/"
# decade bins shared by musicians (decade of birth) and bands (decade of formation); 1700 means 'before 1800'
DECS = [1700] + list(range(1800, 2030, 10))
dec_of = lambda y: None if y is None else (1700 if y < 1800 else min(2020, y // 10 * 10))
decname = lambda d: "before 1800" if d == 1700 else f"{d}s"

FAMS = [("composer", "Composers and arrangers"), ("singer", "Singers"), ("instr", "Instrumentalists"), ("rap", "Rappers and MCs"),
        ("dj", "DJs and producers"), ("conductor", "Conductors and bandleaders"), ("songwriter", "Songwriters"), ("other", "Other musicians")]
GENS = [("classical", "Classical and opera"), ("rock", "Rock and punk"), ("metal", "Metal"), ("pop", "Pop"), ("eapop", "K-pop, J-pop and East Asian pop"),
        ("hiphop", "Hip hop"), ("rnb", "R&B, soul, blues and gospel"), ("jazz", "Jazz"), ("electronic", "Electronic and dance"),
        ("country", "Country"), ("latin", "Latin"), ("reggae", "Reggae, Caribbean and African popular"), ("folk", "Folk and traditional"),
        ("other", "Other or unlabelled genre")]
BTYPES = [("band", "Bands and groups"), ("ens", "Orchestras, choirs and ensembles")]
FAMI = {k: i for i, (k, _) in enumerate(FAMS)}
GENI = {k: i for i, (k, _) in enumerate(GENS)}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text taken from Wikidata (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    raise ValueError(f)

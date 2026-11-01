"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, a, c, d, w, SG, GC, F = R["source"], R["areas"], R["countries"], R["decades"], R["women"], R["signature"]["by"], R["genre_cities"], R["families"]["by"]
N = lambda v: f"{round(v):,}"
size = lambda f: f"{os.path.getsize(os.path.join(DATA, f)) / 1e6:.1f} MB"
mpm = c["metal_per_m"]
readme = f"""# Where the world's music comes from

A world map of where musicians were born and where bands formed: {N(s['n'])} people with a musical occupation in Wikidata, {N(s['n_iso'])} of them with a known birth country and {N(s['n_pt'])} with a birthplace on the map, and {N(s['g_n'])} musical groups, {N(s['g_pt'])} with a place of formation on the map. By city and country, kind of musician, family of genres, decade and gender.

Interactive page: {PAGE}
Paper: {DOI_URL}
Blog post: {BLOG}

## Headline results

- Cities: grouping places within 25 km of a city of 200,000 or more, New York ({N(a['new_york']['n'])}), London ({N(a['london']['n'])}), Paris ({N(a['paris']['n'])}) and Vienna ({N(a['vienna']['n'])}) are the leading birthplaces of musicians; Los Angeles ({N(a['los_angeles']['b'])}), New York ({N(a['new_york']['b'])}) and London ({N(a['london']['b'])}) are where most bands formed.
- Two maps: composers born before 1900 were {R['contrast']['comp_europe_pct']:.1f}% European, led by Vienna ({N(R['contrast']['composers_pre1900'][0]['n'])}) and Paris; pop, rock and metal musicians born since 1940 are {R['contrast']['poprock_europe_pct']:.1f}% European, led by London, New York and Los Angeles.
- Home towns: Seoul has {SG['K-pop']['pct']:.0f}% of K-pop acts on the map, Rio de Janeiro {SG['samba']['pct']:.0f}% of samba, Buenos Aires {SG['tango']['pct']:.0f}% of tango, Kingston {SG['reggae']['pct']:.0f}% of reggae, Lisbon {SG['fado']['pct']:.0f}% of fado; Nashville's acts are {GC['country']['lq'][0]['lq']:.1f} times as likely as the world's to be country. Oslo leads black metal, with Bergen second.
- Bands per head: Finland has {mpm[0]['metal_per_m']:.1f} metal bands per million people, Sweden {mpm[1]['metal_per_m']:.1f} and Norway {mpm[2]['metal_per_m']:.1f}; Germany {c['deu']['metal_per_m']:.1f}, the United States {c['usa']['metal_per_m']:.1f}.
- Women: {w['pct']:.1f}% of musicians with a recorded gender; {w['by']['1700']['pct']:.1f}% of those born before 1800, about a fifth through the 1800s and early 1900s, {w['by']['1990']['pct']:.1f}% of those born in the 1990s. Singers {F['singer']['w_pct']:.1f}%, composers {F['composer']['w_pct']:.1f}%, rappers {F['rap']['w_pct']:.1f}%, conductors {F['conductor']['w_pct']:.1f}%.
- Coverage: a birth country is recorded for {s['notable_bp_pct']:.1f}% of notable musicians ({NOTABLE}+ sitelinks) but {s['sl1_bp_pct']:.0f}% of those with at most one sitelink, and a formation place for {s['g_loc_pct']:.0f}% of groups. This maps the open record of music, not every musician.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`; summaries embedded, `data/map/` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/musicians.csv.gz` | All {N(s['n'])} musicians: Wikidata ID, name, birth year, gender, kinds of musician, genre families, birthplace (ID, name, point), birth country, city area, sitelinks; sorted by country and birthplace ({size('musicians.csv.gz')}, gzipped). |
| `data/groups.csv.gz` | All {N(s['g_n'])} musical groups: Wikidata ID, name, formed, dissolved, type, genre families, formation place (ID, name, point), country, city area, sitelinks ({size('groups.csv.gz')}, gzipped). |
| `data/countries.csv` | By present-day country: musicians born, notable, women's share, per million; groups, per million, metal groups per million. |
| `data/city_areas.csv` | {N(a['n_with'])} city areas with musicians: musicians born and groups formed within 25 km, per 100,000 people, notable, women's share, counts by kind of musician and genre family. |
| `data/genre_cities.csv` | The home town of {R['signature']['n_genres']} named genres. |
| `data/decades.csv` | By decade of birth (musicians) and formation (groups): counts, continent shares, women's share. |
| `data/occupation_families.csv`, `data/genre_families.csv` | How each Wikidata occupation and genre was grouped into families. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/map/` | Page data: `places.json` (places), `acts.bin` (two 32-bit words per act; layout in `code/04_results.py`), `d*.json` (names, loaded on demand), `search.json` (names with {s['search_min_sl']}+ sitelinks). |
| `data/site.json`, `data/world.json`, `data/cities.json` | Country and city summaries, outlines, city labels. |
| `code/` | Scripts, run in order (below), the page, paper and blog templates, and `queries/` (SPARQL drafted to fetch the rest of the musicians export in parts, and birthplace labels). |
| `release/` | Paper PDF and LaTeX source with figures, blog post and figures, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots from the last check of the page at desktop and phone widths. |

## Method in brief

- Musicians: every Wikidata human with an occupation (P106) that is musician (Q639669) or a subclass; place of birth (P19) and its coordinates; birth country is the present-day Natural Earth country the point falls in, else the place's Wikidata country (places that are countries or former states give a country but no point). Groups: every musical group (Q215380 or a subclass), placed at its location of formation (P740), else its country of origin (P495) for the country.
- Kinds and genres: {s['n_occ_values']} occupations grouped into eight kinds of musician and {N(R['genres']['n_genre_values'])} genres into thirteen families by ordered rules on English labels (`code/01_mappings.py`); a person or group counts in every family that applies.
- City areas: points within 25 km of a Natural Earth city of 200,000 or more, nearest city wins; a city within 25 km of a bigger one is merged into it. Per-head rates use present-day population.
- Home towns: for each named genre, the city area with most acts (musicians born and groups formed). Location quotient: a genre family's share of a city's genre-tagged acts divided by its share worldwide.
- Gender: women and trans women as women, men and trans men as men; shares among musicians with a recorded gender ({s['gender_pct']:.0f}%). Notable: {NOTABLE}+ sitelinks.
- Caveats: Wikidata is not a census of musicians; coverage differs greatly by country, fame and genre; occupations are generous; borders are today's.

## How to rerun

Needs Python 3 with numpy, shapely, pyproj, matplotlib, fontTools and Pillow, xelatex (TeX Gyre Pagella, Inter) and pdftotext; node with Playwright for the QA screenshots. Raw inputs are read in place (paths in `code/common.py`): QLever query results on Wikidata (retrieved {RETRIEVED}) and Natural Earth countries, land and populated places. Intermediate files go to `/dev/shm/music/work` (set `MUSTMP` to change).

```
python3 code/01_mappings.py     # occupation and genre families
python3 code/02_parse.py        # parse the query results
python3 code/03_geo.py          # outlines, countries, city areas, city labels
python3 code/04_results.py      # results.json, CSV files and page data
python3 code/05_build_site.py   # index.html (checks the facts stated in words)
python3 code/06_figures.py      # header, blog and paper figures
python3 code/07_paper.py        # paper PDF
python3 code/08_readme.py       # README, LICENSE, Reddit post
python3 code/09_release.py      # blog post, Zenodo files
python3 reddit/collage.py       # collage (checks every label against land polygons)
node code/12_qa.js              # screenshots (serve the folder on port 8818 first)
```

## Sources and licences

- Wikidata, via QLever (https://qlever.cs.uni-freiburg.de/wikidata). CC0.
- Natural Earth countries, land and populated places (public domain).
- Base map tiles on the page: © Esri.

Derived data, text and figures: CC BY 4.0. Code: MIT (see LICENSE).

## Citation

Hotham, T. (2026) Where the world's music comes from: the birthplaces of {N(s['n_iso'])} musicians and the home towns of bands in Wikidata. Zenodo. {DOI_URL}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
for bad in ("—", "–", "DSIT", "DCMS"):
    assert bad not in readme, bad
assert "--" not in readme.replace("|---|---|", "")
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. They are derived from Wikidata
(CC0) and Natural Earth (public domain).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] Where the world's music comes from: the birthplaces of {N(s['n_pt'])} musicians in Wikidata, and the home town of every genre. Seoul has {SG['K-pop']['pct']:.0f}% of K-pop acts, Rio {SG['samba']['pct']:.0f}% of samba, and Finland {mpm[0]['metal_per_m']:.0f} metal bands per million people

## Body

I mapped every musician in Wikidata with a known birthplace ({N(s['n_pt'])} of {N(s['n'])}) and every band with a known place of formation ({N(s['g_pt'])}). Grouping places within 25 km of cities, New York ({N(a['new_york']['n'])}), London, Paris and Vienna are the top birthplaces; Los Angeles is where most bands formed ({N(a['los_angeles']['b'])}). Composers born before 1900 were {R['contrast']['comp_europe_pct']:.0f}% European; pop, rock and metal musicians born since 1940 only {R['contrast']['poprock_europe_pct']:.0f}%. Each label shows a genre's home town and its share of that genre's acts: Kingston {SG['reggae']['pct']:.0f}% of reggae, Lisbon {SG['fado']['pct']:.0f}% of fado, Oslo leads black metal and Nashville's acts are {GC['country']['lq'][0]['lq']:.0f} times likelier than average to be country. Women are {w['by']['1990']['pct']:.0f}% of musicians born in the 1990s, {w['by']['1700']['pct']:.0f}% of those born before 1800. Caveat: Wikidata has a birth country for {s['notable_bp_pct']:.0f}% of famous musicians but only {s['sl1_bp_pct']:.0f}% of obscure ones, and some countries' catalogues are far fuller than others, so this maps the open record, not every musician. Interactive map with a decade slider, genre and kind filters, and search: {PAGE}

## Source comment

Source: Wikidata via QLever (CC0), 2026: every person with an occupation that is musician or a subclass (composer, singer, rapper, DJ, organist and {s['n_occ_values'] - 5} more), with place and date of birth, gender, genres and sitelinks; every musical group with its place and date of formation and genres. Natural Earth countries, land and populated places (public domain). Countries on present-day borders; city areas are places within 25 km of a city of 200,000 or more.

Tools: Python (shapely, pyproj, matplotlib); Leaflet for the interactive map. Labels are placed automatically and checked against Natural Earth land polygons.

Interactive version: {PAGE}
Paper: {DOI_URL}
Blog post: {BLOG}
"""
for bad in ("—", "–", "--"):
    assert bad not in post, bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README", len(readme.split()), "words; post", len(post.split()), "words")

# Where the world's music comes from

A world map of where musicians were born and where bands formed: 478,552 people with a musical occupation in Wikidata, 291,579 of them with a known birth country and 283,424 with a birthplace on the map, and 115,219 musical groups, 29,489 with a place of formation on the map. By city and country, kind of musician, family of genres, decade and gender.

Interactive page: https://maps.tristanhotham.com/music-birthplaces/
Paper: https://doi.org/10.5281/zenodo.23850287
Blog post: https://blog.tristanhotham.com/2026/10/31/music-birthplaces/

## Headline results

- Cities: grouping places within 25 km of a city of 200,000 or more, New York (6,124), London (4,627), Paris (4,466) and Vienna (4,102) are the leading birthplaces of musicians; Los Angeles (1,454), New York (1,380) and London (1,023) are where most bands formed.
- Two maps: composers born before 1900 were 87.7% European, led by Vienna (850) and Paris; pop, rock and metal musicians born since 1940 are 48.4% European, led by London, New York and Los Angeles.
- Home towns: Seoul has 52% of K-pop acts on the map, Rio de Janeiro 57% of samba, Buenos Aires 52% of tango, Kingston 23% of reggae, Lisbon 49% of fado; Nashville's acts are 13.0 times as likely as the world's to be country. Oslo leads black metal, with Bergen second.
- Bands per head: Finland has 84.8 metal bands per million people, Sweden 56.2 and Norway 55.5; Germany 12.3, the United States 6.7.
- Women: 25.4% of musicians with a recorded gender; 8.1% of those born before 1800, about a fifth through the 1800s and early 1900s, 41.9% of those born in the 1990s. Singers 45.7%, composers 12.0%, rappers 11.1%, conductors 7.2%.
- Coverage: a birth country is recorded for 99.8% of notable musicians (20+ sitelinks) but 46% of those with at most one sitelink, and a formation place for 27% of groups. This maps the open record of music, not every musician.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`; summaries embedded, `data/map/` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/musicians.csv.gz` | All 478,552 musicians: Wikidata ID, name, birth year, gender, kinds of musician, genre families, birthplace (ID, name, point), birth country, city area, sitelinks; sorted by country and birthplace (9.1 MB, gzipped). |
| `data/groups.csv.gz` | All 115,219 musical groups: Wikidata ID, name, formed, dissolved, type, genre families, formation place (ID, name, point), country, city area, sitelinks (1.9 MB, gzipped). |
| `data/countries.csv` | By present-day country: musicians born, notable, women's share, per million; groups, per million, metal groups per million. |
| `data/city_areas.csv` | 1,725 city areas with musicians: musicians born and groups formed within 25 km, per 100,000 people, notable, women's share, counts by kind of musician and genre family. |
| `data/genre_cities.csv` | The home town of 34 named genres. |
| `data/decades.csv` | By decade of birth (musicians) and formation (groups): counts, continent shares, women's share. |
| `data/occupation_families.csv`, `data/genre_families.csv` | How each Wikidata occupation and genre was grouped into families. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/map/` | Page data: `places.json` (places), `acts.bin` (two 32-bit words per act; layout in `code/04_results.py`), `d*.json` (names, loaded on demand), `search.json` (names with 3+ sitelinks). |
| `data/site.json`, `data/world.json`, `data/cities.json` | Country and city summaries, outlines, city labels. |
| `code/` | Scripts, run in order (below), the page, paper and blog templates, and `queries/` (SPARQL drafted to fetch the rest of the musicians export in parts, and birthplace labels). |
| `release/` | Paper PDF and LaTeX source with figures, blog post and figures, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots from the last check of the page at desktop and phone widths. |

## Method in brief

- Musicians: every Wikidata human with an occupation (P106) that is musician (Q639669) or a subclass; place of birth (P19) and its coordinates; birth country is the present-day Natural Earth country the point falls in, else the place's Wikidata country (places that are countries or former states give a country but no point). Groups: every musical group (Q215380 or a subclass), placed at its location of formation (P740), else its country of origin (P495) for the country.
- Kinds and genres: 534 occupations grouped into eight kinds of musician and 3,743 genres into thirteen families by ordered rules on English labels (`code/01_mappings.py`); a person or group counts in every family that applies.
- City areas: points within 25 km of a Natural Earth city of 200,000 or more, nearest city wins; a city within 25 km of a bigger one is merged into it. Per-head rates use present-day population.
- Home towns: for each named genre, the city area with most acts (musicians born and groups formed). Location quotient: a genre family's share of a city's genre-tagged acts divided by its share worldwide.
- Gender: women and trans women as women, men and trans men as men; shares among musicians with a recorded gender (96%). Notable: 20+ sitelinks.
- Caveats: Wikidata is not a census of musicians; coverage differs greatly by country, fame and genre; occupations are generous; borders are today's.

## How to rerun

Needs Python 3 with numpy, shapely, pyproj, matplotlib, fontTools and Pillow, xelatex (TeX Gyre Pagella, Inter) and pdftotext; node with Playwright for the QA screenshots. Raw inputs are read in place (paths in `code/common.py`): QLever query results on Wikidata (retrieved 2026) and Natural Earth countries, land and populated places. Intermediate files go to `/dev/shm/music/work` (set `MUSTMP` to change).

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

Hotham, T. (2026) Where the world's music comes from: the birthplaces of 291,579 musicians and the home towns of bands in Wikidata. Zenodo. https://doi.org/10.5281/zenodo.23850287

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.

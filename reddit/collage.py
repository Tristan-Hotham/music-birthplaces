"""r/dataisbeautiful collage for music-birthplaces: 2400 px wide, light background. Numbers from data/results.json.
Labels name each genre's home town. Every label is placed automatically and checked two ways:
1. geometrically, against Natural Earth land polygons (1:50m, every island included) projected to the map: the label box,
   with a margin, may not touch land;
2. on the rendered image: the box may not touch anything that is not plain paper or sea (hexagons, frames, other text),
   another label or a leader line, and its leader line may not cross another label or leader.
Europe, too crowded for the world map, gets its own inset."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from matplotlib import patheffects as pe
from matplotlib.patches import Rectangle
from shapely.geometry import shape, box as sbox, LineString, Point, Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely.affinity import affine_transform

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
A = points(); MUS = A[A[:, 5] == 0]
SG = R["signature"]["by"]; AR = R["areas"]
BGc = "#F7F3EC"
H = 19.6
fig = plt.figure(figsize=(12, H), dpi=200, facecolor=BGc)
fy = lambda px: 1 - px / (H * 200)          # figure y from pixels below the top
fig.text(.045, fy(70), "Where the world's music comes from", fontproperties=DISP, fontsize=44, color=FG, va="top")
fig.text(.045, fy(220), f"The birthplaces of {R['source']['n_pt']:,} musicians in Wikidata, shaded in hexagons, and the home town of each genre:\n"
         f"the city where most of its musicians were born or its bands were formed, with that city's share of all of them.",
         fontproperties=SERP, fontsize=15, color=FG, va="top", linespacing=1.45)

# ---- land polygons in projected coordinates (Equal Earth) ----
LANDP = []
for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]:
    g = shape(f["geometry"])
    for poly in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        xy = np.array(poly.exterior.coords)
        x, y = proj(np.clip(xy[:, 0], -179.99, 179.99), xy[:, 1])
        LANDP.append(Polygon(np.column_stack([x, y])).buffer(0))
LAND = unary_union(LANDP)
LANDPIX = {}


def land_pixels(ax):
    """Land as a prepared geometry in display pixels (y up) for this axes."""
    if ax not in LANDPIX:
        t = ax.transData.get_matrix()          # affine: data -> display
        g = affine_transform(LAND, [t[0, 0], t[0, 1], t[1, 0], t[1, 1], t[0, 2], t[1, 2]])
        LANDPIX[ax] = (g, prep(g))
    return LANDPIX[ax]


HALO = [pe.withStroke(linewidth=4, foreground="#FFFFFF")]
BGRGB = np.array([int(BGc[i:i + 2], 16) for i in (1, 3, 5)])
PAD = 12
LABELS = []; MISSING = []
LBLMASK = None; LDRMASK = None


def render():
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].astype(int)
    return buf, buf.shape[0]


def occupied(buf):
    return np.abs(buf - BGRGB).sum(2) > 24


def integral(m):
    return np.pad(m.astype(np.int32).cumsum(0).cumsum(1), ((1, 0), (1, 0)))


def rectsum(I, r0, c0, r1, c1):
    return I[r1, c1] - I[r0, c1] - I[r1, c0] + I[r0, c0]


def seg_hits(mask, p, q, skip=6):
    n = int(max(abs(q[0] - p[0]), abs(q[1] - p[1]))) + 1
    rr = np.linspace(p[0], q[0], n).round().astype(int); cc = np.linspace(p[1], q[1], n).round().astype(int)
    rr, cc = rr[skip:], cc[skip:]
    ok = (rr >= 0) & (rr < mask.shape[0]) & (cc >= 0) & (cc < mask.shape[1])
    return mask[rr[ok], cc[ok]].any()


def draw_seg(mask, p, q, w=3):
    n = int(max(abs(q[0] - p[0]), abs(q[1] - p[1]))) + 1
    for r, c in zip(np.linspace(p[0], q[0], n).round().astype(int), np.linspace(p[1], q[1], n).round().astype(int)):
        mask[max(r - w, 0):r + w + 1, max(c - w, 0):c + w + 1] = True


def place(ax, items, maxd, fs, first=()):
    """items: (key, text, lon, lat). Greedy: at each step place the label whose nearest free spot is closest."""
    global LBLMASK, LDRMASK
    buf, Hp = render(); occ = occupied(buf)
    _, landp = land_pixels(ax)
    bb = ax.get_window_extent(); r0a, r1a = int(Hp - bb.y1) + 2, int(Hp - bb.y0) - 2; c0a, c1a = int(bb.x0) + 2, int(bb.x1) - 2
    allowed = np.zeros_like(occ); allowed[r0a:r1a, c0a:c1a] = True
    if LBLMASK is None:
        LBLMASK = np.zeros_like(occ); LDRMASK = np.zeros_like(occ)
    block = occ | ~allowed
    rend = fig.canvas.get_renderer(); inv = ax.transData.inverted()
    todo = {}
    for key, txt, lon, lat in items:
        t = ax.text(0, 0, txt, fontsize=fs, family=MONO, linespacing=1.25); e = t.get_window_extent(rend); t.remove()
        x, y = ax.transData.transform(proj(lon, lat))
        todo[key] = (txt, int(e.width) + 2 * PAD, int(e.height) + 2 * PAD, Hp - y, x)
    order = list(first) + [k for k, *_ in items if k not in first]
    while todo:
        I = integral(block | LBLMASK | LDRMASK); best_all = None
        pending_first = [n for n in first if n in todo]
        for nm in (pending_first[:1] or [n for n in order if n in todo]):
            txt, w, h, cr, cc = todo[nm]
            R0 = np.arange(r0a, r1a - h, 4); C0 = np.arange(c0a, c1a - w, 4)
            RR, CC = np.meshgrid(R0, C0, indexing="ij")
            free = rectsum(I, RR, CC, RR + h, CC + w) == 0
            if not free.any():
                continue
            rr, cc_ = RR[free], CC[free]
            nr = np.clip(cr, rr + PAD, rr + h - PAD); nc = np.clip(cc, cc_ + PAD, cc_ + w - PAD)
            d = np.hypot(nr - cr, nc - cc)
            for k in np.argsort(d)[:3000]:
                if d[k] > maxd:
                    break
                if landp.intersects(sbox(cc_[k], Hp - rr[k] - h, cc_[k] + w, Hp - rr[k])):     # geometric land test
                    continue
                if seg_hits(LBLMASK | LDRMASK, (cr, cc), (nr[k], nc[k])):
                    continue
                if best_all is None or d[k] < best_all[0]:
                    best_all = (d[k], nm, rr[k], cc_[k], nr[k], nc[k])
                break
        if best_all is None:
            print("could not place", (pending_first[:1] or [n for n in order if n in todo])[0])
            MISSING.extend(todo); break
        d, nm, r, c, nr, nc = best_all
        txt, w, h, cr, cc = todo.pop(nm)
        LBLMASK[r:r + h, c:c + w] = True
        if d > PAD / 2:
            draw_seg(LDRMASK, (cr, cc), (nr, nc), 4)
            (x0, y0), (x1, y1) = inv.transform([[cc, Hp - cr], [nc, Hp - nr]])
            ax.plot([x0, x1], [y0, y1], color=FG, lw=.7, zorder=6, solid_capstyle="round")
        xc, yc = inv.transform([[c + w / 2, Hp - (r + h / 2)]])[0]
        ax.plot(*inv.transform([[cc, Hp - cr]])[0], "o", ms=3.4, mfc="#fff", mec=FG, mew=.9, zorder=7)
        t = ax.text(xc, yc, txt, fontsize=fs, family=MONO, color=FG, ha="center", va="center", zorder=8, path_effects=HALO, linespacing=1.25)
        LABELS.append((t, ax))


def sig(genre, short=None, city=None):
    s = SG[genre]
    return (genre, f"{city or s['city']}\n{short or genre} {s['pct']:.0f}%", s["lon"], s["lat"])


def area_item(key, name, lon, lat, txt):
    return (key, txt, lon, lat)


AREA_POS = {a[0]: (a[1], a[2]) for a in SITE["areas"]}

# ---- world map ----
ext = (-13.4e6, 15.6e6, -5.6e6, 8.6e6)
mh_px = 2400 * (ext[3] - ext[2]) / (ext[1] - ext[0])
top_px = 360
ax = fig.add_axes([0, fy(top_px + mh_px), 1, mh_px / (H * 200)]); world(ax, lw=.3, ext=ext, ec=BGc, land="#E4DED0")
hexmap(ax, MUS, gs=175, ext=ext, lw=.12)
(ex0, ey0), (ex1, ey1) = proj(-17, 32.5), proj(32, 64)
ax.add_patch(Rectangle((ex0, ey0), ex1 - ex0, ey1 - ey0, fill=False, ec=FG, lw=.9, ls=(0, (3, 2)), zorder=9))
lqc = R["genre_cities"]["country"]["lq"][0]; assert lqc["name"] == "Nashville"
WORLD_ITEMS = [("country music", f"Nashville\ncountry {lqc['lq']:.0f}x", SG["country music"]["lon"], SG["country music"]["lat"]), sig("reggae"), sig("grunge"), sig("samba"), sig("tango"), sig("Afrobeats"), sig("K-pop"),
               sig("J-pop"), sig("cantopop"), sig("reggaeton"), sig("Carnatic music", "Carnatic")]
nyp = AREA_POS["New York"]
place(ax, WORLD_ITEMS, 600, 10.5)
nx, ny = proj(-12, 66.5)
ax.text(nx, ny, "Europe: see inset", fontsize=10.5, family=MONO, color=FG, ha="right", va="center", zorder=9, path_effects=HALO)

# ---- legend and note ----
ly = top_px + mh_px + 40
legend_hex(fig, [.045, fy(ly + 60), .54, 26 / (H * 200)], title="Musicians born in each hexagon (all decades)", fs=9)
fig.text(.6, fy(ly + 40), "Labels: the city area (within 25 km) with most acts\nin each genre, and its share of all such acts on\nthe map (musicians born and bands formed). Nashville\n" f"{lqc['lq']:.0f}x: its acts are {lqc['lq']:.0f} times likelier to be country.\nVienna: the most composers born before 1900.",
         fontsize=10, color=MUT, va="center", linespacing=1.4)

# ---- Europe inset ----
iy = ly + 170
eext = (ex0, ex1, ey0, ey1); iw = .6; ih_px = 2400 * iw * (ey1 - ey0) / (ex1 - ex0)
ax2 = fig.add_axes([.03, fy(iy + ih_px), iw, ih_px / (H * 200)]); world(ax2, lw=.4, ext=eext, ec=BGc, land="#E4DED0")
hexmap(ax2, MUS, gs=520, ext=ext, lw=.1)
ax2.set_xlim(ex0, ex1); ax2.set_ylim(ey0, ey1); ax2.axis("on"); ax2.set_facecolor(BGc); ax2.set_xticks([]); ax2.set_yticks([])
for s_ in ax2.spines.values():
    s_.set_visible(True); s_.set_color(FG); s_.set_linewidth(.9); s_.set_linestyle((0, (3, 2)))
fig.text(.03, fy(iy - 10), "Europe", fontproperties=DISPB, fontsize=17, color=FG, va="bottom")
fig.text(.13, fy(iy - 12), "smaller hexagons, about 55 km across; same colour scale", family=MONO, fontsize=9.5, color=MUT, va="bottom")
vp = AREA_POS["Vienna"]
comp = R["contrast"]["composers_pre1900"][0]; assert comp["name"] == "Vienna"
EUR = [sig("black metal", "black metal", None), sig("fado"), sig("grime"), sig("flamenco"), sig("sardana"), sig("chanson"),
       ("vienna", f"Vienna\n{comp['n']:,} composers\nborn before 1900", vp[0], vp[1])]
place(ax2, EUR, 760, 10, first=("vienna", "grime"))

# ---- big numbers, right of the inset ----
mpm = R["countries"]["metal_per_m"]
nums = [(f"{R['source']['n']:,}", HOT, f"musicians in Wikidata;\n{R['source']['n_pt']:,} with a\nbirthplace on the map"),
        (f"{AR['top_b'][0]['b']:,}", COOL, f"bands formed in and\naround {AR['top_b'][0]['name']}, the most\nof any city"),
        (f"{mpm[0]['metal_per_m']:.0f}", "#3B1442", f"metal bands per million\npeople in {mpm[0]['name']}; {mpm[1]['name']}\n{mpm[1]['metal_per_m']:.0f}, {mpm[2]['name']} {mpm[2]['metal_per_m']:.0f}"),
        (f"{R['women']['by']['1990']['pct']:.0f}%", WCOL, f"of musicians born in the\n1990s are women; before\n1800: {R['women']['by']['1700']['pct']:.0f}%")]
assert AR["top_b"][0]["name"] == "Los Angeles" and [m["iso"] for m in mpm[:3]] == ["FIN", "SWE", "NOR"]
for i, (big, col, small_) in enumerate(nums):
    xx = .68; yy = fy(iy - 20 + i * (ih_px + 20) / 4)
    fig.text(xx, yy, big, fontproperties=DISP, fontsize=34, color=col, va="top")
    fig.text(xx, yy - 95 / (H * 200), small_, family=MONO, fontsize=10.5, color=FG, va="top", linespacing=1.4)


# ---- bottom panels ----
def clean(a):
    a.set_facecolor(BGc)
    for s_ in ("top", "right"): a.spines[s_].set_visible(False)


py = iy + ih_px + 120
ph = (H * 200 - py - 290) / (H * 200)
bt = fy(py) - .012 - ph
T = AR["top"][:10]
a1 = fig.add_axes([.13, bt, .19, ph]); clean(a1)
y = np.arange(len(T))[::-1]
a1.barh(y, [t["n"] for t in T], color=HOT, height=.72)
a1.set_yticks(y); a1.set_yticklabels([t["name"] for t in T], fontsize=10); a1.tick_params(length=0); a1.set_xticks([])
a1.spines["bottom"].set_visible(False); a1.spines["left"].set_visible(False)
for yy, t in zip(y, T): a1.text(t["n"] + 80, yy, f"{t['n']:,}", va="center", fontsize=9.5)
a1.set_xlim(0, T[0]["n"] * 1.3)
fig.text(.045, fy(py - 22), "Top birth cities", family=MONO, fontsize=12.5, color=FG, va="bottom")
fig.text(.045, fy(py), "musicians born within 25 km", family=MONO, fontsize=9.5, color=MUT, va="bottom")

Wd = [w for w in R["women"]["by_dec"] if w["n"] >= 1000]
a2 = fig.add_axes([.40, bt + .012, .24, ph - .012]); clean(a2)
a2.plot(range(len(Wd)), [w["pct"] for w in Wd], color=WCOL, lw=2.6, marker="o", ms=3.5)
a2.set_xticks(range(0, len(Wd), 4)); a2.set_xticklabels([decname(w["dec"]).replace("before ", "<") for w in Wd][::4], fontsize=9)
a2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%")); a2.set_ylim(0, 50); a2.tick_params(labelsize=9)
a2.grid(axis="y", color=RULE)
a2.annotate(f"{Wd[-1]['pct']:.0f}%", (len(Wd) - 1, Wd[-1]["pct"]), xytext=(-6, 5), textcoords="offset points", ha="right", fontsize=10, color=WCOL)
a2.annotate(f"{Wd[0]['pct']:.0f}%", (0, Wd[0]["pct"]), xytext=(9, -3), textcoords="offset points", ha="left", fontsize=10, color=WCOL)
fig.text(.36, fy(py - 22), "Women's share of musicians", family=MONO, fontsize=12.5, color=FG, va="bottom")
fig.text(.36, fy(py), "by decade of birth", family=MONO, fontsize=9.5, color=MUT, va="bottom")

M8 = mpm[:8]
a3 = fig.add_axes([.82, bt, .14, ph]); clean(a3)
y = np.arange(len(M8))[::-1]
a3.barh(y, [m["metal_per_m"] for m in M8], color="#3B1442", height=.72)
a3.set_yticks(y); a3.set_yticklabels([m["name"] for m in M8], fontsize=10); a3.tick_params(length=0); a3.set_xticks([])
a3.spines["bottom"].set_visible(False); a3.spines["left"].set_visible(False)
for yy, m in zip(y, M8): a3.text(m["metal_per_m"] + 1.5, yy, f"{m['metal_per_m']:.1f}", va="center", fontsize=9.5)
a3.set_xlim(0, M8[0]["metal_per_m"] * 1.35)
fig.text(.70, fy(py - 22), "Metal bands", family=MONO, fontsize=12.5, color=FG, va="bottom")
fig.text(.70, fy(py), "per million people", family=MONO, fontsize=9.5, color=MUT, va="bottom")

fig.text(.045, .012, "Source: Wikidata (CC0) via QLever, every person with a musician occupation and every musical group, 2026; Natural Earth (public\n"
         "domain). Wikidata records a birthplace for some musicians far more often than others (famous, European, classical): this maps the open\n"
         "record, not every musician. Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/music-birthplaces",
         family=MONO, fontsize=9, color=MUT, linespacing=1.55, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "where_music_comes_from.png")
assert not MISSING, MISSING

# ---- final checks: land polygons, rendered map, other labels, leaders ----
for t, _ in LABELS: t.set_visible(False)
lines_ = [l for a_ in (ax, ax2) for l in a_.lines]
for l in lines_: l.set_visible(False)
buf, Hp = render(); occ = occupied(buf)
for l in lines_: l.set_visible(True)
for t, _ in LABELS: t.set_visible(True)
fig.canvas.draw(); rend = fig.canvas.get_renderer()
boxes = [t.get_window_extent(rend) for t, _ in LABELS]
problems = []
for i, (t, a_) in enumerate(LABELS):
    e = boxes[i]; r0, r1, c0, c1 = int(Hp - e.y1) - 3, int(Hp - e.y0) + 3, int(e.x0) - 3, int(e.x1) + 3
    g, _ = land_pixels(a_)
    if g.intersects(sbox(e.x0 - 3, e.y0 - 3, e.x1 + 3, e.y1 + 3)):
        problems.append(f"{t.get_text()!r}: box touches land (Natural Earth polygons)")
    if occ[r0:r1, c0:c1].any():
        problems.append(f"{t.get_text()!r}: over hexagons or other drawing ({int(occ[r0:r1, c0:c1].sum())} px)")
    ab = a_.get_window_extent()
    if e.x0 < ab.x0 or e.x1 > ab.x1 or e.y0 < ab.y0 or e.y1 > ab.y1:
        problems.append(f"{t.get_text()!r}: outside its map")
    for j in range(i):
        if e.overlaps(boxes[j]):
            problems.append(f"{t.get_text()!r}: overlaps {LABELS[j][0].get_text()!r}")
for l in lines_:
    if len(l.get_xdata()) != 2: continue
    pts = l.axes.transData.transform(np.column_stack([l.get_xdata(), l.get_ydata()]))
    seg = LineString(pts)
    for t, a_ in LABELS:
        e = t.get_window_extent(rend)
        if seg.crosses(sbox(e.x0, e.y0, e.x1, e.y1)) and not sbox(e.x0 - 14, e.y0 - 14, e.x1 + 14, e.y1 + 14).contains(Point(pts[1])):
            problems.append(f"leader ending at {pts[1].round()} crosses {t.get_text()!r}")
print("label check:", "none" if not problems else problems, "|", len(LABELS), "labels")
assert not problems
fig.savefig(out, facecolor=BGc, dpi=200)
from PIL import Image
print("ok", out, Image.open(out).size)

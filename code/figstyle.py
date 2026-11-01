"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the concert-hall palette, and Natural Earth outlines in the Equal Earth projection."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#67626C", "axes.labelcolor": "#1D1B22",
                     "xtick.color": "#67626C", "ytick.color": "#67626C"})
BG, FG, MUT, LAND, RULE = "#F7F3EC", "#1D1B22", "#67626C", "#E6E0D2", "#E2DBCD"
HOT, COOL, GOLD, PLUM, WCOL = "#B5342B", "#2F5D8C", "#C8962B", "#6B2D6F", "#7A3E9D"
RAMP = ["#F3E3B3", "#E9C46A", "#E09F3E", "#D1603D", "#A8323E", "#6D2047", "#3B1442"]
BINS = [1, 3, 10, 30, 100, 300, 1000, 1e9]
CMAP = ListedColormap(RAMP); NORM = BoundaryNorm(BINS, len(RAMP))
CONT = [("Europe", "#2F5D8C"), ("North America", "#B5342B"), ("Asia", "#C8962B"), ("South America", "#3E8E5E"), ("Africa", "#7A4E9E"), ("Oceania", "#2A9BA8")]

EE = Transformer.from_crs(4326, 8857, always_xy=True)
W = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = []
for f in W["features"]:
    for ring in rings(f["geometry"]):
        x, y = EE.transform(np.clip(ring[:, 0], -179.9, 179.9), ring[:, 1])
        SHAPES.append((f["properties"]["iso"], np.column_stack([x, y])))
WORLD_EXT = (-12.3e6, 15.6e6, -5.9e6, 8.6e6)


def world(ax, colour_of=lambda iso: None, lw=.3, ext=WORLD_EXT, ec="#FFFFFF", land=LAND, z=1):
    for iso, p in SHAPES:
        c = colour_of(iso)
        ax.add_patch(MPoly(p, closed=True, fc=land if c is None else c, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def proj(lon, lat):
    return EE.transform(np.asarray(lon), np.asarray(lat))


def points():
    """Every act on the map: lon, lat, sitelinks, gender (0 man, 1 woman, 2 other, 3 unknown or band), decade index (0 none),
    kind (0 musician, 1 band), family bits, genre bits. Decoded from data/map/acts.bin (see 04_results.py)."""
    import struct
    PL = jload(f"{DATA}/map/places.json")["places"]
    raw = open(f"{DATA}/map/acts.bin", "rb").read()
    W = np.frombuffer(raw, dtype="<u4").reshape(-1, 2).astype(np.int64)
    a, b = W[:, 0], W[:, 1]
    pl = a & 0x3FFFF
    lon = np.array([p[0] for p in PL])[pl]; lat = np.array([p[1] for p in PL])[pl]
    return np.column_stack([lon, lat, b >> 22, (a >> 23) & 3, (a >> 18) & 31, (a >> 25) & 1, b & 255, (b >> 8) & 0x3FFF]).astype(float)


def hexmap(ax, A, gs=150, ext=WORLD_EXT, lw=.25, alpha=1, z=3):
    x, y = proj(A[:, 0], A[:, 1])
    hb = ax.hexbin(x, y, gridsize=gs, extent=ext, mincnt=1, cmap=CMAP, norm=NORM, linewidths=lw, edgecolors=BG, zorder=z, alpha=alpha)
    return hb


def legend_hex(fig, rect, title="musicians born in each hexagon", fs=10):
    ax = fig.add_axes(rect); ax.axis("off"); ax.set_xlim(0, len(RAMP)); ax.set_ylim(0, 1)
    labs = ["1 to 2", "3 to 9", "10 to 29", "30 to 99", "100 to 299", "300 to 999", "1,000+"]
    for i, (c, l) in enumerate(zip(RAMP, labs)):
        ax.add_patch(MPoly(np.array([[i + .05, .45], [i + .95, .45], [i + .95, .95], [i + .05, .95]]), fc=c, ec="none"))
        ax.text(i + .5, .2, l, ha="center", va="center", fontsize=fs, color=FG)
    ax.text(0, 1.25, title, fontsize=fs, color=MUT, va="bottom")
    return ax


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)

"""Header card (header.png), blog figures (release/blog/b_*.png) and paper figures (release/paper/f_*.png)."""
from matplotlib.patches import Patch
from figstyle import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
A = points()
MUS, BAND = A[A[:, 5] == 0], A[A[:, 5] == 1]
GK = [k for k, _ in GENS]; FK = [k for k, _ in FAMS]
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
DECI = lambda d: DECS.index(d) + 1


def shrink(p):
    """Flat-colour figures lose nothing visible when reduced to a 256-colour palette; it keeps the repo light."""
    from PIL import Image
    Image.open(p).convert("RGB").quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(p, optimize=True)


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor()); shrink(os.path.join(PA, "f_" + name + ".png"))
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor()); shrink(os.path.join(BL, "b_" + name + ".png"))
    plt.close(fig)


def clean(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.set_facecolor(BG)


def hbar(ax, names, vals, col, labs=None, fs=11):
    y = np.arange(len(names))[::-1]
    ax.barh(y, vals, color=col, height=.72)
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=fs); ax.tick_params(length=0)
    mx = max(vals)
    for yy, v, l in zip(y, vals, labs or [f"{v:,}" for v in vals]):
        ax.text(v + mx * .01, yy, l, va="center", fontsize=fs - 1, color=FG)
    ax.set_xlim(0, mx * 1.2); ax.set_xticks([]); clean(ax); ax.spines["bottom"].set_visible(False); ax.spines["left"].set_visible(False)


# 1. musicians' birthplaces
fig = plt.figure(figsize=(12, 6.7), facecolor=BG)
ax = fig.add_axes([0, .08, 1, .92]); world(ax, lw=.25)
hexmap(ax, MUS, gs=170)
legend_hex(fig, [.22, .015, .56, .05], fs=9.5)
both(fig, "map")

# 2. bands, women, notable: small multiples
fig = plt.figure(figsize=(12, 3.3), facecolor=BG)
sets = [(BAND, f"Bands formed ({len(BAND):,})"), (MUS[MUS[:, 3] == 1], f"Women ({int((MUS[:, 3] == 1).sum()):,})"),
        (MUS[MUS[:, 2] >= NOTABLE], f"Notable musicians ({int((MUS[:, 2] >= NOTABLE).sum()):,})")]
for k, (S_, t) in enumerate(sets):
    ax = fig.add_axes([.005 + k * .332, .14, .325, .74]); world(ax, lw=.15)
    hexmap(ax, S_, gs=95, lw=.12)
    ax.text(.02, 1.03, t, transform=ax.transAxes, fontproperties=DISPB, fontsize=14, color=FG, va="bottom")
legend_hex(fig, [.22, .0, .56, .08], title="musicians born, or bands formed, in each hexagon", fs=8.5)
both(fig, "small_maps")

# 3. cities: musicians and bands
fig = plt.figure(figsize=(12, 6.4), facecolor=BG)
a1 = fig.add_axes([.14, .06, .32, .84]); a2 = fig.add_axes([.63, .06, .32, .84])
T = R["areas"]["top"][:15]; Tb = R["areas"]["top_b"][:15]
hbar(a1, [t["name"] for t in T], [t["n"] for t in T], HOT)
hbar(a2, [t["name"] for t in Tb], [t["b"] for t in Tb], COOL)
a1.set_title("Musicians born in each city", loc="left", fontsize=13, color=FG, pad=10)
a2.set_title("Bands formed in each city", loc="left", fontsize=13, color=FG, pad=10)
both(fig, "cities")

# 4. composers before 1900 against pop, rock and metal since 1940
fig = plt.figure(figsize=(12, 4.6), facecolor=BG)
comp = MUS[(MUS[:, 6].astype(int) & (1 << FK.index("composer")) > 0) & (MUS[:, 4] >= 1) & (MUS[:, 4] <= DECI(1890))]
prm = sum(1 << GK.index(g) for g in ("pop", "rock", "metal"))
pop = MUS[(MUS[:, 7].astype(int) & prm > 0) & (MUS[:, 4] >= DECI(1940))]
for k, (S_, t) in enumerate([(comp, f"Composers born before 1900 ({len(comp):,})"), (pop, f"Pop, rock and metal musicians born since 1940 ({len(pop):,})")]):
    ax = fig.add_axes([.005 + k * .5, .12, .49, .78]); world(ax, lw=.18)
    hexmap(ax, S_, gs=110, lw=.12)
    ax.text(.02, 1.02, t, transform=ax.transAxes, fontproperties=DISPB, fontsize=15, color=FG, va="bottom")
legend_hex(fig, [.22, .0, .56, .07], fs=9)
both(fig, "contrast")

# 5. genre home towns
SG = sorted([s for s in R["signature"]["rows"] if s["n"] >= 20], key=lambda s: -s["pct"])[:17]
GCOL = {"latin": "#3E8E5E", "eapop": GOLD, "hiphop": PLUM, "folk": "#8A6A12", "reggae": "#2A9BA8", "country": HOT, "metal": "#3B1442", "rock": COOL,
        "pop": "#D1603D", "classical": "#67626C", "electronic": "#7A4E9E", "jazz": "#2F5D8C", "rnb": "#A8323E"}
fig = plt.figure(figsize=(12, 6.8), facecolor=BG)
ax = fig.add_axes([.33, .04, .62, .9])
hbar(ax, [f"{s['genre']}: {s['city']}" for s in SG], [s["pct"] for s in SG], [GCOL.get(s["gfam"], "#888") for s in SG],
     [f"{s['pct']:.0f}%  ({s['n']:,} of {s['of']:,})" for s in SG], fs=11)
ax.set_title("Share of each genre's acts (musicians born and bands formed) in its top city", loc="left", fontsize=12, pad=10)
both(fig, "genres")

# 6. shift by continent, by decade of birth
D = [r for r in R["decades"]["rows"] if r["dec"] <= 2000]
fig = plt.figure(figsize=(12, 5.4), facecolor=BG)
ax = fig.add_axes([.07, .17, .9, .77]); clean(ax)
xs = np.arange(len(D)); bot = np.zeros(len(D))
for k, c in CONT:
    v = np.array([d[k + "_pct"] or 0 for d in D]); ax.bar(xs, v, bottom=bot, color=c, width=.86, label=k); bot += v
ax.set_xticks(xs[::2]); ax.set_xticklabels([decname(d["dec"]).replace("before ", "<") for d in D][::2], fontsize=10)
ax.set_ylim(0, 100); ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.set_ylabel("share of musicians born that decade", fontsize=10)
fig.legend(handles=[Patch(fc=c, label=k) for k, c in CONT], loc="lower center", ncol=6, frameon=False, fontsize=11)
both(fig, "shift")

# 7. rising and falling countries (paper)
Dd = [d for d in R["decades"]["rows"] if 1800 <= d["dec"] <= 2000]
fig = plt.figure(figsize=(12, 5.4), facecolor=BG)
ax = fig.add_axes([.07, .1, .78, .84]); clean(ax)
RS = [("DEU", "Germany", COOL), ("USA", "United States", HOT), ("ITA", "Italy", "#3E8E5E"), ("GBR", "United Kingdom", PLUM), ("JPN", "Japan", GOLD), ("KOR", "South Korea", "#7A4E9E"), ("BRA", "Brazil", "#2A9BA8")]
ends = []
for i, n, c in RS:
    v = [d["c_pct"][i] for d in Dd]; ax.plot(range(len(Dd)), v, color=c, lw=2.4, marker="o", ms=3); ends.append([v[-1], n, c])
ends.sort(); prev = -9
for v, n, c in ends:
    y = max(v, prev + 1.6); prev = y; ax.text(len(Dd) - .6, y, n, color=c, fontsize=11, va="center")
ax.set_xticks(range(0, len(Dd), 2)); ax.set_xticklabels([f"{d['dec']}s" for d in Dd][::2], fontsize=10)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%")); ax.set_ylim(0, 30); ax.grid(axis="y", color=RULE)
ax.set_ylabel("share of musicians born that decade", fontsize=10)
both(fig, "rise", blog=False)

# 8. women: by decade of birth and by kind of musician
Wd = [w for w in R["women"]["by_dec"] if w["n"] >= 300]
fig = plt.figure(figsize=(12, 5), facecolor=BG)
ax = fig.add_axes([.06, .14, .5, .78]); clean(ax)
ax.plot(range(len(Wd)), [w["pct"] for w in Wd], color=WCOL, lw=3, marker="o", ms=4, label="All musicians")
ax.plot(range(len(Wd)), [w["pct_notable"] if w["n_notable"] >= 30 else np.nan for w in Wd], color=GOLD, lw=2, ls="--", marker="o", ms=3, label=f"Notable ({NOTABLE}+ sitelinks)")
ax.set_xticks(range(0, len(Wd), 3)); ax.set_xticklabels([decname(w["dec"]).replace("before ", "<") for w in Wd][::3], fontsize=10)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%")); ax.set_ylim(0, 72); ax.grid(axis="y", color=RULE)
ax.legend(frameon=False, loc="upper left", fontsize=10.5); ax.set_title("Women's share, by decade of birth", loc="left", fontsize=12.5)
a2 = fig.add_axes([.78, .06, .19, .82])
Fm = R["women"]["fam"]
hbar(a2, [f["name"].replace(" and arrangers", "").replace(" and bandleaders", "").replace(" and producers", "/producers").replace(" and MCs", "") for f in Fm], [f["pct"] for f in Fm], WCOL, [f"{f['pct']:.0f}%" for f in Fm], fs=10.5)
a2.set_title("By kind of musician", loc="left", fontsize=12.5)
both(fig, "women")

# 9. bands and metal bands per million
fig = plt.figure(figsize=(12, 5.6), facecolor=BG)
a1 = fig.add_axes([.14, .05, .32, .85]); a2 = fig.add_axes([.64, .05, .32, .85])
B1 = R["countries"]["b_per_m"][:12]; B2 = R["countries"]["metal_per_m"][:12]
hbar(a1, [c["name"] for c in B1], [c["b_per_m"] for c in B1], COOL, [f"{c['b_per_m']:.0f}" for c in B1])
hbar(a2, [c["name"] for c in B2], [c["metal_per_m"] for c in B2], "#3B1442", [f"{c['metal_per_m']:.1f}" for c in B2])
a1.set_title("Bands per million people", loc="left", fontsize=13, pad=10); a2.set_title("Metal bands per million people", loc="left", fontsize=13, pad=10)
both(fig, "metal")

# 10. countries (paper)
fig = plt.figure(figsize=(12, 6), facecolor=BG)
a1 = fig.add_axes([.17, .05, .3, .86]); a2 = fig.add_axes([.66, .05, .3, .86])
T = R["countries"]["top"][:15]; N_ = R["countries"]["top_notable"][:15]
hbar(a1, [t["name"] for t in T], [t["n"] for t in T], [dict(CONT).get(SITE["cont"][t["iso"]], "#888") for t in T])
hbar(a2, [t["name"] for t in N_], [t["n"] for t in N_], [dict(CONT).get(SITE["cont"][t["iso"]], "#888") for t in N_])
a1.set_title("All musicians", loc="left", fontsize=13, pad=10); a2.set_title(f"Notable ({NOTABLE}+ sitelinks)", loc="left", fontsize=13, pad=10)
both(fig, "countries", blog=False)

# 11. coverage by sitelinks
CV = R["coverage"]["by_sl"]
fig = plt.figure(figsize=(12, 4.6), facecolor=BG)
ax = fig.add_axes([.07, .15, .9, .75]); clean(ax)
x = np.arange(len(CV))
ax.bar(x - .2, [c["iso_pct"] for c in CV], .38, color=HOT, label="Musicians with a birth country")
ax.bar(x + .2, [c["g_pt_pct"] for c in CV], .38, color=COOL, label="Bands with a formation place on the map")
for i, c in enumerate(CV):
    ax.text(i - .2, c["iso_pct"] + 1.5, f"{c['iso_pct']:.0f}%", ha="center", fontsize=10); ax.text(i + .2, c["g_pt_pct"] + 1.5, f"{c['g_pt_pct']:.0f}%", ha="center", fontsize=10)
ax.set_xticks(x); ax.set_xticklabels([f"{c['lab']}\n({c['n']:,} musicians)" for c in CV], fontsize=9.5); ax.set_ylim(0, 112); ax.set_yticks([])
ax.spines["left"].set_visible(False); ax.set_xlabel("sitelinks (Wikipedia and other Wikimedia pages)", fontsize=10)
ax.legend(frameon=False, loc="upper left", fontsize=10.5, ncol=2)
both(fig, "coverage")

# header card 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
fig.text(.045, .9, "Where the", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(.045, .76, "world's music", fontproperties=DISP, fontsize=46, color=HOT, va="top")
fig.text(.045, .62, "comes from", fontproperties=DISP, fontsize=46, color=GOLD, va="top")
fig.text(.045, .43, f"The birthplaces of {R['source']['n_pt']:,}\nmusicians and the home towns\nof {R['source']['g_pt']:,} bands in Wikidata", fontproperties=SERP, fontsize=17, color=FG, va="top", linespacing=1.35)
fig.text(.045, .07, "maps.tristanhotham.com/music-birthplaces", fontsize=11, color=MUT)
ax = fig.add_axes([.38, .06, .64, .9]); world(ax, lw=.2, ext=(-11.5e6, 15.6e6, -5.5e6, 8.6e6))
hexmap(ax, A, gs=120, ext=(-11.5e6, 15.6e6, -5.5e6, 8.6e6), lw=.15)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures", sorted(os.listdir(BL)), sorted(os.listdir(PA)))

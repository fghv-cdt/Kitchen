#!/usr/bin/env python3
"""Build the HomeView recipe site from every week file in weeks/.

Usage: python3 build.py [weeks_dir] [out_dir]
Each weeks/<YYYY-MM-DD>.json becomes site/weeks/<YYYY-MM-DD>/.
A photo at photos/<slug>.jpg (or .png) replaces the generated illustration.
Set SITE_URL (e.g. https://name.github.io/kitchen) for absolute image links.
"""
import datetime, html, json, os, pathlib, random, shutil, sys
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).parent
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")

def esc(s): return html.escape(str(s))
def iso(m): return f"PT{int(m)}M"

# ---------------------------------------------------------------- illustrations
W, H, S = 1200, 900, 2  # final size, supersample factor

PIECES = [  # keyword, kind, colours
    ("salmon", "fillet", ["#f28c62", "#f6b08f"]),
    ("trout", "fillet", ["#f29a72", "#f6b896"]),
    ("cod", "fillet", ["#f7f3ea", "#ece4d4"]),
    ("tuna", "nugget", ["#c99a86", "#b88975"]),
    ("tofu", "cube", ["#f1d9a0", "#e8c886"]),
    ("olives", "olive", ["#3b2a3a", "#4e3a4c"]),
    ("cherry tomatoes", "slice", ["#f26b4f", "#c93a2a"]),
    ("frozen peas", "pea", ["#78b843", "#6aa83a"]),
    ("green beans", "strip", ["#4f8f2f", "#5fa03a"]),
    ("carrot", "ribbon", ["#f08a24", "#f5a24a"]),
    ("orange", "slice", ["#f7a83a", "#f2c26b"]),
    ("fennel", "slice", ["#eef3d6", "#cfdc9c"]),
    ("chicory", "leaf", ["#f2f0c4", "#e3e6a8"]),
    ("leek", "slice", ["#e6f0c6", "#9cc067"]),
    ("pomegranate", "pea", ["#b5172f", "#c9283f"]),
    ("almond", "seed", ["#e9d2a8", "#d9bd8e"]),
    ("prawn", "prawn", ["#f08a5d", "#f5a27a"]),
    ("feta", "cube", ["#fbfaf4", "#f0eee4"]),
    ("manchego", "cube", ["#f3dd9b", "#ead08a"]),
    ("parmesan", "shaving", ["#f6e7b0", "#efdc9c"]),
    ("halloumi", "halloumi", ["#e9c27a", "#dfb265"]),
    ("walnut", "nugget", ["#8a5a33", "#a06d42"]),
    ("chickpea", "ball", ["#e2b867", "#d6a855"]),
    ("mushroom", "mushroom", ["#9c7a5b", "#b38f6e"]),
    ("spinach", "leaf", ["#2f6b33", "#3f7f3a"]),
    ("gem lettuce", "leaf", ["#8cc26a", "#a6d27f"]),
    ("courgette", "ribbon", ["#7fae56", "#a7c97a"]),
    ("cucumber", "slice", ["#cfe6a8", "#5e8f3a"]),
    ("radish", "slice", ["#fbeff2", "#d9476a"]),
    ("peppers", "strip", ["#d93a2b", "#f2b632"]),
    ("potato", "potato", ["#e7c983", "#d9b56c"]),
    ("egg", "egg", ["#ffffff", "#f6b62c"]),
    ("pine nut", "seed", ["#f2e2b8", "#e8d39f"]),
    ("pumpkin seed", "seed", ["#6f8b3a", "#7f9b45"]),
    ("pistachio", "seed", ["#9bbf5a", "#b5cf6f"]),
    ("mint", "herb", ["#3c8f4a", "#4ea35a"]),
    ("dill", "herb", ["#4f8f3c", "#6aa84f"]),
    ("rice", "grain", ["#e8dcc0", "#d9c9a3", "#7a5c3e"]),
    ("buckwheat", "grain", ["#b98d5e", "#a67b4f"]),
    ("lemon", "lemon", ["#f7d64a", "#fbe98a"]),
    ("sumac", "dust", ["#a8323e"]),
    ("paprika", "dust", ["#c4462f"]),
]

def base_colour(r):
    t = " ".join(r["ingredients"]).lower()
    if "lentil" in t: return "#6b4a32"
    if "tomato" in t: return "#c8452f"
    if "spinach" in t and "chickpea" in t: return "#d9b46a"
    if "gem lettuce" in t: return "#9fcf78"
    if "buckwheat" in t: return "#c8a272"
    if "rice" in t: return "#ddd0b3"
    return "#e6dcc4"

def blob(d, rnd, cx, cy, rad, fill, n=14, wob=0.12):
    import math
    pts = []
    ph = [rnd.uniform(0, 6.3) for _ in range(3)]
    smooth = n >= 14
    steps = 72 if smooth else n
    for i in range(steps):
        a = 2 * math.pi * i / steps
        if smooth:
            k = (math.sin(3 * a + ph[0]) * .5 + math.sin(5 * a + ph[1]) * .3 + math.sin(2 * a + ph[2]) * .2)
            rr = rad * (1 + wob * .6 * k)
        else:
            rr = rad * (1 + rnd.uniform(-wob, wob))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)

def piece(d, rnd, kind, cols, x, y, s):
    import math
    c = rnd.choice(cols[:2]) if len(cols) > 1 else cols[0]
    a = rnd.uniform(0, math.pi)
    def rot(px, py):
        return (x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a))
    if kind == "prawn":
        for k in range(5):
            r0 = s * (1.1 - k * 0.15)
            d.arc([x - r0, y - r0, x + r0, y + r0], 200 + k * 8 + math.degrees(a), 360 + math.degrees(a), fill=cols[k % 2], width=int(s * 0.45))
    elif kind in ("cube", "halloumi"):
        w = s * (1.6 if kind == "halloumi" else 0.9)
        h = s * (0.9 if kind == "halloumi" else 0.9)
        d.polygon([rot(-w, -h), rot(w, -h), rot(w, h), rot(-w, h)], fill=c, outline="#00000022")
        if kind == "halloumi":
            for k in (-0.5, 0.2, 0.9):
                d.line([rot(-w * 0.8 + k * w * 0.6, -h * 0.8), rot(-w * 0.3 + k * w * 0.6, h * 0.8)], fill="#8a5a2b", width=int(s * 0.18))
    elif kind == "shaving":
        d.polygon([rot(-s * 1.2, 0), rot(0, -s * 0.4), rot(s * 1.2, 0.1 * s), rot(0, s * 0.35)], fill=c)
    elif kind == "nugget":
        blob(d, rnd, x, y, s * 0.7, c, n=9, wob=0.35)
    elif kind == "ball":
        d.ellipse([x - s * .55, y - s * .55, x + s * .55, y + s * .55], fill=c)
        d.ellipse([x - s * .25, y - s * .35, x - s * .05, y - s * .15], fill="#f3d79a")
    elif kind == "mushroom":
        d.chord([x - s, y - s * .8, x + s, y + s * .8], 180, 360, fill="#d8c3a5")
        d.rectangle([x - s * .3, y, x + s * .3, y + s * .7], fill="#e6d6bd")
        d.arc([x - s, y - s * .8, x + s, y + s * .8], 180, 360, fill=cols[0], width=int(s * .3))
    elif kind == "leaf":
        L = s * rnd.uniform(1.6, 2.4)
        d.polygon([rot(-L, 0), rot(-L * .3, -L * .45), rot(L * .5, -L * .3), rot(L, 0), rot(L * .5, L * .3), rot(-L * .3, L * .45)], fill=c)
        d.line([rot(-L, 0), rot(L, 0)], fill="#ffffff55", width=max(2, int(s * .12)))
    elif kind == "ribbon":
        L = s * 2.6
        d.line([rot(-L, -s * .3), rot(0, s * .3), rot(L, -s * .2)], fill=c, width=int(s * .6), joint="curve")
    elif kind == "slice":
        d.ellipse([x - s * .8, y - s * .8, x + s * .8, y + s * .8], fill=cols[1])
        d.ellipse([x - s * .65, y - s * .65, x + s * .65, y + s * .65], fill=cols[0])
    elif kind == "strip":
        d.line([rot(-s * 1.4, 0), rot(s * 1.4, 0)], fill=c, width=int(s * .5))
    elif kind == "potato":
        blob(d, rnd, x, y, s * 1.0, "#c9a35c", n=12, wob=.12)
        blob(d, rnd, x, y, s * .85, c, n=12, wob=.1)
    elif kind == "egg":
        d.ellipse([x - s * 1.2, y - s * .9, x + s * 1.2, y + s * .9], fill=cols[0], outline="#e8e2d6")
        d.ellipse([x - s * .5, y - s * .45, x + s * .5, y + s * .45], fill=cols[1])
    elif kind == "seed":
        d.polygon([rot(-s * .5, 0), rot(0, -s * .22), rot(s * .5, 0), rot(0, s * .22)], fill=c)
    elif kind == "herb":
        for k in range(4):
            d.line([rot(0, 0), rot(s * .9, (k - 1.5) * s * .5)], fill=c, width=max(2, int(s * .18)))
    elif kind == "grain":
        d.ellipse([x - s * .32, y - s * .14, x + s * .32, y + s * .14], fill=c)
    elif kind == "lemon":
        d.pieslice([x - s * 1.4, y - s * 1.4, x + s * 1.4, y + s * 1.4], 0, 120, fill=cols[0])
        d.pieslice([x - s * 1.15, y - s * 1.15, x + s * 1.15, y + s * 1.15], 5, 115, fill=cols[1])
    elif kind == "fillet":
        L, T = s * 3.2, s * 1.6
        d.rounded_rectangle([x - L, y - T, x + L, y + T], radius=int(T), fill=cols[0])
        for k in range(-2, 3):
            d.line([(x + k * L * .32 - s * .5, y - T * .8), (x + k * L * .32 + s * .5, y + T * .8)], fill=cols[1], width=max(2, int(s * .25)))
    elif kind == "olive":
        d.ellipse([x - s * .55, y - s * .4, x + s * .55, y + s * .4], fill=c)
    elif kind == "pea":
        d.ellipse([x - s * .3, y - s * .3, x + s * .3, y + s * .3], fill=c)
    elif kind == "dust":
        d.ellipse([x - s * .12, y - s * .12, x + s * .12, y + s * .12], fill=c)

def illustrate(r, path):
    import math
    rnd = random.Random(r["slug"])
    w, h = W * S, H * S
    salad = r["type"].lower().startswith("lunch")
    bg = "#e9e1d3" if not salad else "#dfe7dc"
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(0, h, 18 * S):  # linen texture
        d.line([(0, i), (w, i)], fill="#ffffff22", width=S)
    cx, cy, R = w / 2, h / 2, h * 0.42
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([cx - R + 20 * S, cy - R + 30 * S, cx + R + 20 * S, cy + R + 30 * S], fill=(60, 40, 20, 90))
    img.paste(shadow.filter(ImageFilter.GaussianBlur(25 * S)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(25 * S)))
    rim = "#2f5d7c" if salad else "#ffffff"
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=rim)
    inner = R * (0.88 if salad else 0.8)
    d.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], fill="#f7f4ee" if not salad else "#f3f1ea")
    blob(d, rnd, cx, cy, inner * 0.82, base_colour(r), n=18, wob=0.08)
    text = " ".join(r["ingredients"]).lower()
    found = [(k, kind, cols) for k, kind, cols in PIECES if k in text]
    if "black pepper" in text and "peppers" not in text:
        found = [f for f in found if f[0] != "peppers"]
    if "yoghurt" in text and "chickpea" in text:  # fatteh-style swirl
        blob(d, rnd, cx + inner * .1, cy - inner * .1, inner * .38, "#fbfaf5", n=14, wob=.15)
    unit = inner / 11
    for k, kind, cols in found:
        count = {"grain": 140, "dust": 60, "seed": 14, "herb": 6, "lemon": 1, "prawn": 8, "mushroom": 10, "fillet": 2, "pea": 22, "olive": 7}.get(kind, 9)
        for _ in range(count):
            ang = rnd.uniform(0, 2 * math.pi)
            dist = inner * 0.72 * math.sqrt(rnd.random())
            if kind == "grain":
                ang2 = rnd.uniform(0.6, 2.2); dist = inner * 0.55 * math.sqrt(rnd.random())
                x = cx + inner * .32 * math.cos(ang2) + dist * .55 * math.cos(ang)
                y = cy + inner * .32 * math.sin(ang2) + dist * .55 * math.sin(ang)
            elif kind == "lemon":
                x, y = cx + inner * .62, cy - inner * .5
            else:
                x, y = cx + dist * math.cos(ang), cy + dist * math.sin(ang)
            scale = {"prawn": 1.9, "mushroom": 1.7, "nugget": 1.3, "egg": 1.15}.get(kind, 1.0)
            piece(d, rnd, kind, cols, x, y, unit * scale * rnd.uniform(0.85, 1.15))
    img = img.resize((W, H), Image.LANCZOS)
    img.save(path, "JPEG", quality=86)

# ---------------------------------------------------------------- pages
CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif;max-width:760px;margin:0 auto;padding:24px;line-height:1.5;color:#1d1d1f;background:#fbfbfd}
h1{font-size:1.9rem;margin:.2em 0}h2{font-size:1.2rem;margin-top:1.6em;border-bottom:1px solid #ddd;padding-bottom:4px}
.meta{color:#555}.flag{background:#fff3cd;border-left:4px solid #e0a800;padding:8px 12px;margin:12px 0}
li{margin:6px 0}.tag{display:inline-block;background:#e8f0fe;border-radius:12px;padding:2px 10px;margin:2px;font-size:.85rem}
img.hero{width:100%;border-radius:14px;margin:12px 0}table{border-collapse:collapse}td{padding:4px 12px 4px 0}a{color:#0066cc}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;padding:0;list-style:none}
.grid a{text-decoration:none;color:inherit}.grid img{width:100%;border-radius:10px}.card{background:#fff;border-radius:12px;padding:10px;box-shadow:0 1px 4px #0001}
"""

def abs_url(rel):
    return f"{SITE_URL}/{rel}" if SITE_URL else rel

def jsonld(r, img_rel):
    n = r["nutrition"]
    return json.dumps({
        "@context": "https://schema.org", "@type": "Recipe",
        "name": r["name"],
        "image": [abs_url(img_rel)],
        "description": f'{r["type"]} for {r["days"]}. {r["timeNote"]}.',
        "author": {"@type": "Person", "name": "Pierre-Guy"},
        "recipeCategory": r["type"], "recipeCuisine": r["cuisine"],
        "recipeYield": ["4", "4 portions"],
        "prepTime": iso(r["prep"]), "cookTime": iso(r["cook"]), "totalTime": iso(r["total"]),
        "suitableForDiet": [f"https://schema.org/{x}" for x in r["diet"]],
        "keywords": ", ".join(["gluten-free", "low GI", "meal prep", r["cuisine"]]),
        "tool": [{"@type": "HowToTool", "name": e} for e in r["equipment"]],
        "recipeIngredient": r["ingredients"],
        "recipeInstructions": [{"@type": "HowToStep", "position": i + 1, "name": s["name"], "text": s["text"], "timeRequired": iso(s["min"])} for i, s in enumerate(r["steps"])],
        "nutrition": {"@type": "NutritionInformation", "servingSize": r.get("nutritionNote", "Pierre-Guy's portion"),
                      "calories": f'{n["kcal"]} kcal', "carbohydrateContent": f'{n["carbs"]} g', "fiberContent": f'{n["fibre"]} g',
                      "proteinContent": f'{n["protein"]} g', "saturatedFatContent": f'{n["satfat"]} g'},
    }, ensure_ascii=False, indent=2)

def head(title, extra=""):
    return f'<!DOCTYPE html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>{esc(title)}</title>{extra}<style>{CSS}</style></head><body>'

def recipe_page(r, week_id, img_file):
    n = r["nutrition"]
    img_rel = f"weeks/{week_id}/{img_file}"
    steps = "".join(f'<li><strong>{esc(s["name"])}</strong> ({s["min"]} min). {esc(s["text"])}</li>' for s in r["steps"])
    ings = "".join(f"<li>{esc(i)}</li>" for i in r["ingredients"])
    ports = "".join(f"<li>{esc(p)}</li>" for p in r["portions"])
    flag = f'<div class="flag">⚑ {esc(r["flag"])}</div>' if r.get("flag") else ""
    if r.get("note"): flag += f'<p class="meta"><em>{esc(r["note"])}</em></p>'
    tags = "".join(f'<span class="tag">{esc(x.replace("LowLactoseDiet","Lactose-free").replace("Diet",""))}</span>' for x in r["diet"])
    extra = (f"<h2>Next day</h2><p>{esc(r['storage'])}</p>" if r.get("storage") else "") + \
            (f"<h2>Mariska's packing</h2><p>{esc(r['packing'])}</p>" if r.get("packing") else "")
    ld = f'<script type="application/ld+json">\n{jsonld(r, img_rel)}\n</script>'
    return head(r["name"], ld) + f"""<article>
<p class="meta"><a href="index.html">← This week's plan</a> · <a href="../../index.html">All weeks</a></p>
<h1>{esc(r["name"])}</h1>
<p class="meta">{esc(r["type"])} · {esc(r["days"])} · Total {r["total"]} min ({esc(r["timeNote"])}) · Serves 4 · {esc(r["cuisine"])}</p>
<img class="hero" src="{esc(img_file)}" alt="{esc(r["name"])}"><p>{tags}</p>{flag}
<h2>Equipment</h2><p>{esc(", ".join(r["equipment"]))}</p>
<h2>Ingredients (4 portions)</h2><ul>{ings}</ul>
<h2>Method</h2><ol>{steps}</ol>
<h2>Portion weights</h2><ul>{ports}</ul>{extra}
<h2>Nutrition, {esc(r.get("nutritionNote","Pierre-Guy's portion"))} (estimate)</h2>
<table><tr><td>Energy</td><td>{n["kcal"]} kcal</td></tr><tr><td>Carbs</td><td>{n["carbs"]}g</td></tr><tr><td>Fibre</td><td>{n["fibre"]}g</td></tr><tr><td>Protein</td><td>{n["protein"]}g</td></tr><tr><td>Saturated fat</td><td>{n["satfat"]}g</td></tr></table>
</article></body></html>"""

def cards(items):
    return '<ul class="grid">' + "".join(
        f'<li class="card"><a href="{href}"><img src="{img}" alt=""><strong>{esc(name)}</strong><br><span class="meta">{esc(sub)}</span></a></li>'
        for href, img, name, sub in items) + "</ul>"

def week_page(data, built):
    groups = {}
    for r, img in built:
        groups.setdefault(r["type"], []).append((f'{r["slug"]}.html', img, r["name"], f'{r["days"]} · {r["total"]} min'))
    body = "".join(f"<h2>{esc(t)}s</h2>" + cards(v) for t, v in groups.items())
    chicken = f'<h2>Chicken for the salads</h2><p>{esc(data["chicken"])}</p>' if data.get("chicken") else ""
    note = f'<p class="meta"><em>{esc(data["note"])}</em></p>' if data.get("note") else ""
    return head(data["week"]) + f'<p class="meta"><a href="../../index.html">← All weeks</a></p><h1>{esc(data["week"])}</h1>{note}{body}{chicken}</body></html>'

def home_page(weeks):
    latest = weeks[0]
    rest = "".join(f'<li><a href="weeks/{w}/index.html">{esc(lbl)}</a></li>' for w, lbl, _ in weeks[1:])
    w, lbl, first_img = latest
    return head("Our kitchen") + f"""<h1>Our kitchen</h1>
<a href="weeks/{w}/index.html" style="text-decoration:none;color:inherit"><div class="card"><img class="hero" src="weeks/{w}/{first_img}" alt=""><h2 style="border:0;margin:0">This week: {esc(lbl)}</h2></div></a>
{"<h2>Previous weeks</h2><ul>" + rest + "</ul>" if rest else ""}</body></html>"""

def main():
    weeks_dir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "weeks")
    out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "site")
    photos = ROOT / "photos"
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    index = []
    for f in sorted(weeks_dir.glob("*.json"), reverse=True):
        week_id = f.stem
        datetime.date.fromisoformat(week_id)  # file names must be YYYY-MM-DD
        data = json.loads(f.read_text(encoding="utf-8"))
        wdir = out / "weeks" / week_id
        wdir.mkdir(parents=True)
        built = []
        for r in data["recipes"]:
            photo = next((p for p in (photos / f'{r["slug"]}.jpg', photos / f'{r["slug"]}.png') if p.exists()), None)
            img_file = f'{r["slug"]}{photo.suffix if photo else ".jpg"}'
            if photo: shutil.copy(photo, wdir / img_file)
            else: illustrate(r, wdir / img_file)
            (wdir / f'{r["slug"]}.html').write_text(recipe_page(r, week_id, img_file), encoding="utf-8")
            built.append((r, img_file))
        (wdir / "index.html").write_text(week_page(data, built), encoding="utf-8")
        index.append((week_id, data["week"], built[0][1]))
        print(f"{week_id}: {len(built)} recipes")
    if not index: sys.exit("No week files found in " + str(weeks_dir))
    (out / "index.html").write_text(home_page(index), encoding="utf-8")
    (out / ".nojekyll").write_text("")

if __name__ == "__main__":
    main()

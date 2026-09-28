"""Build assets/stats.svg from the GitHub GraphQL API (run by .github/workflows/stats.yml)."""
import json, os, sys, urllib.request, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textpath import text_path

USER = os.environ.get("GH_USER", "KiryaBasik")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "stats.svg")

QUERY = """query($login:String!){ user(login:$login){
  createdAt followers{totalCount}
  repositories(ownerAffiliations:OWNER, isFork:false, first:100, orderBy:{field:PUSHED_AT,direction:DESC}){
    totalCount nodes{ stargazerCount languages(first:10, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{name} } } } }
  contributionsCollection{ totalCommitContributions restrictedContributionsCount totalPullRequestContributions
    contributionCalendar{ totalContributions weeks{ contributionDays{ contributionCount date } } } } } }"""


def fetch():
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
                                 headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req, timeout=60))
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]


def summarize(u):
    cc = u["contributionsCollection"]
    langs = {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    return {
        "contrib": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "langs": sorted(langs.items(), key=lambda x: -x[1])[:5],
        "days": [(d["date"], d["contributionCount"]) for d in days],
    }


def render(s):
    W, H = 1200, 360
    P = []
    # --- stat tiles
    tiles = [("Contributions", s["contrib"], "last 12 months"), ("Commits", s["commits"], "last 12 months"),
             ("Repositories", s["repos"], "public, own"), ("Stars", s["stars"], "earned")]
    tw = (W - 80 - 3 * 20) / 4
    for i, (label, val, sub) in enumerate(tiles):
        x = 40 + i * (tw + 20)
        P.append(f'<rect x="{x:.0f}" y="36" width="{tw:.0f}" height="112" rx="14" fill="#1d1638" stroke="#3a2a55"/>')
        n_d, _ = text_path(f"{val:,}".replace(",", " "), "montserrat", 600, 40, x + 24, 100)
        l_d, _ = text_path(label.upper(), "montserrat", 600, 11, x + 26, 124, spacing=2.4)
        s_d, _ = text_path(sub, "montserrat", 500, 11, x + tw - 20, 58, anchor="end")
        P.append(f'<path d="{n_d}" fill="#fbeef2"/><path d="{l_d}" fill="#f39ab3"/><path d="{s_d}" fill="#6f5d8c"/>')
        P.append(f'<circle cx="{x + 26:.0f}" cy="56" r="4" fill="#e0374f"><animate attributeName="opacity" values="1;.35;1" dur="3s" begin="-{i * .7:.1f}s" repeatCount="indefinite"/></circle>')

    # --- heatmap (last 30 weeks) as blooming sakura cells
    days = s["days"][-210:]
    mx = max([c for _, c in days] + [1])
    shades = ["#241b3d", "#5b2f55", "#9b4468", "#e0708f", "#f7b6c8"]
    cell, gap = 13, 4
    hx, hy = 40, 200
    t_d, _ = text_path("ACTIVITY", "montserrat", 600, 11, hx, 186, spacing=2.4)
    P.append(f'<path d="{t_d}" fill="#9d8bb5"/>')
    for i, (date, c) in enumerate(days):
        wk, wd = divmod(i, 7)
        lvl = 0 if c == 0 else min(4, 1 + int(3 * c / mx))
        x, y = hx + wk * (cell + gap), hy + wd * (cell + gap)
        delay = wk * 0.04
        P.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3.5" fill="{shades[lvl]}" opacity="0">'
                 f'<animate attributeName="opacity" values="0;1" begin="{delay:.2f}s" dur=".5s" fill="freeze"/></rect>')

    # --- languages
    lx, lw = 640, W - 40 - 640
    t_d, _ = text_path("TOP LANGUAGES", "montserrat", 600, 11, lx, 186, spacing=2.4)
    P.append(f'<path d="{t_d}" fill="#9d8bb5"/>')
    total = sum(v for _, v in s["langs"]) or 1
    cols = ["#e0374f", "#f39ab3", "#ffcf9e", "#c7a6ff", "#8fd1ff"]
    x = lx
    P.append(f'<clipPath id="bar"><rect x="{lx}" y="200" width="{lw}" height="12" rx="6"/></clipPath><g clip-path="url(#bar)"><rect x="{lx}" y="200" width="{lw}" height="12" fill="#241b3d"/>')
    for i, (name, v) in enumerate(s["langs"]):
        w = lw * v / total
        P.append(f'<rect x="{x:.1f}" y="200" width="0" height="12" fill="{cols[i]}"><animate attributeName="width" values="0;{w:.1f}" begin="{.2 + i * .15:.2f}s" dur=".8s" fill="freeze" calcMode="spline" keySplines=".2 0 .2 1"/></rect>')
        x += w
    P.append("</g>")
    for i, (name, v) in enumerate(s["langs"]):
        cx = lx + (i % 3) * (lw / 3)
        cy = 246 + (i // 3) * 34
        n_d, nw = text_path(name, "montserrat", 500, 14, cx + 18, cy + 5)
        p_d, _ = text_path(f"{100 * v / total:.1f}%", "montserrat", 500, 12, cx + 24 + nw, cy + 5)
        P.append(f'<circle cx="{cx + 5}" cy="{cy}" r="5" fill="{cols[i]}"/><path d="{n_d}" fill="#e6dbe8"/><path d="{p_d}" fill="#6f5d8c"/>')

    upd = dt.datetime.utcnow().strftime("updated %d %b %Y")
    u_d, _ = text_path(upd, "montserrat", 500, 10, W - 40, H - 22, spacing=1, anchor="end")
    P.append(f'<path d="{u_d}" fill="#4d3f66"/>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#18122d"/><stop offset="1" stop-color="#0f0b1d"/></linearGradient></defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="20" fill="url(#bg)" stroke="#3a2a55"/>
{"".join(P)}
</svg>'''


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        import random
        r = random.Random(1)
        today = dt.date.today()
        demo = {"contrib": 77, "commits": 64, "repos": 7, "stars": 3,
                "langs": [("HTML", 50), ("CSS", 25), ("JavaScript", 15), ("Python", 6), ("PHP", 4)],
                "days": [(str(today - dt.timedelta(days=i)), r.choice([0, 0, 0, 1, 2, 4])) for i in range(365, 0, -1)]}
        svg = render(demo)
    else:
        svg = render(summarize(fetch()))
    open(OUT, "w").write(svg)
    print("wrote", OUT)

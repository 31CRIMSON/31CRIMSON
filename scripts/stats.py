#!/usr/bin/env python3
"""
crimson telemetry — генерирует SVG-статистику профиля из GitHub GraphQL API.

Работает от ТВОЕГО токена, поэтому видит приватные репозитории и приватные
контрибуции. Без внешних зависимостей.

  STATS_TOKEN=ghp_xxx python3 scripts/stats.py dist
  python3 scripts/stats.py dist --mock        # проверка вёрстки без API

Переменные окружения:
  STATS_TOKEN     classic PAT со scope: repo, read:user (и read:org, если нужны орг-репо)
  AFFILIATIONS    чьи репо учитывать в языках/репо: OWNER (по умолчанию)
                  или, например, OWNER,COLLABORATOR,ORGANIZATION_MEMBER
  EXCLUDE_LANGS   языки, которые не показывать, через запятую (например: HTML,CSS)
  EXCLUDE_REPOS   репозитории, которые не учитывать в языках, через запятую
  FEATURED_LANGS  языки с визуальным акцентом (цвет/подсветка; проценты не меняются)
"""
import json, os, sys, random, urllib.request, datetime as dt
from xml.sax.saxutils import escape as esc

OUT = sys.argv[1] if len(sys.argv) > 1 else "dist"
MOCK = "--mock" in sys.argv
TOKEN = os.environ.get("STATS_TOKEN", "")
AFF = [a.strip() for a in os.environ.get("AFFILIATIONS", "OWNER").split(",") if a.strip()]
EX_LANGS = {s.strip().lower() for s in os.environ.get("EXCLUDE_LANGS", "").split(",") if s.strip()}
FEATURED = [s.strip() for s in os.environ.get("FEATURED_LANGS", "TypeScript,Python,JavaScript").split(",") if s.strip()]
EX_REPOS = {s.strip().lower() for s in os.environ.get("EXCLUDE_REPOS", "").split(",") if s.strip()}

MONO = "'JetBrains Mono','Fira Code','SFMono-Regular',Consolas,'Courier New',monospace"
RED, TXT, DIM = "#FF1E3C", "#D9D9DE", "#6B6B75"


# ------------------------------------------------------------------ API
def gql(query, variables=None):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "crimson-telemetry"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            if "errors" in data:
                raise RuntimeError(data["errors"])
            return data["data"]
        except Exception as e:  # noqa
            if attempt == 2:
                raise
            print("retry:", e, file=sys.stderr)


Q_USER = """query { viewer { login createdAt } }"""

Q_REPOS = """query($aff:[RepositoryAffiliation], $after:String) { viewer {
  repositories(ownerAffiliations:$aff, isFork:false, first:100, after:$after) {
    totalCount pageInfo { hasNextPage endCursor }
    nodes { nameWithOwner isPrivate stargazerCount
      languages(first:12, orderBy:{field:SIZE, direction:DESC}) { edges { size node { name } } } }
  } } }"""

Q_YEAR = """query($from:DateTime!, $to:DateTime!) { viewer { contributionsCollection(from:$from, to:$to) {
  totalCommitContributions restrictedContributionsCount
  totalPullRequestContributions totalPullRequestReviewContributions totalIssueContributions
  contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
} } }"""


def fetch():
    u = gql(Q_USER)["viewer"]
    repos, after = [], None
    while True:
        d = gql(Q_REPOS, {"aff": AFF, "after": after})["viewer"]["repositories"]
        repos += d["nodes"]
        if not d["pageInfo"]["hasNextPage"]:
            break
        after = d["pageInfo"]["endCursor"]

    created = dt.datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    now = dt.datetime.now(dt.timezone.utc)
    days, t = {}, dict(commits=0, prs=0, reviews=0, issues=0, total=0, year_commits=0)
    start = created
    while start < now:
        end = min(start + dt.timedelta(days=365), now)
        c = gql(Q_YEAR, {"from": start.isoformat(), "to": end.isoformat()})["viewer"]["contributionsCollection"]
        commits = c["totalCommitContributions"] + c["restrictedContributionsCount"]
        t["commits"] += commits
        t["prs"] += c["totalPullRequestContributions"]
        t["reviews"] += c["totalPullRequestReviewContributions"]
        t["issues"] += c["totalIssueContributions"]
        for w in c["contributionCalendar"]["weeks"]:
            for day in w["contributionDays"]:
                days[day["date"]] = day["contributionCount"]
        start = end
    # коммиты за последние 365 дней (отдельный запрос, чтобы не зависеть от границ окон)
    c = gql(Q_YEAR, {"from": (now - dt.timedelta(days=365)).isoformat(), "to": now.isoformat()})["viewer"]["contributionsCollection"]
    t["year_commits"] = c["totalCommitContributions"] + c["restrictedContributionsCount"]
    t["total"] = sum(days.values())

    langs = {}
    for r in repos:
        if r["nameWithOwner"].lower() in EX_REPOS or r["nameWithOwner"].split("/")[1].lower() in EX_REPOS:
            continue
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            if n.lower() in EX_LANGS:
                continue
            langs[n] = langs.get(n, 0) + e["size"]
    return dict(
        login=u["login"], days=days, langs=langs, **t,
        repos=len(repos), private=sum(r["isPrivate"] for r in repos),
        stars=sum(r["stargazerCount"] for r in repos))


def mock():
    random.seed(31)
    today = dt.date.today()
    days = {}
    for i in range(400):
        d = today - dt.timedelta(days=i)
        base = 0 if random.random() < .18 else random.randint(1, 9)
        days[d.isoformat()] = base + (random.randint(5, 18) if random.random() < .08 else 0)
    langs = {"TypeScript": 980000, "Python": 520000, "JavaScript": 410000, "PHP": 230000, "HCL": 160000,
             "Shell": 120000, "Dockerfile": 30000, "CSS": 80000, "SCSS": 60000}
    langs = {k: v for k, v in langs.items() if k.lower() not in EX_LANGS}
    return dict(login="31CRIMSON", days=days, langs=langs, commits=2841, prs=213, reviews=187, issues=64,
                total=sum(days.values()), year_commits=1630, repos=58, private=41, stars=37)


# ------------------------------------------------------------------ helpers
def streaks(days):
    today = dt.date.today()
    cur, d = 0, today
    if days.get(d.isoformat(), 0) == 0:
        d -= dt.timedelta(days=1)
    while days.get(d.isoformat(), 0) > 0:
        cur += 1; d -= dt.timedelta(days=1)
    best = run = 0
    for k in sorted(days):
        run = run + 1 if days[k] > 0 else 0
        best = max(best, run)
    return cur, best


def fmt(n):
    return f"{n/1000:.1f}k".replace(".0k", "k") if n >= 10000 else f"{n:,}".replace(",", " ")


def stamp():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


STYLE = f"""text {{ font-family: {MONO}; }}
.h {{ fill: {RED}; font-size: 13px; font-weight: 700; letter-spacing: 2px; }}
.s {{ fill: {DIM}; font-size: 11px; }}
.fade {{ opacity: 0; animation: in .7s ease-out forwards; }}
@keyframes in {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes blink {{ 0%,50% {{ opacity: 1; }} 50.01%,100% {{ opacity: .15; }} }}
.live {{ animation: blink 1.4s steps(1) infinite; }}"""


def frame(W, H, title, right, body, extra_style=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<style>{STYLE}{extra_style}</style>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="#0b0b0d" stroke="{RED}" stroke-opacity=".3"/>
<circle class="live" cx="26" cy="31" r="4.5" fill="{RED}"/>
<text x="40" y="36" class="h">{esc(title)}</text>
<text x="{W-24}" y="36" text-anchor="end" class="s">{esc(right)}</text>
<line x1="20" y1="54" x2="{W-20}" y2="54" stroke="{RED}" stroke-opacity=".15"/>
{body}
</svg>'''


# ------------------------------------------------------------------ cards
def stats_svg(s):
    cur, best = streaks(s["days"])
    year = dt.date.today().year
    tiles = [
        ("CONTRIBUTIONS", fmt(s["total"]), "all time · incl. private"),
        ("COMMITS", fmt(s["year_commits"]), "last 365 days"),
        ("PULL REQUESTS", fmt(s["prs"]), f"{fmt(s['reviews'])} code reviews"),
        ("REPOSITORIES", fmt(s["repos"]), f"{s['private']} private · {s['repos']-s['private']} public"),
        ("CURRENT STREAK", f"{cur}d", "days in a row"),
        ("LONGEST STREAK", f"{best}d", "personal record"),
        ("ALL-TIME COMMITS", fmt(s["commits"]), "since account creation"),
        ("STARS EARNED", fmt(s["stars"]), f"{fmt(s['issues'])} issues opened"),
    ]
    W, cols, pad, gap, th = 1000, 4, 20, 14, 92
    tw_ = (W - 2 * pad - (cols - 1) * gap) / cols
    b = []
    for i, (k, v, sub) in enumerate(tiles):
        x = pad + (i % cols) * (tw_ + gap); y = 70 + (i // cols) * (th + gap)
        b.append(f'<g class="fade" style="animation-delay:{i*0.12:.2f}s">'
                 f'<rect x="{x:.1f}" y="{y}" width="{tw_:.1f}" height="{th}" rx="10" fill="#120709" stroke="{RED}" stroke-opacity=".18"/>'
                 f'<rect x="{x:.1f}" y="{y+16}" width="3" height="{th-32}" rx="1.5" fill="{RED}"/>'
                 f'<text x="{x+18:.1f}" y="{y+26}" style="fill:#ff7a8a;font-size:11px;letter-spacing:1.5px">{k}</text>'
                 f'<text x="{x+18:.1f}" y="{y+60}" style="fill:#fff;font-size:30px;font-weight:800">{esc(v)}</text>'
                 f'<text x="{x+18:.1f}" y="{y+80}" style="fill:{DIM};font-size:11px">{esc(sub)}</text></g>')
    H = 70 + 2 * th + gap + pad
    return frame(W, H, "TELEMETRY // GITHUB", f"private repos included · updated {stamp()}", "".join(b))


def activity_svg(s, n=120):
    today = dt.date.today()
    vals = [s["days"].get((today - dt.timedelta(days=n - 1 - i)).isoformat(), 0) for i in range(n)]
    W, H, L, R, T, B = 1000, 270, 50, 24, 78, 40
    pw, ph = W - L - R, H - T - B
    mx = max(max(vals), 1)
    xs = [L + i * pw / (n - 1) for i in range(n)]
    ys = [T + ph - v / mx * ph for v in vals]
    # сглаженная кривая (catmull-rom → bezier)
    d = f"M{xs[0]:.1f} {ys[0]:.1f}"
    for i in range(n - 1):
        p0 = (xs[max(i - 1, 0)], ys[max(i - 1, 0)]); p1 = (xs[i], ys[i])
        p2 = (xs[i + 1], ys[i + 1]); p3 = (xs[min(i + 2, n - 1)], ys[min(i + 2, n - 1)])
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        c1 = (c1[0], min(c1[1], T + ph)); c2 = (c2[0], min(c2[1], T + ph))
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    area = d + f" L{xs[-1]:.1f} {T+ph} L{xs[0]:.1f} {T+ph} Z"
    b = ['<defs><linearGradient id="a" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{RED}" stop-opacity=".45"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></linearGradient>'
         '<filter id="gl" x="-5%" y="-30%" width="110%" height="160%"><feGaussianBlur stdDeviation="3" result="b"/>'
         '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>']
    for k in range(5):
        y = T + ph * k / 4
        b.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="#fff" stroke-opacity=".05"/>')
        b.append(f'<text x="{L-10}" y="{y+4:.1f}" text-anchor="end" class="s">{round(mx*(4-k)/4)}</text>')
    last_m = None
    for i in range(n):
        day = today - dt.timedelta(days=n - 1 - i)
        if day.day == 1 or (i == 0 and day.day < 20):
            if last_m != day.month:
                b.append(f'<text x="{xs[i]:.1f}" y="{H-14}" class="s">{day.strftime("%b").upper()}</text>')
                b.append(f'<line x1="{xs[i]:.1f}" y1="{T}" x2="{xs[i]:.1f}" y2="{T+ph}" stroke="#fff" stroke-opacity=".04"/>')
                last_m = day.month
    b.append(f'<path d="{area}" fill="url(#a)" class="fade" style="animation-delay:1.2s"/>')
    b.append(f'<path d="{d}" fill="none" stroke="{RED}" stroke-width="2.5" filter="url(#gl)" pathLength="1" class="draw"/>')
    pk = max(range(n), key=lambda i: vals[i])
    b.append(f'<g class="fade" style="animation-delay:2s"><circle cx="{xs[pk]:.1f}" cy="{ys[pk]:.1f}" r="5" fill="#fff" stroke="{RED}" stroke-width="2"/>'
             f'<text x="{xs[pk]:.1f}" y="{ys[pk]-12:.1f}" text-anchor="middle" style="fill:#fff;font-size:11px">peak {vals[pk]}</text></g>')
    b.append(f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="4" fill="{RED}"><animate attributeName="r" values="4;9;4" dur="1.6s" repeatCount="indefinite"/>'
             '<animate attributeName="opacity" values="1;.3;1" dur="1.6s" repeatCount="indefinite"/></circle>')
    total = sum(vals)
    extra = ".draw { stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 2.2s ease-out forwards; } @keyframes draw { to { stroke-dashoffset: 0; } }"
    return frame(W, H, f"CONTRIBUTION HEARTBEAT // {n} DAYS", f"{total} contributions · avg {total/n:.1f}/day", "".join(b), extra)


def langs_svg(s, top=8):
    items = sorted(s["langs"].items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in items) or 1
    head, rest = items[:top], sum(v for _, v in items[top:])
    if rest:
        head.append(("Other", rest))
    hot = ["#FF1E3C", "#FF4D63", "#E0284A"]          # акцентные языки
    cold = ["#6E2A35", "#5A2330", "#4A1D28", "#3D1821", "#33141C", "#2A1017"]
    fl = [f.lower() for f in FEATURED]
    colors, hi, ci = [], 0, 0
    for n, _ in head:
        if n.lower() in fl:
            colors.append(hot[hi % len(hot)]); hi += 1
        else:
            colors.append(cold[ci % len(cold)]); ci += 1
    W, pad = 1000, 24
    bw = W - 2 * pad
    b, x = [], pad
    b.append('<defs><filter id="hg" x="-20%" y="-200%" width="140%" height="500%"><feGaussianBlur stdDeviation="4" result="b"/>'
             '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    b.append(f'<clipPath id="bar"><rect x="{pad}" y="76" width="{bw}" height="16" rx="8"/></clipPath><g clip-path="url(#bar)">')
    for i, (n, v) in enumerate(head):
        w = v / total * bw
        b.append(f'<rect x="{x:.1f}" y="76" width="{w+0.5:.1f}" height="16" fill="{colors[i]}" class="fade" style="animation-delay:{i*0.08:.2f}s"/>')
        x += w
    b.append('</g>')
    cols, colw = 3, bw / 3
    for i, (n, v) in enumerate(head):
        cx = pad + (i % cols) * colw; cy = 126 + (i // cols) * 32
        pct = v / total * 100
        feat = n.lower() in fl
        name_style = "fill:#fff;font-size:14px;font-weight:700" if feat else f"fill:{DIM};font-size:13px"
        pct_style = f"fill:{RED};font-size:14px;font-weight:700" if feat else f"fill:{DIM};font-size:13px"
        dot = (f'<rect x="{cx:.1f}" y="{cy-11}" width="12" height="12" rx="3" fill="{colors[i]}" filter="url(#hg)"/>' if feat
               else f'<rect x="{cx:.1f}" y="{cy-11}" width="12" height="12" rx="3" fill="{colors[i]}"/>')
        b.append(f'<g class="fade" style="animation-delay:{0.6+i*0.08:.2f}s">{dot}'
                 f'<text x="{cx+22:.1f}" y="{cy}" style="{name_style}">{esc(n)}</text>'
                 f'<text x="{cx+colw-30:.1f}" y="{cy}" text-anchor="end" style="{pct_style}">{pct:.1f}%</text></g>')
    H = 126 + ((len(head) - 1) // cols) * 32 + 30
    return frame(W, H, "LANGUAGE FOOTPRINT // BY BYTES", "public + private repositories", "".join(b))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    s = mock() if MOCK else fetch()
    for name, fn in [("stats", stats_svg), ("activity", activity_svg), ("langs", langs_svg)]:
        with open(os.path.join(OUT, f"{name}.svg"), "w") as f:
            f.write(fn(s))
    print(f"{s['login']}: {s['total']} contributions, {s['repos']} repos ({s['private']} private)")

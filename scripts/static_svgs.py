"""Генерирует статичные SVG: карту стека и карточки проектов."""
import sys, textwrap
from xml.sax.saxutils import escape as esc

OUT = sys.argv[1]
MONO = "'JetBrains Mono','Fira Code','SFMono-Regular',Consolas,'Courier New',monospace"
RED, DIM, TXT = "#FF1E3C", "#6B6B75", "#D9D9DE"
CW = 0.602  # ширина моноширинного символа в em


def tw(s, size):
    return len(s) * size * CW


# ---------------------------------------------------------------- stack map
STACK = [
    ("Infrastructure & orchestration", ["Kubernetes", "RKE2", "EKS", "Rancher", "Helm", "Docker", "Compose", "containerd", "Terraform", "Terragrunt", "Ansible", "Linux", "Bare metal", "VPS"]),
    ("Cloud & delivery", ["AWS", "GCP", "Cloud Run", "Artifact Registry", "GitHub Actions", "GitLab CI", "Bitbucket Pipelines", "Jenkins", "Argo CD", "Argo Workflows", "Fleet", "GitOps"]),
    ("Backend & APIs", ["TypeScript", "JavaScript", "Python", "PHP", "Node.js", "Express", "Flask", "Laravel", "REST", "GraphQL", "WebSockets"]),
    ("Frontend & mobile", ["React", "Next.js", "React Native", "Expo", "Redux Toolkit", "Vite", "HTML", "CSS"]),
    ("Databases & messaging", ["PostgreSQL", "MySQL", "MongoDB", "Redis", "ClickHouse", "Percona XtraDB", "ProxySQL", "RabbitMQ"]),
    ("Observability", ["Prometheus", "Grafana", "Loki", "Tempo", "Mimir", "OpenTelemetry", "Alertmanager", "Zabbix"]),
    ("Networking & edge", ["Nginx", "HAProxy", "Traefik", "Cloudflare", "DNS", "TLS", "Load balancing", "WAF", "Rate limiting", "DDoS mitigation"]),
    ("Security & reliability", ["Vault", "Secrets mgmt", "RBAC", "SSO", "Network isolation", "HA", "Failover", "DR", "Backups", "Zero-downtime deploys"]),
    ("Automation & tooling", ["Bash", "Python scripting", "Scraping", "Browser automation", "Postman", "OpenAPI", "Jest", "Git"]),
    ("CMS & e-commerce", ["WordPress", "Magento", "OpenCart"]),
]


def stack_svg():
    W, colW, gap, pad = 1000, 485, 30, 18
    fs, chipH, cgap = 12, 24, 8
    cards = []
    for i, (title, items) in enumerate(STACK):
        x, y, rows = 0, 0, []
        line = []
        for it in items:
            w = tw(it, fs) + 20
            if x + w > colW - 2 * pad and line:
                rows.append(line); line = []; x = 0
            line.append((it, x, w)); x += w + cgap
        rows.append(line)
        h = 58 + len(rows) * (chipH + cgap) + pad - cgap
        cards.append((i, title, rows, h))

    parts, y = [], 0
    for r in range(0, len(cards), 2):
        pair = cards[r:r + 2]
        rh = max(c[3] for c in pair)
        for j, (i, title, rows, _) in enumerate(pair):
            cx = j * (colW + gap)
            d = i * 0.35
            g = [f'<g transform="translate({cx},{y})"><g class="card" style="animation-delay:{d:.2f}s">']
            g.append(f'<rect width="{colW}" height="{rh}" rx="12" fill="#0d0d0f" stroke="{RED}" stroke-opacity=".22"/>')
            g.append(f'<rect class="bar" x="0" y="14" width="3" height="{rh-28}" rx="1.5" fill="{RED}" style="animation-delay:{d:.2f}s"/>')
            g.append(f'<text x="{pad}" y="32" class="idx">{i+1:02d}</text>')
            g.append(f'<text x="{pad+30}" y="32" class="ttl">{esc(title.upper())}</text>')
            g.append(f'<line x1="{pad}" y1="44" x2="{colW-pad}" y2="44" stroke="{RED}" stroke-opacity=".15"/>')
            for ri, line in enumerate(rows):
                cy = 58 + ri * (chipH + cgap)
                for it, x, w in line:
                    g.append(f'<rect x="{pad+x:.1f}" y="{cy}" width="{w:.1f}" height="{chipH}" rx="5" class="chip"/>')
                    g.append(f'<text x="{pad+x+w/2:.1f}" y="{cy+16}" text-anchor="middle" class="ct">{esc(it)}</text>')
            g.append('</g></g>')
            parts.append("".join(g))
        y += rh + gap
    H = y - gap
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<style>
text {{ font-family: {MONO}; }}
.idx {{ fill: {RED}; font-size: 13px; font-weight: 700; }}
.ttl {{ fill: #fff; font-size: 13px; font-weight: 700; letter-spacing: 1.5px; }}
.chip {{ fill: #1a0a0f; stroke: {RED}; stroke-opacity: .28; }}
.ct {{ fill: {TXT}; font-size: {fs}px; }}
.card {{ opacity: 0; animation: in .6s ease-out forwards; }}
.bar {{ animation: glow 3.5s ease-in-out infinite; }}
@keyframes in {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; }} }}
@keyframes glow {{ 0%,100% {{ opacity: .25; }} 15% {{ opacity: 1; }} 35% {{ opacity: .25; }} }}
</style>
{"".join(parts)}
</svg>'''


# ---------------------------------------------------------------- project cards
PROJECTS = [
    dict(n="01", title="E-commerce Analytics Platform", badge="PUBLIC ↗",
         flow=["TS SDK", "Express API", "MongoDB", "Next.js"],
         desc="TypeScript SDK for tracking user events, a Node.js backend that collects and processes them, and a dashboard for user activity and business metrics.",
         tags=["TypeScript", "Node.js", "Express", "MongoDB", "Next.js"]),
    dict(n="02", title="TierTracker", badge="■ PRIVATE",
         flow=["Expo App", "Node API", "MongoDB", "Cloud Run"],
         desc="App for pet owners with gamification, achievements and activity tracking. Mobile client, Node.js API and Next.js editor, shipped to Cloud Run via CI.",
         tags=["React Native", "Expo", "Node.js", "MongoDB", "Firebase", "Docker", "GitHub Actions", "Cloud Run"]),
    dict(n="03", title="ZooCamp", badge="■ PRIVATE",
         flow=["Catalog", "Search", "Favorites", "Cart"],
         desc="E-commerce platform for pet products: catalog, search, cart, favorites, blog and the rest of the storefront components, with animated UI.",
         tags=["Next.js 15", "React 19", "SCSS", "GSAP", "Swiper"]),
    dict(n="04", title="Task Management Board", badge="",
         flow=["React UI", "Redux", "REST API", "Database"],
         desc="Kanban board with full task CRUD, drag-and-drop between columns and task management on top of a REST API.",
         tags=["React", "TypeScript", "Redux Toolkit", "Express / NestJS", "MongoDB / PostgreSQL"]),
]


CONTACTS = [
    ("github", "github", "/31CRIMSON"),
    ("telegram", "telegram", "@your_username"),
    ("linkedin", "linkedin", "/dmitriy-kuzmik"),
    ("email", "email", "dmitriy.kuzzmik@gmail.com"),
]


def contact_svg(key, label, value):
    fs = 13
    lw = tw(label, 11) + len(label) * 1.5 + 34
    W = int(lw + tw(value, fs) + 40)
    H = 40
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<style>text {{ font-family: {MONO}; }} .sw {{ animation: sw 3s ease-in-out infinite; }} @keyframes sw {{ 0%,100% {{ opacity: .35; }} 50% {{ opacity: 1; }} }}</style>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="8" fill="#0d0d0f" stroke="{RED}" stroke-opacity=".45"/>
<path d="M.5 8.5a8 8 0 0 1 8-8H{lw}V{H-.5}H8.5a8 8 0 0 1-8-8z" fill="#1a0a0f"/>
<line x1="{lw}" y1="0" x2="{lw}" y2="{H}" stroke="{RED}" stroke-opacity=".45"/>
<circle class="sw" cx="13" cy="{H/2}" r="3" fill="{RED}"/>
<text x="22" y="{H/2+4}" style="fill:{RED};font-size:11px;letter-spacing:1.5px;font-weight:700">{label.upper()}</text>
<text x="{lw+14}" y="{H/2+4.5}" style="fill:#fff;font-size:{fs}px">{esc(value)}</text>
<text x="{W-12}" y="{H/2+4.5}" text-anchor="end" style="fill:{RED};font-size:12px">↗</text>
</svg>'''


def project_svg(p):
    W, H, pad = 490, 315, 22
    o = [f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="#0d0d0f" stroke="{RED}" stroke-opacity=".35"/>',
         f'<path d="M1 60V15a14 14 0 0 1 14-14h{W-30}a14 14 0 0 1 14 14v45z" fill="#16090d"/>',
         f'<text x="{pad}" y="38" class="n">{p["n"]} //</text>',
         f'<text x="{pad+50}" y="38" class="t">{esc(p["title"].upper())}</text>',
         f'<text x="{W-pad}" y="38" text-anchor="end" class="{"go" if "PUBLIC" in p["badge"] else "lock"}">{esc(p["badge"])}</text>']
    # pipeline
    n = len(p["flow"]); bw, bh, by = 96, 34, 86
    span = (W - 2 * pad - bw) / (n - 1)
    xs = [pad + i * span for i in range(n)]
    path = f"M{xs[0]+bw:.1f} {by+bh/2} H{xs[-1]:.1f}"
    o.append(f'<path d="{path}" class="wire"/>')
    o.append(f'<path d="{path}" class="flow"/>')
    for k in range(3):
        o.append(f'<circle r="3.5" fill="#fff" filter="url(#g)" opacity="0"><set attributeName="opacity" to="1" begin="{k*0.8}s"/><animateMotion dur="2.4s" begin="{k*0.8}s" repeatCount="indefinite" path="{path}"/></circle>')
    for i, (x, lbl) in enumerate(zip(xs, p["flow"])):
        o.append(f'<rect x="{x:.1f}" y="{by}" width="{bw}" height="{bh}" rx="7" class="node"/>')
        o.append(f'<text x="{x+bw/2:.1f}" y="{by+22}" text-anchor="middle" class="nl">{esc(lbl)}</text>')
    # description
    ly = 160
    for line in textwrap.wrap(p["desc"], 56):
        o.append(f'<text x="{pad}" y="{ly}" class="d">{esc(line)}</text>'); ly += 21
    # tags
    x, ty = pad, ly + 10
    for t in p["tags"]:
        w = tw(t, 11) + 16
        if x + w > W - pad:
            x = pad; ty += 28
        o.append(f'<rect x="{x:.1f}" y="{ty}" width="{w:.1f}" height="22" rx="11" class="tag"/>')
        o.append(f'<text x="{x+w/2:.1f}" y="{ty+15}" text-anchor="middle" class="tt">{esc(t)}</text>')
        x += w + 7
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs><filter id="g" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.5" result="b"/><feFlood flood-color="{RED}"/><feComposite in2="b" operator="in"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<style>
text {{ font-family: {MONO}; }}
.n {{ fill: {RED}; font-size: 15px; font-weight: 800; }}
.t {{ fill: #fff; font-size: 14px; font-weight: 700; letter-spacing: 1px; }}
.go {{ fill: {RED}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; }}\n.lock {{ fill: {DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; }}
.node {{ fill: #1a0a0f; stroke: {RED}; stroke-width: 1.5; }}
.nl {{ fill: #fff; font-size: 12px; }}
.wire {{ stroke: {RED}; stroke-opacity: .25; stroke-width: 2; fill: none; }}
.flow {{ stroke: {RED}; stroke-width: 2; fill: none; stroke-dasharray: 6 10; animation: dash 1s linear infinite; }}
.d {{ fill: {TXT}; font-size: 13px; }}
.tag {{ fill: none; stroke: {RED}; stroke-opacity: .5; }}
.tt {{ fill: #ff9aa8; font-size: 11px; }}
@keyframes dash {{ to {{ stroke-dashoffset: -16; }} }}
</style>
{"".join(o)}
</svg>'''


open(f"{OUT}/stack.svg", "w").write(stack_svg())
for p in PROJECTS:
    open(f"{OUT}/project-{p['n']}.svg", "w").write(project_svg(p))
for key, label, value in CONTACTS:
    open(f"{OUT}/contact-{key}.svg", "w").write(contact_svg(key, label, value))
print("ok")

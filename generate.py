"""Render dark_mode.svg / light_mode.svg: ASCII portrait + neofetch-style profile card.

Stats come from the GitHub API. Set GH_TOKEN to a token that can see private
contributions (a classic PAT with `repo` + `read:user`), otherwise counts are public-only.
"""
import datetime as dt
import html
import json
import os
import urllib.request

USER = "manojkumarm-integrate"
ACCOUNT_CREATED = dt.date(2022, 4, 19)
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

PROFILE = [
    ("OS", "macOS, Linux"),
    ("Uptime", None),  # filled from ACCOUNT_CREATED
    ("Host", "Integrate"),
    ("Kernel", "Software Engineer"),
    ("IDE", "Claude Code, Rider, VS Code"),
    None,
    ("Languages.Programming", "C#, Python, TypeScript, Go"),
    ("Languages.Data", "SQL, MongoDB, Snowflake"),
    ("Stack.Runtime", ".NET, gRPC, Kubernetes"),
    ("Stack.Messaging", "Kafka, RabbitMQ"),
    ("Stack.Observability", "Datadog, Sentry"),
]

THEMES = {
    "dark": dict(bg="#0d1117", fg="#c9d1d9", key="#ffa657", val="#a5d6ff", dots="#616e7f", add="#3fb950", rem="#f85149", head="#58a6ff"),
    "light": dict(bg="#f6f8fa", fg="#24292f", key="#953800", val="#0a3069", dots="#c2cfde", add="#1a7f37", rem="#cf222e", head="#0969da"),
}

WIDTH = 60  # characters in the info column


def api(path=None, query=None):
    url = "https://api.github.com/graphql" if query else f"https://api.github.com/{path}"
    data = json.dumps({"query": query}).encode() if query else None
    req = urllib.request.Request(url, data=data, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"bearer {TOKEN}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def fetch_stats():
    v = api(query="""{ viewer {
        repositories(ownerAffiliations: OWNER) { totalCount }
        repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST]) { totalCount }
        pullRequests { totalCount }
        followers { totalCount }
        contributionsCollection { contributionCalendar { totalContributions } }
    } }""")["data"]["viewer"]
    count = lambda q: api(f"search/{q}&per_page=1")["total_count"]
    return {
        "repos": v["repositories"]["totalCount"],
        "contributed": v["repositoriesContributedTo"]["totalCount"],
        "prs": v["pullRequests"]["totalCount"],
        "merged": count(f"issues?q=author:{USER}+type:pr+is:merged"),
        "reviews": count(f"issues?q=reviewed-by:{USER}+type:pr"),
        "commits": count(f"commits?q=author:{USER}"),
        "followers": v["followers"]["totalCount"],
        "year": v["contributionsCollection"]["contributionCalendar"]["totalContributions"],
    }


def uptime(start, today=None):
    today = today or dt.date.today()
    y, m, d = today.year - start.year, today.month - start.month, today.day - start.day
    if d < 0:
        m -= 1
        d += (today.replace(day=1) - dt.timedelta(days=1)).day
    if m < 0:
        y -= 1
        m += 12
    return f"{y} years, {m} months, {d} days"


def esc(s):
    return html.escape(s, quote=False)


def kv(key, value, width=WIDTH):
    """`Key: ....... value` padded to width, as tspans."""
    dots = max(width - len(key) - 2 - len(value) - 2, 1)
    return (f'<tspan class="key">{esc(key)}</tspan>:<tspan class="dots"> {"." * dots} </tspan>'
            f'<tspan class="val">{esc(value)}</tspan>')


def kv_pair(k1, v1, k2, v2):
    half = (WIDTH - 3) // 2
    return kv(k1, v1, half) + " | " + kv(k2, v2, WIDTH - half - 3)


def header(title):
    return f'<tspan class="head">— {esc(title)} </tspan><tspan class="dots">{"—" * (WIDTH - len(title) - 3)}</tspan>'


def build_lines(s):
    lines = [f'<tspan class="head">{USER}</tspan><tspan class="dots"> {"—" * (WIDTH - len(USER) - 1)}</tspan>']
    for item in PROFILE:
        if item is None:
            lines.append("")
            continue
        k, v = item
        lines.append(kv(k, v or uptime(ACCOUNT_CREATED)))
    lines += [
        "",
        header("Contact"),
        kv("GitHub", f"github.com/{USER}"),
        "",
        header("GitHub Stats"),
        kv_pair("Repos", f"{s['repos']} {{Contributed: {s['contributed']}}}", "Followers", f"{s['followers']:,}"),
        kv_pair("Commits", f"{s['commits']:,}", "Reviews", f"{s['reviews']:,}"),
        kv("Pull Requests", f"{s['prs']:,} ( {s['merged']:,} merged )"),
        kv("Contributions (last 12 months)", f"{s['year']:,}"),
    ]
    return lines


def render(theme, ascii_rows, info_lines):
    c = THEMES[theme]
    lh, fs = 20, 14
    rows = max(len(ascii_rows), len(info_lines))
    height = rows * lh + 60
    ascii_x, info_x = 20, 420
    out = [
        f'<?xml version="1.0" encoding="utf-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="985px" height="{height}px" font-size="{fs}px">',
        "<style>",
        "@font-face { src: local('Consolas'), local('Consolas Bold'); font-family: 'ConsolasFallback'; font-display: swap; -webkit-size-adjust: 109%; size-adjust: 109%; }",
        f".key {{fill: {c['key']};}} .val {{fill: {c['val']};}} .dots {{fill: {c['dots']};}} .head {{fill: {c['head']};}}",
        "text, tspan {white-space: pre;}",
        "</style>",
        f'<rect width="985px" height="{height}px" fill="{c["bg"]}" rx="15"/>',
    ]
    pad_top = 30 + (rows - len(ascii_rows)) * lh // 2
    out.append(f'<text x="{ascii_x}" y="{pad_top}" fill="{c["fg"]}" font-size="12px" class="ascii">')
    for i, row in enumerate(ascii_rows):
        out.append(f'<tspan x="{ascii_x}" y="{pad_top + i * lh}">{esc(row)}</tspan>')
    out.append("</text>")
    info_top = 30 + (rows - len(info_lines)) * lh // 2
    out.append(f'<text x="{info_x}" y="{info_top}" fill="{c["fg"]}">')
    for i, line in enumerate(info_lines):
        out.append(f'<tspan x="{info_x}" y="{info_top + i * lh}">{line}</tspan>')
    out.append("</text></svg>")
    return "\n".join(out) + "\n"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ascii_rows = open(os.path.join(here, "ascii.txt")).read().rstrip("\n").split("\n")
    info = build_lines(fetch_stats())
    for theme in THEMES:
        with open(os.path.join(here, f"{theme}_mode.svg"), "w") as f:
            f.write(render(theme, ascii_rows, info))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate self-hosted SVG assets for the kirawebdesigner profile README."""

from __future__ import annotations

import argparse
import json
import math
import os
import textwrap
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

ACCENT = "#2DA44E"
ACCENT_DARK = "#3FB950"
DARK_BG = "#0D1117"
DARK_PANEL = "#161B22"
DARK_TEXT = "#F0F6FC"
DARK_MUTED = "#8B949E"
LIGHT_BG = "#FFFFFF"
LIGHT_PANEL = "#F6F8FA"
LIGHT_TEXT = "#1F2328"
LIGHT_MUTED = "#59636E"
EXCLUDED_LANGUAGES = {"html", "css", "shell", "makefile", "dockerfile", "batchfile", "procfile"}


def api_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "kirawebdesigner-profile-generator/1.0"})
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"warning: could not fetch {url}: {exc}")
        return {}


def write_svg(path: Path, body: str, width: int, height: int) -> None:
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">\n{body}\n</svg>\n',
        encoding="utf-8",
    )


def theme(dark: bool) -> tuple[str, str, str, str]:
    return (DARK_BG, DARK_PANEL, DARK_TEXT, DARK_MUTED) if dark else (LIGHT_BG, LIGHT_PANEL, LIGHT_TEXT, LIGHT_MUTED)


def points_for(values: list[float], cx: float, cy: float, radius: float) -> str:
    result = []
    for index, value in enumerate(values):
        angle = -math.pi / 2 + (2 * math.pi * index / len(values))
        result.append(f"{cx + math.cos(angle) * radius * value:.1f},{cy + math.sin(angle) * radius * value:.1f}")
    return " ".join(result)


def generate_radar(data: dict, out_base: Path) -> None:
    axes = data.get("axes", [])
    if not axes:
        return
    labels = [str(axis.get("label", "Skill")) for axis in axes]
    values = [max(0.0, min(100.0, float(axis.get("value", 0))) / 100.0) for axis in axes]
    width, height, cx, cy, radius = 500, 410, 250, 225, 125
    for dark in (True, False):
        bg, panel, foreground, muted = theme(dark)
        lines = [f'<rect width="{width}" height="{height}" rx="18" fill="{bg}"/>', f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="17" fill="none" stroke="{ACCENT_DARK if dark else ACCENT}" stroke-opacity=".34"/>']
        lines.append(f'<text x="26" y="36" fill="{foreground}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="19" font-weight="700">{escape(str(data.get("title", "Skill Radar")))}</text>')
        lines.append(f'<text x="26" y="59" fill="{muted}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="12">{escape(str(data.get("subtitle", "A current, self-rated snapshot - 0-100")))}</text>')
        for level in (0.25, 0.5, 0.75, 1.0):
            lines.append(f'<polygon points="{points_for([level] * len(values), cx, cy, radius)}" fill="none" stroke="{muted}" stroke-opacity=".24"/>')
        for index, label in enumerate(labels):
            angle = -math.pi / 2 + (2 * math.pi * index / len(labels))
            x2 = cx + math.cos(angle) * radius
            y2 = cy + math.sin(angle) * radius
            lines.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{muted}" stroke-opacity=".24"/>')
            lx = cx + math.cos(angle) * (radius + 27)
            ly = cy + math.sin(angle) * (radius + 27)
            anchor = "middle" if abs(math.cos(angle)) < 0.35 else ("start" if math.cos(angle) > 0 else "end")
            lines.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" fill="{foreground}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="12">{escape(label)}</text>')
        lines.append(f'<polygon points="{points_for(values, cx, cy, radius)}" fill="{ACCENT_DARK if dark else ACCENT}" fill-opacity=".27" stroke="{ACCENT_DARK if dark else ACCENT}" stroke-width="2.5"/>')
        for index, value in enumerate(values):
            angle = -math.pi / 2 + (2 * math.pi * index / len(values))
            x = cx + math.cos(angle) * radius * value
            y = cy + math.sin(angle) * radius * value
            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{bg}" stroke="{ACCENT_DARK if dark else ACCENT}" stroke-width="2"/>')
            lx = cx + math.cos(angle) * (radius * value + 14)
            ly = cy + math.sin(angle) * (radius * value + 14)
            lines.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" fill="{ACCENT_DARK if dark else ACCENT}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="11" font-weight="700">{int(round(value*100))}</text>')
        write_svg(out_base.with_name(out_base.name + ("-dark.svg" if dark else "-light.svg")), "\n".join(lines), width, height)


def wrap_lines(value: str, width: int = 47, limit: int = 2) -> list[str]:
    lines = textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False) or [""]
    return lines[:limit]


def format_count(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def fetch_repositories(user: str) -> list[dict]:
    repos = api_json(f"https://api.github.com/users/{user}/repos?per_page=100&type=owner&sort=updated")
    return repos if isinstance(repos, list) else []


def fetch_language_bytes(user: str, repos: list[dict]) -> dict[str, int]:
    totals: defaultdict[str, int] = defaultdict(int)
    for repo in repos:
        name = repo.get("name")
        if not name or repo.get("fork"):
            continue
        languages = api_json(f"https://api.github.com/repos/{user}/{name}/languages")
        if isinstance(languages, dict):
            for language, amount in languages.items():
                if language.lower() not in EXCLUDED_LANGUAGES:
                    totals[language] += int(amount)
    return dict(totals)


def generate_language_radar(language_bytes: dict[str, int], out_base: Path) -> None:
    if not language_bytes:
        language_bytes = {"No data yet": 1}
    ranked = sorted(language_bytes.items(), key=lambda pair: pair[1], reverse=True)[:7]
    max_value = max(value for _, value in ranked) or 1
    curve = 0.4
    axes = [{"label": f"{language[:16]} {format_count(value)}", "value": round((value ** curve) / (max_value ** curve) * 100)} for language, value in ranked]
    generate_radar({"title": "Public language mix", "subtitle": "Aggregated public repository language bytes", "axes": axes}, out_base)


def generate_cards(user: str, projects: list[dict], repos_by_name: dict[str, dict], out_dir: Path) -> None:
    for project in projects[:4]:
        repo_name = project.get("repo", "")
        if not repo_name:
            continue
        meta = repos_by_name.get(repo_name, {})
        display_name = project.get("name") or meta.get("name") or repo_name
        description = project.get("description") or meta.get("description") or "A project built and maintained by Kirubel."
        language = meta.get("language") or "Project build"
        stars = int(meta.get("stargazers_count", 0) or 0)
        forks = int(meta.get("forks_count", 0) or 0)
        slug = repo_name.lower().replace("/", "-")
        for dark in (True, False):
            bg, panel, foreground, muted = theme(dark)
            accent = ACCENT_DARK if dark else ACCENT
            lines = [f'<rect width="440" height="180" rx="16" fill="{bg}"/>', f'<rect x="1" y="1" width="438" height="178" rx="15" fill="none" stroke="{accent}" stroke-opacity=".5"/>', f'<rect x="22" y="22" width="5" height="136" rx="2.5" fill="{accent}"/>', f'<text x="46" y="52" fill="{foreground}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="19" font-weight="700">{escape(str(display_name))}</text>']
            y = 83
            for line in wrap_lines(str(description)):
                lines.append(f'<text x="46" y="{y}" fill="{muted}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="13">{escape(line)}</text>')
                y += 20
            lines.extend([f'<rect x="46" y="126" width="112" height="25" rx="12.5" fill="{panel}" stroke="{muted}" stroke-opacity=".32"/>', f'<text x="102" y="143" text-anchor="middle" fill="{foreground}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="11">{escape(str(language))}</text>', f'<text x="46" y="169" fill="{muted}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="11">* {stars} stars   {forks} forks   github.com/{escape(user)}/{escape(repo_name)}</text>'])
            write_svg(out_dir / f"card-{slug}-{'dark' if dark else 'light'}.svg", "\n".join(lines), 440, 180)


def generate_stats(user: str, repos: list[dict], out_dir: Path) -> None:
    stars = sum(int(repo.get("stargazers_count", 0) or 0) for repo in repos)
    forks = sum(int(repo.get("forks_count", 0) or 0) for repo in repos)
    public_repos = len(repos)
    profile = api_json(f"https://api.github.com/users/{user}")
    followers = int(profile.get("followers", 0) or 0) if isinstance(profile, dict) else 0
    values = [("Public repos", public_repos), ("Stars", stars), ("Forks", forks), ("Followers", followers)]
    for dark in (True, False):
        bg, panel, foreground, muted = theme(dark)
        accent = ACCENT_DARK if dark else ACCENT
        lines = [f'<rect width="760" height="146" rx="16" fill="{bg}"/>', f'<rect x="1" y="1" width="758" height="144" rx="15" fill="none" stroke="{accent}" stroke-opacity=".45"/>', f'<text x="28" y="35" fill="{foreground}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="18" font-weight="700">GitHub snapshot - @{escape(user)}</text>', f'<text x="28" y="57" fill="{muted}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="12">Public profile metrics refreshed from GitHub</text>']
        for index, (label, value) in enumerate(values):
            x = 28 + index * 182
            lines.extend([f'<rect x="{x}" y="78" width="160" height="48" rx="10" fill="{panel}"/>', f'<text x="{x+14}" y="99" fill="{accent}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="18" font-weight="700">{format_count(value)}</text>', f'<text x="{x+14}" y="116" fill="{muted}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="11">{escape(label)}</text>'])
        write_svg(out_dir / f"github-stats-{'dark' if dark else 'light'}.svg", "\n".join(lines), 760, 146)


def generate_activity(user: str, out_dir: Path) -> None:
    events = api_json(f"https://api.github.com/users/{user}/events/public?per_page=100")
    events = events if isinstance(events, list) else []
    counts = Counter(str(event.get("type", "Other")).replace("Event", "") for event in events)
    ranked = counts.most_common(6) or [("No recent public events", 0)]
    max_count = max((count for _, count in ranked), default=1) or 1
    for dark in (True, False):
        bg, panel, foreground, muted = theme(dark)
        accent = ACCENT_DARK if dark else ACCENT
        lines = [f'<rect width="760" height="230" rx="16" fill="{bg}"/>', f'<rect x="1" y="1" width="758" height="228" rx="15" fill="none" stroke="{accent}" stroke-opacity=".45"/>', f'<text x="28" y="36" fill="{foreground}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="18" font-weight="700">Recent public activity</text>', f'<text x="28" y="58" fill="{muted}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="12">Event types in the latest public activity window</text>']
        for index, (label, count) in enumerate(ranked):
            y = 84 + index * 23
            bar_width = 520 * count / max_count if max_count else 0
            lines.extend([f'<text x="28" y="{y+12}" fill="{foreground}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="11">{escape(label[:24])}</text>', f'<rect x="190" y="{y}" width="520" height="14" rx="7" fill="{panel}"/>', f'<rect x="190" y="{y}" width="{bar_width:.1f}" height="14" rx="7" fill="{accent}" fill-opacity=".86"/>', f'<text x="724" y="{y+12}" text-anchor="end" fill="{muted}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="11">{count}</text>'])
        write_svg(out_dir / f"activity-{'dark' if dark else 'light'}.svg", "\n".join(lines), 760, 230)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", required=True)
    parser.add_argument("--data", type=Path, default=Path("assets/skills.json"))
    parser.add_argument("--projects", type=Path, default=Path("assets/projects.json"))
    parser.add_argument("--out", type=Path, default=Path("assets"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    skills = json.loads(args.data.read_text(encoding="utf-8"))
    project_config = json.loads(args.projects.read_text(encoding="utf-8"))
    repos = fetch_repositories(args.user)
    repos_by_name = {repo.get("name", ""): repo for repo in repos}
    generate_radar(skills, args.out / "radar")
    generate_language_radar(fetch_language_bytes(args.user, repos), args.out / "language-radar")
    generate_cards(args.user, project_config.get("projects", []), repos_by_name, args.out)
    generate_stats(args.user, repos, args.out)
    generate_activity(args.user, args.out)
    print(f"generated profile assets for {args.user}: {len(repos)} public repositories found")


if __name__ == "__main__":
    main()

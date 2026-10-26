"""Write a small weekly JSON summary. This does not call an AI or publish the site."""

import json
import sys
from datetime import datetime, timedelta

from collect_metrics import DATA, JST, MISSING, contains_secret


def snapshots():
    found = []
    cutoff = datetime.now(JST) - timedelta(days=7)
    for path in sorted(DATA.glob("snapshot-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            collected = datetime.fromisoformat(payload["collected_at"])
        except (OSError, json.JSONDecodeError, KeyError, ValueError):
            continue
        if collected.tzinfo is None:
            collected = collected.replace(tzinfo=JST)
        if collected >= cutoff:
            found.append(payload)
    return found


def numeric(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def sum_metric(rows, section, key):
    values = [numeric(row.get(section, {}).get(key)) for row in rows]
    if not values or any(item is None for item in values):
        return MISSING
    return sum(values)


def latest_downloads(rows):
    downloads = MISSING
    for row in rows:
        github = row.get("downloads", {}).get("github_exe")
        if isinstance(github, list):
            downloads = github
    if not isinstance(downloads, list):
        return {"github_exe": MISSING, "delta": MISSING, "site_clicks": MISSING}
    earliest = None
    for row in rows:
        github = row.get("downloads", {}).get("github_exe")
        if isinstance(github, list):
            earliest = github
            break
    delta = []
    for end in downloads:
        start = next((item for item in earliest if item.get("file") == end.get("file")), None)
        end_total = numeric(end.get("total"))
        start_total = numeric(start.get("total")) if start else None
        change = end_total - start_total if end_total is not None and start_total is not None and earliest is not downloads else MISSING
        if earliest is downloads:
            change = MISSING
        delta.append({"version": end.get("version"), "file": end.get("file"), "total": end.get("total", MISSING), "delta": change})
    return {"github_exe": delta, "site_clicks": MISSING}


def merge_queries(rows):
    merged = {}
    saw_list = False
    for row in rows:
        queries = row.get("search", {}).get("queries")
        if not isinstance(queries, list):
            continue
        saw_list = True
        for item in queries:
            key = item.get("query")
            clicks = numeric(item.get("clicks"))
            impressions = numeric(item.get("impressions"))
            if not key or clicks is None or impressions is None:
                continue
            current = merged.setdefault(key, {"query": key, "clicks": 0, "impressions": 0})
            current["clicks"] += clicks
            current["impressions"] += impressions
    if not saw_list:
        return MISSING
    ranked = sorted(merged.values(), key=lambda item: item["impressions"], reverse=True)
    return ranked[:25] or MISSING


def build():
    rows = snapshots()
    now = datetime.now(JST)
    summary = {
        "generated_at": now.isoformat(timespec="seconds"),
        "window_days": 7,
        "snapshots": len(rows),
        "ai": "not_run",
        "publish": "not_run",
        "search": {
            "clicks": sum_metric(rows, "search", "clicks"),
            "impressions": sum_metric(rows, "search", "impressions"),
            "ctr": MISSING,
            "position": MISSING,
            "queries": merge_queries(rows),
        },
        "traffic": {
            "visitors_sum_of_daily": sum_metric(rows, "traffic", "visitors"),
            "pageviews": sum_metric(rows, "traffic", "pageviews"),
            "referrers": MISSING,
        },
        "downloads": latest_downloads(rows),
    }
    clicks = numeric(summary["search"]["clicks"])
    impressions = numeric(summary["search"]["impressions"])
    if clicks is not None and impressions not in (None, 0):
        summary["search"]["ctr"] = clicks / impressions
    positions = []
    weights = []
    for row in rows:
        position = numeric(row.get("search", {}).get("position"))
        weight = numeric(row.get("search", {}).get("impressions"))
        if position is None or weight is None:
            positions = []
            break
        positions.append(position * weight)
        weights.append(weight)
    if positions and sum(weights) > 0:
        summary["search"]["position"] = sum(positions) / sum(weights)
    referrers = rows[-1].get("traffic", {}).get("referrers") if rows else MISSING
    summary["traffic"]["referrers"] = referrers if isinstance(referrers, list) else MISSING
    if contains_secret(summary):
        raise RuntimeError("summary refused")
    return summary


def main():
    summary = build()
    DATA.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(JST).strftime("%G-W%V")
    path = DATA / ("week-%s.json" % stamp)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("saved=%s" % path.name)
    print("snapshots=%s" % summary["snapshots"])
    print("ai=%s" % summary["ai"])
    print("publish=%s" % summary["publish"])
    try:
        with (DATA / "collector.log").open("a", encoding="utf-8") as handle:
            handle.write("week %s snapshots=%s ai=not_run publish=not_run\n" % (path.name, summary["snapshots"]))
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

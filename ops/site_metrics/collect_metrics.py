"""Collect OKAWARI Tools metrics into local JSON and SQLite.

Credentials are read only from %APPDATA%\\OKAWARI\\site-metrics\\ and are never
printed or stored with the metrics. A source that cannot be read is saved as
未取得. This script does not modify or publish the website.

Run:
  py -3 ops/site_metrics/collect_metrics.py
  py -3 ops/site_metrics/collect_metrics.py --self-test
"""

import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

MISSING = "未取得"
JST = timezone(timedelta(hours=9))
REPO = "mstyleworks1234-droid/OKAWARI-Tools"
ORIGIN = "https://okawari-tools.pages.dev"
SITEMAP = ORIGIN + "/sitemap.xml"
GSC_SITE = ORIGIN + "/"
ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parent / "data"
SECRETS = Path(os.environ.get("APPDATA", "")) / "OKAWARI" / "site-metrics"
USER_AGENT = "okawari-site-metrics/1"
def nth_sunday(year, month, n):
    first = datetime(year, month, 1, tzinfo=timezone.utc)
    offset = (6 - first.weekday()) % 7
    return first.day + offset + (n - 1) * 7


def pacific_zone(utc):
    """Search Console dates use US Pacific time, including daylight saving."""
    year = utc.year
    dst_start = datetime(year, 3, nth_sunday(year, 3, 2), 10, tzinfo=timezone.utc)
    dst_end = datetime(year, 11, nth_sunday(year, 11, 1), 9, tzinfo=timezone.utc)
    hours = -7 if dst_start <= utc < dst_end else -8
    return timezone(timedelta(hours=hours))


def pacific_now():
    utc = datetime.now(timezone.utc)
    return utc.astimezone(pacific_zone(utc))


SECRET_KEYS = {
    "refresh_token",
    "client_secret",
    "api_token",
    "access_token",
    "id_token",
    "authorization",
    "private_key",
}


class ApiError(Exception):
    def __init__(self, status, detail):
        self.status = status
        self.detail = detail
        super().__init__("http %s" % status)


def public_text(value):
    text = str(value).replace("\n", " ")
    lowered = text.lower()
    if "bearer " in lowered or "ya29." in lowered or "refresh_token" in lowered:
        return "redacted"
    return text[:240]


def contains_secret(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in SECRET_KEYS or contains_secret(item):
                return True
        return False
    if isinstance(value, list):
        return any(contains_secret(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return "bearer " in lowered or "ya29." in lowered or "refresh_token=" in lowered
    return False


def fetch(url, method="GET", headers=None, payload=None, timeout=30):
    data = None
    sent = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        sent.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        sent["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=sent, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def fetch_json(url, method="GET", headers=None, payload=None):
    status, body = fetch(url, method, headers, payload)
    if status < 200 or status >= 300:
        raise ApiError(status, public_text(body))
    if not body.strip():
        return {}
    return json.loads(body)


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def catalog_exes():
    text = (ROOT / "website" / "catalog.js").read_text(encoding="utf-8")
    names = re.findall(r'fileName:\s*"(QuickShot-[^"]+\.exe)"', text)
    versions = re.findall(r'version:\s*"(\d+\.\d+\.\d+)"', text)
    if not names or not versions or len(names) != len(versions):
        raise ValueError("catalog")
    return versions[0], versions[1:], names


def delta(current, previous):
    if isinstance(current, int) and isinstance(previous, int):
        return current - previous
    return MISSING


def previous_snapshot():
    files = sorted(DATA.glob("snapshot-*.json"))
    if not files:
        return None
    return load_json(files[-1])


def collect_github(previous):
    reason = "ボタンはGitHubのEXEへ直接リンクしており、サイト内のクリック計測はない"
    base = {
        "site_clicks": MISSING,
        "site_clicks_reason": reason,
        "github_status": MISSING,
        "github_exe": MISSING,
        "github_extension_zip": MISSING,
    }
    try:
        current, old_versions, names = catalog_exes()
    except (OSError, ValueError):
        base["github_status"] = "catalog_unreadable"
        return base
    previous_totals = {}
    if previous:
        prior = previous.get("downloads", {})
        prior_rows = []
        if isinstance(prior.get("github_exe"), list):
            prior_rows.extend(prior["github_exe"])
        if isinstance(prior.get("github_extension_zip"), list):
            prior_rows.extend(prior["github_extension_zip"])
        for item in prior_rows:
            if isinstance(item.get("total"), int):
                previous_totals[item.get("file")] = item["total"]
    try:
        payload = fetch_json(
            "https://api.github.com/repos/%s/releases?per_page=100" % REPO,
            headers={"Accept": "application/vnd.github+json"},
        )
    except (ApiError, json.JSONDecodeError, urllib.error.URLError, TimeoutError):
        base["github_status"] = "request_failed"
        base["current_version"] = current
        base["old_versions"] = len(old_versions)
        return base
    totals = {}
    extensions = []
    for release in payload:
        for asset in release.get("assets") or []:
            name = asset.get("name")
            count = asset.get("download_count")
            if not isinstance(name, str) or not isinstance(count, int):
                continue
            if name in names:
                totals[name] = count
            elif name.startswith("QuickShot-extension-") and name.endswith(".zip"):
                extensions.append({
                    "file": name,
                    "total": count,
                    "delta_since_previous_snapshot": delta(count, previous_totals.get(name)),
                })
    rows = []
    for version, name in zip([current] + old_versions, names):
        total = totals.get(name, MISSING)
        rows.append({
            "version": version,
            "file": name,
            "role": "current" if version == current else "old",
            "total": total,
            "delta_since_previous_snapshot": delta(total, previous_totals.get(name)),
        })
    base.update({
        "github_status": "ok",
        "current_version": current,
        "old_versions": len(old_versions),
        "matched_assets": sum(1 for row in rows if isinstance(row["total"], int)),
        "github_exe": rows,
        "github_extension_zip": extensions or MISSING,
    })
    return base


def gsc_files():
    client = load_json(SECRETS / "gsc-client.json")
    token = load_json(SECRETS / "gsc-token.json")
    installed = None
    if isinstance(client, dict):
        installed = client.get("installed") or client.get("web")
    if not isinstance(installed, dict) or not isinstance(token, dict):
        return None
    needed = ("client_id", "client_secret")
    if any(not installed.get(key) for key in needed) or not token.get("refresh_token"):
        return None
    return installed, token


def gsc_access_token(installed, token):
    body = urllib.parse.urlencode({
        "client_id": installed["client_id"],
        "client_secret": installed["client_secret"],
        "refresh_token": token["refresh_token"],
        "grant_type": "refresh_token",
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": USER_AGENT},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ApiError(exc.code, "token_refresh_failed")
    access = payload.get("access_token")
    if not isinstance(access, str) or not access:
        raise ApiError(0, "token_refresh_failed")
    return access


def gsc_query(access, start, end, dimensions):
    site = urllib.parse.quote(GSC_SITE, safe="")
    url = "https://www.googleapis.com/webmasters/v3/sites/%s/searchAnalytics/query" % site
    payload = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": dimensions,
        "rowLimit": 25,
        "dataState": "final",
    }
    return fetch_json(url, "POST", {"Authorization": "Bearer " + access}, payload)


def aggregate_search(rows):
    if not rows:
        return None
    clicks = 0.0
    impressions = 0.0
    weighted = 0.0
    for row in rows:
        click = row.get("clicks")
        impression = row.get("impressions")
        position = row.get("position")
        if not all(isinstance(item, (int, float)) for item in (click, impression, position)):
            return None
        clicks += click
        impressions += impression
        weighted += position * impression
    if impressions <= 0:
        return {"clicks": clicks, "impressions": impressions, "ctr": MISSING, "position": MISSING}
    return {
        "clicks": clicks,
        "impressions": impressions,
        "ctr": clicks / impressions,
        "position": weighted / impressions,
    }


def dimension_rows(rows, label):
    found = []
    for row in rows:
        keys = row.get("keys") or []
        if not keys:
            continue
        found.append({
            label: keys[0],
            "clicks": row.get("clicks", MISSING),
            "impressions": row.get("impressions", MISSING),
            "ctr": row.get("ctr", MISSING),
            "position": row.get("position", MISSING),
        })
    return found or MISSING


def empty_search(status):
    return {
        "status": status,
        "timezone": "America/Los_Angeles",
        "clicks": MISSING,
        "impressions": MISSING,
        "ctr": MISSING,
        "position": MISSING,
        "queries": MISSING,
        "pages": MISSING,
        "by_date": MISSING,
    }


def collect_search():
    files = gsc_files()
    if not files:
        return empty_search("credentials_missing")
    installed, token = files
    end = pacific_now().date() - timedelta(days=2)
    start = end - timedelta(days=6)
    try:
        access = gsc_access_token(installed, token)
        by_date = gsc_query(access, start, end, ["date"]).get("rows") or []
        queries = gsc_query(access, start, end, ["query"]).get("rows") or []
        pages = gsc_query(access, start, end, ["page"]).get("rows") or []
    except (ApiError, json.JSONDecodeError, urllib.error.URLError, TimeoutError, KeyError):
        result = empty_search("request_failed")
        result["start"] = start.isoformat()
        result["end"] = end.isoformat()
        return result
    totals = aggregate_search(by_date)
    result = empty_search("empty_response" if totals is None else "ok")
    result["start"] = start.isoformat()
    result["end"] = end.isoformat()
    if totals is None:
        return result
    result.update(totals)
    result["by_date"] = dimension_rows(by_date, "date")
    result["queries"] = dimension_rows(queries, "query")
    result["pages"] = dimension_rows(pages, "page")
    return result


def can_submit_sitemap(token):
    scopes = str(token.get("scope") or "").split()
    return "https://www.googleapis.com/auth/webmasters" in scopes


def submit_sitemap():
    files = gsc_files()
    if not files:
        return {"status": MISSING, "reason": "credentials_missing"}
    installed, token = files
    if not can_submit_sitemap(token):
        return {"status": MISSING, "reason": "write_scope_missing"}
    try:
        access = gsc_access_token(installed, token)
        site = urllib.parse.quote(GSC_SITE, safe="")
        feed = urllib.parse.quote(SITEMAP, safe="")
        url = "https://www.googleapis.com/webmasters/v3/sites/%s/sitemaps/%s" % (site, feed)
        status, _body = fetch(url, "PUT", {"Authorization": "Bearer " + access})
    except (urllib.error.URLError, TimeoutError):
        return {"status": MISSING, "reason": "request_failed"}
    if status in (200, 204):
        return {"status": "submitted", "sitemap": SITEMAP}
    return {"status": MISSING, "reason": "http_%s" % status}


def collect_traffic():
    result = {
        "status": "credentials_missing",
        "timezone": "Asia/Tokyo",
        "visitors": MISSING,
        "pageviews": MISSING,
        "referrers": MISSING,
    }
    config = load_json(SECRETS / "cloudflare.json")
    if not isinstance(config, dict):
        return result
    account = config.get("account_id")
    token = config.get("api_token")
    site_tag = config.get("site_tag")
    if not all(isinstance(item, str) and item.strip() for item in (account, token, site_tag)):
        result["status"] = "credentials_incomplete"
        return result
    day = datetime.now(JST).date() - timedelta(days=1)
    start = datetime(day.year, day.month, day.day, tzinfo=JST)
    end = start + timedelta(days=1)
    since = start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    until = end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    query = """
    query($accountTag: String!, $siteTag: String!, $since: Time!, $until: Time!) {
      viewer {
        accounts(filter: { accountTag: $accountTag }) {
          totals: rumPageloadEventsAdaptiveGroups(
            filter: { datetime_geq: $since, datetime_lt: $until, siteTag: $siteTag }
            limit: 1
          ) { count sum { visits } }
          referrers: rumPageloadEventsAdaptiveGroups(
            filter: { datetime_geq: $since, datetime_lt: $until, siteTag: $siteTag }
            limit: 20
            orderBy: [count_DESC]
          ) { count sum { visits } dimensions { metric: refererHost } }
        }
      }
    }
    """
    result["date"] = day.isoformat()
    try:
        payload = fetch_json(
            "https://api.cloudflare.com/client/v4/graphql",
            "POST",
            {"Authorization": "Bearer " + token},
            {
                "query": query,
                "variables": {
                    "accountTag": account,
                    "siteTag": site_tag,
                    "since": since,
                    "until": until,
                },
            },
        )
    except (ApiError, json.JSONDecodeError, urllib.error.URLError, TimeoutError):
        result["status"] = "request_failed"
        return result
    if payload.get("errors"):
        result["status"] = "request_failed"
        return result
    try:
        account_payload = payload["data"]["viewer"]["accounts"][0]
        totals = account_payload["totals"]
    except (KeyError, IndexError, TypeError):
        result["status"] = "empty_response"
        return result
    if not totals:
        result["status"] = "empty_response"
        return result
    visits = totals[0].get("sum", {}).get("visits")
    views = totals[0].get("count")
    referrers = []
    for row in account_payload.get("referrers") or []:
        host = (row.get("dimensions") or {}).get("metric")
        if host is None:
            continue
        referrers.append({
            "referrer": host,
            "pageviews": row.get("count", MISSING),
            "visits": (row.get("sum") or {}).get("visits", MISSING),
        })
    result.update({
        "status": "ok",
        "visitors": visits if isinstance(visits, (int, float)) else MISSING,
        "pageviews": views if isinstance(views, (int, float)) else MISSING,
        "referrers": referrers or MISSING,
    })
    return result


def probe_site():
    result = {
        "status": MISSING,
        "current_version": MISSING,
        "old_release_links": MISSING,
        "script_srcs": MISSING,
        "analytics_beacon": MISSING,
        "sitemap_urls": MISSING,
        "github_pages": MISSING,
    }
    try:
        expected_current, expected_old, expected_names = catalog_exes()
    except (OSError, ValueError):
        expected_current, expected_old, expected_names = None, [], []
    try:
        home_status, home = fetch(ORIGIN + "/")
        catalog_status, catalog = fetch(ORIGIN + "/catalog.js")
        sitemap_status, sitemap = fetch(SITEMAP)
        pages_status, _pages = fetch("https://api.github.com/repos/%s/pages" % REPO)
    except (urllib.error.URLError, TimeoutError):
        return result
    if home_status == 200:
        scripts = re.findall(r'<script[^>]*\ssrc="([^"]+)"', home)
        result["script_srcs"] = scripts
        result["analytics_beacon"] = "cloudflareinsights.com" in home or "cf-beacon" in home
    if catalog_status == 200:
        versions = re.findall(r'version:\s*"(\d+\.\d+\.\d+)"', catalog)
        hrefs = re.findall(r"releases/download/quickshot-\d+\.\d+\.\d+/", catalog)
        if versions:
            result["current_version"] = versions[0]
            result["old_release_links"] = max(0, len(versions) - 1)
        result["release_hrefs"] = len(hrefs)
    if sitemap_status == 200:
        result["sitemap_urls"] = len(re.findall(r"<loc>", sitemap))
    result["github_pages"] = "disabled" if pages_status == 404 else "http_%s" % pages_status
    expected = (
        result["current_version"] == expected_current
        and result["old_release_links"] == len(expected_old)
        and result.get("release_hrefs") == len(expected_names)
        and result["script_srcs"] == ["catalog.js", "app.js"]
        and result["analytics_beacon"] is False
        and result["sitemap_urls"] == 5
    )
    result["status"] = "ok" if expected else "mismatch"
    return result


def build_snapshot():
    previous = previous_snapshot()
    now = datetime.now(JST)
    return {
        "collected_at": now.isoformat(timespec="seconds"),
        "publish": "not_run",
        "ai": "not_run",
        "search": collect_search(),
        "sitemap": submit_sitemap(),
        "traffic": collect_traffic(),
        "downloads": collect_github(previous),
        "site_probe": probe_site(),
    }


def save_snapshot(snapshot):
    if contains_secret(snapshot):
        raise RuntimeError("snapshot refused")
    DATA.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(JST).strftime("%Y%m%dT%H%M%S")
    path = DATA / ("snapshot-%s.json" % stamp)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    database = DATA / "metrics.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS documents (collected_at TEXT PRIMARY KEY, body TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT OR REPLACE INTO documents (collected_at, body) VALUES (?, ?)",
            (snapshot["collected_at"], json.dumps(snapshot, ensure_ascii=False)),
        )
    return path


def write_log(lines):
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        with (DATA / "collector.log").open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    except OSError:
        return


def print_status(snapshot, path):
    search = snapshot["search"]
    traffic = snapshot["traffic"]
    downloads = snapshot["downloads"]
    probe = snapshot["site_probe"]
    print("saved=%s" % path.name)
    print("search=%s" % search.get("clicks"))
    print("impressions=%s" % search.get("impressions"))
    print("ctr=%s" % search.get("ctr"))
    print("position=%s" % search.get("position"))
    print("queries=%s" % ("list" if isinstance(search.get("queries"), list) else search.get("queries")))
    print("visitors=%s" % traffic.get("visitors"))
    print("pageviews=%s" % traffic.get("pageviews"))
    print("referrers=%s" % ("list" if isinstance(traffic.get("referrers"), list) else traffic.get("referrers")))
    print("site_clicks=%s" % downloads.get("site_clicks"))
    print("github_status=%s" % downloads.get("github_status"))
    print("live_version=%s" % probe.get("current_version"))
    print("live_old_releases=%s" % probe.get("old_release_links"))
    print("analytics_beacon=%s" % probe.get("analytics_beacon"))
    print("probe=%s" % probe.get("status"))
    write_log([
        snapshot["collected_at"],
        "saved=%s" % path.name,
        "search=%s" % search.get("clicks"),
        "visitors=%s" % traffic.get("visitors"),
        "site_clicks=%s" % downloads.get("site_clicks"),
        "github_status=%s" % downloads.get("github_status"),
        "probe=%s" % probe.get("status"),
    ])


def self_test():
    assert delta(5, None) == MISSING
    assert delta(5, 5) == 0
    assert delta(7, 5) == 2
    assert delta(MISSING, 1) == MISSING
    assert contains_secret({"note": "Bearer secret"})
    assert contains_secret({"refresh_token": "x"})
    assert not contains_secret({"search": {"clicks": MISSING, "queries": ["quickshot"]}})
    summer = datetime(2026, 7, 1, tzinfo=timezone.utc)
    winter = datetime(2026, 1, 15, tzinfo=timezone.utc)
    assert nth_sunday(2026, 3, 2) == 8
    assert nth_sunday(2026, 11, 1) == 1
    assert summer.astimezone(pacific_zone(summer)).utcoffset() == timedelta(hours=-7)
    assert winter.astimezone(pacific_zone(winter)).utcoffset() == timedelta(hours=-8)
    assert aggregate_search([]) is None
    totals = aggregate_search([
        {"clicks": 1, "impressions": 4, "position": 10},
        {"clicks": 1, "impressions": 6, "position": 5},
    ])
    assert totals["clicks"] == 2
    assert totals["impressions"] == 10
    assert totals["ctr"] == 0.2
    assert totals["position"] == 7
    missing = empty_search("credentials_missing")
    assert missing["clicks"] == MISSING and missing["queries"] == MISSING
    print("self-test ok")
    return 0


def main():
    if "--self-test" in sys.argv:
        return self_test()
    snapshot = build_snapshot()
    try:
        path = save_snapshot(snapshot)
    except RuntimeError:
        print("snapshot refused")
        return 1
    print_status(snapshot, path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

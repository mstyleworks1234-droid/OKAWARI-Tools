"""One-time Google Search Console authorization.

Place the Desktop OAuth client JSON at:
  %APPDATA%\\OKAWARI\\site-metrics\\gsc-client.json

The refresh token is written beside it as gsc-token.json. Nothing is printed
except whether the file was saved. This script does not deploy the website.
"""

import json
import os
import secrets
import sys
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SECRETS = Path(os.environ.get("APPDATA", "")) / "OKAWARI" / "site-metrics"
CLIENT = SECRETS / "gsc-client.json"
TOKEN = SECRETS / "gsc-token.json"
REDIRECT = "http://127.0.0.1:8765/"
SCOPE = "https://www.googleapis.com/auth/webmasters"


class Callback(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.result = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        body = "認証が完了しました。このタブを閉じてください。".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


def client_config():
    try:
        payload = json.loads(CLIENT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    config = payload.get("installed") or payload.get("web") if isinstance(payload, dict) else None
    if not isinstance(config, dict):
        return None
    if not config.get("client_id") or not config.get("client_secret"):
        return None
    return config


def main():
    config = client_config()
    if not config:
        print("gsc-client.json が %APPDATA%\\OKAWARI\\site-metrics\\ にありません。")
        print("Google Cloudで Search Console API を有効にし、デスクトップアプリのOAuthクライアントJSONをその場所へ保存してから、もう一度実行してください。")
        return 2
    state = secrets.token_urlsafe(24)
    query = urllib.parse.urlencode({
        "client_id": config["client_id"],
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    })
    try:
        server = HTTPServer(("127.0.0.1", 8765), Callback)
    except OSError:
        print("127.0.0.1:8765 を開けません。")
        return 2
    server.result = None
    server.timeout = 180
    webbrowser.open("https://accounts.google.com/o/oauth2/v2/auth?" + query)
    server.handle_request()
    server.server_close()
    result = server.result or {}
    if result.get("state", [""])[0] != state or "code" not in result:
        print("認証コードを受け取れませんでした。")
        return 2
    body = urllib.parse.urlencode({
        "code": result["code"][0],
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "redirect_uri": REDIRECT,
        "grant_type": "authorization_code",
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "okawari-site-metrics/1"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError:
        print("トークンの交換に失敗しました。")
        return 2
    refresh = payload.get("refresh_token")
    if not isinstance(refresh, str) or not refresh:
        print("更新トークンが返りませんでした。Googleアカウントのアプリ権限を取り消してから、もう一度実行してください。")
        return 2
    SECRETS.mkdir(parents=True, exist_ok=True)
    TOKEN.write_text(json.dumps({
        "refresh_token": refresh,
        "scope": payload.get("scope") or SCOPE,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("更新トークンをリポジトリの外へ保存しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

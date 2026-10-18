"""Local bridge between QuickShot and the browser extension.

The HTTP server listens on 127.0.0.1 only. A request is accepted only with the
token delivered through native messaging. Web origins are rejected.
"""

import json
import os
import shutil
import struct
import sys
import threading
import time
import urllib.error
import urllib.request
import winreg
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST_NAME = "com.okawari.quickshot"
EXTENSION_ID = "pkmnihodlggfbgdolpaajonjfgodahhh"
MAX_BODY = 60 * 1024 * 1024


def app_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, "OKAWARI", "QuickShot")
    os.makedirs(folder, exist_ok=True)
    return folder


def extension_source():
    here = os.path.dirname(os.path.abspath(__file__))
    bundled = os.path.join(getattr(sys, "_MEIPASS", here), "extension")
    if os.path.isdir(bundled):
        return bundled
    return os.path.join(here, "extension")


def install_extension_files():
    source = extension_source()
    target = os.path.join(app_dir(), "extension")
    os.makedirs(target, exist_ok=True)
    for name in ("manifest.json", "background.js"):
        shutil.copyfile(os.path.join(source, name), os.path.join(target, name))
    return target


def bridge_path():
    return os.path.join(app_dir(), "bridge.json")


def host_manifest_path():
    return os.path.join(app_dir(), f"{HOST_NAME}.json")


def native_host_command():
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "native_host.bat")


def register_native_host():
    path = native_host_command()
    manifest = {
        "name": HOST_NAME,
        "description": "QuickShot page capture",
        "path": path,
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{EXTENSION_ID}/"],
    }
    destination = host_manifest_path()
    with open(destination, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle)
    for key in (
        rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}",
        rf"Software\Microsoft\Edge\NativeMessagingHosts\{HOST_NAME}",
    ):
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as handle:
            winreg.SetValueEx(handle, "", 0, winreg.REG_SZ, destination)
    return destination


class Bridge:
    def __init__(self):
        self.token = ""
        self.port = 0
        self.command = None
        self.last_seen = 0.0
        self.inbox = []
        self.lock = threading.Lock()
        self.server = None

    def start(self):
        import secrets

        self.token = secrets.token_hex(16)
        install_extension_files()
        register_native_host()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.server.bridge = self
        self.port = self.server.server_address[1]
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        payload = {"port": self.port, "token": self.token}
        temp = bridge_path() + ".tmp"
        with open(temp, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        os.replace(temp, bridge_path())
        return install_extension_files()

    def connected(self):
        return time.time() - self.last_seen < 45

    def request_capture(self):
        with self.lock:
            self.command = {"type": "capture"}

    def take_messages(self):
        with self.lock:
            items = self.inbox
            self.inbox = []
        return items

    def stop(self):
        if self.server is not None:
            self.server.shutdown()
            self.server = None


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format, *_args):
        return

    def _authorized(self):
        origin = self.headers.get("Origin", "")
        if origin.startswith("http://") or origin.startswith("https://"):
            return False
        if origin.startswith("chrome-extension://") and origin != f"chrome-extension://{EXTENSION_ID}":
            return False
        header = self.headers.get("X-QuickShot-Token", "")
        return header == self.server.bridge.token

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length < 0 or length > 1024 * 1024:
            return {}
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _send(self, code, body=b"", content_type="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        if not self._authorized() or not self.path.startswith("/command"):
            self._send(403, b"{}")
            return
        bridge = self.server.bridge
        bridge.last_seen = time.time()
        deadline = time.time() + 20
        command = None
        while time.time() < deadline:
            with bridge.lock:
                if bridge.command is not None:
                    command = bridge.command
                    bridge.command = None
                    break
            time.sleep(0.1)
        if command is None:
            command = {"type": "idle"}
        self._send(200, json.dumps(command).encode("utf-8"))

    def do_POST(self):
        if not self._authorized():
            self._send(403, b"{}")
            return
        bridge = self.server.bridge
        bridge.last_seen = time.time()
        path = self.path.split("?", 1)[0]
        if path == "/hello":
            self._send(200, b"{}")
            return
        if path == "/event":
            message = self._read_json()
            with bridge.lock:
                bridge.inbox.append(message)
            self._send(200, b"{}")
            return
        if path == "/save":
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length < 8 or length > MAX_BODY:
                self._send(413, b"{}")
                return
            data = self.rfile.read(length)
            if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                self._send(400, b"{}")
                return
            with bridge.lock:
                bridge.inbox.append({"type": "png", "data": data})
            self._send(200, b"{}")
            return
        self._send(404, b"{}")


def _send_message(obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def _read_message():
    raw = sys.stdin.buffer.read(4)
    if len(raw) < 4:
        return None
    size = struct.unpack("<I", raw)[0]
    if size > 1024 * 1024:
        return None
    data = sys.stdin.buffer.read(size)
    if len(data) < size:
        return None
    return json.loads(data.decode("utf-8"))


def _request(info, method, path, body=None, content_type="application/json"):
    request = urllib.request.Request(
        f"http://127.0.0.1:{info['port']}{path}",
        data=body,
        method=method,
        headers={"X-QuickShot-Token": info["token"], "Content-Type": content_type},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _stdin_loop(info):
    while True:
        try:
            message = _read_message()
        except Exception:
            return
        if message is None:
            return
        try:
            _request(info, "POST", "/event", json.dumps(message).encode("utf-8"))
        except Exception:
            return


def run_native_host():
    try:
        with open(bridge_path(), encoding="utf-8") as handle:
            info = json.load(handle)
        _send_message({"type": "hello", "port": info["port"], "token": info["token"]})
        _request(info, "POST", "/hello", b"{}")
    except Exception:
        try:
            _send_message({"type": "error", "message": "QuickShot が起動していません。"})
        except Exception:
            pass
        return
    threading.Thread(target=_stdin_loop, args=(info,), daemon=True).start()
    while True:
        try:
            raw = _request(info, "GET", "/command")
            command = json.loads(raw.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return
        if command.get("type") == "capture":
            try:
                _send_message(command)
            except Exception:
                return


def stdio_is_pipe():
    import ctypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-10)
    if not handle or handle == ctypes.c_void_p(-1).value:
        return False
    return kernel32.GetFileType(handle) == 3

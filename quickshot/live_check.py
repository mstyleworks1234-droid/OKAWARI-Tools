"""Dedicated Edge check for QuickShot. Does not use the user's Chrome profile or cookies."""

import ctypes
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

import websocket

import imageutil

ROOT = os.path.dirname(os.path.abspath(__file__))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
EXT = r"D:\qs-live-ext"
PROFILE = r"D:\qs-live-profile"
READY = r"D:\qs-live-ready"
DEBUG = 19357
EXT_ID = "pkmnihodlggfbgdolpaajonjfgodahhh"
LOG = os.path.join(os.environ["APPDATA"], "OKAWARI", "QuickShot", "quickshot.log")
PICTURES = os.path.join(os.environ["USERPROFILE"], "Pictures", "QuickShot")


class Cdp:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=20, suppress_origin=True)
        self.n = 0

    def call(self, method, params=None, timeout=30):
        self.n += 1
        ident = self.n
        self.ws.settimeout(timeout)
        self.ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") != ident:
                continue
            if "error" in message:
                raise RuntimeError(str(message["error"]))
            return message.get("result")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def targets():
    with urllib.request.urlopen("http://127.0.0.1:%d/json" % DEBUG, timeout=5) as handle:
        return json.load(handle)


def wait_target(kind, needle, seconds=25):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            found = targets()
        except Exception:
            time.sleep(0.4)
            continue
        for item in found:
            if item.get("type") == kind and needle in item.get("url", "") and item.get("webSocketDebuggerUrl"):
                return item
        time.sleep(0.4)
    raise TimeoutError(kind)


def evaluate(cdp, expression, timeout=30, context_id=None):
    params = {
        "expression": expression,
        "awaitPromise": True,
        "returnByValue": True,
    }
    if context_id:
        params["contextId"] = context_id
    result = cdp.call("Runtime.evaluate", params, timeout=timeout)
    details = result.get("exceptionDetails")
    if details:
        exception = details.get("exception") or {}
        raise RuntimeError(exception.get("description") or details.get("text") or "evaluate failed")
    return (result.get("result") or {}).get("value")


def page_kind():
    return """(() => {
      const host = location.hostname;
      const parts = (location.pathname || "/").split("/").filter(Boolean);
      const known = host === "chatgpt.com" || host === "chat.openai.com";
      let kind = "other";
      if (!known) kind = "other";
      else if (!parts.length) kind = "home";
      else if (parts[0] === "c") kind = "conversation";
      else if (parts[0] === "g" && parts.indexOf("c") > 0) kind = "conversation";
      else if (parts[0] === "g") kind = "gpt";
      else kind = "site";
      return {known: known, kind: kind};
    })()"""


def scroll_probe():
    return """(() => {
      const nodes = document.querySelectorAll("div, main, section, article");
      let extra = 0;
      let top = 0;
      let height = 0;
      const count = Math.min(nodes.length, 4000);
      for (let index = 0; index < count; index += 1) {
        const el = nodes[index];
        const room = Math.max(0, (el.scrollHeight || 0) - (el.clientHeight || 0));
        if (room > extra && (el.clientHeight || 0) > 80) {
          extra = room;
          top = el.scrollTop || 0;
          height = el.clientHeight || 0;
        }
      }
      const root = document.scrollingElement || document.documentElement;
      return {
        top: Math.round(top),
        extra: Math.round(extra),
        height: Math.round(height),
        win: Math.round(window.scrollY || 0),
        doc: Math.round((root && root.scrollTop) || 0),
        viewW: window.innerWidth || 0,
        viewH: window.innerHeight || 0
      };
    })()"""


def nudge_scroll():
    return """(() => {
      const nodes = document.querySelectorAll("div, main, section, article");
      let best = null;
      let extra = 0;
      const count = Math.min(nodes.length, 4000);
      for (let index = 0; index < count; index += 1) {
        const el = nodes[index];
        const room = Math.max(0, (el.scrollHeight || 0) - (el.clientHeight || 0));
        if (room > extra && (el.clientHeight || 0) > 80) {
          extra = room;
          best = el;
        }
      }
      if (!best || extra < 500 || (best.scrollTop || 0) > 40) return 0;
      best.scrollTop = Math.min(480, extra - 20);
      return Math.round(best.scrollTop || 0);
    })()"""


def focus_conversation():
    return """(async () => {
      const tabs = await chrome.tabs.query({});
      for (const tab of tabs) {
        let conversation = false;
        try {
          const parsed = new URL(tab.url || "");
          const known = parsed.hostname === "chatgpt.com" || parsed.hostname === "chat.openai.com";
          const parts = parsed.pathname.split("/").filter(Boolean);
          conversation = known && (parts[0] === "c" || (parts[0] === "g" && parts.indexOf("c") > 0));
        } catch (_error) {
          conversation = false;
        }
        if (!conversation || tab.id == null) continue;
        await chrome.tabs.update(tab.id, {active: true});
        return true;
      }
      return false;
    })()"""


def conversation_target():
    for item in targets():
        if item.get("type") != "page" or not item.get("webSocketDebuggerUrl"):
            continue
        url = item.get("url") or ""
        if "chatgpt.com" not in url and "chat.openai.com" not in url:
            continue
        page = Cdp(item["webSocketDebuggerUrl"])
        try:
            kind = evaluate(page, page_kind())
        except Exception:
            page.close()
            continue
        if kind and kind.get("kind") == "conversation":
            return page, kind
        page.close()
    return None, None


def log_since(offset):
    if not os.path.exists(LOG):
        return []
    with open(LOG, encoding="utf-8", errors="replace") as handle:
        handle.seek(offset)
        return [line.strip() for line in handle if line.strip()]


def interesting(lines):
    kept = []
    for line in lines:
        if "chat detect " in line or "page armed " in line or "page saved " in line or "page error " in line or "page done " in line:
            kept.append(line)
    return kept


def png_names():
    if not os.path.isdir(PICTURES):
        return set()
    return {name for name in os.listdir(PICTURES) if name.lower().endswith(".png")}


def _samples(buf, width, height, stride, box, step):
    x0, y0, x1, y1 = box
    found = []
    y = y0
    while y < y1:
        row = y * stride
        x = x0
        while x < x1:
            pos = row + x * 3
            if 0 <= pos + 2 < len(buf):
                found.append((buf[pos], buf[pos + 1], buf[pos + 2]))
            x += step
        y += step
    return found


def _summary(samples):
    count = len(samples)
    if not count:
        return {"n": 0, "mean": 0, "var": 0}
    values = [((item[2] * 299) + (item[1] * 587) + (item[0] * 114)) // 1000 for item in samples]
    mean = sum(values) // count
    var = sum((value - mean) * (value - mean) for value in values) // count
    return {"n": count, "mean": mean, "var": var}


def inspect_png(path, view_w):
    imageutil.startup()
    image = imageutil._load(path)
    try:
        width, height = imageutil._size(image)
        rect = imageutil._Rect(0, 0, width, height)
        data = imageutil._BitmapData()
        imageutil._check(
            imageutil.gdiplus.GdipBitmapLockBits(
                image, ctypes.byref(rect), 1, imageutil.PixelFormat24bppRGB, ctypes.byref(data)
            ),
            "lock",
        )
        try:
            stride = int(data.Stride)
            if stride < 0 or not data.Scan0:
                return {"file": os.path.basename(path), "width": width, "height": height, "readable": False}
            buf = ctypes.string_at(data.Scan0, stride * height)
        finally:
            imageutil.gdiplus.GdipBitmapUnlockBits(image, ctypes.byref(data))
    finally:
        imageutil._dispose(image)
    band = max(8, width // 25)
    left = _summary(_samples(buf, width, height, stride, (0, height // 10, band, height - height // 10), 4))
    right = _summary(_samples(buf, width, height, stride, (width - band, height // 10, width, height - height // 10), 4))
    mid = _summary(_samples(buf, width, height, stride, (width * 3 // 10, height // 4, width * 7 // 10, height * 3 // 4), 6))
    bottom_top = max(0, height - max(24, height // 12))
    bottom = _summary(_samples(buf, width, height, stride, (width // 8, bottom_top, width * 7 // 8, height - 2), 4))
    flags = []
    if mid["var"] < 40:
        flags.append("blank")
    if view_w and width >= view_w - 40:
        flags.append("full-window")
    if left["var"] < 250 and mid["var"] > 80 and abs(left["mean"] - mid["mean"]) >= 28:
        flags.append("sidebar-band")
    if left["var"] > 500:
        flags.append("left-edge-busy")
    if right["var"] > 500:
        flags.append("right-edge-busy")
    if bottom["var"] < 150 and abs(bottom["mean"] - mid["mean"]) > 22:
        flags.append("bottom-band")
    return {
        "file": os.path.basename(path),
        "width": width,
        "height": height,
        "readable": True,
        "left": left,
        "right": right,
        "mid": mid,
        "bottom": bottom,
        "flags": flags,
    }


def close_browser(edge):
    try:
        for item in targets():
            if item.get("type") == "browser" and item.get("webSocketDebuggerUrl"):
                browser = Cdp(item["webSocketDebuggerUrl"])
                try:
                    browser.call("Browser.close", timeout=5)
                finally:
                    browser.close()
                break
        edge.wait(timeout=8)
        return
    except Exception:
        pass
    subprocess.call(["taskkill", "/PID", str(edge.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def load_unpacked():
    version = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json/version" % DEBUG, timeout=5))
    browser = Cdp(version["webSocketDebuggerUrl"])
    try:
        browser.call("Extensions.loadUnpacked", {"path": EXT})
    finally:
        browser.close()


def worker_context(cdp):
    cdp.call("Runtime.enable")
    cdp.ws.settimeout(2)
    for _ in range(8):
        try:
            message = json.loads(cdp.ws.recv())
        except Exception:
            break
        if message.get("method") == "Runtime.executionContextCreated":
            return message.get("params", {}).get("context", {}).get("id") or 1
    return 1


def port_open():
    try:
        targets()
        return True
    except Exception:
        return False


def main():
    login = "--login" in sys.argv
    attached = port_open()
    edge = None
    if attached:
        print("LIVE attach %d" % DEBUG, flush=True)
    else:
        if os.path.isdir(EXT):
            shutil.rmtree(EXT)
        shutil.copytree(os.path.join(ROOT, "extension"), EXT)
        os.makedirs(PROFILE, exist_ok=True)
        command = [
            EDGE,
            "--user-data-dir=" + PROFILE,
            "--load-extension=" + EXT,
            "--disable-extensions-except=" + EXT,
            "--remote-debugging-port=%d" % DEBUG,
            "--remote-allow-origins=*",
            "--enable-unsafe-extension-debugging",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=CalculateNativeWinOcclusion,DisableLoadExtensionCommandLineSwitch",
            "--window-size=1280,900",
            "--window-position=40,40",
        ]
        if login or not os.path.exists(READY):
            command.append("https://chatgpt.com/")
        else:
            command.append("--restore-last-session")
        edge = subprocess.Popen(command)
        print("LIVE ready %d" % edge.pid, flush=True)
    try:
        load_unpacked()
    except Exception:
        pass
    report = {"edge": edge.pid if edge is not None else 0, "attached": attached}
    keep_open = True
    worker = None
    page = None
    try:
        item = wait_target("service_worker", EXT_ID)
        worker = Cdp(item["webSocketDebuggerUrl"])
        context_id = worker_context(worker)
        deadline = time.time() + 20
        connected = None
        while time.time() < deadline:
            try:
                connected = evaluate(
                    worker,
                    "({port: !!(config && config.port), version: chrome.runtime.getManifest().version})",
                    context_id=context_id,
                )
            except RuntimeError:
                time.sleep(0.4)
                continue
            if connected and connected.get("port"):
                break
            time.sleep(0.4)
        report["extension"] = connected
        print("LIVE extension %s" % json.dumps(connected, ensure_ascii=False), flush=True)
        print("LIVE waiting", flush=True)
        deadline = None if login else time.time() + 40
        kind = None
        while deadline is None or time.time() < deadline:
            try:
                page, kind = conversation_target()
            except Exception:
                page, kind = None, None
            if page is not None:
                break
            time.sleep(2)
        report["page"] = kind or {"kind": "none"}
        if page is None:
            report["capture"] = "paused-not-a-conversation"
            report["resume"] = "py -3 live_check.py --login"
            print(json.dumps(report, ensure_ascii=False))
            return
        keep_open = False
        with open(READY, "w", encoding="ascii") as handle:
            handle.write("conversation\n")
        print("LIVE conversation", flush=True)
        try:
            evaluate(worker, "1", context_id=context_id)
        except Exception:
            try:
                worker.close()
            except Exception:
                pass
            item = wait_target("service_worker", EXT_ID)
            worker = Cdp(item["webSocketDebuggerUrl"])
            context_id = worker_context(worker)
        try:
            page.call("Page.bringToFront")
        except Exception:
            pass
        try:
            evaluate(worker, focus_conversation(), context_id=context_id)
        except Exception:
            pass
        time.sleep(0.4)
        before_scroll = evaluate(page, scroll_probe())
        nudged = evaluate(page, nudge_scroll())
        if nudged:
            time.sleep(0.3)
            before_scroll = evaluate(page, scroll_probe())
        report["scrollBefore"] = before_scroll
        report["nudged"] = nudged or 0
        log_at = os.path.getsize(LOG) if os.path.exists(LOG) else 0
        existing = png_names()
        evaluate(worker, "post({type:'diag', event:'live-arm', mode:'chat'}); 'sent'", context_id=context_id)
        armed = False
        arm_deadline = time.time() + 6
        while time.time() < arm_deadline:
            if any("page armed chat" in line for line in log_since(log_at)):
                armed = True
                break
            time.sleep(0.2)
        report["armed"] = armed
        try:
            evaluate(worker, "captureActivePage('chat')", timeout=150, context_id=context_id)
            report["capture"] = "returned"
        except Exception as error:
            report["capture"] = str(error).splitlines()[0][:180]
        seen = []
        end = time.time() + 20
        while time.time() < end:
            seen = interesting(log_since(log_at))
            if any("page saved " in line or "page error " in line or "chat detect " in line for line in seen):
                if any("page done " in line or "page error " in line or "chat detect " in line for line in seen):
                    break
            time.sleep(0.4)
        report["log"] = seen[-12:]
        time.sleep(0.6)
        try:
            report["scrollAfter"] = evaluate(page, scroll_probe())
        except Exception:
            report["scrollAfter"] = None
        before = report.get("scrollBefore") or {}
        after = report.get("scrollAfter") or {}
        if before and after and "top" in before and "top" in after:
            report["scrollRestored"] = abs(int(before.get("top") or 0) - int(after.get("top") or 0)) <= 8
        else:
            report["scrollRestored"] = False
        created = []
        for name in sorted(png_names() - existing):
            if name.startswith("QuickShot-chat-") or name.startswith("QuickShot-page-"):
                created.append(os.path.join(PICTURES, name))
        view_w = int((before or {}).get("viewW") or 0)
        report["images"] = [inspect_png(path, view_w) for path in created]
        print(json.dumps(report, ensure_ascii=False))
    finally:
        if worker:
            worker.close()
        if page:
            page.close()
        if not keep_open and edge is not None:
            close_browser(edge)
        elif keep_open:
            print("LIVE browser-left-open", flush=True)


if __name__ == "__main__":
    main()

const HOST = "com.okawari.quickshot";
const MAX_CSS_HEIGHT = 20000;
let config = null;
let port = null;

function connect() {
  if (port) return;
  try {
    port = chrome.runtime.connectNative(HOST);
  } catch (error) {
    port = null;
    return;
  }
  port.onMessage.addListener((message) => {
    if (!message || typeof message !== "object") return;
    if (message.type === "hello") {
      config = message;
      return;
    }
    if (message.type === "capture") {
      captureActivePage().catch((error) => {
        post({type: "error", message: error && error.message ? error.message : "ページ全体の撮影に失敗しました"});
      });
    }
  });
  port.onDisconnect.addListener(() => {
    port = null;
    setTimeout(connect, 1500);
  });
}

function post(message) {
  if (port) {
    try {
      port.postMessage(message);
    } catch (_error) {
      /* QuickShot shows the failure if the result never arrives. */
    }
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function runInPage(tabId, func, args) {
  const results = await chrome.scripting.executeScript({
    target: {tabId},
    func,
    args: args || [],
  });
  return results && results[0] ? results[0].result : null;
}

async function captureActivePage() {
  if (!config || !config.port || !config.token) {
    throw new Error("QuickShot との接続がまだありません。QuickShot を起動してから拡張機能を読み込み直してください。");
  }
  const tabs = await chrome.tabs.query({active: true, lastFocusedWindow: true});
  const tab = tabs && tabs[0];
  if (!tab || tab.id == null) {
    throw new Error("表示中のページが見つかりません。");
  }
  if (!/^https?:\/\//i.test(tab.url || "")) {
    throw new Error("Chrome または Edge で http または https のページを開いてください。");
  }
  const metrics = await runInPage(tab.id, () => {
    const root = document.scrollingElement || document.documentElement;
    return {
      y: window.scrollY || 0,
      height: Math.max(root.scrollHeight || 0, window.innerHeight || 0),
      view: window.innerHeight || 1,
      width: window.innerWidth || 1,
    };
  });
  if (!metrics || !metrics.view) {
    throw new Error("ページのサイズを取得できませんでした。");
  }
  const limit = Math.min(metrics.height, MAX_CSS_HEIGHT);
  const truncated = metrics.height > MAX_CSS_HEIGHT;
  try {
    await runInPage(tab.id, () => {
      const hidden = [];
      const nodes = document.body ? document.body.querySelectorAll("*") : [];
      const maxNodes = Math.min(nodes.length, 4000);
      for (let index = 0; index < maxNodes; index += 1) {
        const el = nodes[index];
        const position = getComputedStyle(el).position;
        if (position === "fixed" || position === "sticky") {
          hidden.push([el, el.style.visibility]);
          el.style.visibility = "hidden";
        }
      }
      window.__quickshotHidden = hidden;
    });
    const shots = [];
    const tops = [];
    let y = 0;
    for (let step = 0; step < 40; step += 1) {
      const top = Math.max(0, Math.min(y, limit - metrics.view));
      await runInPage(tab.id, (pos) => window.scrollTo(0, pos), [top]);
      await delay(220);
      post({type: "progress", text: `撮影中 ${step + 1}`});
      const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, {format: "png"});
      const bitmap = await createImageBitmap(await (await fetch(dataUrl)).blob());
      shots.push(bitmap);
      tops.push(top);
      if (top + metrics.view >= limit - 1) break;
      y = top + Math.max(1, metrics.view - 48);
    }
    const scale = shots[0].height / metrics.view;
    const canvas = new OffscreenCanvas(shots[0].width, Math.max(1, Math.ceil(limit * scale)));
    const context = canvas.getContext("2d");
    shots.forEach((bitmap, index) => {
      context.drawImage(bitmap, 0, Math.round(tops[index] * scale));
      bitmap.close();
    });
    const bytes = new Uint8Array(await (await canvas.convertToBlob({type: "image/png"})).arrayBuffer());
    const response = await fetch(`http://127.0.0.1:${config.port}/save`, {
      method: "POST",
      headers: {"X-QuickShot-Token": config.token, "Content-Type": "application/octet-stream"},
      body: bytes,
    });
    if (!response.ok) throw new Error("画像の受け渡しに失敗しました。");
    post({type: "done", truncated});
  } finally {
    try {
      await runInPage(tab.id, (pos) => {
        const hidden = window.__quickshotHidden || [];
        hidden.forEach(([el, visibility]) => {
          el.style.visibility = visibility;
        });
        window.scrollTo(0, pos);
      }, [metrics.y]);
    } catch (_error) {
      /* The page may have closed during capture. */
    }
  }
}

connect();

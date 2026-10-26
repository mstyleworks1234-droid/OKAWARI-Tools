const HOST = "com.okawari.quickshot";
let config = null;
let port = null;

function connect() {
  if (port) return;
  try {
    port = chrome.runtime.connectNative(HOST);
  } catch (error) {
    port = null;
    setTimeout(connect, 1500);
    return;
  }
  port.onMessage.addListener((message) => {
    if (!message || typeof message !== "object") return;
    if (message.type === "hello") {
      config = message;
      post({type: "diag", event: "host-connected", version: chrome.runtime.getManifest().version});
      reportTab("hello", true);
      return;
    }
    if (message.type === "report") {
      reportTab("menu", true);
      return;
    }
    if (message.type === "capture") {
      post({type: "status", stage: "accepted", mode: message.mode === "chat" ? "chat" : "page"});
      captureActivePage(message.mode === "chat" ? "chat" : "page").catch((error) => {
        post({
          type: "error",
          message: error && error.message ? error.message : "ページ全体の撮影に失敗しました",
          saved: error && error.saved ? error.saved : 0,
        });
      });
    }
  });
  port.onDisconnect.addListener(() => {
    void chrome.runtime.lastError;
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

function withTimeout(promise, ms) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("capture-timeout")), ms);
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        clearTimeout(timer);
        reject(error);
      }
    );
  });
}

async function runInPage(tabId, func, args) {
  const results = await withTimeout(chrome.scripting.executeScript({
    target: {tabId},
    func,
    args: args || [],
  }), 8000);
  return results && results[0] ? results[0].result : null;
}

function tabLocation(tab) {
  const current = tab && tab.url || "";
  const pending = tab && tab.pendingUrl || "";
  if (/^https?:\/\//i.test(current)) return current;
  if (/^https?:\/\//i.test(pending)) return pending;
  return current || pending;
}

function classifyPage(url) {
  try {
    const parsed = new URL(url || "");
    const name = parsed.hostname;
    if (name !== "chatgpt.com" && name !== "chat.openai.com") {
      return {chat: false, host: name ? "other" : "", path: ""};
    }
    const parts = parsed.pathname.split("/").filter(Boolean);
    let path = "/other";
    if (!parts.length) path = "/";
    else if (parts[0] === "c") path = "/c";
    else if (parts[0] === "g" && parts.indexOf("c") > 0) path = "/g/c";
    else if (parts[0] === "g") path = "/g";
    return {chat: true, host: name, path: path};
  } catch (_error) {
    return {chat: false, host: "", path: ""};
  }
}

function isChatUrl(url) {
  return classifyPage(url).chat;
}

async function captureActivePage(mode) {
  if (!config || !config.port || !config.token) {
    throw new Error("QuickShot との接続がまだありません。QuickShot を起動してから拡張機能を読み込み直してください。");
  }
  const tabs = await chrome.tabs.query({active: true, lastFocusedWindow: true});
  const tab = tabs && tabs[0];
  const pageUrl = tabLocation(tab);
  if (!tab || tab.id == null) {
    throw new Error("表示中のページが見つかりません。");
  }
  if (!/^https?:\/\//i.test(pageUrl)) {
    throw new Error("Chrome または Edge で http または https のページを開いてください。");
  }
  let granted = false;
  try {
    granted = await chrome.permissions.contains({origins: ["<all_urls>"]});
  } catch (_error) {
    granted = true;
  }
  if (!granted) {
    post({type: "status", stage: "permission"});
    throw new Error("Either the '<all_urls>' or 'activeTab' permission is required.");
  }
  const chat = mode === "chat";
  if (chat && !isChatUrl(pageUrl)) {
    throw new Error("ChatGPTのページを前面にしてから、もう一度選んでください。");
  }
  post({type: "status", stage: "capturing"});
  let picked = null;
  const tries = chat ? 4 : 1;
  for (let attempt = 0; attempt < tries; attempt += 1) {
    try {
      picked = await runInPage(tab.id, (wantChat) => {
    function extra(el) {
      if (!el) return 0;
      return Math.max(0, (el.scrollHeight || 0) - (el.clientHeight || 0));
    }
    function visible(el) {
      const rect = el.getBoundingClientRect();
      if (rect.width < 120 || rect.height < 120) return false;
      const shown = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
      return shown > 80 && rect.right > 0 && rect.left < window.innerWidth;
    }
    function largest() {
      let best = null;
      let bestExtra = 0;
      const nodes = document.querySelectorAll("div, main, section, article, ul, ol");
      const count = Math.min(nodes.length, 6000);
      for (let index = 0; index < count; index += 1) {
        const el = nodes[index];
        const overflow = getComputedStyle(el).overflowY;
        if (overflow !== "auto" && overflow !== "scroll" && overflow !== "overlay") continue;
        if (!visible(el)) continue;
        const amount = extra(el);
        if (amount > bestExtra) {
          best = el;
          bestExtra = amount;
        }
      }
      return {el: best, extra: bestExtra};
    }
    function conversationScroller() {
      const selector = [
        "[data-message-author-role]",
        "[data-message-id]",
        "[data-testid^='conversation-turn']",
        "[data-turn-id-container]",
        "[data-turn-key]",
        "article[data-turn]",
        "section[data-turn]",
      ].join(",");
      const hits = [];
      const probe = {
        top: window === window.top ? 1 : 0,
        roots: 0,
        nodes: 0,
        mains: 0,
        articles: 0,
        logs: 0,
        role: 0,
        msgid: 0,
        turntest: 0,
        turnid: 0,
        turnarticle: 0,
        turnsection: 0,
        dataturn: 0,
        testid: 0,
        frames: 0,
        frameopen: 0,
        frameblocked: 0,
        framenodes: 0,
        shadows: 0,
        capped: 0,
      };
      try {
        probe.nodes = document.querySelectorAll("*").length;
      } catch (_error) {
        probe.nodes = 0;
      }
      function tally(rootNode, spec) {
        try {
          return rootNode.querySelectorAll(spec).length;
        } catch (_error) {
          return 0;
        }
      }
      const visit = (rootNode) => {
        if (!rootNode || !rootNode.querySelectorAll || hits.length > 2000) return;
        probe.roots += 1;
        probe.mains += tally(rootNode, "main");
        probe.articles += tally(rootNode, "article");
        probe.logs += tally(rootNode, "[role='log']");
        probe.role += tally(rootNode, "[data-message-author-role]");
        probe.msgid += tally(rootNode, "[data-message-id]");
        probe.turntest += tally(rootNode, "[data-testid^='conversation-turn']");
        probe.turnid += tally(rootNode, "[data-turn-id-container]");
        probe.turnarticle += tally(rootNode, "article[data-turn]");
        probe.turnsection += tally(rootNode, "section[data-turn]");
        probe.dataturn += tally(rootNode, "[data-turn]");
        probe.testid += tally(rootNode, "[data-testid]");
        rootNode.querySelectorAll(selector).forEach((el) => hits.push(el));
        const nodes = rootNode.querySelectorAll("*");
        const limit = Math.min(nodes.length, 12000);
        if (nodes.length > limit) probe.capped = 1;
        for (let index = 0; index < limit; index += 1) {
          if (nodes[index].shadowRoot) {
            probe.shadows += 1;
            visit(nodes[index].shadowRoot);
          }
        }
        rootNode.querySelectorAll("iframe, frame").forEach((frame) => {
          probe.frames += 1;
          let child = null;
          try {
            child = frame.contentDocument;
          } catch (_error) {
            child = null;
          }
          if (!child) {
            probe.frameblocked += 1;
            return;
          }
          probe.frameopen += 1;
          try {
            probe.framenodes += child.querySelectorAll("*").length;
          } catch (_error) {
            probe.frameopen -= 1;
            probe.frameblocked += 1;
            return;
          }
          visit(child);
        });
      };
      visit(document);
      let navCount = 0;
      let smallCount = 0;
      const messages = [];
      const seen = new Set();
      function visibleAnchor(el) {
        let node = el;
        for (let depth = 0; node && depth < 6; depth += 1) {
          const rect = node.getBoundingClientRect();
          if (rect.width >= 80 && rect.height >= 12) return true;
          const owner = node.getRootNode && node.getRootNode();
          node = node.parentElement || (owner && owner.host) || null;
        }
        return false;
      }
      hits.forEach((el) => {
        if (!el || el.nodeType !== 1 || seen.has(el)) return;
        seen.add(el);
        if (el.closest && el.closest("nav")) {
          navCount += 1;
          return;
        }
        if (!visibleAnchor(el)) {
          smallCount += 1;
          return;
        }
        messages.push(el);
      });
      const census = {
        raw: seen.size,
        small: smallCount,
        nav: navCount,
        frames: probe.frames,
        shadows: probe.shadows,
        capped: probe.capped,
        top: probe.top,
        roots: probe.roots,
        nodes: probe.nodes,
        mains: probe.mains,
        articles: probe.articles,
        logs: probe.logs,
        role: probe.role,
        msgid: probe.msgid,
        turntest: probe.turntest,
        turnid: probe.turnid,
        turnarticle: probe.turnarticle,
        turnsection: probe.turnsection,
        dataturn: probe.dataturn,
        testid: probe.testid,
        frameopen: probe.frameopen,
        frameblocked: probe.frameblocked,
        framenodes: probe.framenodes,
      };
      const empty = {
        el: null,
        stage: seen.size ? "filtered" : "no-messages",
        messages: 0,
        candidates: 0,
        width: 0,
        height: 0,
        ...census,
      };
      if (!messages.length) return empty;
      function parentOf(node) {
        if (node.parentElement) return node.parentElement;
        const owner = node.getRootNode && node.getRootNode();
        return owner && owner.host ? owner.host : null;
      }
      function sidebar(el) {
        const rect = el.getBoundingClientRect();
        return rect.width < window.innerWidth * 0.34 && rect.right < window.innerWidth * 0.42;
      }
      function composer(el) {
        const rect = el.getBoundingClientRect();
        return rect.top > window.innerHeight * 0.72 && rect.height < 220 && rect.height > 0;
      }
      function usable(el) {
        if (!el || el === document.body || el === document.documentElement) return false;
        const rect = el.getBoundingClientRect();
        if (rect.width < 240 || rect.height < 80 || sidebar(el) || composer(el)) return false;
        const flow = getComputedStyle(el).overflowY;
        const marked = el.hasAttribute("data-scroll-root") || el.id === "thread";
        const scrolls = flow === "auto" || flow === "scroll" || flow === "overlay" || marked || extra(el) > 24;
        return scrolls || messages.every((item) => el.contains(item));
      }
      const score = new Map();
      messages.forEach((el) => {
        let node = el;
        for (let guard = 0; node && guard < 30; guard += 1) {
          if (usable(node)) {
            const contained = messages.filter((item) => node.contains(item)).length;
            const prev = score.get(node);
            if (!prev || contained > prev.count) {
              score.set(node, {count: contained, extra: extra(node)});
            }
          }
          node = parentOf(node);
        }
      });
      function scrolls(el) {
        const flow = getComputedStyle(el).overflowY;
        return flow === "auto" || flow === "scroll" || flow === "overlay"
          || el.hasAttribute("data-scroll-root") || el.id === "thread" || extra(el) > 24;
      }
      let chosen = null;
      let bestCount = 0;
      let bestWidth = 0;
      let bestScroll = false;
      score.forEach((info, el) => {
        const width = el.getBoundingClientRect().width;
        const does = scrolls(el);
        const betterCount = info.count > bestCount;
        const betterScroll = info.count === bestCount && does && !bestScroll;
        const tighter = info.count === bestCount && does === bestScroll && chosen && width < bestWidth;
        if (betterCount || betterScroll || tighter) {
          chosen = el;
          bestCount = info.count;
          bestWidth = width;
          bestScroll = does;
        }
      });
      if (!chosen) {
        return {el: null, stage: "no-scroller", messages: messages.length, candidates: 0, width: 0, height: 0, ...census};
      }
      const rect = chosen.getBoundingClientRect();
      return {
        el: chosen,
        stage: "found",
        messages: messages.length,
        candidates: score.size,
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        ...census,
      };
    }
    const root = document.scrollingElement || document.documentElement;
    let target = null;
    let detect = {stage: "found", messages: 0, candidates: 0, width: 0, height: 0};
    if (wantChat) {
      detect = conversationScroller();
      target = detect.el;
      if (!target) {
        return {
          ok: false,
          stage: detect.stage,
          messages: detect.messages,
          candidates: detect.candidates,
          width: detect.width,
          height: detect.height,
          raw: detect.raw || 0,
          small: detect.small || 0,
          nav: detect.nav || 0,
          frames: detect.frames || 0,
          shadows: detect.shadows || 0,
          capped: detect.capped || 0,
          top: detect.top || 0,
          roots: detect.roots || 0,
          nodes: detect.nodes || 0,
          mains: detect.mains || 0,
          articles: detect.articles || 0,
          logs: detect.logs || 0,
          role: detect.role || 0,
          msgid: detect.msgid || 0,
          turntest: detect.turntest || 0,
          turnid: detect.turnid || 0,
          turnarticle: detect.turnarticle || 0,
          turnsection: detect.turnsection || 0,
          dataturn: detect.dataturn || 0,
          testid: detect.testid || 0,
          frameopen: detect.frameopen || 0,
          frameblocked: detect.frameblocked || 0,
          framenodes: detect.framenodes || 0,
        };
      }
    } else {
      const found = largest();
      const rootExtra = Math.max(extra(root), extra(document.documentElement), extra(document.body));
      target = rootExtra >= found.extra ? root : (found.el || root);
    }
    window.__qsTarget = target;
    window.__qsChat = !!wantChat;
    window.__qsOrigin = null;
    const el = window.__qsTarget;
    const windowMode = el === root || el === document.documentElement || el === document.body;
    window.__qsOrigin = windowMode ? (window.scrollY || 0) : (el.scrollTop || 0);
    window.__qsOriginHeight = el.scrollHeight || 0;
    window.__qsPrepended = 0;
    const box = target && target.getBoundingClientRect ? target.getBoundingClientRect() : null;
    return {
      ok: true,
      stage: wantChat ? "found" : "page",
      messages: detect.messages || 0,
      candidates: detect.candidates || 0,
      width: box ? Math.round(box.width) : 0,
      height: box ? Math.round(box.height) : 0,
      raw: detect.raw || 0,
      small: detect.small || 0,
      nav: detect.nav || 0,
      frames: detect.frames || 0,
      shadows: detect.shadows || 0,
      capped: detect.capped || 0,
    };
  }, [chat]);
    } catch (error) {
      if (chat) {
        post({type: "diag", event: "chat-detect", stage: "inject", messages: 0, candidates: 0, width: 0, height: 0});
      }
      throw error;
    }
    if (!chat || (picked && picked.ok) || !picked || picked.stage !== "no-messages") break;
    await delay(400);
  }
  if (chat && picked) {
    post({
      type: "diag",
      event: "chat-detect",
      stage: picked.stage || "no-messages",
      messages: picked.messages || 0,
      candidates: picked.candidates || 0,
      width: picked.width || 0,
      height: picked.height || 0,
      raw: picked.raw || 0,
      small: picked.small || 0,
      nav: picked.nav || 0,
      frames: picked.frames || 0,
      shadows: picked.shadows || 0,
      capped: picked.capped || 0,
      top: picked.top || 0,
      roots: picked.roots || 0,
      nodes: picked.nodes || 0,
      mains: picked.mains || 0,
      articles: picked.articles || 0,
      logs: picked.logs || 0,
      role: picked.role || 0,
      msgid: picked.msgid || 0,
      turntest: picked.turntest || 0,
      turnid: picked.turnid || 0,
      turnarticle: picked.turnarticle || 0,
      turnsection: picked.turnsection || 0,
      dataturn: picked.dataturn || 0,
      testid: picked.testid || 0,
      frameopen: picked.frameopen || 0,
      frameblocked: picked.frameblocked || 0,
      framenodes: picked.framenodes || 0,
    });
  }
  if (chat && picked && picked.ok === false) {
    throw new Error("会話本文の領域を特定できませんでした。通常のページ全体撮影は使えます。");
  }
  if (!picked || !picked.ok) throw new Error("ページのサイズを取得できませんでした。");

  async function readMetrics() {
    return runInPage(tab.id, () => {
      const el = window.__qsTarget || document.scrollingElement || document.documentElement;
      const root = document.scrollingElement || document.documentElement;
      const windowMode = el === root || el === document.documentElement || el === document.body;
      const doc = document.documentElement;
      const box = windowMode ? null : el.getBoundingClientRect();
      let frameX = 0;
      let frameY = 0;
      let frameView = el.ownerDocument && el.ownerDocument.defaultView;
      for (let guard = 0; !windowMode && frameView && frameView.frameElement && guard < 4; guard += 1) {
        const frame = frameView.frameElement.getBoundingClientRect();
        frameX += frame.left;
        frameY += frame.top;
        frameView = frameView.frameElement.ownerDocument.defaultView;
      }
      const view = Math.max(1, windowMode ? (doc.clientHeight || window.innerHeight || 1) : (el.clientHeight || 1));
      const rect = windowMode
        ? {x: 0, y: 0, w: doc.clientWidth || window.innerWidth || 1, h: view}
        : {x: box.x + el.clientLeft + frameX, y: box.y + el.clientTop + frameY, w: el.clientWidth || 1, h: el.clientHeight || 1};
      let barX = 0;
      let barY = 0;
      if (!window.__qsBarHidden) {
        if (windowMode) {
          barX = Math.max(0, (window.innerWidth || 0) - (doc.clientWidth || 0));
          barY = Math.max(0, (window.innerHeight || 0) - (doc.clientHeight || 0));
        } else {
          barX = Math.max(0, el.offsetWidth - el.clientWidth - el.clientLeft * 2);
          barY = Math.max(0, el.offsetHeight - el.clientHeight - el.clientTop * 2);
        }
      }
      return {
        y: windowMode ? (window.scrollY || 0) : (el.scrollTop || 0),
        height: el.scrollHeight || 0,
        view,
        winW: window.innerWidth || 1,
        winH: window.innerHeight || 1,
        rect,
        barX: Math.min(40, barX),
        barY: Math.min(40, barY),
      };
    });
  }

  async function scrollTo(pos) {
    return runInPage(tab.id, (target) => {
      const el = window.__qsTarget || document.scrollingElement || document.documentElement;
      const root = document.scrollingElement || document.documentElement;
      if (el === root || el === document.documentElement || el === document.body) {
        window.scrollTo(0, target);
        return window.scrollY || 0;
      }
      el.scrollTop = target;
      return el.scrollTop || 0;
    }, [pos]);
  }

  let partsSaved = 0;
  try {
    let lastHeight = 0;
    let stable = 0;
    let grew = 0;
    const started = Date.now();
    while (grew < 8 && Date.now() - started < 10000) {
      await scrollTo(48);
      await scrollTo(0);
      await delay(400);
      let sample = await readMetrics();
      if (!sample || !sample.view) throw new Error("ページのサイズを取得できませんでした。");
      if (sample.y > 80) {
        await scrollTo(0);
        await delay(400);
        sample = await readMetrics();
      }
      if (sample.height <= lastHeight + 4) {
        stable += 1;
        if (stable >= 2) break;
      } else {
        stable = 0;
        lastHeight = sample.height;
        grew += 1;
      }
    }
    await runInPage(tab.id, () => {
      const el = window.__qsTarget || document.scrollingElement || document.documentElement;
      const now = el.scrollHeight || 0;
      window.__qsPrepended = Math.max(0, now - (window.__qsOriginHeight || now));
    });
    const topPartial = stable < 2;
    await runInPage(tab.id, () => {
      const target = window.__qsTarget || document.scrollingElement || document.documentElement;
      const beforeW = target.clientWidth || 0;
      const beforeH = target.clientHeight || 0;
      const style = document.createElement("style");
      style.setAttribute("data-qs", "bar");
      style.textContent = "html,body,*{scrollbar-width:none !important}*{scrollbar-color:transparent transparent !important}*::-webkit-scrollbar{width:0 !important;height:0 !important}";
      document.documentElement.appendChild(style);
      const shifted = Math.abs((target.clientWidth || 0) - beforeW) > 1 || Math.abs((target.clientHeight || 0) - beforeH) > 1;
      if (shifted) style.remove();
      window.__qsBarStyle = shifted ? null : style;
      window.__qsBarHidden = !shifted;
      const saved = [];
      const headers = [];
      const footers = [];
      const nodes = [];
      const scan = (root) => {
        if (!root || !root.querySelectorAll || nodes.length > 4000) return;
        const found = root.querySelectorAll("*");
        const count = Math.min(found.length, 4000 - nodes.length);
        for (let index = 0; index < count; index += 1) nodes.push(found[index]);
      };
      scan(document.body || document.documentElement);
      for (let index = 0; index < Math.min(nodes.length, 800); index += 1) {
        if (nodes[index].shadowRoot) scan(nodes[index].shadowRoot);
      }
      const hide = (el) => {
        saved.push([el, el.style.visibility]);
        el.style.visibility = "hidden";
      };
      for (let index = 0; index < nodes.length; index += 1) {
        const el = nodes[index];
        if (el === target || (target.contains && target.contains(el) === false && el.contains && el.contains(target))) continue;
        if (el.contains && el.contains(target)) continue;
        const position = getComputedStyle(el).position;
        if (position !== "fixed" && position !== "sticky") continue;
        const rect = el.getBoundingClientRect();
        if (rect.width < 8 || rect.height < 8 || rect.bottom < 0 || rect.top > window.innerHeight) continue;
        const wide = rect.width >= window.innerWidth * 0.45;
        const header = rect.top <= 6 && rect.height <= 240 && wide;
        const footer = rect.bottom >= window.innerHeight - 64 && rect.height <= 240 && wide && rect.top > window.innerHeight * 0.5;
        if (header) headers.push(el);
        else if (footer) {
          footers.push(el);
          hide(el);
        } else hide(el);
      }
      if (window.__qsChat && target && target.querySelectorAll) {
        target.querySelectorAll("button, [role='button']").forEach((el) => {
          const position = getComputedStyle(el).position;
          if (position === "fixed" || position === "sticky") hide(el);
        });
        const fields = document.querySelectorAll("textarea, [contenteditable='true']");
        const composers = [];
        fields.forEach((field) => {
          const form = field.closest ? (field.closest("form") || field) : field;
          const formRect = form.getBoundingClientRect();
          const fieldRect = field.getBoundingClientRect();
          const box = formRect.height > 320 ? fieldRect : formRect;
          const node = formRect.height > 320 ? field : form;
          if (box.top > window.innerHeight * 0.55 && box.width > 160 && box.height > 24 && box.height < 320) {
            hide(node);
            composers.push(node);
          }
        });
        window.__qsComposer = composers;
      }
      window.__qsHeaders = headers;
      window.__qsFooters = footers;
      window.__qsHidden = saved;
    });
    const MAX_PART_HEIGHT = 16384;
    const MAX_PART_PIXELS = 24000000;
    const MAX_PARTS = 24;
    let y = 0;
    let previous = -1;
    let pageHeight = lastHeight;
    let reached = false;
    let capped = false;
    let covered = null;
    let partSlices = [];
    let partH = 0;
    let partWidth = 0;

    function limitFor(width) {
      return Math.min(MAX_PART_HEIGHT, Math.floor(MAX_PART_PIXELS / Math.max(1, width)));
    }

    async function flushPart(keep) {
      if (!partSlices.length || partH < 2 || !partWidth) return;
      const canvas = new OffscreenCanvas(partWidth, partH);
      const context = canvas.getContext("2d");
      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, partWidth, partH);
      const crops = new Set();
      partSlices.forEach((slice) => {
        context.drawImage(
          slice.crop, 0, slice.srcY, slice.crop.width, slice.srcH,
          0, slice.destY, partWidth, slice.srcH
        );
        crops.add(slice.crop);
      });
      partSlices = [];
      partH = 0;
      const bytes = new Uint8Array(await (await canvas.convertToBlob({type: "image/png"})).arrayBuffer());
      const response = await fetch(`http://127.0.0.1:${config.port}/save`, {
        method: "POST",
        headers: {
          "X-QuickShot-Token": config.token,
          "Content-Type": "application/octet-stream",
          "X-QuickShot-Part": String(partsSaved + 1),
        },
        body: bytes,
      });
      if (!response.ok) {
        const failed = new Error("画像の受け渡しに失敗しました。");
        failed.saved = partsSaved;
        throw failed;
      }
      partsSaved += 1;
      crops.forEach((crop) => {
        if (crop === keep) return;
        try {
          crop.close();
        } catch (_error) {
          /* This frame was already released. */
        }
      });
    }

    async function pushSlice(crop, srcY, srcH) {
      let originY = srcY;
      let left = srcH;
      while (left >= 2) {
        let room = limitFor(partWidth) - partH;
        if (room < 2) {
          await flushPart(crop);
          if (partsSaved >= MAX_PARTS) {
            try {
              crop.close();
            } catch (_error) {
              /* Already released with the saved part. */
            }
            return false;
          }
          room = limitFor(partWidth) - partH;
        }
        const take = Math.min(left, room);
        if (take < 2) return false;
        partSlices.push({crop, srcY: originY, srcH: take, destY: partH});
        partH += take;
        originY += take;
        left -= take;
      }
      return true;
    }

    for (let step = 0; step < 240; step += 1) {
      const sampleBefore = await readMetrics();
      pageHeight = sampleBefore.height;
      const requested = Math.max(0, Math.min(y, Math.max(0, pageHeight - 1)));
      await scrollTo(requested);
      await delay(180);
      let metrics = await readMetrics();
      if (Math.abs(metrics.y - requested) > 40) {
        await delay(320);
        metrics = await readMetrics();
      }
      pageHeight = metrics.height;
      const stuck = step > 0 && metrics.y <= previous + 1;
      if (stuck && metrics.y + metrics.view < pageHeight - 64) {
        reached = false;
        break;
      }
      previous = metrics.y;
      const atEnd = (metrics.y + metrics.view) >= pageHeight - 64;
      await runInPage(tab.id, (showFooter, hideHeader) => {
        const saved = window.__qsHidden || [];
        if (hideHeader) {
          (window.__qsHeaders || []).forEach((el) => {
            if (saved.some((item) => item[0] === el)) return;
            saved.push([el, el.style.visibility]);
            el.style.visibility = "hidden";
          });
        }
        (window.__qsFooters || []).forEach((el) => {
          if ((window.__qsComposer || []).indexOf(el) >= 0) {
            el.style.visibility = "hidden";
            return;
          }
          const known = saved.find((item) => item[0] === el);
          if (showFooter) {
            if (known) el.style.visibility = known[1];
          } else if (!known) {
            saved.push([el, el.style.visibility]);
            el.style.visibility = "hidden";
          } else el.style.visibility = "hidden";
        });
        window.__qsHidden = saved;
      }, [atEnd, step > 0]);
      await delay(520);
      post({type: "progress", text: `撮影中 ${step + 1}`});
      let dataUrl = null;
      for (let attempt = 0; attempt < 3; attempt += 1) {
        try {
          dataUrl = await withTimeout(
            chrome.tabs.captureVisibleTab(tab.windowId, {format: "png"}),
            8000
          );
          break;
        } catch (error) {
          const message = error && error.message ? error.message : "";
          const quota = message.includes("MAX_CAPTURE_VISIBLE_TAB");
          const readback = /readback|Failed to capture tab/i.test(message);
          if ((!quota && !readback) || attempt === 2) throw error;
          try {
            await chrome.windows.update(tab.windowId, {focused: true, state: "normal"});
          } catch (_focus) {
            /* Focusing the window needs the windows permission. Capture still retries. */
          }
          await delay(1000);
        }
      }
      const bitmap = await createImageBitmap(await (await fetch(dataUrl)).blob());
      const scaleX = bitmap.width / metrics.winW;
      const scaleY = bitmap.height / metrics.winH;
      let sx = 0;
      let sy = 0;
      let sw = bitmap.width;
      let sh = bitmap.height;
      if (metrics.rect) {
        sx = Math.max(0, Math.round(metrics.rect.x * scaleX));
        sy = Math.max(0, Math.round(metrics.rect.y * scaleY));
        sw = Math.min(bitmap.width - sx, Math.round(metrics.rect.w * scaleX));
        sh = Math.min(bitmap.height - sy, Math.round(metrics.rect.h * scaleY));
      }
      const crop = new OffscreenCanvas(Math.max(1, sw), Math.max(1, sh));
      crop.getContext("2d").drawImage(bitmap, sx, sy, sw, sh, 0, 0, sw, sh);
      bitmap.close();
      if (!partWidth) {
        partWidth = crop.width;
        if (partWidth < 1 || partWidth > 8192 || limitFor(partWidth) < 256) {
          crop.close();
          throw new Error("画面が広すぎて1枚に保存できません");
        }
      }
      if (covered === null) covered = metrics.y;
      const cropScale = crop.height / Math.max(1, metrics.view);
      const skip = Math.max(0, covered - metrics.y);
      const srcY = Math.min(crop.height, Math.round(skip * cropScale));
      const srcH = crop.height - srcY;
      let placed = true;
      if (srcH >= 2) placed = await pushSlice(crop, srcY, srcH);
      else {
        try {
          crop.close();
        } catch (_error) {
          /* Nothing new was visible in this frame. */
        }
      }
      if (!placed) {
        capped = true;
        reached = false;
        break;
      }
      covered = metrics.y + metrics.view;
      const end = covered;
      if (partsSaved >= MAX_PARTS && partH < 2) {
        capped = true;
        reached = false;
        break;
      }
      if (end >= pageHeight - 3 || (stuck && atEnd)) {
        reached = end >= pageHeight - 64;
        break;
      }
      y = metrics.y + Math.max(1, metrics.view - 64);
    }
    await flushPart(null);
    if (!partsSaved) throw new Error("ページ全体の撮影に失敗しました。");
    let partial = "";
    if (topPartial) partial = "top";
    else if (!reached || capped) partial = "bottom";
    post({
      type: "done",
      truncated: capped,
      partial,
      parts: partsSaved,
      mode: chat ? "chat" : "page",
    });
  } catch (error) {
    if (error && typeof error === "object") error.saved = error.saved || partsSaved;
    throw error;
  } finally {
    try {
      await runInPage(tab.id, () => {
        const hidden = window.__qsHidden || [];
        hidden.forEach(([el, visibility]) => {
          el.style.visibility = visibility;
        });
        if (window.__qsBarStyle && window.__qsBarStyle.remove) window.__qsBarStyle.remove();
        window.__qsBarStyle = null;
        window.__qsBarHidden = false;
        window.__qsHeaders = null;
        window.__qsFooters = null;
        window.__qsComposer = null;
        const el = window.__qsTarget;
        const root = document.scrollingElement || document.documentElement;
        const pos = (window.__qsOrigin || 0) + (window.__qsPrepended || 0);
        if (!el || el === root || el === document.documentElement || el === document.body) window.scrollTo(0, pos);
        else el.scrollTop = pos;
        window.__qsHidden = null;
        window.__qsTarget = null;
        window.__qsOrigin = null;
        window.__qsOriginHeight = null;
        window.__qsPrepended = null;
        window.__qsChat = false;
      });
    } catch (_error) {
      /* The page may have closed during capture. */
    }
  }
}

let lastTabKey = "";
let browserTag = "";

function newTag() {
  let tag = "";
  while (tag.length < 8) tag += Math.random().toString(16).slice(2);
  return tag.slice(0, 8);
}

async function ownTag() {
  if (browserTag) return browserTag;
  try {
    const stored = await chrome.storage.session.get("qsTag");
    if (stored && typeof stored.qsTag === "string" && /^[0-9a-f]{8}$/.test(stored.qsTag)) {
      browserTag = stored.qsTag;
      return browserTag;
    }
    browserTag = newTag();
    await chrome.storage.session.set({qsTag: browserTag});
  } catch (_error) {
    browserTag = browserTag || newTag();
  }
  return browserTag;
}

async function reportTab(reason, force) {
  try {
    const tabs = await chrome.tabs.query({active: true, lastFocusedWindow: true});
    const info = classifyPage(tabLocation(tabs && tabs[0]));
    const key = [info.chat ? "1" : "0", info.host, info.path].join("|");
    if (!force && key === lastTabKey) return;
    lastTabKey = key;
    post({
      type: "tab",
      chat: info.chat,
      host: info.host,
      path: info.path,
      tag: await ownTag(),
      version: chrome.runtime.getManifest().version,
      reason: reason || "event",
    });
  } catch (_error) {
    post({type: "diag", event: "tab-query-failed"});
  }
}

chrome.tabs.onActivated.addListener(() => reportTab("event"));
chrome.tabs.onUpdated.addListener((_id, info) => {
  if (info.url || info.status === "complete") reportTab("event");
});
chrome.tabs.onRemoved.addListener(() => reportTab("event"));
connect();
reportTab("event");

import { createIcon, fileVisual } from "./arhub-icons.js";

const EDITOR_ROUTE = /^\/workflow\/([^/]+)\/editor\/?$/;
const state = {
  scheduled: false,
  contextOpen: false,
  // The studio keeps navigation out of the reading path until the user asks for it.
  filesCollapsed: true,
  focusMode: false,
  lastFile: "",
  filesBeforeContext: false,
  autoCompactContext: false,
  mobileFilesOpen: false,
};

function isEditorRoute() {
  return EDITOR_ROUTE.test(window.location.pathname);
}

function editorParts() {
  const shell = document.querySelector(".mw-editor-shell");
  if (!(shell instanceof HTMLElement)) return null;
  const files = shell.querySelector(":scope > .mw-files-panel");
  const agent = shell.querySelector(":scope > .mw-agent-panel");
  const workbench = shell.querySelector(":scope > .mw-workbench");
  const header = agent?.querySelector(":scope > .mw-agent-header");
  const thread = agent?.querySelector(":scope > .mw-agent-thread");
  if (!(files instanceof HTMLElement) || !(agent instanceof HTMLElement)) return null;
  if (!(workbench instanceof HTMLElement) || !(header instanceof HTMLElement)) return null;
  return { shell, files, agent, workbench, header, thread };
}

function iconButton(icon, label, className) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `arhub-codex-editor-button ${className}`;
  button.title = label;
  button.setAttribute("aria-label", label);
  button.append(createIcon(icon, { size: 17 }));
  return button;
}

function normalizeFileName(value) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  const matched = text.match(
    /(?:[\w\u3400-\u9fff.@()+-]+[\\/])*[\w\u3400-\u9fff.@()+-]+\.(?:md|markdown|tex|py|json|ya?ml|toml|csv|tsv|docx|xlsx|pptx|pdf|png|jpe?g|webp|gif|svg|drawio|html?|css|jsx?|tsx?|txt|bib|ris)/i,
  );
  return (matched?.[0] || text).slice(0, 160);
}

function shouldCompactForContext() {
  const query = window.matchMedia?.("(max-width: 1360px)");
  return query ? query.matches : window.innerWidth <= 1360;
}

function setContext(open, fileName = "") {
  const parts = editorParts();
  if (!parts) return;
  const nextOpen = Boolean(open);
  if (nextOpen && !state.contextOpen) {
    state.filesBeforeContext = state.filesCollapsed;
    // A selected file is the context, so the file browser should never remain a
    // third permanent column beside the Agent and the preview.
    state.autoCompactContext = !state.filesCollapsed;
    if (state.autoCompactContext) state.filesCollapsed = true;
    state.mobileFilesOpen = false;
  }
  if (!nextOpen && state.contextOpen && state.autoCompactContext) {
    state.filesCollapsed = state.filesBeforeContext;
    state.autoCompactContext = false;
  }
  state.contextOpen = nextOpen;
  if (fileName) state.lastFile = normalizeFileName(fileName);
  parts.shell.dataset.arhubCodexContext = state.contextOpen ? "open" : "closed";
  parts.shell.dataset.arhubCodexFiles = state.filesCollapsed ? "collapsed" : "expanded";
  parts.shell.dataset.arhubCodexMobileFiles = state.mobileFilesOpen ? "open" : "closed";
  parts.workbench.setAttribute("aria-hidden", String(!state.contextOpen));
  syncChrome(parts);
}

function setFilesCollapsed(collapsed) {
  const parts = editorParts();
  if (!parts) return;
  state.filesCollapsed = Boolean(collapsed);
  parts.shell.dataset.arhubCodexFiles = state.filesCollapsed ? "collapsed" : "expanded";
  syncChrome(parts);
}

function setMobileFilesOpen(open) {
  const parts = editorParts();
  if (!parts) return;
  state.mobileFilesOpen = Boolean(open);
  parts.shell.dataset.arhubCodexMobileFiles = state.mobileFilesOpen ? "open" : "closed";
  syncChrome(parts);
}

function setFocusMode(enabled) {
  const parts = editorParts();
  if (!parts) return;
  state.focusMode = Boolean(enabled);
  parts.shell.dataset.arhubCodexFocus = state.focusMode ? "true" : "false";
  syncChrome(parts);
}

function contextLabel(parts) {
  const active = parts.files.querySelector(
    "[aria-current='true'], .is-active, [data-active='true']",
  );
  const fromActive = normalizeFileName(active?.textContent);
  return state.lastFile || fromActive || "选择文件或点击对话中的文件引用";
}

function ensureContextBar(parts) {
  let bar = parts.workbench.querySelector(":scope > .arhub-codex-context-bar");
  if (bar instanceof HTMLElement) return bar;
  bar = document.createElement("header");
  bar.className = "arhub-codex-context-bar";
  bar.setAttribute("aria-label", "当前文件上下文");
  const title = document.createElement("div");
  title.className = "arhub-codex-context-title";
  const graphic = document.createElement("span");
  graphic.className = "arhub-codex-context-icon";
  const text = document.createElement("span");
  text.className = "arhub-codex-context-name";
  title.append(graphic, text);
  const close = iconButton("X", "关闭文件上下文", "arhub-codex-context-close");
  close.addEventListener("click", () => setContext(false));
  bar.append(title, close);
  parts.workbench.prepend(bar);
  return bar;
}

function decorateFileNavigation(parts) {
  for (const button of parts.files.querySelectorAll("button")) {
    if (!(button instanceof HTMLButtonElement)) continue;
    if (button.dataset.arhubCodexFileIcon === "true") continue;
    const name = normalizeFileName(
      button.dataset.mwFilePath || button.dataset.path || button.textContent,
    );
    if (!/\.[a-z0-9]{1,10}$/i.test(name)) continue;
    const visual = fileVisual(name);
    const icon = document.createElement("span");
    icon.className = "arhub-codex-file-icon";
    icon.dataset.kind = visual.kind;
    icon.setAttribute("aria-hidden", "true");
    icon.append(createIcon(visual.icon, { size: 15 }));
    button.prepend(icon);
    button.dataset.arhubCodexFileIcon = "true";
    button.dataset.arhubCodexFileKind = visual.kind;
  }
}

function ensureCompactFileLauncher(parts) {
  let launcher = parts.files.querySelector(":scope > .arhub-codex-file-launcher");
  if (!(launcher instanceof HTMLButtonElement)) {
    launcher = iconButton("FolderOpen", "打开文件列表", "arhub-codex-file-launcher");
    launcher.addEventListener("click", (event) => {
      event.stopPropagation();
      setMobileFilesOpen(!state.mobileFilesOpen);
    });
    parts.files.prepend(launcher);
  }
  launcher.setAttribute("aria-expanded", String(state.mobileFilesOpen));
  launcher.style.setProperty("display", "grid", "important");
  launcher.style.setProperty("opacity", "1", "important");
  launcher.style.setProperty("pointer-events", "auto", "important");
  return launcher;
}

function ensureAgentToolbar(parts) {
  let toolbar = parts.header.querySelector(":scope > .arhub-codex-agent-toolbar");
  if (toolbar instanceof HTMLElement) return toolbar;
  toolbar = document.createElement("div");
  toolbar.className = "arhub-codex-agent-toolbar";
  toolbar.setAttribute("role", "toolbar");
  toolbar.setAttribute("aria-label", "编辑器视图");

  const files = iconButton("PanelLeft", "显示或隐藏文件导航", "arhub-codex-files-toggle");
  files.addEventListener("click", () => setFilesCollapsed(!state.filesCollapsed));
  const context = iconButton("PanelRight", "显示或隐藏文件上下文", "arhub-codex-context-toggle");
  context.addEventListener("click", () => setContext(!state.contextOpen));
  const focus = iconButton("MessagesSquare", "专注 Agent 对话", "arhub-codex-focus-toggle");
  focus.addEventListener("click", () => setFocusMode(!state.focusMode));
  toolbar.append(files, context, focus);
  parts.header.append(toolbar);
  return toolbar;
}

function syncChrome(parts) {
  const toolbar = ensureAgentToolbar(parts);
  const filesToggle = toolbar.querySelector(".arhub-codex-files-toggle");
  const contextToggle = toolbar.querySelector(".arhub-codex-context-toggle");
  const focusToggle = toolbar.querySelector(".arhub-codex-focus-toggle");
  filesToggle?.setAttribute("aria-pressed", String(!state.filesCollapsed));
  contextToggle?.setAttribute("aria-pressed", String(state.contextOpen));
  focusToggle?.setAttribute("aria-pressed", String(state.focusMode));

  const bar = ensureContextBar(parts);
  const name = bar.querySelector(".arhub-codex-context-name");
  const icon = bar.querySelector(".arhub-codex-context-icon");
  const label = contextLabel(parts);
  if (name) name.textContent = label;
  if (icon) {
    icon.replaceChildren(createIcon(fileVisual(label).icon, { size: 16 }));
  }
  bar.classList.toggle("is-empty", !state.lastFile);
  ensureCompactFileLauncher(parts);
}

function enhanceEditor() {
  if (!isEditorRoute()) {
    document.documentElement.classList.remove("arhub-codex-editor-active");
    return;
  }
  const parts = editorParts();
  if (!parts) return;
  document.documentElement.classList.add("arhub-codex-editor-active");
  parts.shell.dataset.arhubCodexContext ||= state.contextOpen ? "open" : "closed";
  parts.shell.dataset.arhubCodexFiles ||= state.filesCollapsed ? "collapsed" : "expanded";
  parts.shell.dataset.arhubCodexFocus ||= state.focusMode ? "true" : "false";
  parts.shell.dataset.arhubCodexMobileFiles ||= state.mobileFilesOpen ? "open" : "closed";
  decorateFileNavigation(parts);
  syncChrome(parts);
}

function scheduleEnhance() {
  if (state.scheduled) return;
  state.scheduled = true;
  window.requestAnimationFrame(() => {
    state.scheduled = false;
    enhanceEditor();
  });
}

function rememberFileContext(target) {
  const reference = target.closest(
    ".mw-file-reference, .mw-files-panel button, .mw-files-panel a",
  );
  if (!(reference instanceof HTMLElement)) return;
  const fileName = normalizeFileName(
    reference.dataset.mwFilePath || reference.dataset.path || reference.textContent,
  );
  if (!fileName) return;
  window.setTimeout(() => setContext(true, fileName), 0);
}

document.addEventListener("click", (event) => {
  if (!isEditorRoute() || !(event.target instanceof Element)) return;
  rememberFileContext(event.target);
});

window.addEventListener("keydown", (event) => {
  if (!isEditorRoute()) return;
  if (event.key === "Escape" && state.contextOpen) {
    setContext(false);
    return;
  }
  if (event.altKey && !event.ctrlKey && !event.metaKey && event.key === "1") {
    event.preventDefault();
    setFilesCollapsed(!state.filesCollapsed);
  }
  if (event.altKey && !event.ctrlKey && !event.metaKey && event.key === "2") {
    event.preventDefault();
    setContext(!state.contextOpen);
  }
});

window.addEventListener("arhub:open-context", (event) => {
  const detail = event instanceof CustomEvent ? event.detail : null;
  setContext(true, typeof detail?.file === "string" ? detail.file : "");
});
window.addEventListener("arhub:toggle-files", () => {
  if (isEditorRoute()) setFilesCollapsed(!state.filesCollapsed);
});
window.addEventListener("arhub:close-context", () => {
  if (isEditorRoute()) setContext(false);
});
window.addEventListener("popstate", scheduleEnhance);
window.addEventListener("resize", scheduleEnhance, { passive: true });

const root = document.getElementById("root");
if (root) {
  new MutationObserver(scheduleEnhance).observe(root, {
    childList: true,
    subtree: true,
    characterData: true,
  });
}

scheduleEnhance();

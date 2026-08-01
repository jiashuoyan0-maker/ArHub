const SHELL_STORAGE_KEY = "arhub-codex-shell:sidebar-collapsed";
const THEME_STORAGE_KEY = "ArHub-theme";
const EDITOR_PATH = /^\/workflow\/([^/]+)\/editor\/?$/;
const WORKFLOW_PATH = /^\/workflow\/([^/]+)\/?$/;
const FILE_REFERENCE_PATTERN =
  /(?:^|[\s("'`])((?:[\w\u3400-\u9fff.@()+-]+[\\/])*[\w\u3400-\u9fff.@()+-]+\.(?:md|markdown|tex|py|json|ya?ml|toml|csv|tsv|docx|xlsx|pptx|pdf|png|jpe?g|webp|gif|svg|drawio|html?|css|jsx?|tsx?|txt|bib|ris))(?:$|[\s),:;"'`])/i;

const ICONS = {
  panelLeft:
    '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/>',
  panelRight:
    '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M15 3v18"/>',
  plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
  inbox:
    '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="m5.45 5.11-3.03 6.68A2 2 0 0 0 4.24 15h15.52a2 2 0 0 0 1.82-3.21l-3.03-6.68A2 2 0 0 0 16.73 4H7.27a2 2 0 0 0-1.82 1.11Z"/><path d="M6 20h12"/>',
  settings:
    '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.09a2 2 0 0 1-1-1.74v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2Z"/><circle cx="12" cy="12" r="3"/>',
  puzzle:
    '<path d="M19.439 7.85c-.049.322-.059.648-.01.97.118.764.65 1.432 1.428 1.684l.232.075c.886.287 1.451 1.173 1.307 2.093A2 2 0 0 1 20.42 14.4h-1.45a1 1 0 0 0-1 1v3.5a2 2 0 0 1-2 2h-3.5a1 1 0 0 1-1-1v-.9c0-1.1-.9-2-2-2s-2 .9-2 2v.9a1 1 0 0 1-1 1h-3.5a2 2 0 0 1-2-2v-3.5a1 1 0 0 1 1-1h.9c1.1 0 2-.9 2-2s-.9-2-2-2h-.9a1 1 0 0 1-1-1V6a2 2 0 0 1 2-2h3.5a1 1 0 0 1 1 1v.9c0 1.1.9 2 2 2s2-.9 2-2V5a1 1 0 0 1 1-1h3.5a2 2 0 0 1 2 2v1.43c0 .14-.01.281-.031.42Z"/>',
  refresh:
    '<path d="M20 11a8.1 8.1 0 0 0-15.5-2M4 4v5h5"/><path d="M4 13a8.1 8.1 0 0 0 15.5 2M20 20v-5h-5"/>',
  columns:
    '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M12 3v18"/>',
  message:
    '<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/>',
  code:
    '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
  eye:
    '<path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/>',
  file:
    '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/>',
  menu: '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
  chevronLeft: '<path d="m15 18-6-6 6-6"/>',
  external: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  send: '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.42 1.42"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.42"/>',
  moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
};

const shellState = {
  workflows: [],
  workflowsLoadedAt: 0,
  workflowsPromise: null,
  scheduled: false,
  lastPath: "",
  panelWorkflowId: null,
  filesOpen: false,
  contextOpen: false,
  currentContextPath: "",
};

function createIcon(name, size = 16) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("width", String(size));
  svg.setAttribute("height", String(size));
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "1.8");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");
  svg.classList.add("mw-lucide");
  svg.innerHTML = ICONS[name] || ICONS.file;
  return svg;
}

function createButton(icon, label, className = "") {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `mw-shell-icon-button ${className}`.trim();
  button.title = label;
  button.setAttribute("aria-label", label);
  button.append(createIcon(icon));
  return button;
}

function activeTheme() {
  return document.documentElement.getAttribute("data-theme") === "light"
    ? "light"
    : "dark";
}

function syncThemeControl() {
  const button = document.querySelector(".mw-shell-theme-toggle");
  if (!(button instanceof HTMLButtonElement)) return;
  const theme = activeTheme();
  const icon = theme === "dark" ? "sun" : "moon";
  const label = theme === "dark" ? "切换到浅色模式" : "切换到深色模式";
  if (button.dataset.mwThemeIcon !== icon) {
    button.replaceChildren(createIcon(icon));
    button.dataset.mwThemeIcon = icon;
  }
  button.dataset.mwTheme = theme;
  button.title = label;
  button.setAttribute("aria-label", label);
  button.setAttribute("aria-pressed", String(theme === "dark"));
}

function toggleTheme() {
  const nativeToggle = document.querySelector(".nav-bar .theme-toggle");
  if (nativeToggle instanceof HTMLElement) {
    nativeToggle.click();
  } else {
    const nextTheme = activeTheme() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", nextTheme);
    localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
  }
  window.requestAnimationFrame(syncThemeControl);
  window.setTimeout(syncThemeControl, 80);
}

function createNavLink(href, icon, label, route) {
  const link = document.createElement("a");
  link.href = href;
  link.className = "mw-shell-nav-link";
  link.dataset.mwRoute = route;
  link.append(createIcon(icon));
  const text = document.createElement("span");
  text.textContent = label;
  link.append(text);
  return link;
}

function getRoute() {
  const path = window.location.pathname;
  const editorMatch = path.match(EDITOR_PATH);
  const workflowMatch = path.match(WORKFLOW_PATH);
  if (editorMatch) return { kind: "editor", workflowId: editorMatch[1], path };
  if (workflowMatch) return { kind: "workflow", workflowId: workflowMatch[1], path };
  if (path === "/new" || path === "/new/") return { kind: "new", path };
  if (path.startsWith("/settings")) return { kind: "settings", path };
  return { kind: "workflows", path };
}

function statusClass(status) {
  const value = String(status || "").toLowerCase();
  if (/running|执行|运行/.test(value)) return "is-running";
  if (/completed|done|完成|success/.test(value)) return "is-complete";
  if (/failed|error|失败/.test(value)) return "is-failed";
  return "is-idle";
}

function currentWorkflow(route = getRoute()) {
  return shellState.workflows.find(
    (workflow) => String(workflow.id) === String(route.workflowId || ""),
  );
}

function renderRecentWorkflows() {
  const list = document.getElementById("mw-shell-recents");
  if (!list) return;
  const route = getRoute();
  const signature = JSON.stringify({
    active: route.workflowId || "",
    workflows: shellState.workflows.slice(0, 10).map((workflow) => [
      workflow.id,
      workflow.title,
      workflow.status,
      workflow.current_step,
      workflow.template,
    ]),
  });
  if (list.dataset.mwSignature === signature) return;
  list.dataset.mwSignature = signature;
  list.replaceChildren();

  if (!shellState.workflows.length) {
    const empty = document.createElement("p");
    empty.className = "mw-shell-empty";
    empty.textContent = "暂无任务";
    list.append(empty);
    return;
  }

  shellState.workflows.slice(0, 10).forEach((workflow) => {
    const link = document.createElement("a");
    link.href = `/workflow/${encodeURIComponent(workflow.id)}`;
    link.className = "mw-shell-task";
    link.classList.toggle(
      "is-active",
      String(route.workflowId || "") === String(workflow.id),
    );
    link.title = workflow.title || "未命名任务";

    const dot = document.createElement("span");
    dot.className = `mw-shell-task-dot ${statusClass(workflow.status)}`;
    const text = document.createElement("span");
    text.className = "mw-shell-task-text";
    const title = document.createElement("strong");
    title.textContent = workflow.title || "未命名任务";
    const meta = document.createElement("span");
    meta.textContent = workflow.current_step || workflow.template || "工作流";
    text.append(title, meta);
    link.append(dot, text);
    list.append(link);
  });
}

async function loadWorkflows(force = false) {
  const fresh = Date.now() - shellState.workflowsLoadedAt < 20_000;
  if (!force && fresh) return shellState.workflows;
  if (shellState.workflowsPromise) return shellState.workflowsPromise;

  shellState.workflowsPromise = fetch("/api/workflows", { cache: "no-store" })
    .then((response) => (response.ok ? response.json() : []))
    .then((payload) => {
      shellState.workflows = Array.isArray(payload)
        ? payload
        : Array.isArray(payload?.workflows)
          ? payload.workflows
          : [];
      shellState.workflows.sort((left, right) => {
        const a = new Date(left.updated_at || left.created_at || 0).getTime();
        const b = new Date(right.updated_at || right.created_at || 0).getTime();
        return b - a;
      });
      shellState.workflowsLoadedAt = Date.now();
      renderRecentWorkflows();
      updateRouteChrome();
      return shellState.workflows;
    })
    .catch(() => {
      renderRecentWorkflows();
      return shellState.workflows;
    })
    .finally(() => {
      shellState.workflowsPromise = null;
    });
  return shellState.workflowsPromise;
}

function toggleSidebar(force) {
  const body = document.body;
  const mobile = window.matchMedia("(max-width: 860px)").matches;
  if (mobile) {
    const next = force ?? !body.classList.contains("mw-shell-mobile-open");
    body.classList.toggle("mw-shell-mobile-open", next);
    return;
  }
  const next = force ?? !body.classList.contains("mw-shell-collapsed");
  body.classList.toggle("mw-shell-collapsed", next);
  localStorage.setItem(SHELL_STORAGE_KEY, next ? "true" : "false");
}

function openExtensions() {
  window.dispatchEvent(new CustomEvent("arhub:open-extensions"));
}

function buildSidebar() {
  const sidebar = document.createElement("aside");
  sidebar.id = "mw-codex-sidebar";
  sidebar.setAttribute("aria-label", "主导航");

  const brand = document.createElement("div");
  brand.className = "mw-shell-brand-row";
  const brandLink = document.createElement("a");
  brandLink.href = "/";
  brandLink.className = "mw-shell-brand";
  const logo = document.createElement("img");
  logo.src = "/logo.svg";
  logo.alt = "ArHub";
  const brandText = document.createElement("span");
  const brandName = document.createElement("strong");
  brandName.textContent = "ArHub";
  const brandEdition = document.createElement("small");
  brandEdition.textContent = "Open Workspace";
  brandText.append(brandName, brandEdition);
  brandLink.append(logo, brandText);
  const collapse = createButton("panelLeft", "收起侧栏", "mw-shell-collapse");
  collapse.addEventListener("click", () => toggleSidebar());
  brand.append(brandLink, collapse);

  const newTask = document.createElement("a");
  newTask.href = "/new";
  newTask.className = "mw-shell-new-task";
  newTask.append(createIcon("plus"));
  const newTaskLabel = document.createElement("span");
  newTaskLabel.textContent = "新建任务";
  newTask.append(newTaskLabel);

  const primary = document.createElement("nav");
  primary.className = "mw-shell-primary";
  primary.append(
    createNavLink("/", "inbox", "任务", "workflows"),
    createNavLink("/settings", "settings", "设置", "settings"),
  );

  const recent = document.createElement("section");
  recent.className = "mw-shell-recent";
  const recentHeader = document.createElement("header");
  const recentTitle = document.createElement("span");
  recentTitle.textContent = "最近任务";
  const refresh = createButton("refresh", "刷新任务", "mw-shell-refresh");
  refresh.addEventListener("click", () => loadWorkflows(true));
  recentHeader.append(recentTitle, refresh);
  const recentList = document.createElement("div");
  recentList.id = "mw-shell-recents";
  recentList.className = "mw-shell-recents";
  recent.append(recentHeader, recentList);

  const footer = document.createElement("div");
  footer.className = "mw-shell-sidebar-footer";
  const extensions = document.createElement("button");
  extensions.type = "button";
  extensions.className = "mw-shell-nav-link";
  extensions.append(createIcon("puzzle"));
  const extensionLabel = document.createElement("span");
  extensionLabel.textContent = "扩展";
  extensions.append(extensionLabel);
  extensions.addEventListener("click", openExtensions);
  footer.append(extensions);

  sidebar.append(brand, newTask, primary, recent, footer);
  return sidebar;
}

function buildTopbar() {
  const topbar = document.createElement("header");
  topbar.id = "mw-codex-topbar";

  const left = document.createElement("div");
  left.className = "mw-shell-topbar-left";
  const menu = createButton("menu", "打开侧栏", "mw-shell-mobile-menu");
  menu.addEventListener("click", () => toggleSidebar(true));
  const title = document.createElement("div");
  title.className = "mw-shell-route-title";
  const eyebrow = document.createElement("span");
  eyebrow.id = "mw-shell-eyebrow";
  const heading = document.createElement("strong");
  heading.id = "mw-shell-title";
  title.append(eyebrow, heading);
  left.append(menu, title);

  const right = document.createElement("div");
  right.className = "mw-shell-topbar-right";
  const editorActions = document.createElement("div");
  editorActions.id = "mw-shell-editor-actions";
  const themeToggle = createButton(
    "sun",
    "切换到浅色模式",
    "mw-shell-theme-toggle",
  );
  themeToggle.addEventListener("click", toggleTheme);
  const localStatus = document.createElement("span");
  localStatus.className = "mw-shell-local-status";
  const statusDot = document.createElement("i");
  const statusText = document.createElement("span");
  statusText.textContent = "本地";
  localStatus.append(statusDot, statusText);
  right.append(editorActions, themeToggle, localStatus);
  topbar.append(left, right);
  return topbar;
}

function buildScrim() {
  const scrim = document.createElement("button");
  scrim.id = "mw-shell-scrim";
  scrim.type = "button";
  scrim.setAttribute("aria-label", "关闭侧栏");
  scrim.addEventListener("click", () => toggleSidebar(false));
  return scrim;
}

function ensureShell() {
  document.documentElement.classList.add("mw-codex-ui");
  if (localStorage.getItem(SHELL_STORAGE_KEY) === "true") {
    document.body.classList.add("mw-shell-collapsed");
  }
  if (!document.getElementById("mw-codex-sidebar")) {
    document.body.append(buildSidebar());
  }
  if (!document.getElementById("mw-codex-topbar")) {
    document.body.append(buildTopbar());
  }
  if (!document.getElementById("mw-shell-scrim")) {
    document.body.append(buildScrim());
  }
  syncThemeControl();
}

function proxyButton(icon, label, selector, group) {
  const button = createButton(icon, label);
  button.dataset.mwProxy = selector;
  button.dataset.mwProxyGroup = group;
  button.addEventListener("click", () => {
    const target = document.querySelector(selector);
    if (target instanceof HTMLElement) target.click();
    window.requestAnimationFrame(syncEditorActions);
  });
  return button;
}

function panelButton(icon, label, group, action) {
  const button = createButton(icon, label);
  button.dataset.mwProxyGroup = group;
  button.addEventListener("click", action);
  return button;
}

function applyPanelState() {
  const shell = document.querySelector(".mw-editor-shell");
  if (!shell) return;
  shell.classList.toggle("mw-shell-files-open", shellState.filesOpen);
  shell.classList.toggle("mw-shell-context-open", shellState.contextOpen);
  document.documentElement.dataset.mwFilesOpen = String(shellState.filesOpen);
  document.documentElement.dataset.mwContextOpen = String(shellState.contextOpen);
  syncEditorActions();
}

function setPanelState(next) {
  if (Object.hasOwn(next, "filesOpen")) {
    shellState.filesOpen = Boolean(next.filesOpen);
  }
  if (Object.hasOwn(next, "contextOpen")) {
    shellState.contextOpen = Boolean(next.contextOpen);
  }
  applyPanelState();
}

function showChatOnly() {
  setPanelState({ filesOpen: false, contextOpen: false });
}

function ensurePanelState(route, shell) {
  if (shellState.panelWorkflowId !== route.workflowId) {
    shellState.panelWorkflowId = route.workflowId;
    shellState.filesOpen = false;
    shellState.contextOpen = false;
    shellState.currentContextPath = "";
  }
  if (shell.dataset.mwShellBaseLayout !== "true") {
    shell.dataset.mwShellBaseLayout = "true";
    const rightLayout = document.querySelector('[data-mw-layout="right"]');
    if (
      rightLayout instanceof HTMLElement &&
      document.documentElement.dataset.mwLayout !== "right"
    ) {
      rightLayout.click();
    }
  }
  applyPanelState();
}

function extractFileReference(value) {
  let source = String(value || "").trim();
  try {
    source = decodeURIComponent(source);
  } catch {
    // Keep the literal value if it is not URL encoded.
  }
  const match = ` ${source} `.match(FILE_REFERENCE_PATTERN);
  return (match?.[1] || "").replaceAll("\\", "/");
}

function findFileControl(path) {
  const panel = document.querySelector(".mw-files-panel");
  if (!panel || !path) return null;
  const normalized = path.toLowerCase();
  const basename = normalized.split("/").pop() || normalized;
  const candidates = Array.from(
    panel.querySelectorAll("button, a, [role='button']"),
  );
  return (
    candidates.find((element) => {
      const text = String(element.textContent || "")
        .replaceAll("\\", "/")
        .toLowerCase();
      return text.includes(normalized);
    }) ||
    candidates.find((element) => {
      const text = String(element.textContent || "").toLowerCase();
      return text.includes(basename);
    }) ||
    null
  );
}

function openFileReference(path) {
  if (!path) return;
  shellState.currentContextPath = path;
  const control = findFileControl(path);
  if (control instanceof HTMLElement && control.dataset.mwOpening !== "true") {
    control.dataset.mwOpening = "true";
    control.click();
    window.setTimeout(() => delete control.dataset.mwOpening, 0);
  }
  setPanelState({ filesOpen: false, contextOpen: true });
}

function decorateFileReferences() {
  document
    .querySelectorAll(".mw-agent-thread .mw-message a, .mw-agent-thread .mw-message code")
    .forEach((element) => {
      if (element.closest("pre") || element.dataset.mwFileReady === "true") return;
      const source = `${element.textContent || ""} ${element.getAttribute("href") || ""}`;
      const path = extractFileReference(source);
      if (!path) return;
      element.dataset.mwFileReady = "true";
      element.dataset.mwFilePath = path;
      element.classList.add("mw-file-reference");
      element.setAttribute("role", "button");
      element.tabIndex = 0;
      element.title = `在上下文中打开 ${path}`;
      const open = (event) => {
        event.preventDefault();
        event.stopPropagation();
        openFileReference(path);
      };
      element.addEventListener("click", open);
      element.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") open(event);
      });
    });
}

function ensurePanelHandles(shell) {
  let contextClose = shell.querySelector(":scope > .mw-context-close");
  if (!contextClose) {
    contextClose = createButton("x", "关闭文件上下文", "mw-context-close");
    contextClose.addEventListener("click", () =>
      setPanelState({ contextOpen: false }),
    );
    shell.append(contextClose);
  }
  let filesClose = shell.querySelector(":scope > .mw-files-close");
  if (!filesClose) {
    filesClose = createButton("x", "关闭文件列表", "mw-files-close");
    filesClose.addEventListener("click", () => setPanelState({ filesOpen: false }));
    shell.append(filesClose);
  }
}

function renderEditorActions() {
  const host = document.getElementById("mw-shell-editor-actions");
  if (!host) return;
  const route = getRoute();
  host.classList.toggle("is-visible", route.kind === "editor");
  if (route.kind !== "editor") {
    host.replaceChildren();
    return;
  }
  if (host.childElementCount) {
    syncEditorActions();
    return;
  }

  const navigation = document.createElement("div");
  navigation.className = "mw-shell-action-group";
  navigation.append(
    panelButton("panelLeft", "显示或隐藏文件", "files", () =>
      setPanelState({ filesOpen: !shellState.filesOpen }),
    ),
  );

  const workspace = document.createElement("div");
  workspace.className = "mw-shell-action-group";
  workspace.append(
    panelButton("message", "Agent 对话", "chat", showChatOnly),
    panelButton("panelRight", "显示或隐藏文件上下文", "context", () =>
      setPanelState({ contextOpen: !shellState.contextOpen }),
    ),
  );

  const canvas = document.createElement("div");
  canvas.className = "mw-shell-action-group mw-shell-canvas-group";
  canvas.append(
    proxyButton("code", "编辑器", '[data-mw-canvas="editor"]', "canvas-editor"),
    proxyButton("columns", "编辑与预览", '[data-mw-canvas="split"]', "canvas-split"),
    proxyButton("eye", "预览", '[data-mw-canvas="preview"]', "canvas-preview"),
  );

  const extensions = createButton("puzzle", "扩展中心");
  extensions.addEventListener("click", openExtensions);
  host.append(navigation, workspace, canvas, extensions);
  syncEditorActions();
}

function syncEditorActions() {
  const host = document.getElementById("mw-shell-editor-actions");
  const shell = document.querySelector(".mw-editor-shell");
  if (!host || !shell) return;
  const canvas = shell.dataset.mwCanvas || "split";

  host.querySelectorAll("[data-mw-proxy-group]").forEach((button) => {
    const group = button.dataset.mwProxyGroup;
    const active =
      (group === "files" && shellState.filesOpen) ||
      (group === "context" && shellState.contextOpen) ||
      (group === "chat" && !shellState.filesOpen && !shellState.contextOpen) ||
      (group === `canvas-${canvas}`);
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function decorateEditor() {
  const route = getRoute();
  if (route.kind !== "editor") return;
  const shell = document.querySelector(".mw-editor-shell");
  if (!shell) return;
  ensurePanelState(route, shell);
  ensurePanelHandles(shell);
  const send = document.querySelector("[data-send-btn]");
  if (send && !send.querySelector(".mw-lucide")) {
    send.prepend(createIcon("send", 15));
  }
  document.querySelector(".mw-files-panel")?.setAttribute("aria-label", "文件导航");
  document.querySelector(".mw-workbench")?.setAttribute("aria-label", "工作上下文");
  document.querySelector(".mw-agent-panel")?.setAttribute("aria-label", "Agent 对话");
  decorateFileReferences();
  syncEditorActions();
}

function syncRoutePage(route = getRoute()) {
  document.documentElement.dataset.mwPage = route.kind;
  return route;
}

function updateRouteChrome() {
  const route = syncRoutePage();
  const workflow = currentWorkflow(route);
  const title = document.getElementById("mw-shell-title");
  const eyebrow = document.getElementById("mw-shell-eyebrow");
  const labels = {
    workflows: ["工作区", "任务"],
    new: ["工作区", "新建任务"],
    settings: ["ArHub", "设置"],
    workflow: ["任务", workflow?.title || "工作流"],
    editor: ["Agent 工作区", workflow?.title || "编辑任务"],
  };
  const [nextEyebrow, nextTitle] = labels[route.kind] || labels.workflows;
  if (title) {
    title.textContent = nextTitle;
    title.title = nextTitle;
  }
  if (eyebrow) eyebrow.textContent = nextEyebrow;

  document.querySelectorAll("[data-mw-route]").forEach((link) => {
    const active =
      link.dataset.mwRoute === route.kind ||
      (link.dataset.mwRoute === "workflows" &&
        ["workflow", "editor"].includes(route.kind));
    link.classList.toggle("is-active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  renderRecentWorkflows();
  renderEditorActions();
  decorateEditor();
  shellState.lastPath = route.path;
}

function enhanceShell() {
  ensureShell();
  updateRouteChrome();
  loadWorkflows();
}

function scheduleShellEnhance() {
  if (shellState.scheduled) return;
  shellState.scheduled = true;
  window.requestAnimationFrame(() => {
    shellState.scheduled = false;
    enhanceShell();
  });
}

function installNavigationBridge() {
  ["pushState", "replaceState"].forEach((method) => {
    const original = history[method];
    if (original.__mwShellPatched) return;
    const wrapped = function (...args) {
      const result = original.apply(this, args);
      window.dispatchEvent(new Event("arhub:navigation"));
      return result;
    };
    wrapped.__mwShellPatched = true;
    history[method] = wrapped;
  });
}

function handleFilePanelClick(event) {
  if (getRoute().kind !== "editor") return;
  const target = event.target instanceof Element ? event.target : null;
  const panel = target?.closest(".mw-files-panel");
  if (!panel) return;
  const actionable =
    target.closest("button, a, [role='button']") || target.closest("div");
  const source = `${actionable?.textContent || ""} ${actionable?.getAttribute?.("title") || ""}`;
  const path = extractFileReference(source);
  if (!path) return;
  window.setTimeout(() => {
    shellState.currentContextPath = path;
    setPanelState({ filesOpen: false, contextOpen: true });
  }, 0);
}

installNavigationBridge();
document.addEventListener("click", handleFilePanelClick);
const root = document.getElementById("root");
if (root) {
  new MutationObserver(scheduleShellEnhance).observe(root, {
    childList: true,
    subtree: true,
    characterData: true,
    attributes: true,
    attributeFilter: ["class", "data-mw-layout", "data-mw-canvas"],
  });
}
new MutationObserver(syncThemeControl).observe(document.documentElement, {
  attributes: true,
  attributeFilter: ["data-theme"],
});
window.addEventListener("storage", (event) => {
  if (event.key === THEME_STORAGE_KEY) syncThemeControl();
});
function handleShellNavigation() {
  syncRoutePage();
  scheduleShellEnhance();
}

window.addEventListener("popstate", handleShellNavigation);
window.addEventListener("arhub:navigation", handleShellNavigation);
window.addEventListener("resize", () => {
  if (window.innerWidth > 860) document.body.classList.remove("mw-shell-mobile-open");
  scheduleShellEnhance();
});
window.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "b") {
    event.preventDefault();
    toggleSidebar();
  }
  if (event.key === "Escape") {
    document.body.classList.remove("mw-shell-mobile-open");
  }
});

scheduleShellEnhance();

import { createIcon, fileVisual } from "./arhub-icons.js";

const EDITOR_ROUTE = /^\/workflow\/([^/]+)\/editor\/?$/;
const STORAGE_PREFIX = "arhub-open-workspace:";
const PROFILE_MARKER = "[ArHub Agent Profile]";
const PROFILE_END_MARKER = "[End ArHub Agent Profile]";
const LEGACY_PROFILE_MARKER = "[ArHub Agent Profile]";
const LEGACY_PROFILE_END_MARKER = "[End ArHub Agent Profile]";

const FALLBACK_REGISTRY = {
  schema_version: "1.0",
  extensions: [
    {
      id: "arhub.core",
      name: "ArHub Core Profiles",
      version: "1.0.0",
      source: "builtin",
      contribution_counts: { agent_profiles: 4, commands: 4, tool_adapters: 0 },
    },
  ],
  agent_profiles: [
    {
      id: "arhub.core/general",
      label: "通用执行",
      description: "跨文件分析、修改与验证",
      mode: "agent",
      accent: "#0a84ff",
      capabilities: ["read", "write", "run", "review"],
      system_prompt:
        "你是通用执行 Agent。先理解目标和当前工作区，再选择最少但充分的文件与工具完成任务。修改后必须验证，并清楚报告未完成项。",
      source: "builtin",
    },
    {
      id: "arhub.core/code",
      label: "代码工程",
      description: "面向代码实现、调试和测试",
      mode: "agent",
      accent: "#30d158",
      capabilities: ["read", "write", "run", "test", "debug"],
      system_prompt:
        "你是代码工程 Agent。遵循现有代码风格，先定位真实根因，再做范围最小的实现。必须运行与改动风险相称的测试。",
      source: "builtin",
    },
    {
      id: "arhub.core/research",
      label: "研究写作",
      description: "面向论文、报告与证据组织",
      mode: "agent",
      accent: "#bf5af2",
      capabilities: ["read", "write", "analyze", "cite"],
      system_prompt:
        "你是研究写作 Agent。围绕论点、证据和结构工作，区分已知事实与推断，保留可追溯来源。",
      source: "builtin",
    },
    {
      id: "arhub.core/reviewer",
      label: "审查改进",
      description: "发现风险、缺口和回归",
      mode: "agent",
      accent: "#ff9f0a",
      capabilities: ["read", "review", "compare", "test"],
      system_prompt:
        "你是审查 Agent。先寻找错误、行为回归、安全风险和缺失验证，按严重程度给出具体证据。",
      source: "builtin",
    },
  ],
  commands: [
    {
      id: "arhub.core/inspect-context",
      label: "检查当前上下文",
      description: "先理解文件与任务状态",
      prompt: "检查当前文件和相关上下文，先列出你确认的事实、信息缺口和下一步，再开始修改。",
    },
    {
      id: "arhub.core/plan-change",
      label: "规划本次修改",
      description: "形成短而可执行的实现方案",
      prompt: "针对当前目标形成一份简洁的修改计划，明确会改哪些文件、保留哪些行为以及如何验证，然后按计划执行。",
    },
    {
      id: "arhub.core/review-changes",
      label: "审查当前改动",
      description: "检查错误、回归和测试缺口",
      prompt: "审查当前工作区的改动，优先找行为错误、回归风险、安全问题和缺失测试；给出具体文件与证据。",
    },
    {
      id: "arhub.core/summarize-workspace",
      label: "总结工作区",
      description: "形成当前状态和下一步摘要",
      prompt: "总结当前工作区已经完成的内容、仍存在的问题、关键产物和最合理的下一步。",
    },
  ],
  tool_adapters: [],
  views: [],
  actions: [],
  errors: [],
  policy: { manifest_only: true, third_party_code_execution: false },
};

const state = {
  nativeFetch: window.fetch.bind(window),
  registry: FALLBACK_REGISTRY,
  registryPromise: null,
  settings: null,
  settingsPromise: null,
  activeProfile: null,
  workflowId: null,
  preferences: null,
  parts: null,
  scheduled: false,
  effectiveLayout: "right",
  resizeSaveTimer: null,
  attachments: [],
  attachmentSerial: 0,
  claudeCapability: null,
  claudeCapabilityPromise: null,
};

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function routeWorkflowId() {
  return window.location.pathname.match(EDITOR_ROUTE)?.[1] || null;
}

function defaultPreferences() {
  return {
    layout: "auto",
    previousLayout: "auto",
    canvas: "split",
    filesVisible: true,
    agentWidth: 460,
    agentBottomHeight: 360,
    floatBounds: null,
    profileId: "arhub.core/general",
  };
}

const ROLE_RUNTIME_KEYS = Object.freeze({
  executor: "executor_agent_runtime",
  reviewer: "reviewer_agent_runtime",
  editor_ai: "editor_ai_agent_runtime",
});

function activeAgentName(parts = state.parts) {
  return parts && isLiteAgentMode(parts) ? "editor_ai" : "executor";
}

function selectedRuntime(agentName = activeAgentName()) {
  return (
    state.settings?.[ROLE_RUNTIME_KEYS[agentName]] ||
    state.settings?.agent_runtime ||
    "openai_compatible"
  );
}

function selectedEffort(agentName = activeAgentName(), runtime = selectedRuntime(agentName)) {
  return runtime === "local_claude"
    ? state.settings?.[`${agentName}_reasoning_effort`] ||
        state.settings?.claude_effort ||
        "high"
    : state.settings?.[`${agentName}_reasoning_effort`] || "default";
}

function loadPreferences(workflowId) {
  const defaults = defaultPreferences();
  try {
    const saved = JSON.parse(
      localStorage.getItem(`${STORAGE_PREFIX}${workflowId}`) || "{}",
    );
    return { ...defaults, ...saved };
  } catch {
    return defaults;
  }
}

function savePreferences() {
  if (!state.workflowId || !state.preferences) return;
  localStorage.setItem(
    `${STORAGE_PREFIX}${state.workflowId}`,
    JSON.stringify(state.preferences),
  );
}

function setReactValue(input, value) {
  const prototype =
    input instanceof HTMLTextAreaElement
      ? HTMLTextAreaElement.prototype
      : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(prototype, "value")?.set?.call(input, value);
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.focus();
}

function readyAttachments() {
  return state.attachments.filter((item) => item.status === "ready");
}

function attachmentPromptBlock(items) {
  if (!items.length) return "";
  const lines = items.map((item) => {
    const extracted = item.extractedPath
      ? ` (extracted text: ${item.extractedPath})`
      : "";
    return `- ${item.path}${extracted}`;
  });
  return [
    "[ArHub Attached Workspace Files]",
    ...lines,
    "Use these files as task context. Prefer an extracted text path when provided.",
    "[End Attached Workspace Files]",
  ].join("\n");
}

function selectedProfile() {
  return (
    state.registry.agent_profiles?.find(
      (profile) => profile.id === state.preferences?.profileId,
    ) || state.registry.agent_profiles?.[0] || null
  );
}

function installFetchProfileAdapter() {
  if (window.__arhubOpenWorkspaceFetch) return;
  window.__arhubOpenWorkspaceFetch = true;

  window.fetch = async (input, init) => {
    const url =
      typeof input === "string"
        ? input
        : input instanceof Request
          ? input.url
          : String(input);
    const path = new URL(url, window.location.href).pathname;
    const method = String(init?.method || "GET").toUpperCase();

    const editorRequest =
      method === "POST" &&
      /^\/api\/editor\/[^/]+\/(ai-agent|ai-edit)$/.test(path) &&
      typeof init?.body === "string";
    let requestInit = init;
    let submittedAttachments = [];

    if (editorRequest) {
      const profile = state.activeProfile || selectedProfile();
      try {
        const payload = JSON.parse(init.body);
        if (typeof payload.message === "string") {
          if (
            profile?.system_prompt &&
            typeof payload.message === "string" &&
            !payload.message.startsWith(PROFILE_MARKER) &&
            !payload.message.startsWith(LEGACY_PROFILE_MARKER)
          ) {
            payload.message = [
              PROFILE_MARKER,
              `id: ${profile.id}`,
              `name: ${profile.label}`,
              profile.system_prompt,
              PROFILE_END_MARKER,
              "",
              payload.message,
            ].join("\n");
          }
          submittedAttachments = readyAttachments();
          const attachmentBlock = attachmentPromptBlock(submittedAttachments);
          if (attachmentBlock) {
            payload.message += `\n\n${attachmentBlock}`;
          }
          const headers = new Headers(init.headers || {});
          if (profile?.id) {
            headers.set("X-ArHub-Agent-Profile", profile.id);
          }
          requestInit = {
            ...init,
            headers,
            body: JSON.stringify(payload),
          };
        }
      } catch {
        // Preserve the original request if another frontend version changes its body.
      }
    }

    const response = await state.nativeFetch(input, requestInit);
    if (editorRequest && response.ok && submittedAttachments.length) {
      const submittedIds = new Set(submittedAttachments.map((item) => item.id));
      state.attachments = state.attachments.filter(
        (item) => !submittedIds.has(item.id),
      );
      scheduleEnhance();
    }
    return response;
  };
}

function loadRegistry(force = false) {
  if (force) state.registryPromise = null;
  if (state.registryPromise) return state.registryPromise;
  state.registryPromise = state.nativeFetch("/api/extensions/registry", {
    cache: "no-store",
  })
    .then((response) => (response.ok ? response.json() : FALLBACK_REGISTRY))
    .then((registry) => {
      if (!Array.isArray(registry?.agent_profiles)) return FALLBACK_REGISTRY;
      state.registry = registry;
      if (
        state.preferences &&
        !state.registry.agent_profiles.some(
          (profile) => profile.id === state.preferences?.profileId,
        )
      ) {
        state.preferences.profileId = state.registry.agent_profiles[0]?.id || "";
        savePreferences();
      }
      state.activeProfile = selectedProfile();
      scheduleEnhance();
      return registry;
    })
    .catch(() => {
      state.registry = FALLBACK_REGISTRY;
      state.activeProfile = selectedProfile();
      return FALLBACK_REGISTRY;
    });
  return state.registryPromise;
}

function loadSettings() {
  if (state.settingsPromise) return state.settingsPromise;
  state.settingsPromise = state.nativeFetch("/api/settings", { cache: "no-store" })
    .then((response) => (response.ok ? response.json() : null))
    .then((payload) => {
      state.settings = payload?.settings || {};
      scheduleEnhance();
      return state.settings;
    })
    .catch(() => ({}));
  return state.settingsPromise;
}

function loadClaudeCapability(force = false) {
  if (force) state.claudeCapabilityPromise = null;
  if (state.claudeCapabilityPromise) return state.claudeCapabilityPromise;
  state.claudeCapabilityPromise = state.nativeFetch("/api/settings/detect-claude", {
    cache: "no-store",
  })
    .then((response) => (response.ok ? response.json() : null))
    .then((capability) => {
      state.claudeCapability = capability;
      scheduleEnhance();
      return capability;
    })
    .catch(() => null);
  return state.claudeCapabilityPromise;
}

async function saveSettingsPatch(patch) {
  const response = await state.nativeFetch("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ settings: patch }),
  });
  if (!response.ok) {
    throw new Error((await response.text()) || `HTTP ${response.status}`);
  }
  state.settings = { ...(state.settings || {}), ...patch };
  scheduleEnhance();
}

function setOptimisticSetting(key, value) {
  state.settings = { ...(state.settings || {}), [key]: value };
  scheduleEnhance();
}

function restoreSetting(key, previous) {
  const next = { ...(state.settings || {}) };
  if (previous == null) delete next[key];
  else next[key] = previous;
  state.settings = next;
  scheduleEnhance();
}

function findEditorParts() {
  const input = document.querySelector(
    'textarea[placeholder*="Agent"], input[placeholder*="Agent"]',
  );
  if (!input) return null;
  const agentPanel = input.closest(".card");
  const shell = agentPanel?.parentElement;
  if (!agentPanel || !shell || shell.children.length < 3) return null;

  const children = Array.from(shell.children);
  const agentIndex = children.indexOf(agentPanel);
  if (agentIndex < 2) return null;
  const filesPanel = children[0];
  const workbench = children[agentIndex - 1];
  const header = Array.from(agentPanel.children).find(
    (element) =>
      element.classList.contains("p-3") &&
      element.classList.contains("border-b"),
  );
  const thread = Array.from(agentPanel.children).find(
    (element) =>
      element.classList.contains("flex-1") &&
      element.classList.contains("overflow-y-auto"),
  );
  const composer = input.closest(".p-3.border-t");
  if (!header || !thread || !composer) return null;

  const directCards = Array.from(workbench.children).filter((element) =>
    element.classList.contains("card"),
  );
  const previewSurface = directCards.find((element) =>
    /预览|编译日志|脚本输出/.test(
      element.firstElementChild?.textContent || element.textContent?.slice(0, 80) || "",
    ),
  );
  const editorSurface =
    directCards.find(
      (element) =>
        element !== previewSurface && element.classList.contains("flex-1"),
    ) || directCards.find((element) => element !== previewSurface);

  return {
    shell,
    filesPanel,
    workbench,
    editorSurface,
    previewSurface,
    agentPanel,
    header,
    thread,
    composer,
    input,
  };
}

function createIconButton(icon, label, className = "") {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `mw-icon-button ${className}`.trim();
  button.textContent = icon;
  button.title = label;
  button.setAttribute("aria-label", label);
  return button;
}

function createLucideButton(icon, label, className = "") {
  const button = createIconButton("", label, className);
  button.append(createIcon(icon, { size: 17, strokeWidth: 1.8 }));
  button.dataset.mwIcon = icon;
  return button;
}

function setControlIcon(button, icon, label) {
  if (button.dataset.mwIcon !== icon || !button.querySelector("svg")) {
    button.replaceChildren(createIcon(icon, { size: 17, strokeWidth: 2 }));
    button.dataset.mwIcon = icon;
  }
  button.title = label;
  button.setAttribute("aria-label", label);
}

function sanitizedAttachmentName(value) {
  const base = String(value || "attachment")
    .split(/[\\/]/)
    .pop()
    .replace(/[<>:"/\\|?*\u0000-\u001f]/g, "_")
    .replace(/[. ]+$/g, "")
    .slice(0, 140) || "attachment";
  state.attachmentSerial += 1;
  return `${Date.now().toString(36)}-${state.attachmentSerial}-${base}`;
}

function attachmentNeedsExtraction(name) {
  return /\.(pdf|docx?)$/i.test(name);
}

function wait(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

async function responseError(response) {
  const body = await response.text().catch(() => "");
  if (!body) return `HTTP ${response.status}`;
  try {
    const payload = JSON.parse(body);
    return payload.detail || payload.message || JSON.stringify(payload);
  } catch {
    return body;
  }
}

async function waitForAttachmentExtraction(workflowId, storedName) {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    const response = await state.nativeFetch(
      `/api/workflows/${workflowId}/artifacts/extract-status?target_dir=attachments`,
      { cache: "no-store" },
    );
    if (response.ok) {
      const payload = await response.json();
      const status = payload?.files?.[storedName];
      if (status?.status === "done") {
        return status.extracted_path
          ? `attachments/${status.extracted_path}`
          : "";
      }
      if (status?.status === "failed") {
        throw new Error(status.error || "File text extraction failed");
      }
    }
    await wait(500);
  }
  throw new Error("File text extraction timed out");
}

function renderAttachmentStrip(parts = state.parts) {
  if (!parts?.composer) return;
  const row = parts.input.closest(".mw-composer-row, .flex.gap-2");
  if (!row) return;
  let strip = parts.composer.querySelector(".mw-attachment-strip");
  if (!strip) {
    strip = document.createElement("div");
    strip.className = "mw-attachment-strip";
    strip.setAttribute("role", "list");
    strip.setAttribute("aria-label", "已附加文件");
    parts.composer.insertBefore(strip, row);
  }
  strip.replaceChildren();
  strip.hidden = state.attachments.length === 0;
  state.attachments.forEach((item) => {
    const chip = document.createElement("div");
    chip.className = `mw-attachment-chip is-${item.status}`;
    chip.setAttribute("role", "listitem");
    chip.title = item.error || item.path;
    const visual = fileVisual(item.name);
    chip.append(createIcon(visual.icon, { size: 14, strokeWidth: 1.8 }));
    const label = document.createElement("span");
    label.className = "mw-attachment-name";
    label.textContent = item.name;
    chip.append(label);
    if (item.status !== "ready") {
      const status = document.createElement("span");
      status.className = "mw-attachment-status";
      status.textContent =
        item.status === "uploading"
          ? "上传中"
          : item.status === "processing"
            ? "解析中"
            : "失败";
      chip.append(status);
    }
    const remove = createLucideButton("X", `移除 ${item.name}`, "mw-attachment-remove");
    remove.disabled = item.status === "uploading" || item.status === "processing";
    remove.addEventListener("click", async () => {
      state.attachments = state.attachments.filter(
        (attachment) => attachment.id !== item.id,
      );
      renderAttachmentStrip(parts);
      if (!state.workflowId || !item.path) return;
      const paths = [item.path, item.extractedPath].filter(Boolean);
      await Promise.allSettled(
        paths.map((path) =>
          state.nativeFetch(
            `/api/editor/${state.workflowId}/file?path=${encodeURIComponent(path)}`,
            { method: "DELETE" },
          ),
        ),
      );
    });
    chip.append(remove);
    strip.append(chip);
  });
}

async function uploadAttachment(file, parts) {
  const workflowId = state.workflowId;
  if (!workflowId) return;
  const storedName = sanitizedAttachmentName(file.name);
  const item = {
    id: `${Date.now()}-${state.attachmentSerial}`,
    name: file.name || storedName,
    path: `attachments/${storedName}`,
    extractedPath: "",
    status: "uploading",
    error: "",
  };
  state.attachments.push(item);
  renderAttachmentStrip(parts);
  if (file.size > 100 * 1024 * 1024) {
    item.status = "error";
    item.error = "单个附件不能超过 100 MB";
    renderAttachmentStrip(parts);
    return;
  }

  try {
    const body = new FormData();
    body.append("files", file, storedName);
    const response = await state.nativeFetch(
      `/api/workflows/${workflowId}/artifacts/upload?target_dir=attachments`,
      { method: "POST", body },
    );
    if (!response.ok) throw new Error(await responseError(response));
    if (attachmentNeedsExtraction(storedName)) {
      item.status = "processing";
      renderAttachmentStrip(parts);
      try {
        item.extractedPath = await waitForAttachmentExtraction(
          workflowId,
          storedName,
        );
      } catch (error) {
        item.status = "error";
        item.error = String(error?.message || error);
        renderAttachmentStrip(parts);
        return;
      }
    }
    item.status = "ready";
  } catch (error) {
    item.status = "error";
    item.error = String(error?.message || error);
  }
  renderAttachmentStrip(parts);
  scheduleEnhance();
}

function uploadAttachments(files, parts) {
  const availableSlots = Math.max(0, 8 - state.attachments.length);
  const selected = Array.from(files || []).slice(0, availableSlots);
  selected.forEach((file) => void uploadAttachment(file, parts));
}

function createControlGroup(label) {
  const group = document.createElement("div");
  group.className = "mw-control-group";
  group.setAttribute("role", "group");
  group.setAttribute("aria-label", label);
  return group;
}

function ensureWorkspaceControls() {
  let controls = document.getElementById("mw-workspace-controls");
  if (controls) return controls;

  controls = document.createElement("div");
  controls.id = "mw-workspace-controls";
  controls.className = "mw-workspace-controls";
  controls.setAttribute("role", "toolbar");
  controls.setAttribute("aria-label", "工作区布局");

  const fileGroup = createControlGroup("文件面板");
  const filesButton = createLucideButton("PanelLeft", "显示或隐藏文件面板");
  filesButton.dataset.mwAction = "files";
  filesButton.addEventListener("click", () => {
    state.preferences.filesVisible = !state.preferences.filesVisible;
    savePreferences();
    applyWorkspaceState();
  });
  fileGroup.append(filesButton);

  const canvasGroup = createControlGroup("主工作区");
  [
    ["editor", "FileText", "仅显示编辑器"],
    ["split", "Columns2", "同时显示编辑器和预览"],
    ["preview", "Eye", "仅显示预览"],
  ].forEach(([mode, icon, label]) => {
    const button = createLucideButton(icon, label);
    button.dataset.mwCanvas = mode;
    button.addEventListener("click", () => {
      state.preferences.canvas = mode;
      savePreferences();
      applyWorkspaceState();
    });
    canvasGroup.append(button);
  });

  const layoutGroup = createControlGroup("Agent 布局");
  [
    ["auto", "LayoutDashboard", "自动布局"],
    ["right", "PanelRight", "Agent 停靠右侧"],
    ["bottom", "PanelBottom", "Agent 停靠底部"],
    ["float", "PanelsTopLeft", "Agent 浮动窗口"],
    ["focus", "Maximize2", "专注 Agent"],
    ["hidden", "EyeOff", "隐藏 Agent"],
  ].forEach(([mode, icon, label]) => {
    const button = createLucideButton(icon, label);
    button.dataset.mwLayout = mode;
    button.addEventListener("click", () => setLayout(mode));
    layoutGroup.append(button);
  });

  const extensionGroup = createControlGroup("扩展");
  const extensionButton = createLucideButton("Puzzle", "打开扩展中心");
  extensionButton.dataset.mwAction = "extensions";
  extensionButton.addEventListener("click", openExtensionDrawer);
  extensionGroup.append(extensionButton);

  controls.append(fileGroup, canvasGroup, layoutGroup, extensionGroup);
  document.body.append(controls);
  return controls;
}

function ensureAgentLauncher() {
  let launcher = document.getElementById("mw-agent-launcher");
  if (launcher) return launcher;
  launcher = createLucideButton("Bot", "显示 Agent", "mw-agent-launcher");
  launcher.id = "mw-agent-launcher";
  launcher.addEventListener("click", () => {
    setLayout(state.preferences.previousLayout || "auto");
  });
  document.body.append(launcher);
  return launcher;
}

function setLayout(layout) {
  if (layout === "hidden") {
    state.preferences.previousLayout =
      state.preferences.layout === "hidden" ? "auto" : state.preferences.layout;
  }
  state.preferences.layout = layout;
  savePreferences();
  applyWorkspaceState();
}

function isAgentRunning(parts) {
  return (
    Boolean(
      parts.composer.querySelector(
        '.mw-agent-action[data-mw-agent-action="stop"]',
      ),
    ) ||
    Array.from(parts.composer.querySelectorAll("button")).some(
      (button) => button.textContent?.trim() === "停止",
    ) || /执行中|思考中/.test(parts.thread.textContent || "")
  );
}

function isLiteAgentMode(parts) {
  const active = Array.from(parts.header.querySelectorAll("button")).find(
    (button) =>
      button.classList.contains("font-medium") &&
      /轻量|编辑助手|代码大师/.test(button.textContent || ""),
  );
  return Boolean(active) || selectedProfile()?.mode === "lite";
}

function computeAutoLayout(parts) {
  const width = window.innerWidth;
  if (width < 1180) return "bottom";
  const longConversation =
    parts.thread.scrollHeight > Math.max(parts.thread.clientHeight * 1.7, 900);
  if (isAgentRunning(parts) || longConversation) return "split";
  return "right";
}

function defaultFloatBounds() {
  const width = clamp(Math.round(window.innerWidth * 0.42), 430, 620);
  const height = clamp(Math.round(window.innerHeight * 0.72), 520, 760);
  return {
    left: Math.max(18, window.innerWidth - width - 24),
    top: 78,
    width,
    height,
  };
}

function normalizedFloatBounds() {
  const source = state.preferences.floatBounds || defaultFloatBounds();
  const width = clamp(Number(source.width) || 520, 390, window.innerWidth - 24);
  const height = clamp(Number(source.height) || 680, 420, window.innerHeight - 24);
  return {
    left: clamp(Number(source.left) || 18, 12, window.innerWidth - width - 12),
    top: clamp(Number(source.top) || 72, 62, window.innerHeight - height - 12),
    width,
    height,
  };
}

function applyFloatBounds(panel) {
  const bounds = normalizedFloatBounds();
  panel.style.setProperty("--mw-float-left", `${bounds.left}px`);
  panel.style.setProperty("--mw-float-top", `${bounds.top}px`);
  panel.style.setProperty("--mw-float-width", `${bounds.width}px`);
  panel.style.setProperty("--mw-float-height", `${bounds.height}px`);
}

function updateControlState() {
  const controls = document.getElementById("mw-workspace-controls");
  if (!controls) return;
  controls.querySelectorAll("[data-mw-layout]").forEach((button) => {
    const active = button.dataset.mwLayout === state.preferences.layout;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  controls.querySelectorAll("[data-mw-canvas]").forEach((button) => {
    const active = button.dataset.mwCanvas === state.preferences.canvas;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  const filesButton = controls.querySelector('[data-mw-action="files"]');
  filesButton?.classList.toggle("is-active", state.preferences.filesVisible);
  filesButton?.setAttribute(
    "aria-pressed",
    String(state.preferences.filesVisible),
  );
}

function applyWorkspaceState() {
  const parts = state.parts;
  if (!parts || !state.preferences) return;
  const requested = state.preferences.layout;
  const effective = requested === "auto" ? computeAutoLayout(parts) : requested;
  state.effectiveLayout = effective;
  parts.shell.dataset.mwLayout = effective;
  parts.shell.dataset.mwCanvas = state.preferences.canvas;
  parts.shell.classList.toggle(
    "mw-files-hidden",
    !state.preferences.filesVisible || effective === "focus",
  );
  parts.shell.style.setProperty(
    "--mw-agent-width",
    `${clamp(Number(state.preferences.agentWidth) || 460, 360, 680)}px`,
  );
  parts.shell.style.setProperty(
    "--mw-agent-bottom-height",
    `${clamp(Number(state.preferences.agentBottomHeight) || 360, 280, 620)}px`,
  );
  applyFloatBounds(parts.agentPanel);
  document.documentElement.dataset.mwLayout = effective;
  ensureAgentLauncher().classList.toggle("is-visible", effective === "hidden");
  updateControlState();
}

function installDockResizer(parts) {
  const { shell, agentPanel } = parts;
  let resizer = agentPanel.querySelector(":scope > .mw-agent-resizer");
  if (!resizer) {
    resizer = document.createElement("div");
    resizer.className = "mw-agent-resizer";
    resizer.setAttribute("role", "separator");
    resizer.setAttribute("aria-label", "调整 Agent 面板尺寸");
    resizer.tabIndex = 0;
    agentPanel.prepend(resizer);
  }
  if (resizer.dataset.mwReady === "true") return;
  resizer.dataset.mwReady = "true";

  resizer.addEventListener("pointerdown", (event) => {
    const layout = state.effectiveLayout;
    if (!["right", "split", "bottom"].includes(layout)) return;
    const visuallyBottom =
      layout === "bottom" ||
      (window.matchMedia("(max-width: 980px)").matches &&
        (layout === "right" || layout === "split"));
    event.preventDefault();
    const startX = event.clientX;
    const startY = event.clientY;
    const rect = agentPanel.getBoundingClientRect();
    document.documentElement.classList.add("mw-is-resizing");
    resizer.setPointerCapture?.(event.pointerId);

    const move = (moveEvent) => {
      if (visuallyBottom) {
        const height = clamp(rect.height + startY - moveEvent.clientY, 280, 620);
        state.preferences.agentBottomHeight = Math.round(height);
        shell.style.setProperty("--mw-agent-bottom-height", `${height}px`);
      } else {
        const width = clamp(rect.width + startX - moveEvent.clientX, 360, 680);
        state.preferences.agentWidth = Math.round(width);
        shell.style.setProperty("--mw-agent-width", `${width}px`);
      }
    };
    const end = () => {
      document.documentElement.classList.remove("mw-is-resizing");
      savePreferences();
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", end);
      window.removeEventListener("pointercancel", end);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", end, { once: true });
    window.addEventListener("pointercancel", end, { once: true });
  });
}

function installFloatDrag(parts) {
  const { header, agentPanel } = parts;
  if (header.dataset.mwFloatDrag === "true") return;
  header.dataset.mwFloatDrag = "true";
  header.addEventListener("pointerdown", (event) => {
    if (state.effectiveLayout !== "float") return;
    if (window.matchMedia("(max-width: 720px)").matches) return;
    if (event.target.closest("button, select, input, textarea, a")) return;
    event.preventDefault();
    const startX = event.clientX;
    const startY = event.clientY;
    const rect = agentPanel.getBoundingClientRect();
    header.setPointerCapture?.(event.pointerId);
    document.documentElement.classList.add("mw-is-dragging");

    const move = (moveEvent) => {
      const left = clamp(
        rect.left + moveEvent.clientX - startX,
        8,
        window.innerWidth - rect.width - 8,
      );
      const top = clamp(
        rect.top + moveEvent.clientY - startY,
        60,
        window.innerHeight - rect.height - 8,
      );
      agentPanel.style.setProperty("--mw-float-left", `${left}px`);
      agentPanel.style.setProperty("--mw-float-top", `${top}px`);
      state.preferences.floatBounds = {
        left: Math.round(left),
        top: Math.round(top),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
      };
    };
    const end = () => {
      document.documentElement.classList.remove("mw-is-dragging");
      savePreferences();
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", end);
      window.removeEventListener("pointercancel", end);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", end, { once: true });
    window.addEventListener("pointercancel", end, { once: true });
  });

  let resizeHandle = agentPanel.querySelector(":scope > .mw-float-resizer");
  if (!resizeHandle) {
    resizeHandle = document.createElement("div");
    resizeHandle.className = "mw-float-resizer";
    resizeHandle.setAttribute("role", "separator");
    resizeHandle.setAttribute("aria-label", "调整浮动 Agent 窗口尺寸");
    agentPanel.append(resizeHandle);
  }
  if (resizeHandle.dataset.mwReady !== "true") {
    resizeHandle.dataset.mwReady = "true";
    resizeHandle.addEventListener("pointerdown", (event) => {
      if (
        state.effectiveLayout !== "float" ||
        window.matchMedia("(max-width: 720px)").matches
      ) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      const startX = event.clientX;
      const startY = event.clientY;
      const rect = agentPanel.getBoundingClientRect();
      resizeHandle.setPointerCapture?.(event.pointerId);
      document.documentElement.classList.add("mw-is-resizing");
      const move = (moveEvent) => {
        const width = clamp(
          rect.width + moveEvent.clientX - startX,
          390,
          window.innerWidth - rect.left - 12,
        );
        const height = clamp(
          rect.height + moveEvent.clientY - startY,
          420,
          window.innerHeight - rect.top - 12,
        );
        agentPanel.style.setProperty("--mw-float-width", `${width}px`);
        agentPanel.style.setProperty("--mw-float-height", `${height}px`);
        state.preferences.floatBounds = {
          left: Math.round(rect.left),
          top: Math.round(rect.top),
          width: Math.round(width),
          height: Math.round(height),
        };
      };
      const end = () => {
        document.documentElement.classList.remove("mw-is-resizing");
        savePreferences();
        window.removeEventListener("pointermove", move);
        window.removeEventListener("pointerup", end);
        window.removeEventListener("pointercancel", end);
      };
      window.addEventListener("pointermove", move);
      window.addEventListener("pointerup", end, { once: true });
      window.addEventListener("pointercancel", end, { once: true });
    });
  }

  if (!agentPanel.__mwResizeObserver && "ResizeObserver" in window) {
    agentPanel.__mwResizeObserver = new ResizeObserver(() => {
      if (state.effectiveLayout !== "float") return;
      window.clearTimeout(state.resizeSaveTimer);
      state.resizeSaveTimer = window.setTimeout(() => {
        const rect = agentPanel.getBoundingClientRect();
        state.preferences.floatBounds = {
          left: Math.round(rect.left),
          top: Math.round(rect.top),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        };
        savePreferences();
      }, 160);
    });
    agentPanel.__mwResizeObserver.observe(agentPanel);
  }
}

function ensureProfileControls(parts) {
  const { header } = parts;
  const titleRow = header.firstElementChild;
  if (!titleRow) return;
  titleRow.classList.add("mw-agent-title-row");
  const title = titleRow.querySelector("p");
  title?.classList.add("mw-agent-title");

  let meta = header.querySelector(".mw-agent-meta");
  if (!meta) {
    meta = document.createElement("div");
    meta.className = "mw-agent-meta";
    const dot = document.createElement("span");
    dot.className = "mw-status-dot";
    const status = document.createElement("span");
    status.className = "mw-status-label";
    const separator = document.createElement("span");
    separator.className = "mw-meta-separator";
    const model = document.createElement("span");
    model.className = "mw-model-label";
    meta.append(dot, status, separator, model);
    titleRow.insertAdjacentElement("afterend", meta);
  }

  let profileRow = header.querySelector(".mw-profile-row");
  if (!profileRow) {
    profileRow = document.createElement("div");
    profileRow.className = "mw-profile-row";
    const select = document.createElement("select");
    select.className = "mw-profile-select";
    select.setAttribute("aria-label", "Agent Profile");
    select.addEventListener("change", () => {
      state.preferences.profileId = select.value;
      state.activeProfile = selectedProfile();
      savePreferences();
      syncProfileMode(parts, state.activeProfile);
      updateAgentMeta(parts);
      updateComposerContext(parts);
    });
    const extensions = createLucideButton("Puzzle", "打开扩展中心");
    extensions.addEventListener("click", openExtensionDrawer);
    profileRow.append(select, extensions);
    meta.insertAdjacentElement("afterend", profileRow);
  }

  const select = profileRow.querySelector("select");
  const profileSignature = (state.registry.agent_profiles || [])
    .map((profile) => `${profile.id}:${profile.label}`)
    .join("|");
  if (select.dataset.mwProfiles !== profileSignature) {
    select.replaceChildren();
    (state.registry.agent_profiles || []).forEach((profile) => {
      const option = document.createElement("option");
      option.value = profile.id;
      option.textContent = profile.label;
      select.append(option);
    });
    select.dataset.mwProfiles = profileSignature;
  }
  if (select.value !== state.preferences.profileId) {
    select.value = state.preferences.profileId;
  }

  Array.from(header.children).forEach((element) => {
    if (
      element.tagName === "DIV" &&
      element.querySelectorAll(":scope > button").length >= 2 &&
      !element.classList.contains("mw-agent-title-row") &&
      !element.classList.contains("mw-profile-row")
    ) {
      element.classList.add("mw-agent-segmented");
    }
  });
  updateAgentMeta(parts);
  syncProfileMode(parts, selectedProfile());
}

function syncProfileMode(parts, profile) {
  if (!profile) return;
  const title = parts.header.querySelector(".mw-agent-title")?.textContent || "";
  const wantsLite = profile.mode === "lite";
  const isLite = /轻量|代码大师|编辑助手/.test(title);
  if (wantsLite === isLite) return;
  const target = Array.from(parts.header.querySelectorAll("button")).find((button) => {
    const text = button.textContent?.trim() || "";
    return wantsLite ? text.includes("轻量") : text === "AI Agent";
  });
  target?.click();
}

function updateAgentMeta(parts) {
  const profile = selectedProfile();
  state.activeProfile = profile;
  const running = isAgentRunning(parts);
  const status = parts.header.querySelector(".mw-status-label");
  const dot = parts.header.querySelector(".mw-status-dot");
  const nextStatus = running ? "运行中" : "就绪";
  if (status && status.textContent !== nextStatus) status.textContent = nextStatus;
  dot?.classList.toggle("is-running", running);
  if (profile?.accent) {
    parts.agentPanel.style.setProperty("--mw-profile-accent", profile.accent);
  }
  const agentName = activeAgentName(parts);
  const runtime = selectedRuntime(agentName);
  const model =
    runtime === "local_claude"
      ? state.settings?.[`${agentName}_claude_model`] ||
        state.settings?.claude_model ||
        "Claude Code"
      : state.settings?.[`${agentName}_model_id`];
  const modelLabel = parts.header.querySelector(".mw-model-label");
  const nextModel = model || "模型未配置";
  if (modelLabel && modelLabel.textContent !== nextModel) {
    modelLabel.textContent = nextModel;
    modelLabel.title = model ? `当前模型: ${model}` : "当前模型未配置";
  }
  const composerModel = parts.composer.querySelector(".mw-composer-model-text");
  if (composerModel && composerModel.textContent !== nextModel) {
    composerModel.textContent = nextModel;
  }
  const runtimeSelect = parts.composer.querySelector(".mw-runtime-select");
  if (runtimeSelect && runtimeSelect.value !== runtime) runtimeSelect.value = runtime;
  const effortSelect = parts.composer.querySelector(".mw-effort-select");
  const effort = selectedEffort(agentName, runtime);
  if (effortSelect && effortSelect.value !== effort) effortSelect.value = effort;
  const composerModelControl = parts.composer.querySelector(".mw-composer-model");
  if (composerModelControl) {
    const requested = effort === "default" ? "默认" : effort;
    const effective =
      runtime === "local_claude" && state.claudeCapability?.effective_effort
        ? state.claudeCapability.effective_effort
        : requested;
    composerModelControl.title = [
      model ? `当前模型: ${model}` : "当前模型未配置",
      `运行时: ${runtime === "local_claude" ? "本机 Claude" : "开放模型"}`,
      `思考强度: ${requested}${effective !== requested ? ` -> ${effective}` : ""}`,
    ].join("\n");
  }
}

function messageContent(message) {
  const content = Array.from(message.children).find(
    (element) =>
      element.tagName !== "SPAN" &&
      !element.classList.contains("mw-message-actions"),
  );
  return (content?.innerText || content?.textContent || "").trim();
}

function stripProfileEnvelope(text) {
  const endMarker = text.startsWith(PROFILE_MARKER)
    ? PROFILE_END_MARKER
    : text.startsWith(LEGACY_PROFILE_MARKER)
      ? LEGACY_PROFILE_END_MARKER
      : null;
  if (!endMarker) return text;
  const end = text.indexOf(endMarker);
  if (end < 0) return text;
  return text.slice(end + endMarker.length).trimStart();
}

function cleanVisibleProfileEnvelope(message) {
  const content = Array.from(message.children).find(
    (element) =>
      element.tagName !== "SPAN" &&
      !element.classList.contains("mw-message-actions"),
  );
  if (!content) return;
  const raw = (content.innerText || content.textContent || "").trim();
  const clean = stripProfileEnvelope(raw);
  if (clean !== raw) content.textContent = clean;
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const helper = document.createElement("textarea");
  helper.value = text;
  helper.style.position = "fixed";
  helper.style.opacity = "0";
  document.body.append(helper);
  helper.select();
  document.execCommand("copy");
  helper.remove();
}

function installMessageActions(message, role, input) {
  if (message.querySelector(":scope > .mw-message-actions")) return;
  const actions = document.createElement("div");
  actions.className = "mw-message-actions";
  const copy = createIconButton("⧉", "复制消息");
  copy.addEventListener("click", async () => {
    const text = messageContent(message);
    if (!text) return;
    try {
      await copyText(text);
      copy.textContent = "✓";
      window.setTimeout(() => {
        copy.textContent = "⧉";
      }, 1100);
    } catch {
      copy.title = "复制失败";
    }
  });
  actions.append(copy);
  if (role === "user") {
    const reuse = createIconButton("↩", "复用这条指令");
    reuse.addEventListener("click", () => {
      const text = messageContent(message);
      if (text) setReactValue(input, text);
    });
    actions.append(reuse);
  }
  message.append(actions);
}

function decorateMessages(parts) {
  let count = 0;
  Array.from(parts.thread.children).forEach((element) => {
    const label = element.firstElementChild;
    const roleText = label?.tagName === "SPAN" ? label.textContent?.trim() : "";
    if (roleText !== "你" && roleText !== "AI") return;
    const role = roleText === "你" ? "user" : "assistant";
    count += 1;
    element.classList.add("mw-message");
    element.dataset.role = role;
    label.classList.add("mw-message-label");
    if (role === "user") cleanVisibleProfileEnvelope(element);
    const content = messageContent(element);
    element.classList.toggle(
      "is-activity",
      /LOG 日志|执行中|正在后台运行|运行成功|运行失败/.test(content),
    );
    installMessageActions(element, role, parts.input);
  });
  const empty = Array.from(parts.thread.children).find(
    (element) =>
      !element.classList.contains("mw-message") &&
      element.classList.contains("space-y-2"),
  );
  empty?.classList.toggle("mw-agent-empty", count === 0);
}

function currentFileLabel(parts) {
  const candidates = Array.from(parts.workbench.querySelectorAll("span"));
  const match = candidates.find(
    (element) =>
      element.classList.contains("font-mono") &&
      element.classList.contains("text-xs"),
  );
  return (match?.textContent || "未选择文件").trim().split(/\s{2,}/)[0];
}

function updateComposerContext(parts) {
  const profile = selectedProfile();
  let context = parts.composer.querySelector(".mw-context-strip");
  const row = parts.input.closest(".flex.gap-2");
  if (!context) {
    context = document.createElement("div");
    context.className = "mw-context-strip";
    const file = document.createElement("span");
    file.className = "mw-context-file";
    const profileLabel = document.createElement("span");
    profileLabel.className = "mw-context-profile";
    context.append(file, profileLabel);
    parts.composer.insertBefore(context, row);
  }
  const file = context.querySelector(".mw-context-file");
  const profileLabel = context.querySelector(".mw-context-profile");
  const nextFile = currentFileLabel(parts);
  const nextProfile = profile?.label || "通用执行";
  if (file.textContent !== nextFile) file.textContent = nextFile;
  if (profileLabel.textContent !== nextProfile) profileLabel.textContent = nextProfile;
}

function closeCommandPalette() {
  document.getElementById("mw-command-palette")?.remove();
}

function openCommandPalette(parts, anchor) {
  closeCommandPalette();
  const palette = document.createElement("div");
  palette.id = "mw-command-palette";
  palette.className = "mw-command-palette";
  palette.setAttribute("role", "menu");
  (state.registry.commands || []).forEach((command) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mw-command-item";
    button.setAttribute("role", "menuitem");
    const label = document.createElement("strong");
    label.textContent = command.label;
    const description = document.createElement("span");
    description.textContent = command.description || "";
    button.append(label, description);
    button.addEventListener("click", () => {
      setReactValue(parts.input, command.prompt);
      closeCommandPalette();
    });
    palette.append(button);
  });
  document.body.append(palette);
  const rect = anchor.getBoundingClientRect();
  const width = Math.min(360, window.innerWidth - 24);
  palette.style.width = `${width}px`;
  palette.style.left = `${clamp(rect.left, 12, window.innerWidth - width - 12)}px`;
  const top = rect.top - palette.offsetHeight - 10;
  palette.style.top = `${Math.max(68, top)}px`;
  window.setTimeout(() => {
    document.addEventListener(
      "pointerdown",
      (event) => {
        if (!palette.contains(event.target) && event.target !== anchor) {
          closeCommandPalette();
        }
      },
      { once: true },
    );
  });
}

function enhanceComposer(parts) {
  const row = parts.input.closest(".flex.gap-2");
  if (!row) return;
  row?.classList.add("mw-composer-row");
  parts.input.classList.add("mw-agent-input");
  parts.input.setAttribute("aria-label", "向 Agent 发送指令");
  parts.input.setAttribute("aria-multiline", "true");
  if (parts.input instanceof HTMLTextAreaElement) {
    const grow = () => {
      parts.input.style.height = "auto";
      parts.input.style.height = `${clamp(parts.input.scrollHeight, 104, 260)}px`;
    };
    if (parts.input.dataset.mwGrow !== "true") {
      parts.input.addEventListener("input", grow);
      parts.input.dataset.mwGrow = "true";
    }
    grow();
  }

  let commandButton = row.querySelector(".mw-command-trigger");
  if (!commandButton) {
    commandButton = createLucideButton(
      "Command",
      "打开命令面板",
      "mw-command-trigger",
    );
    commandButton.addEventListener("click", () => openCommandPalette(parts, commandButton));
    row.prepend(commandButton);
  }
  setControlIcon(commandButton, "Command", "打开命令面板");

  let fileInput = parts.composer.querySelector(".mw-attachment-input");
  if (!fileInput) {
    fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.multiple = true;
    fileInput.className = "mw-attachment-input";
    fileInput.setAttribute("aria-label", "选择要交给 Agent 的文件");
    fileInput.addEventListener("change", () => {
      uploadAttachments(fileInput.files, parts);
      fileInput.value = "";
    });
    parts.composer.append(fileInput);
  }

  let attachmentButton = row.querySelector(".mw-attachment-trigger");
  if (!attachmentButton) {
    attachmentButton = createLucideButton(
      "Paperclip",
      "添加文件",
      "mw-attachment-trigger",
    );
    attachmentButton.addEventListener("click", () => fileInput.click());
    commandButton.insertAdjacentElement("afterend", attachmentButton);
  }

  const imageButton = Array.from(row.querySelectorAll(":scope > button")).find(
    (button) =>
      !button.classList.contains("mw-command-trigger") &&
      !button.classList.contains("mw-attachment-trigger") &&
      !button.hasAttribute("data-send-btn") &&
      /IMG|生图/.test(button.textContent || ""),
  );
  if (imageButton) {
    imageButton.classList.add("mw-image-trigger");
    setControlIcon(imageButton, "Sparkles", "生成示意图");
  }

  let composerModel = row.querySelector(".mw-composer-model");
  if (!composerModel) {
    composerModel = document.createElement("span");
    composerModel.className = "mw-composer-model";
    composerModel.append(createIcon("Bot", { size: 14, strokeWidth: 1.8 }));
    const modelText = document.createElement("span");
    modelText.className = "mw-composer-model-text";
    composerModel.append(modelText);
    row.append(composerModel);
  }

  let runtimeSelect = composerModel.querySelector(".mw-runtime-select");
  if (!runtimeSelect) {
    let runtimeChangeSerial = 0;
    runtimeSelect = document.createElement("select");
    runtimeSelect.className = "mw-runtime-select";
    runtimeSelect.setAttribute("aria-label", "Agent 运行时");
    [
      ["openai_compatible", "开放模型"],
      ["local_claude", "本机 Claude"],
    ].forEach(([value, label]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      runtimeSelect.append(option);
    });
    runtimeSelect.addEventListener("change", async () => {
      const agentName = activeAgentName(parts);
      const runtimeKey = ROLE_RUNTIME_KEYS[agentName];
      const nextRuntime = runtimeSelect.value;
      const previous = selectedRuntime(agentName);
      const requestId = ++runtimeChangeSerial;
      setOptimisticSetting(runtimeKey, nextRuntime);
      try {
        if (nextRuntime === "local_claude") {
          const payload = await loadClaudeCapability(true);
          if (!payload?.compatible) throw new Error("未检测到可用的本机 Claude Code");
        }
        if (requestId !== runtimeChangeSerial) return;
        await saveSettingsPatch({ [runtimeKey]: nextRuntime });
      } catch (error) {
        if (requestId !== runtimeChangeSerial) return;
        if (state.settings?.[runtimeKey] === nextRuntime) {
          restoreSetting(runtimeKey, previous);
          runtimeSelect.value = previous;
        }
        runtimeSelect.title = String(error?.message || error);
      }
    });
    composerModel.append(runtimeSelect);
  }

  let effortSelect = composerModel.querySelector(".mw-effort-select");
  if (!effortSelect) {
    let effortChangeSerial = 0;
    effortSelect = document.createElement("select");
    effortSelect.className = "mw-effort-select";
    effortSelect.setAttribute("aria-label", "思考强度");
    [
      ["default", "默认"],
      ["off", "关闭"],
      ["low", "低"],
      ["medium", "中"],
      ["high", "高"],
      ["xhigh", "极高"],
      ["max", "最大"],
    ].forEach(([value, label]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      effortSelect.append(option);
    });
    effortSelect.addEventListener("change", async () => {
      const agentName = activeAgentName(parts);
      const runtime = selectedRuntime(agentName);
      const key = `${agentName}_reasoning_effort`;
      const nextEffort = effortSelect.value;
      const fallback = runtime === "local_claude" ? "high" : "default";
      const previous = state.settings?.[key] || fallback;
      const requestId = ++effortChangeSerial;
      setOptimisticSetting(key, nextEffort);
      try {
        await saveSettingsPatch({ [key]: nextEffort });
      } catch (error) {
        if (requestId !== effortChangeSerial) return;
        if (state.settings?.[key] === nextEffort) {
          restoreSetting(key, previous);
          effortSelect.value = previous;
        }
        effortSelect.title = String(error?.message || error);
      }
    });
    composerModel.append(effortSelect);
  }

  const send = row.querySelector("[data-send-btn]");
  const stop = Array.from(row.querySelectorAll(":scope > button")).find(
    (button) =>
      button.dataset.mwAgentAction === "stop" ||
      button.textContent?.trim() === "停止",
  );
  const action = send || stop;
  if (action) {
    if (composerModel.nextElementSibling !== action) {
      row.insertBefore(composerModel, action);
    }
    const stopping = !send;
    action.classList.add("mw-agent-action");
    action.dataset.mwAgentAction = stopping ? "stop" : "send";
    setControlIcon(
      action,
      stopping ? "Square" : "ArrowUp",
      stopping ? "终止 Agent" : "发送 (Enter)",
    );
    const busy = state.attachments.some(
      (item) => item.status === "uploading" || item.status === "processing",
    );
    if (!stopping) {
      action.disabled = busy || !parts.input.value.trim();
    }
    attachmentButton.disabled = stopping || busy;
    fileInput.disabled = stopping || busy;
  }

  if (parts.input.dataset.mwAttachmentGuard !== "true") {
    parts.input.dataset.mwAttachmentGuard = "true";
    parts.input.addEventListener(
      "keydown",
      (event) => {
        const busy = state.attachments.some(
          (item) => item.status === "uploading" || item.status === "processing",
        );
        if (busy && event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          event.stopImmediatePropagation();
        }
      },
      true,
    );
  }

  if (parts.composer.dataset.mwDropReady !== "true") {
    parts.composer.dataset.mwDropReady = "true";
    parts.composer.addEventListener("dragover", (event) => {
      if (!event.dataTransfer?.types.includes("Files")) return;
      event.preventDefault();
      parts.composer.classList.add("is-dragging-file");
    });
    parts.composer.addEventListener("dragleave", (event) => {
      if (!parts.composer.contains(event.relatedTarget)) {
        parts.composer.classList.remove("is-dragging-file");
      }
    });
    parts.composer.addEventListener("drop", (event) => {
      if (!event.dataTransfer?.files?.length) return;
      event.preventDefault();
      parts.composer.classList.remove("is-dragging-file");
      if (isAgentRunning(parts)) return;
      uploadAttachments(event.dataTransfer.files, parts);
    });
  }

  updateComposerContext(parts);
  renderAttachmentStrip(parts);
  updateAgentMeta(parts);
}

function ensureJumpButton(parts) {
  let button = parts.agentPanel.querySelector(":scope > .mw-jump-latest");
  if (!button) {
    button = createIconButton("↓", "跳到最新消息", "mw-jump-latest");
    button.addEventListener("click", () => {
      parts.thread.scrollTo({ top: parts.thread.scrollHeight, behavior: "smooth" });
    });
    parts.agentPanel.insertBefore(button, parts.composer);
  }
  if (parts.thread.dataset.mwScroll !== "true") {
    const update = () => {
      const distance =
        parts.thread.scrollHeight - parts.thread.scrollTop - parts.thread.clientHeight;
      button.classList.toggle("is-visible", distance > 140);
    };
    parts.thread.addEventListener("scroll", update, { passive: true });
    parts.thread.dataset.mwScroll = "true";
    update();
  }
}

function closeExtensionDrawer() {
  document.getElementById("mw-extension-overlay")?.remove();
}

function extensionSection(title, values, renderRow) {
  const section = document.createElement("section");
  section.className = "mw-extension-section";
  const heading = document.createElement("h3");
  heading.textContent = title;
  section.append(heading);
  const list = document.createElement("div");
  list.className = "mw-extension-list";
  if (!values.length) {
    const empty = document.createElement("p");
    empty.className = "mw-extension-empty";
    empty.textContent = "暂无项目";
    list.append(empty);
  } else {
    values.forEach((value) => list.append(renderRow(value)));
  }
  section.append(list);
  return section;
}

function extensionRow(title, subtitle, badge, tone = "neutral") {
  const row = document.createElement("div");
  row.className = "mw-extension-row";
  const text = document.createElement("div");
  const strong = document.createElement("strong");
  strong.textContent = title;
  const detail = document.createElement("span");
  detail.textContent = subtitle || "";
  text.append(strong, detail);
  const chip = document.createElement("span");
  chip.className = "mw-extension-chip";
  chip.textContent = badge;
  chip.dataset.tone = tone;
  row.append(text, chip);
  return row;
}

function renderExtensionDrawer() {
  const body = document.querySelector("#mw-extension-overlay .mw-extension-body");
  if (!body) return;
  body.replaceChildren();
  body.append(
    extensionSection("已发现扩展", state.registry.extensions || [], (extension) =>
      extensionRow(
        extension.name,
        `${extension.id} · ${extension.version}`,
        extension.source === "user" ? "用户" : "内置",
      ),
    ),
    extensionSection("Agent Profiles", state.registry.agent_profiles || [], (profile) =>
      extensionRow(
        profile.label,
        profile.description,
        profile.source === "user" ? "用户" : "内置",
      ),
    ),
    extensionSection("命令", state.registry.commands || [], (command) =>
      extensionRow(command.label, command.description, "Prompt"),
    ),
    extensionSection("Tool Adapters", state.registry.tool_adapters || [], (tool) =>
      extensionRow(
        tool.label,
        [tool.description, ...(tool.permissions || [])].filter(Boolean).join(" · "),
        tool.enabled ? "启用" : "未启用",
        tool.enabled ? "allowed" : "blocked",
      ),
    ),
    extensionSection("视图", state.registry.views || [], (view) =>
      extensionRow(
        view.label,
        `${view.description || ""}${view.output_contract ? ` · ${view.output_contract}` : ""}`,
        view.kind,
      ),
    ),
    extensionSection("操作", state.registry.actions || [], (action) =>
      extensionRow(
        action.label,
        [action.description, ...(action.permissions || [])].filter(Boolean).join(" · "),
        action.enabled ? "可用" : "已阻止",
        action.enabled ? "allowed" : "blocked",
      ),
    ),
  );
  if (state.registry.errors?.length) {
    body.append(
      extensionSection("加载问题", state.registry.errors, (error) =>
        extensionRow(error.manifest || "manifest.json", error.message, error.source),
      ),
    );
  }
}

function openExtensionDrawer() {
  closeExtensionDrawer();
  const overlay = document.createElement("div");
  overlay.id = "mw-extension-overlay";
  overlay.className = "mw-extension-overlay";
  const drawer = document.createElement("div");
  drawer.className = "mw-extension-drawer";
  drawer.setAttribute("role", "dialog");
  drawer.setAttribute("aria-modal", "true");
  drawer.setAttribute("aria-label", "扩展中心");
  const header = document.createElement("header");
  const title = document.createElement("div");
  const heading = document.createElement("h2");
  heading.textContent = "扩展中心";
  const version = document.createElement("span");
  version.textContent = `Manifest ${state.registry.schema_version || "1.0"}`;
  title.append(heading, version);
  const actions = document.createElement("div");
  const refresh = createLucideButton("RefreshCw", "刷新扩展");
  refresh.addEventListener("click", async () => {
    refresh.disabled = true;
    await loadRegistry(true);
    renderExtensionDrawer();
    refresh.disabled = false;
  });
  const close = createLucideButton("X", "关闭扩展中心");
  close.addEventListener("click", closeExtensionDrawer);
  actions.append(refresh, close);
  header.append(title, actions);
  const body = document.createElement("div");
  body.className = "mw-extension-body";
  drawer.append(header, body);
  overlay.append(drawer);
  overlay.addEventListener("pointerdown", (event) => {
    if (event.target === overlay) closeExtensionDrawer();
  });
  document.body.append(overlay);
  renderExtensionDrawer();
}

function markEditorParts(parts) {
  parts.shell.classList.add("mw-editor-shell");
  parts.filesPanel.classList.add("mw-files-panel");
  parts.workbench.classList.add("mw-workbench");
  parts.editorSurface?.classList.add("mw-editor-surface");
  parts.previewSurface?.classList.add("mw-preview-surface");
  parts.agentPanel.classList.add("mw-agent-panel");
  parts.header.classList.add("mw-agent-header");
  parts.thread.classList.add("mw-agent-thread");
  parts.composer.classList.add("mw-agent-composer");
}

function teardownEditorChrome() {
  document.documentElement.classList.remove("mw-editor-active");
  delete document.documentElement.dataset.mwLayout;
  document.getElementById("mw-workspace-controls")?.remove();
  document.getElementById("mw-agent-launcher")?.remove();
  closeCommandPalette();
  closeExtensionDrawer();
  state.parts = null;
}

function enhanceEditor() {
  const workflowId = routeWorkflowId();
  if (!workflowId) {
    teardownEditorChrome();
    return;
  }
  if (state.workflowId !== workflowId || !state.preferences) {
    if (state.workflowId && state.workflowId !== workflowId) {
      state.attachments = [];
    }
    state.workflowId = workflowId;
    state.preferences = loadPreferences(workflowId);
    state.activeProfile = selectedProfile();
  }
  document.documentElement.classList.add("mw-editor-active");
  const parts = findEditorParts();
  if (!parts) return;
  state.parts = parts;
  markEditorParts(parts);
  ensureWorkspaceControls();
  ensureAgentLauncher();
  installDockResizer(parts);
  installFloatDrag(parts);
  ensureProfileControls(parts);
  decorateMessages(parts);
  enhanceComposer(parts);
  ensureJumpButton(parts);
  applyWorkspaceState();
  loadRegistry();
  loadSettings();
  loadClaudeCapability();
}

function scheduleEnhance() {
  if (state.scheduled) return;
  state.scheduled = true;
  window.requestAnimationFrame(() => {
    state.scheduled = false;
    enhanceEditor();
  });
}

installFetchProfileAdapter();
const root = document.getElementById("root");
if (root) {
  new MutationObserver(scheduleEnhance).observe(root, {
    childList: true,
    subtree: true,
    characterData: true,
  });
}
window.addEventListener("popstate", scheduleEnhance);
window.addEventListener("resize", scheduleEnhance, { passive: true });
window.addEventListener("arhub:open-extensions", async () => {
  await loadRegistry();
  openExtensionDrawer();
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeCommandPalette();
    closeExtensionDrawer();
  }
});
scheduleEnhance();

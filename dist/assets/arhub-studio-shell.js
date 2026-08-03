import { createIcon, fileVisual } from "./arhub-icons.js";

const EDITOR_ROUTE = /^\/workflow\/[^/]+\/editor\/?$/;
const WORKFLOW_ROUTE = /^\/workflow\/[^/]+\/?$/;
const ARTIFACT_ROUTE = /^\/workflow\/[^/]+\/artifact\//;
const FILE_NAME_PATTERN = /(?:^|\/)[^/]+\.[a-z0-9]{1,8}$/i;
const TYPE_MARKERS = new Set([
  "MD",
  "MARKDOWN",
  "PDF",
  "DOC",
  "DOCX",
  "TXT",
  "JSON",
  "YAML",
  "YML",
  "CSV",
  "XLSX",
  "PPTX",
  "IMG",
  "IMAGE",
  "PY",
  "JS",
  "TS",
  "DRAWIO",
]);

const KICKERS = Object.freeze({
  workflows: "ARHUB WORKSPACE",
  workflow: "WORKFLOW STUDIO",
  artifact: "ARTIFACT VIEWER",
  settings: "SYSTEM SETTINGS",
  new: "NEW WORKFLOW",
});

let scheduled = false;
let runtimeSettingsPromise = null;

function currentView() {
  const path = window.location.pathname;
  if (EDITOR_ROUTE.test(path)) return "";
  if (ARTIFACT_ROUTE.test(path)) return "artifact";
  if (WORKFLOW_ROUTE.test(path)) return "workflow";
  if (path.startsWith("/settings")) return "settings";
  if (path === "/new" || path === "/new/") return "new";
  return "workflows";
}

function normalizedText(element) {
  return String(element?.textContent || "")
    .replace(/\s+/g, " ")
    .trim();
}

function hasDirectClass(element, className) {
  return Array.from(element.children).some((child) => child.classList?.contains(className));
}

function addLeadingIcon(element, iconName, className, size = 16) {
  if (!(element instanceof HTMLElement) || hasDirectClass(element, className)) return;
  const holder = document.createElement("span");
  holder.className = className;
  holder.setAttribute("aria-hidden", "true");
  holder.append(createIcon(iconName, { size, strokeWidth: 1.75 }));
  element.prepend(holder);
}

function actionIcon(label) {
  if (/^(?:导入|上传文件)$/.test(label)) return "Upload";
  if (/^下载$/.test(label)) return "Download";
  if (/^导出$/.test(label)) return "ArrowDown";
  if (/^全屏查看$/.test(label)) return "ExternalLink";
  if (/^(?:重新运行|重新执行此步骤)$/.test(label)) return "RefreshCw";
  if (/^测试连接$/.test(label)) return "Link2";
  if (/^保存(?:配置|设置)?$/.test(label)) return "Save";
  if (/^编辑器$/.test(label)) return "FilePenLine";
  if (/^新建工作流$/.test(label)) return "Plus";
  return "";
}

function decorateActions(main) {
  main.querySelectorAll("button, a").forEach((element) => {
    const label = normalizedText(element);
    const iconName = actionIcon(label.replace(/^\+\s*/, ""));
    if (!iconName || label.length > 40) return;
    if (/^\+\s*新建工作流$/.test(label)) {
      Array.from(element.childNodes).forEach((node) => {
        if (node.nodeType === Node.TEXT_NODE) {
          node.textContent = String(node.textContent || "").replace(/^\s*\+\s*/, "");
        }
      });
    }
    element.classList.add("arhub-studio-action");
    addLeadingIcon(element, iconName, "arhub-studio-action-icon");
  });
}

function decorateKicker(main, view) {
  const heading = main.querySelector("h1");
  const parent = heading?.parentElement;
  if (!(heading instanceof HTMLElement) || !(parent instanceof HTMLElement)) return;
  let kicker = Array.from(parent.children).find((child) =>
    child.classList?.contains("arhub-studio-kicker"),
  );
  if (!(kicker instanceof HTMLElement)) {
    kicker = document.createElement("span");
    kicker.className = "arhub-studio-kicker";
    parent.insertBefore(kicker, heading);
  }
  if (!kicker.querySelector(":scope > svg")) {
    kicker.append(createIcon(view === "settings" ? "SlidersHorizontal" : "Sparkles", {
      size: 13,
      strokeWidth: 1.9,
    }));
  }
  let caption = kicker.querySelector(":scope > .arhub-studio-kicker-text");
  if (!(caption instanceof HTMLElement)) {
    caption = document.createElement("span");
    caption.className = "arhub-studio-kicker-text";
    kicker.append(caption);
  }
  caption.textContent = KICKERS[view] || "ARHUB STUDIO";
}

function decorateWorkflowSummary(main) {
  const stats = main.querySelector(".grid.grid-cols-4");
  if (stats instanceof HTMLElement) {
    stats.classList.add("arhub-studio-stat-grid");
    const iconByLabel = ["LayoutDashboard", "Zap", "Check", "CircleDotDashed"];
    Array.from(stats.children).forEach((card, index) => {
      if (!(card instanceof HTMLElement)) return;
      card.classList.add("arhub-studio-stat");
      card.dataset.arhubStat = String(index);
      if (!hasDirectClass(card, "arhub-studio-stat-icon")) {
        const icon = document.createElement("span");
        icon.className = "arhub-studio-stat-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.append(createIcon(iconByLabel[index] || "Gauge", { size: 16, strokeWidth: 1.8 }));
        card.prepend(icon);
      }
    });
  }

  main.querySelectorAll(".space-y-2 > .card").forEach((row) => {
    if (!(row instanceof HTMLElement)) return;
    const link = row.querySelector('a[href^="/workflow/"]');
    if (!(link instanceof HTMLElement)) return;
    row.classList.add("arhub-studio-workflow-row");
    link.classList.add("arhub-studio-workflow-title");
    addLeadingIcon(link, "Workflow", "arhub-studio-workflow-icon", 18);
  });
}

function findArtifactRow(button, main) {
  let row = button.parentElement;
  for (let depth = 0; row && row !== main && depth < 4; depth += 1, row = row.parentElement) {
    if (row.querySelector('a[href*="/artifacts/"]')) return row;
  }
  return null;
}

function decorateFileRows(main) {
  main.querySelectorAll("button").forEach((button) => {
    const fileName = normalizedText(button);
    if (!FILE_NAME_PATTERN.test(fileName)) return;
    const row = findArtifactRow(button, main);
    if (!(row instanceof HTMLElement)) return;
    row.classList.add("arhub-studio-file-row");
    button.classList.add("arhub-studio-file-name");
    const visual = fileVisual(fileName);
    addLeadingIcon(button, visual.icon, "arhub-studio-file-name-icon", 16);
  });

  main.querySelectorAll("button").forEach((button) => {
    const label = normalizedText(button);
    if (!/\d+\s*个文件$/.test(label)) return;
    button.classList.add("arhub-studio-artifact-group");
    addLeadingIcon(button, "FolderOpen", "arhub-studio-artifact-group-icon", 16);
  });

  main.querySelectorAll(".arhub-studio-file-row").forEach((row) => {
    row.querySelectorAll("a").forEach((link) => {
      const label = normalizedText(link);
      if (label === "下载") addLeadingIcon(link, "Download", "arhub-studio-inline-link-icon", 14);
      if (label === "全屏查看") {
        addLeadingIcon(link, "ExternalLink", "arhub-studio-inline-link-icon", 14);
      }
    });
  });
}

function decorateFileTypeMarkers(main) {
  main.querySelectorAll("div, span").forEach((marker) => {
    if (!(marker instanceof HTMLElement) || marker.children.length > 0) return;
    const type = normalizedText(marker).toUpperCase();
    if (!TYPE_MARKERS.has(type) || marker.dataset.arhubStudioType === type) return;
    const row = marker.closest(".arhub-studio-file-row");
    if (!(row instanceof HTMLElement)) return;
    const fileName = normalizedText(row.querySelector(".arhub-studio-file-name"));
    if (!FILE_NAME_PATTERN.test(fileName)) return;
    const visual = fileVisual(fileName);
    marker.dataset.arhubStudioType = type;
    marker.classList.add("arhub-studio-file-type");
    marker.setAttribute("title", `${visual.label} file`);
    marker.setAttribute("aria-label", `${visual.label} file`);
    marker.replaceChildren(createIcon(visual.icon, { size: 17, strokeWidth: 1.8 }));
  });
}

function findLeafTextElement(root, pattern) {
  return Array.from(root.querySelectorAll("span, div, p")).find((element) =>
    element.children.length === 0 && pattern.test(normalizedText(element)),
  );
}

function decoratePipeline(main) {
  const grid = main.querySelector(".grid.grid-cols-1");
  const pipeline = grid?.firstElementChild;
  if (!(pipeline instanceof HTMLElement) || !pipeline.classList.contains("space-y-2")) return;
  pipeline.classList.add("arhub-studio-pipeline");
  Array.from(pipeline.children).forEach((row) => {
    if (!(row instanceof HTMLElement)) return;
    const toggle = Array.from(row.children).find((child) => child instanceof HTMLButtonElement);
    if (!(toggle instanceof HTMLButtonElement) || !/^[✓✔]/.test(normalizedText(toggle))) return;
    row.classList.add("arhub-studio-step-row");
    toggle.classList.add("arhub-studio-step-toggle");

    const check = findLeafTextElement(toggle, /^[✓✔]$/);
    if (check instanceof HTMLElement && !check.classList.contains("arhub-studio-status-icon")) {
      check.className = `${check.className} arhub-studio-status-icon`.trim();
      check.replaceChildren(createIcon("Check", { size: 15, strokeWidth: 2.2 }));
      check.setAttribute("aria-label", "completed");
    }

    const checkpoint = findLeafTextElement(toggle, /检查点/);
    if (checkpoint instanceof HTMLElement) {
      checkpoint.classList.add("arhub-studio-checkpoint");
      addLeadingIcon(checkpoint, "Flag", "arhub-studio-checkpoint-icon", 13);
    }
  });
}

function settingsSelect(options) {
  const select = document.createElement("select");
  options.forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    select.append(option);
  });
  return select;
}

function runtimeField(labelText, control, setting) {
  const field = document.createElement("label");
  field.className = "arhub-studio-field arhub-runtime-field";
  const label = document.createElement("span");
  label.className = "arhub-studio-field-label";
  label.textContent = labelText;
  control.dataset.runtimeSetting = setting;
  field.append(label, control);
  return field;
}

function runtimeCardValues(card) {
  const values = {};
  card.querySelectorAll("[data-runtime-setting]").forEach((control) => {
    values[control.dataset.runtimeSetting] = control.value.trim();
  });
  return values;
}

function syncRuntimeCard(card, settings) {
  card.querySelectorAll("[data-runtime-setting]").forEach((control) => {
    const key = control.dataset.runtimeSetting;
    if (key && settings[key] != null) control.value = settings[key];
  });
  const current = { ...settings, ...runtimeCardValues(card) };
  card.querySelectorAll("[data-runtime-role]").forEach((row) => {
    const agent = row.dataset.runtimeRole;
    const runtime =
      current[`${agent}_agent_runtime`] ||
      current.agent_runtime ||
      "openai_compatible";
    row.dataset.runtimeEffective = runtime;
    row.querySelectorAll("[data-runtime-scope]").forEach((field) => {
      const inactive =
        (field.dataset.runtimeScope === "local" && runtime !== "local_claude") ||
        (field.dataset.runtimeScope === "open" && runtime === "local_claude");
      field.dataset.inactive = String(inactive);
      const control = field.querySelector("input, select");
      if (control) control.disabled = inactive;
    });
  });
}

function runtimeRole(label, agent) {
  const row = document.createElement("section");
  row.className = "arhub-runtime-role";
  row.dataset.runtimeRole = agent;
  const title = document.createElement("strong");
  title.className = "arhub-runtime-role-title";
  title.textContent = label;
  const controls = document.createElement("div");
  controls.className = "arhub-runtime-role-controls";
  const kernel = settingsSelect([
    ["", "沿用默认内核"],
    ["openai_compatible", "开放模型"],
    ["local_claude", "本机 Claude Code"],
  ]);
  const provider = settingsSelect([
    ["auto", "自动识别"],
    ["deepseek", "DeepSeek"],
    ["glm", "GLM"],
    ["openai", "OpenAI"],
    ["generic", "通用兼容"],
  ]);
  const reasoning = settingsSelect([
    ["default", "模型默认"],
    ["off", "关闭"],
    ["low", "低"],
    ["medium", "中"],
    ["high", "高"],
    ["xhigh", "极高"],
    ["max", "最大"],
  ]);
  const claudeModel = document.createElement("input");
  claudeModel.type = "text";
  claudeModel.placeholder = "沿用默认 Claude 模型";
  const kernelField = runtimeField("Agent 内核", kernel, `${agent}_agent_runtime`);
  const providerField = runtimeField("Provider", provider, `${agent}_provider`);
  const reasoningField = runtimeField(
    "思考强度",
    reasoning,
    `${agent}_reasoning_effort`,
  );
  const modelField = runtimeField(
    "Claude 模型",
    claudeModel,
    `${agent}_claude_model`,
  );
  providerField.dataset.runtimeScope = "open";
  modelField.dataset.runtimeScope = "local";
  controls.append(kernelField, providerField, reasoningField, modelField);
  row.append(title, controls);
  kernel.addEventListener("change", () => {
    const card = row.closest("#arhub-runtime-settings");
    if (card) syncRuntimeCard(card, runtimeCardValues(card));
  });
  return row;
}

function installRuntimeSettings(main) {
  const host = main.querySelector(".space-y-6");
  if (!(host instanceof HTMLElement)) return;
  let card = host.querySelector("#arhub-runtime-settings");
  if (!card) {
    card = document.createElement("section");
    card.id = "arhub-runtime-settings";
    card.className = "card arhub-studio-settings-card arhub-runtime-settings";

    const heading = document.createElement("div");
    heading.className = "arhub-studio-settings-heading";
    addLeadingIcon(heading, "Cpu", "arhub-studio-settings-heading-icon", 19);
    const title = document.createElement("p");
    title.textContent = "Agent 运行时";
    heading.append(title);

    const grid = document.createElement("div");
    grid.className = "arhub-runtime-global-grid";
    const runtime = settingsSelect([
      ["openai_compatible", "开放模型"],
      ["local_claude", "本机 Claude Code"],
    ]);
    const claudeBin = document.createElement("input");
    claudeBin.type = "text";
    claudeBin.placeholder = "claude";
    const claudeModel = document.createElement("input");
    claudeModel.type = "text";
    claudeModel.placeholder = "Claude Code 默认模型";
    const claudeEffort = settingsSelect([
      ["default", "模型默认"],
      ["off", "关闭"],
      ["low", "低"],
      ["medium", "中"],
      ["high", "高"],
      ["xhigh", "极高"],
      ["max", "最大"],
    ]);

    const runtimeControl = runtimeField("默认 Agent 内核", runtime, "agent_runtime");
    const binControl = runtimeField("Claude Code", claudeBin, "claude_bin");
    const modelControl = runtimeField("默认 Claude 模型", claudeModel, "claude_model");
    const effortControl = runtimeField(
      "默认 Claude 强度",
      claudeEffort,
      "claude_effort",
    );
    grid.append(runtimeControl, binControl, modelControl, effortControl);

    const roles = document.createElement("div");
    roles.className = "arhub-runtime-roles";
    roles.append(
      runtimeRole("执行者 Agent", "executor"),
      runtimeRole("审稿者 Agent", "reviewer"),
      runtimeRole("编辑器助手", "editor_ai"),
    );

    const actions = document.createElement("div");
    actions.className = "arhub-runtime-actions";
    const status = document.createElement("span");
    status.className = "arhub-runtime-status";
    status.setAttribute("aria-live", "polite");
    const detect = document.createElement("button");
    detect.type = "button";
    detect.className = "btn-ghost arhub-studio-action";
    detect.textContent = "检测本机 Claude";
    detect.setAttribute("aria-label", "检测本机 Claude Code");
    addLeadingIcon(detect, "ScanSearch", "arhub-studio-action-icon", 15);
    const save = document.createElement("button");
    save.type = "button";
    save.className = "btn-primary";
    save.textContent = "保存运行时";
    addLeadingIcon(save, "Save", "arhub-studio-action-icon", 15);
    actions.append(status, detect, save);
    card.append(heading, grid, roles, actions);
    host.prepend(card);

    runtime.addEventListener("change", () =>
      syncRuntimeCard(card, runtimeCardValues(card)),
    );
    const detectLocal = async () => {
      status.textContent = "检测中...";
      const response = await fetch("/api/settings/detect-claude", {
        cache: "no-store",
      });
      const payload = response.ok ? await response.json() : null;
      const recommended = payload?.candidates?.find(
        (candidate) => candidate.path === payload?.recommended,
      );
      status.textContent = payload?.compatible
        ? recommended?.version || "本机 Claude Code 可用"
        : "未检测到本机 Claude Code";
      status.dataset.state = payload?.compatible ? "ready" : "error";
      if (payload?.recommended && !claudeBin.value.trim()) {
        claudeBin.value = payload.recommended;
      }
      return Boolean(payload?.compatible);
    };
    detect.addEventListener("click", () => void detectLocal());
    save.addEventListener("click", async () => {
      const values = runtimeCardValues(card);
      const needsLocal = ["executor", "reviewer", "editor_ai"].some(
        (agent) =>
          (values[`${agent}_agent_runtime`] || values.agent_runtime) ===
          "local_claude",
      );
      if (needsLocal && !(await detectLocal())) return;
      save.disabled = true;
      try {
        const response = await fetch("/api/settings", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ settings: values }),
        });
        if (!response.ok) throw new Error(await response.text());
        status.textContent = "已保存";
        status.dataset.state = "ready";
        runtimeSettingsPromise = Promise.resolve(values);
      } catch (error) {
        status.textContent = String(error?.message || error);
        status.dataset.state = "error";
      } finally {
        save.disabled = false;
      }
    });
  }

  if (!runtimeSettingsPromise) {
    runtimeSettingsPromise = fetch("/api/settings", { cache: "no-store" })
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => payload?.settings || {})
      .catch(() => ({}));
  }
  runtimeSettingsPromise.then((settings) => syncRuntimeCard(card, settings));
}

function decorateSettings(main) {
  installRuntimeSettings(main);
  main.querySelectorAll(".space-y-6 > .card").forEach((card, index) => {
    if (!(card instanceof HTMLElement)) return;
    card.classList.add("arhub-studio-settings-card");
    const text = normalizedText(card);
    const icon = /执行者/.test(text)
      ? "Bot"
      : /审稿/.test(text)
        ? "ScanSearch"
        : /编辑器/.test(text)
          ? "FilePenLine"
          : index === 3
            ? "SlidersHorizontal"
            : "Settings";
    const title = Array.from(card.querySelectorAll("p")).find((item) => {
      const value = normalizedText(item);
      return /(?:执行者|审稿者|编辑器 AI 助手|其他配置)/.test(value);
    });
    let heading = title?.parentElement;
    // "其他配置" keeps its title and description directly in the card.  Do
    // not turn the whole card into the two-column heading grid: that makes the
    // following form grid shrink to the icon column.  Give those two lines a
    // real heading wrapper instead.
    if (heading === card && title instanceof HTMLElement) {
      const subtitle = title.nextElementSibling;
      const wrapper = document.createElement("div");
      wrapper.className = "arhub-studio-settings-heading";
      card.insertBefore(wrapper, title);
      wrapper.append(title);
      if (subtitle instanceof HTMLParagraphElement) wrapper.append(subtitle);
      heading = wrapper;
    }
    card.classList.remove("arhub-studio-settings-heading");
    if (heading instanceof HTMLElement) {
      heading.classList.add("arhub-studio-settings-heading");
      addLeadingIcon(heading, icon, "arhub-studio-settings-heading-icon", 19);
    }
  });

  main.querySelectorAll("input, textarea, select").forEach((field) => {
    const container = field.parentElement;
    if (!(container instanceof HTMLElement)) return;
    container.classList.add("arhub-studio-field");
    const label = Array.from(container.children).find(
      (child) => child !== field && child instanceof HTMLElement,
    );
    if (!(label instanceof HTMLElement)) return;
    label.classList.add("arhub-studio-field-label");
    const text = normalizedText(label);
    const icon = /Base URL/i.test(text)
      ? "Network"
      : /API Key/i.test(text)
        ? "KeyRound"
        : /Model ID/i.test(text)
          ? "BrainCircuit"
          : /Image/i.test(text)
            ? "ImagePlus"
            : "";
    if (icon) addLeadingIcon(label, icon, "arhub-studio-field-label-icon", 13);
  });
}

function decorateStudio(view) {
  const main = document.querySelector("#root main");
  if (!(main instanceof HTMLElement)) return;
  main.dataset.arhubStudioView = view;
  main.classList.add("arhub-studio-main");
  decorateKicker(main, view);
  decorateActions(main);

  if (view === "workflows") decorateWorkflowSummary(main);
  if (view === "workflow" || view === "artifact") {
    decoratePipeline(main);
    decorateFileRows(main);
    decorateFileTypeMarkers(main);
  }
  if (view === "settings") decorateSettings(main);
}

function syncStudioRouteState() {
  const view = currentView();
  const html = document.documentElement;
  html.classList.toggle("arhub-studio-shell-active", Boolean(view));
  document.body.classList.toggle("arhub-studio-shell", Boolean(view));

  if (!view) {
    delete html.dataset.arhubStudioView;
    return view;
  }

  html.dataset.arhubStudioView = view;
  if (!window.matchMedia("(max-width: 860px)").matches) {
    document.body.classList.remove("mw-shell-collapsed");
  }
  return view;
}

function applyStudioShell() {
  const view = syncStudioRouteState();
  if (!view) return;
  decorateStudio(view);
}

function scheduleApply() {
  if (scheduled) return;
  scheduled = true;
  window.requestAnimationFrame(() => {
    scheduled = false;
    applyStudioShell();
  });
}

function handleStudioNavigation() {
  syncStudioRouteState();
  scheduleApply();
}

window.addEventListener("arhub:navigation", handleStudioNavigation);
window.addEventListener("popstate", handleStudioNavigation);
window.addEventListener("resize", scheduleApply, { passive: true });

const root = document.getElementById("root");
if (root) {
  new MutationObserver(scheduleApply).observe(root, { childList: true, subtree: true });
}

scheduleApply();

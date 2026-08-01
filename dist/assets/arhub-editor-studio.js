import { createIcon } from "./arhub-icons.js";

const EDITOR_ROUTE = /^\/workflow\/([^/]+)\/editor\/?$/;
let scheduled = false;

function editorRoute() {
  return window.location.pathname.match(EDITOR_ROUTE);
}

function isEditorRoute() {
  return Boolean(editorRoute());
}

function studioButton(className, iconName, label, text) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.title = label;
  button.setAttribute("aria-label", label);
  button.append(createIcon(iconName, { size: 16 }));
  const caption = document.createElement("span");
  caption.textContent = text;
  button.append(caption);
  return button;
}

function ensureBackLink(routeMatch) {
  const topbar = document.getElementById("mw-codex-topbar");
  const left = topbar?.querySelector(".mw-shell-topbar-left");
  if (!(left instanceof HTMLElement)) return;

  let back = left.querySelector(".arhub-studio-back");
  if (!(back instanceof HTMLAnchorElement)) {
    back = document.createElement("a");
    back.className = "arhub-studio-back";
    back.title = "返回任务概览";
    back.setAttribute("aria-label", "返回任务概览");
    back.append(createIcon("ChevronLeft", { size: 16 }));
    const caption = document.createElement("span");
    caption.textContent = "任务";
    back.append(caption);
    left.prepend(back);
  }
  back.href = "/workflow/" + encodeURIComponent(routeMatch[1]);
}

function ensureFilesTrigger() {
  const header = document.querySelector(".mw-editor-shell .mw-agent-header");
  if (!(header instanceof HTMLElement)) return;
  let trigger = header.querySelector(".arhub-studio-files-trigger");
  if (!(trigger instanceof HTMLButtonElement)) {
    trigger = studioButton("arhub-studio-files-trigger", "FolderOpen", "显示文件", "文件");
    trigger.addEventListener("click", () => {
      window.dispatchEvent(new Event("arhub:toggle-files"));
    });
    header.prepend(trigger);
  }

  const shell = document.querySelector(".mw-editor-shell");
  const filesOpen =
    shell instanceof HTMLElement &&
    shell.dataset.arhubCodexFiles === "expanded" &&
    shell.dataset.arhubCodexContext !== "open";
  trigger.setAttribute("aria-pressed", String(filesOpen));
  trigger.title = filesOpen ? "收起文件" : "显示文件";
  trigger.setAttribute("aria-label", trigger.title);
}

function replaceControlContents(button, iconName, caption = "") {
  if (!(button instanceof HTMLButtonElement)) return;
  const signature = `${iconName}:${caption}`;
  if (button.dataset.arhubStudioIcon === signature) return;
  button.replaceChildren(createIcon(iconName, { size: 16, strokeWidth: 1.8 }));
  if (caption) {
    const label = document.createElement("span");
    label.className = "arhub-studio-control-label";
    label.textContent = caption;
    button.append(label);
  }
  button.dataset.arhubStudioIcon = signature;
  button.classList.add("arhub-studio-icon-control");
  button.classList.toggle("is-icon-only", !caption);
}

function decorateNativeEditorControls() {
  const header = document.querySelector(".mw-editor-shell .mw-agent-header");
  if (header instanceof HTMLElement) {
    header.querySelectorAll("button").forEach((button) => {
      const label = String(button.textContent || "").replace(/\s+/g, " ").trim();
      const title = button.getAttribute("title") || button.getAttribute("aria-label") || "";
      if (title.includes("打开扩展中心") || label === "⊞") {
        replaceControlContents(button, "Puzzle");
      } else if (/^(?:💬\s*)?轻量$/.test(label)) {
        replaceControlContents(button, "MessageSquare", "轻量");
      } else if (label === "AI Agent") {
        replaceControlContents(button, "Sparkles", "AI Agent");
      }
    });
  }

  const command = document.querySelector(".mw-command-trigger");
  replaceControlContents(command, "Command");

  const jump = document.querySelector(".mw-jump-latest");
  replaceControlContents(jump, "ArrowDown");

  document.querySelectorAll(".mw-composer-row button").forEach((button) => {
    const label = String(button.textContent || "").replace(/\s+/g, " ").trim();
    if (/^(?:IMG\s*)?生图$/.test(label)) {
      replaceControlContents(button, "ImagePlus", "生图");
    }
  });

  const files = document.querySelector(".mw-files-panel");
  if (files instanceof HTMLElement) {
    files.querySelectorAll("button").forEach((button) => {
      const label = String(button.textContent || "").replace(/\s+/g, " ").trim();
      if (label === "＋" || label === "+") replaceControlContents(button, "Plus");
      if (label === "上传") replaceControlContents(button, "Upload", "上传");
    });
  }
}

function decorateEditor() {
  const routeMatch = editorRoute();
  const root = document.documentElement;
  if (!routeMatch) {
    root.classList.remove("arhub-editor-studio-active");
    document.querySelector(".arhub-studio-back")?.remove();
    return;
  }
  root.classList.add("arhub-editor-studio-active");
  ensureBackLink(routeMatch);
  ensureFilesTrigger();
  decorateNativeEditorControls();
}

function scheduleDecorate() {
  if (scheduled) return;
  scheduled = true;
  window.requestAnimationFrame(() => {
    scheduled = false;
    decorateEditor();
  });
}

window.addEventListener("arhub:navigation", scheduleDecorate);
window.addEventListener("popstate", scheduleDecorate);
window.addEventListener("resize", scheduleDecorate, { passive: true });
window.addEventListener("arhub:toggle-files", () => window.setTimeout(scheduleDecorate, 0));
window.addEventListener("arhub:open-context", () => window.setTimeout(scheduleDecorate, 0));
window.addEventListener("arhub:close-context", () => window.setTimeout(scheduleDecorate, 0));
document.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target.closest(".mw-agent-segmented button") : null;
  if (!target) return;
  // React replaces the mode buttons after its click handler completes.  Re-run
  // decoration on both the next tick and after the transition settles.
  window.setTimeout(scheduleDecorate, 0);
  window.setTimeout(scheduleDecorate, 96);
  window.setTimeout(scheduleDecorate, 240);
}, true);

const root = document.getElementById("root");
if (root) {
  new MutationObserver(scheduleDecorate).observe(root, {
    childList: true,
    subtree: true,
  });
}

scheduleDecorate();

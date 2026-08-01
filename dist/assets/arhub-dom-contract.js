/**
 * 增强层与上游编译 bundle 之间的 DOM 契约。
 *
 * overlay 没有 React 源码，只能靠 Tailwind 工具类、placeholder 文案等锚点定位
 * 上游渲染出来的 DOM。所有锚点集中在这里维护：上游 bundle 更新后若某个锚点
 * 失效，trackEditorContract 会在控制台给出明确警告，而不是让增强层静默失效。
 * tests-js/dom-contract.test.cjs 会用同一份表检查 bundle 文本，双保险。
 */

export const ANCHORS = Object.freeze({
  agentInput: {
    selector: 'textarea[placeholder*="Agent"], input[placeholder*="Agent"]',
    editorRoute: true,
  },
  panelCard: { selector: ".card", className: "card", editorRoute: true },
  agentHeader: {
    selector: ".p-3.border-b",
    classes: ["p-3", "border-b"],
    editorRoute: true,
  },
  agentThread: {
    selector: ".flex-1.overflow-y-auto",
    classes: ["flex-1", "overflow-y-auto"],
    editorRoute: true,
  },
  agentComposer: { selector: ".p-3.border-t", editorRoute: true },
  composerRow: { selector: ".flex.gap-2", editorRoute: true },
  sendButton: { selector: "[data-send-btn]", editorRoute: true },
  workbenchFileLabel: {
    selector: "span.font-mono.text-xs",
    classes: ["font-mono", "text-xs"],
  },
  previewHeading: { pattern: "预览|编译日志|脚本输出" },
  filesRow: { selector: "button.w-full.text-left" },
  templateRadio: { selector: 'input[type="radio"][name="template"]' },
  nativeThemeToggle: { selector: ".nav-bar .theme-toggle" },
  uploadLabelScope: { selector: "main .max-w-2xl p, main .max-w-2xl label" },
});

const contractState = { firstFailAt: 0, reported: false };

export function trackEditorContract(found) {
  if (found) {
    contractState.firstFailAt = 0;
    return;
  }
  const now = Date.now();
  if (!contractState.firstFailAt) contractState.firstFailAt = now;
  if (contractState.reported || now - contractState.firstFailAt < 3000) return;
  contractState.reported = true;
  const missing = Object.entries(ANCHORS)
    .filter(
      ([, anchor]) =>
        anchor.editorRoute &&
        anchor.selector &&
        !document.querySelector(anchor.selector),
    )
    .map(([name]) => name);
  console.warn(
    "[ArHub overlay] 编辑器 DOM 锚点连续 3 秒未匹配" +
      (missing.length ? `：${missing.join(", ")}` : "") +
      "。上游 bundle 可能已更新，相关增强功能已自动停用（应用本体不受影响）。",
  );
}

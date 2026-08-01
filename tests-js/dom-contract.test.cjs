'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const test = require('node:test');

const projectRoot = path.resolve(__dirname, '..');
const assetsDir = path.join(projectRoot, 'dist', 'assets');

function readBundle() {
  const entry = fs
    .readdirSync(assetsDir)
    .find((name) => /^index-[\w-]+\.js$/.test(name));
  assert.ok(entry, 'compiled frontend bundle (dist/assets/index-*.js) must exist');
  return fs.readFileSync(path.join(assetsDir, entry), 'utf8');
}

// 每个锚点在编译 bundle 里的文本探针。上游 bundle 更新后跑本测试，
// 失败项就是需要跟进修复的 overlay 锚点（对应 dist/assets/arhub-dom-contract.js）。
const BUNDLE_PROBES = {
  agentInput: /placeholder:[\s\S]{0,120}Agent/,
  panelCard: /className:`(?:[^`]* )?card(?: [^`]*)?`/,
  agentHeader: /className:`[^`]*p-3 border-b[^`]*`/,
  agentThread: /className:`[^`]*flex-1 overflow-y-auto[^`]*`/,
  agentComposer: /className:`[^`]*p-3 border-t[^`]*`/,
  composerRow: /className:`[^`]*flex gap-2[^`]*`/,
  sendButton: /data-send-btn/,
  workbenchFileLabel:
    /className:`[^`]*(?:font-mono[^`]*text-xs|text-xs[^`]*font-mono)[^`]*`/,
  previewHeading: /预览|编译日志|脚本输出/,
  filesRow: /className:`[^`]*w-full text-left[^`]*`/,
  templateRadio: /name:`template`/,
  nativeThemeToggle: /theme-toggle/,
  uploadLabelScope: /max-w-2xl/,
};

test('overlay DOM anchors still exist in the compiled bundle', async () => {
  const { ANCHORS } = await import(
    pathToFileURL(path.join(assetsDir, 'arhub-dom-contract.js')).href
  );
  const bundle = readBundle();
  for (const name of Object.keys(ANCHORS)) {
    const probe = BUNDLE_PROBES[name];
    assert.ok(probe, `anchor "${name}" is missing a bundle probe in this test`);
    assert.match(
      bundle,
      probe,
      `anchor "${name}" no longer matches the compiled bundle`,
    );
  }
  // isAgentRunning 依赖 composer 停止按钮的文案。
  assert.match(bundle, /停止/, 'the composer stop-button label has changed');
});

test('both overlays import the shared DOM contract', () => {
  const html = fs.readFileSync(path.join(projectRoot, 'dist', 'index.html'), 'utf8');
  const usesLegacyAppleShell = html.includes('/assets/apple-ui-20260727.css');
  for (const file of ['arhub-workspace.js', 'arhub-codex-shell.js']) {
    const source = fs.readFileSync(path.join(assetsDir, file), 'utf8');
    assert.ok(
      usesLegacyAppleShell || /from "\.\/arhub-dom-contract\.js"/.test(source),
      `${file} must import the DOM contract outside the pinned legacy Apple shell`,
    );
  }
});

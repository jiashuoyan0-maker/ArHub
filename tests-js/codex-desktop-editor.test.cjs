'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const projectRoot = path.resolve(__dirname, '..');
const read = (...parts) => fs.readFileSync(path.join(projectRoot, ...parts), 'utf8');

test('Codex-inspired editor layer loads last and keeps contextual panels accessible', () => {
  const html = read('dist', 'index.html');
  const script = read('dist', 'assets', 'arhub-codex-desktop.js');
  const css = read('dist', 'assets', 'arhub-codex-desktop.css');
  const studioScript = read('dist', 'assets', 'arhub-editor-studio.js');
  const studioCss = read('dist', 'assets', 'arhub-editor-studio.css');

  assert.ok(html.indexOf('/assets/arhub-codex-desktop.css') > html.indexOf('/assets/arhub-codex-shell.css'));
  assert.ok(html.indexOf('/assets/arhub-codex-desktop.js') > html.indexOf('/assets/arhub-codex-shell.js'));
  assert.ok(html.indexOf('/assets/arhub-editor-studio.css') > html.indexOf('/assets/arhub-codex-desktop.css'));
  assert.ok(html.indexOf('/assets/arhub-editor-studio.js') > html.indexOf('/assets/arhub-codex-desktop.js'));
  assert.match(script, /arhubCodexContext/);
  assert.match(script, /arhub:open-context/);
  assert.match(script, /aria-pressed/);
  assert.match(script, /Alt\+1|event\.key === "1"/);
  assert.match(css, /grid-template-areas:\s*"files agent context"/);
  assert.match(css, /min-height:\s*44px/);
  assert.match(css, /backdrop-filter:/);
  assert.match(css, /prefers-reduced-motion:\s*reduce/);
  assert.match(css, /@supports not \(backdrop-filter/);
  assert.match(studioScript, /arhub:toggle-files/);
  assert.match(studioScript, /arhub-editor-studio-active/);
  assert.match(studioCss, /#mw-codex-sidebar/);
  assert.match(studioCss, /data-arhub-codex-context="open"/);
  assert.match(studioCss, /prefers-reduced-motion:\s*reduce/);
});

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
  const shellScript = read('dist', 'assets', 'arhub-codex-shell.js');
  const shellCss = read('dist', 'assets', 'arhub-codex-shell.css');

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
  assert.match(shellScript, /community\.href = "https:\/\/linux\.do\/"/);
  assert.match(shellScript, /community\.target = "_blank"/);
  assert.match(shellScript, /community\.rel = "noopener noreferrer"/);
  assert.match(shellScript, /footer\.append\(extensions, community\)/);
  assert.match(shellCss, /\.mw-shell-community-link/);
});

test('Agent composer keeps the prompt dominant and exposes runtime controls', () => {
  const script = read('dist', 'assets', 'arhub-workspace.js');
  const css = read('dist', 'assets', 'arhub-workspace.css');
  const finalCss = read('dist', 'assets', 'arhub-editor-studio.css');

  assert.match(script, /createLucideButton\(\s*"Paperclip"/);
  assert.match(script, /stopping \? "Square" : "ArrowUp"/);
  assert.match(script, /data-mw-agent-action/);
  assert.match(script, /mw-composer-model-text/);
  assert.match(script, /mw-attachment-input/);
  assert.match(script, /artifacts\/upload\?target_dir=attachments/);
  assert.match(script, /extract-status\?target_dir=attachments/);
  assert.match(script, /event\.dataTransfer\.files/);
  assert.match(css, /\.mw-agent-input\s*{[^}]*flex:\s*0 0 100% !important/s);
  assert.match(css, /min-height:\s*104px !important/);
  assert.match(css, /max-height:\s*260px/);
  assert.match(css, /\.mw-composer-row > button\s*{[^}]*width:\s*44px/s);
  assert.match(css, /\.mw-composer-model\s*{/);
  assert.match(css, /\.mw-attachment-chip\s*{/);
  assert.match(css, /backdrop-filter:\s*saturate\(170%\) blur\(28px\)/);
  assert.match(finalCss, /html\.arhub-editor-studio-active\.mw-editor-active \.mw-composer-row\s*{[^}]*display:\s*flex !important/s);
  assert.match(finalCss, /html\.arhub-editor-studio-active\.mw-editor-active \.mw-agent-input\s*{[^}]*flex:\s*0 0 100% !important/s);
  assert.match(finalCss, /width:\s*100% !important/);
  assert.match(finalCss, /\.mw-composer-row > \.mw-agent-action\s*{[^}]*order:\s*3/s);
});

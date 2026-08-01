'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const projectRoot = path.resolve(__dirname, '..');

test('the selected frosted visual layer keeps motion accessible and the background grid off', () => {
  const html = fs.readFileSync(path.join(projectRoot, 'dist', 'index.html'), 'utf8');
  const legacyApple = html.includes('/assets/apple-ui-20260727.css');
  const assetName = legacyApple ? 'apple-ui-20260727.css' : 'arhub-glass.css';
  const css = fs.readFileSync(
    path.join(projectRoot, 'dist', 'assets', assetName),
    'utf8',
  );
  if (legacyApple) {
    assert.ok(html.indexOf('/assets/apple-ui-20260727.css') > html.indexOf('/assets/index-CMaY7UcM.css'));
    assert.match(css, /\.bg-grid[\s\S]{0,180}background-image:\s*none/);
  } else {
    assert.ok(
      html.indexOf('/assets/arhub-glass.css') > html.indexOf('/assets/arhub-codex-shell.css'),
      'glass stylesheet must load after the structural shell stylesheet',
    );
  }
  assert.match(css, /backdrop-filter:\s*(?:saturate\([^)]*\)\s*)?blur\(/);
  assert.match(css, /prefers-reduced-motion:\s*reduce/);
});

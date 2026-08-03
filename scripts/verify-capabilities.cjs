'use strict';

const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..');
const templatesPath = path.join(projectRoot, 'backend', 'workflow_templates.json');
const templates = JSON.parse(fs.readFileSync(templatesPath, 'utf8'));
const requiredSkills = new Set();

for (const template of Object.values(templates)) {
  if (template.pipeline_skill) requiredSkills.add(String(template.pipeline_skill));
  for (const step of template.sub_steps || []) {
    if (step.skill_name && step.skill_name !== 'docx-export') requiredSkills.add(String(step.skill_name));
  }
}

const missing = [];
for (const skillName of [...requiredSkills].sort()) {
  const skillFile = path.join(projectRoot, 'skills', skillName, 'SKILL.md');
  if (!fs.existsSync(skillFile)) missing.push(`skill:${skillName}`);
}

for (const relativePath of [
  'extension.schema.json',
  'extensions/core/manifest.json',
  'extensions/diagram/manifest.json',
  'extensions/web/manifest.json',
  'tools/docx-cn-engine/package.json',
  'tools/docx_style_profiles/default_cn_thesis.json',
]) {
  if (!fs.existsSync(path.join(projectRoot, relativePath))) missing.push(`resource:${relativePath}`);
}

if (missing.length > 0) {
  throw new Error(`Capability verification failed:\n${missing.map((item) => `- ${item}`).join('\n')}`);
}

const message = `Capability verification passed: ${requiredSkills.size} workflow skills and 6 packaged resources.`;
if (require.main === module) console.log(message);

module.exports = { message, requiredSkillCount: requiredSkills.size };

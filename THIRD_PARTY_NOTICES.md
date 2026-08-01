# Third-Party Notices

ArHub 自有代码使用 MIT License。仓库还包含以下第三方资源，其许可证不因
ArHub 的 MIT License 而改变。

| 组件 | 位置 | 许可证 |
|---|---|---|
| Noto Sans SC / Source Han Sans | skills/shared-scripts/NotoSansSC-Regular.ttf | SIL Open Font License 1.1 |
| Ubuntu Mono | 多个 skills/comp-paper-*/templates/*/fonts/ 目录 | Ubuntu Font Licence 1.0 |
| KaTeX fonts | dist/assets/KaTeX_* | SIL Open Font License 1.1 |
| Lucide Icons 1.28.0（离线子集） | dist/assets/arhub-icons.js | ISC；部分 Feather 衍生图标为 MIT |
| React 及前端依赖 | dist/assets/index-*.js | 各上游软件包许可证 |
| Electron 与 Chromium | Windows 桌面外壳 | MIT、BSD 及 Chromium 第三方许可证 |
| CPython 与 Python 软件包 | `runtime/python` | PSF License 及各软件包上游许可证 |
| Node.js、npm 与 Corepack | `runtime/node` | MIT 及各上游软件包许可证 |
| Git for Windows | `runtime/git` | GPL-2.0 及随发行版提供的第三方许可证 |
| Pandoc | `runtime/pandoc` | GPL-2.0-or-later |
| Draw.io Desktop | `runtime/draw.io` | Apache-2.0 及 Electron/Chromium 第三方许可证 |
| MiKTeX/TeX packages | `runtime/texlive` | 各 TeX 软件包声明的上游许可证 |

字体文件内嵌的主要版权声明包括：Noto Sans SC / Source Han Sans 为
Adobe 及其贡献者版权，Ubuntu Mono 为 Canonical Ltd. 版权。完整归属以
各字体文件的 name table 为准。

许可证全文：

- [SIL Open Font License 1.1](licenses/OFL-1.1.txt)
- [Ubuntu Font Licence 1.0](licenses/UBUNTU-FONT-LICENCE-1.0.txt)
- [Lucide ISC / Feather MIT](licenses/LUCIDE-ISC.txt)

`dist/` 是恢复的生产构建产物，尚未恢复原始前端依赖锁文件。每个 Windows
Release 会附带 Node 与 Python CycloneDX SBOM；runtime 的精确版本和 Python
包全集记录在 `packaging/`。各第三方发行版内自带的许可证文件会随安装包原样
保留。前端恢复产物的来源边界仍需在 Release 说明中明确披露。

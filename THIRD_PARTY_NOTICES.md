# Third-Party Notices

ArHub 自有代码使用 MIT License。仓库还包含以下第三方资源，其许可证不因
ArHub 的 MIT License 而改变。

| 组件 | 位置 | 许可证 |
|---|---|---|
| Noto Sans SC / Source Han Sans | skills/shared-scripts/NotoSansSC-Regular.ttf | SIL Open Font License 1.1 |
| Ubuntu Mono | 多个 skills/comp-paper-*/templates/*/fonts/ 目录 | Ubuntu Font Licence 1.0 |
| KaTeX fonts | dist/assets/KaTeX_* | SIL Open Font License 1.1 |
| React 及前端依赖 | dist/assets/index-*.js | 各上游软件包许可证 |

字体文件内嵌的主要版权声明包括：Noto Sans SC / Source Han Sans 为
Adobe 及其贡献者版权，Ubuntu Mono 为 Canonical Ltd. 版权。完整归属以
各字体文件的 name table 为准。

许可证全文：

- [SIL Open Font License 1.1](licenses/OFL-1.1.txt)
- [Ubuntu Font Licence 1.0](licenses/UBUNTU-FONT-LICENCE-1.0.txt)

dist/ 是恢复的生产构建产物，尚未恢复原始依赖锁文件。正式发布二进制包前，
必须从可维护前端源码重新构建并生成完整的依赖 SBOM 与许可证清单。

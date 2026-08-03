# Open-Source Release Checklist

## 当前结论

ArHub 当前已具备源码发布条件：后端、Agent、工作流、编辑器和 DOCX
链路均有可审查实现；38 个 Python 回归测试、26 个 Node 测试、70 路由导入、
真实浏览器验收和公开文件开源审计均已通过。

恢复仓库的旧 Git 历史仍不应公开，因为它包含恢复过程与本机路径痕迹。公开版
应从审计后的当前文件创建干净根提交：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\export-public-snapshot.ps1
```

该命令只导出 Git 候选文件，重新执行开源审计，并初始化一个无提交、无远程的
`main` 分支。它不会创建 GitHub 仓库、提交或推送。

## 已完成的本地门槛

- [x] Python 30 个测试通过
- [x] Python compileall 与 JavaScript 语法检查通过
- [x] FastAPI 入口成功导入，共 70 条应用路由
- [x] 动态文件面板、Agent 工作区、亮色主题与 DOCX 预览通过真实浏览器验收
- [x] 当前公开候选文件无 API Key、激活码、私钥、用户数据库或机器绝对路径
- [x] LICENSE、第三方许可、贡献指南和安全策略已纳入候选文件
- [x] 自动更新固定到官方 GitHub Releases，并要求发布者签名校验
- [x] 完整 runtime 版本、Python 包、目录统计和关键文件哈希已锁定
- [x] NSIS、SBOM、校验和、来源证明及签名发布工作流已纳入仓库
- [x] 签名白名单只覆盖 ArHub 主程序、顶层提权助手和 NSIS 产物，第三方运行时保持上游签名
- [x] Dependabot、每周安全/运行时维护和 CodeQL 工作流已纳入仓库

## GitHub 公开前仍需人工完成

- [ ] 在服务商控制台吊销并重新生成任何曾在聊天、截图或日志中暴露的 API Key
- [x] 审阅干净快照后创建新的 GitHub 仓库与根提交
- [x] 在 `package.json` 添加最终 `repository`、`bugs` 和 `homepage` URL
- [x] 启用 GitHub Secret scanning、推送保护、Dependabot 安全更新和 Private vulnerability reporting
- [ ] 在首次 Actions 检查通过后启用 `main` 分支保护
- [x] 默认分支、Issue 模板、PR 模板和贡献流程已确认

## 发布边界

源码 Release 可以继续准备。Windows 安装包的发布链已经建立，但正式二进制
Release 暂不应发布，直到所有未完成门槛在干净机器上通过：

- [x] Electron 与完整 runtime 的锁定、分发和组装
- [x] 安装包从已提交的 `dist/` 生产产物和锁定 runtime 可复现构建
- [x] Node/Python SBOM、第三方许可、后端与完整捆绑 Python 环境漏洞审计
- [ ] 使用公开可信证书完成安装包、主程序和卸载器签名验收
- [x] `electron-updater` 的 SHA-512、发布者签名校验和原子安装替代旧覆盖更新
- [x] 在隔离目录完成未签名候选的安装、后端/前端启动和卸载自动验收
- [ ] 在干净 Windows 环境完成签名版安装、模型调用、升级和卸载测试

前端模块化源码仍未完全恢复，这是贡献体验和长期维护限制，但不是当前二进制
可复现性的假前提：发布链明确使用仓库中审计后的 `dist/` 产物，并在 README 中
公开说明这一边界。

`scripts/deploy-installed.ps1` 仅用于已有安装版的本地兼容验证，会备份明确列出
的文件。它不是打包流程，也不应在 GitHub Actions 中执行。

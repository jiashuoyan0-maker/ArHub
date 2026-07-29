/**
 * Electron preload — 安全地暴露少量 API 给渲染进程
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  isDesktop: true,
  platform: process.platform,

  // ────────────────────────────────────────────
  // 自动更新 API
  // ────────────────────────────────────────────
  updater: {
    // 主动检查更新 (用户点"检查更新"按钮)
    checkNow: () => ipcRenderer.invoke('updater:check-now'),

    // 开始下载更新 (用户点"立即更新")
    startDownload: () => ipcRenderer.invoke('updater:start-download'),

    // 应用更新 + 重启
    applyAndRestart: () => ipcRenderer.invoke('updater:apply-and-restart'),

    // 取消下载
    abort: () => ipcRenderer.invoke('updater:abort'),

    // 跳过这个版本 (本机不再提示)
    skipVersion: (version) => ipcRenderer.invoke('updater:skip-version', version),

    // 拉取主进程已缓存的检查结果 (前端激活后挂载时调用, 不重新请求服务器)
    getCached: () => ipcRenderer.invoke('updater:get-cached'),

    // 监听: 有更新可用 (启动后自动触发)
    onUpdateAvailable: (cb) => {
      const handler = (_e, info) => cb(info);
      ipcRenderer.on('update-available', handler);
      return () => ipcRenderer.removeListener('update-available', handler);
    },

    // 监听: 下载进度
    onProgress: (cb) => {
      const handler = (_e, progress) => cb(progress);
      ipcRenderer.on('update-progress', handler);
      return () => ipcRenderer.removeListener('update-progress', handler);
    },
  },
});

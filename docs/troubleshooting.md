# 故障排查指南

## E001 设备未检测到

确认设备已连接、USB 调试已开启，并在设备弹窗中授权调试。WSL 环境下还需要确认 USB 已转发到 WSL。

```bash
adb devices
```

## E002 CTS Verifier 未安装

将 `CtsVerifier.apk` 放到 `apk/CtsVerifier.apk`，然后运行：

```bash
cts-verify device setup
```

## E003 UI 元素未找到

通常是 CTS Verifier 版本 UI 文案变化或页面还未加载完成。先使用 `--verbose` 查看日志，再基于实机 UI dump 调整专用测试脚本。

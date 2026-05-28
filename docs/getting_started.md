# 快速入门指南

## 环境要求

- Ubuntu 22.04
- Python 3.10+
- ADB
- Android 设备，已开启 USB 调试
- CTS Verifier APK

## 安装

```bash
./setup.sh
```

或手动安装：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## 首次运行

```bash
cts-verify device list
cts-verify device setup
cts-verify quickstart
```

# CTS Verifier 自动化测试工具

基于设计文档在当前目录落地的 Android 16 CTS Verifier 自动化框架。目标是在 Ubuntu 22.04 上通过 ADB 和 UIAutomator2 连接 Android 设备，自动启动 CTS Verifier、执行可自动化测试项并生成报告。

## 快速开始

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

cts-verify list --automatable
cts-verify device list
cts-verify quickstart
```

## 常用命令

```bash
cts-verify list
cts-verify list --module AUDIO --automatable
cts-verify list --category audio --automatable
cts-verify device info --id <device-id>
cts-verify device setup --id <device-id>
cts-verify run --module AUDIO --test "Ringer Mode" --platform android15
cts-verify run --format junit --output reports/results.xml
cts-verify report --input reports/results.json --format html --output reports/report.html
```

## 当前实现范围

- 项目骨架、配置文件、CLI 入口。
- ADB 与 UIAutomator2 设备连接封装。
- 通用 CTS Verifier UI 测试骨架，用于可通过可见文本判断 Pass/Fail 的测试。
- 首批优先测试注册表，覆盖设计文档里的 high/medium/low 示例项。
- 支持按文档模块筛选测试，例如 `--module AUDIO`、`--module NETWORKING`。
- 支持 Android 14/15/16 平台 profile，差异配置在 `config/platforms/` 下维护。
- HTML、JSON、JUnit XML 报告导出。
- 环境检查、设备初始化、APK 安装脚本。

复杂测试项仍需要基于实机 UI dump 和手工流程记录继续补专用脚本。

## 目录

```text
config/        全局配置和测试清单
src/core/      ADB、设备、UIAutomator2、错误恢复
src/cli/       命令行入口
src/runner/    测试运行器
src/tests/     测试基类、注册表、通用测试流程
src/report/    报告生成和导出
scripts/       环境、设备、APK 辅助脚本
docs/          使用和开发文档
```

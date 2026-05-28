# CLAUDE.md — CTS Verifier 自动化测试框架

> 本文件是 Claude Code 在本项目中的工作指南。Claude 在每次会话中应遵循以下规则。

## 项目概述

Android CTS Verifier 自动化测试框架（`cts-verifier-automation` v0.1.0）。通过 ADB + UIAutomator2 驱动连接的 Android 设备，自动执行 CTS Verifier 测试并生成报告。

- **语言**: Python 3.10+（使用 `X | Y` 联合类型，`from __future__ import annotations`）
- **目标平台**: Ubuntu 22.04 主机 + Android 14/15/16 设备
- **CLI 入口**: `cts-verify`（`src.main:main`）
- **界面语言**: 用户面向中文（README、文档、错误信息），代码注释保持英文

## 项目结构

```
src/
  main.py              CLI 入口（argparse 子命令）
  cli/                 命令实现：run, list, report, device, config, quickstart
  core/                基础设施：ADBClient, DeviceManager, UIAutomatorClient, RecoveryHandler
  runner/              TestRunner 编排 + ProgressBar
  tests/               测试实现：BaseTest, GenericCtsUiTest, RingerModeTest, Registry
  report/              报告生成：Reporter + HTML/JSON/JUnit exporters
  validators/          验证器：UI, Image (OpenCV), Log
  platforms/           PlatformProfile（Android 14/15/16 差异配置）
config/
  settings.yaml        全局运行时配置
  test_cases.yaml      测试清单、优先级、排除项、超时
  platforms/            per-Android-version YAML profiles
tests/                  pytest 单元测试
scripts/                Shell 辅助脚本
docs/                   中文文档（getting_started, troubleshooting, writing_tests）
```

## 开发规则

### 代码风格

- 使用 `black` 格式化，`flake8` 检查，`mypy` 类型检查
- 类型注解使用 Python 3.10+ 语法：`str | None` 而非 `Optional[str]`，`dict[str, Any]` 而非 `Dict`
- 不写多余注释，只在 WHY 不明显时加一行短注释
- 不写多行 docstring

### 测试

- 运行测试：`python -m pytest tests/ -v`
- 单元测试放在 `tests/` 目录，与源码模块对应
- 测试使用 `tmp_path` fixture 处理文件输出，不写入项目目录
- 新增功能必须附带单元测试

### 测试用例开发

- 所有测试类必须继承 `BaseTest`，遵循 `setup→execute→validate→teardown` 流程
- 简单测试（仅凭 UI 文本判断 Pass/Fail）：在 `TEST_SPECS` 添加条目即可，`GenericCtsUiTest` 自动处理
- 复杂测试（多步操作、Shell 命令、状态切换）：继承 `BaseTest` 实现专用类，在 `build_tests()` 注册策略
- UI 文本匹配需兼容中英文（参考 `config/settings.yaml` 中 `pass_texts` / `fail_texts`）
- 涉及 Android 版本差异时，在 `config/platforms/android*.yaml` 添加配置项

### 设备交互

- `DeviceManager` 是唯一对外接口，不要直接使用 `ADBClient` 或 `UIAutomatorClient`
- 所有 ADB Shell 命令必须设置 `timeout`
- `uiautomator2` 操作后需适当等待（`time.sleep` 或 `u2.wait_idle()`）
- 注意不同设备分辨率差异，滑动坐标应基于屏幕尺寸比例计算

### 配置与报告

- 配置通过 `src/core/config.py` 加载，支持深键访问 `config.get("device.wait_timeout")`
- 报告导出是 Strategy 模式：新增格式在 `src/report/exporters/` 新建模块
- `build_report()` 聚合逻辑与格式导出分离

### 不可做的事

- 不要在 `src/` 下创建新的顶层子包，除非是新增测试类别目录（如 `src/tests/camera/`）
- 不要修改 `BaseTest` 的 `run_once()` 流程骨架
- 不要硬编码 UI 文本字符串，应从 `PlatformProfile` 或 `settings.yaml` 读取
- 不要在测试代码中使用 `input()` 或任何阻塞式人工交互
- 不要跳过 `TEST_SPECS` 注册——未注册的测试无法被 CLI 发现
- 不要将 `.apk` 文件提交到 Git

## 常用命令

```bash
# 环境设置
source venv/bin/activate
pip install -r requirements.txt && pip install -e .

# 运行测试
python -m pytest tests/ -v

# 代码检查
black --check src/ tests/
flake8 src/ tests/
mypy src/

# CLI 使用
cts-verify list --automatable
cts-verify device list
cts-verify quickstart
cts-verify run --module AUDIO --platform android15
```

## 关键设计决策

1. **Template Method 模式**: `BaseTest.run_once()` 定义不可变骨架，子类只覆写步骤方法
2. **Registry + Factory**: `TEST_SPECS` 集中注册 + `build_tests()` 工厂分发，确保 CLI 和 Runner 使用同一数据源
3. **Platform Profile**: Android 版本差异外置到 YAML，避免代码中 `if android_version == 16` 分支
4. **Facade 模式**: `DeviceManager` 封装底层驱动，上层代码不感知 ADB/u2 细节
5. **Strategy 模式**: 恢复策略和报告导出均可独立扩展，不影响已有实现

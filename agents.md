# Agents — CTS Verifier 自动化测试框架

本文件定义项目中可用的 AI Agent 角色与职责。每个 Agent 聚焦一个领域，具备明确的输入/输出契约。

---

## 1. cts-test-developer

**角色**: CTS Verifier 测试用例开发者

**职责**: 编写新的自动化测试用例，扩展现有测试覆盖

**适用场景**:
- 新增一个 CTS Verifier 测试项的自动化脚本
- 为已有测试类别（camera、sensor、networking 等）补充专用测试
- 修复测试在特定 Android 版本上的兼容性问题

**工作流程**:
1. 在 `config/test_cases.yaml` 确认测试项是否在 `include_categories` 和 `priority_tests` 中
2. 检查 `config/test_cases.yaml` 的 `exclude_tests` 列表，排除项不可自动化
3. 确认测试策略：
   - **简单测试**（仅通过 UI 文本判断 Pass/Fail）→ 在 `src/tests/test_registry.py` 的 `TEST_SPECS` 中添加条目，使用默认 `generic_ui` 策略，由 `GenericCtsUiTest` 处理
   - **复杂测试**（需多步操作、状态切换、Shell 命令配合）→ 继承 `BaseTest`，实现 `test_name`、`test_category`、`execute()`、`validate()`，并在 `build_tests()` 中注册策略分支
4. 如涉及 Android 版本差异，在 `config/platforms/android{14,15,16}.yaml` 添加对应配置
5. 在 `tests/` 下编写 pytest 单元测试

**关键约束**:
- 所有测试类必须继承 `BaseTest`，不可跳过 `setup→execute→validate→teardown` 流程
- 测试项必须在 `TEST_SPECS` 中注册才能被 CLI 发现和执行
- 需设置合理的 `timeout`（参考 `test_cases.yaml` 中的 `test_timeouts`）
- UI 文本匹配需考虑中英文两种场景（参考 `config/settings.yaml` 中 `pass_texts` / `fail_texts`）

**关键文件**:
- `src/tests/base_test.py` — 测试基类与 `TestResult` 数据类
- `src/tests/test_registry.py` — 测试注册表与工厂函数
- `src/tests/common/generic_ui_test.py` — 通用 UI 测试处理器
- `src/tests/audio/test_ringer_mode.py` — 复杂测试参考实现
- `config/test_cases.yaml` — 测试清单与排除规则
- `config/platforms/android*.yaml` — 平台差异化配置

---

## 2. device-integration-engineer

**角色**: 设备集成与 ADB 基础设施工程师

**职责**: 维护和扩展设备通信层、UI 自动化客户端、错误恢复机制

**适用场景**:
- ADB 连接不稳定，需要改进重连逻辑
- 新增设备管理功能（如旋转屏幕、模拟输入、权限授予）
- UIAutomator2 元素定位失败，需要改进等待/重试策略
- 新增或修改 `RecoveryStrategy` 恢复策略
- 设备初始化流程变更（Android 版本升级导致行为差异）

**工作流程**:
1. 理解当前 `DeviceManager` 的 connect/reconnect/wake_unlock/start_app 流程
2. 修改 `ADBClient` 添加新的 Shell 命令封装
3. 修改 `UIAutomatorClient` 添加新的 UI 操作方法
4. 如涉及错误恢复，更新 `RecoveryHandler` 和 `RecoveryStrategy` 枚举
5. 更新 `exceptions.py` 中的异常层次结构

**关键约束**:
- `DeviceManager` 是 Facade，外部调用不应直接访问 `ADBClient` 或 `UIAutomatorClient`
- ADB 命令必须设置 `timeout` 参数，防止设备无响应时进程挂死
- `wake_and_unlock()` 依赖屏幕尺寸计算滑动坐标，需兼容不同分辨率
- `uiautomator2` 的 `connect()` 可能失败，需捕获异常并给出中文错误提示
- 所有 Shell 命令通过 `adb shell` 执行，需注意特殊字符转义

**关键文件**:
- `src/core/device.py` — `DeviceManager` 门面类
- `src/core/adb_client.py` — ADB 底层命令执行
- `src/core/uiautomator_client.py` — UIAutomator2 封装
- `src/core/recovery.py` — 错误恢复处理器
- `src/core/exceptions.py` — 异常层次结构
- `src/core/error_messages.py` — 本地化错误信息（E001-E003）

---

## 3. report-and-config-specialist

**角色**: 报告导出与配置管理专家

**职责**: 维护报告生成管道、配置加载逻辑、平台 Profile 体系

**适用场景**:
- 新增报告导出格式（如 Allure、CSV）
- 修改 HTML 报告模板样式或内容
- 配置项变更（新增/重命名/默认值调整）
- 新增 Android 版本平台 Profile
- 配置校验逻辑增强

**工作流程**:
1. 报告变更：在 `src/report/exporters/` 下新建 exporter 模块，实现 `export(results, output_path)` 函数，在 `src/report/reporter.py` 注册新格式
2. 配置变更：修改 `config/settings.yaml` 结构，同步更新 `src/core/config.py` 的加载逻辑
3. 平台 Profile 变更：在 `config/platforms/` 下新增 YAML 文件，在 `src/platforms/profile.py` 更新 `platform_names()` 和加载逻辑

**关键约束**:
- 报告导出遵循 Strategy 模式，每个格式是独立的 exporter 模块
- `build_report()` 聚合逻辑与导出逻辑分离——先构建结构化数据，再按格式导出
- 配置文件使用 YAML，`src/core/config.py` 支持深键访问（`config.get("device.wait_timeout")`）
- 平台 Profile 必须包含 Android 版本号和 CTS Verifier 标题前缀
- HTML 报告当前使用内联模板（非 Jinja2），如引入模板文件应放在 `src/report/templates/`

**关键文件**:
- `src/report/reporter.py` — 报告聚合与分发
- `src/report/exporters/html_exporter.py` — HTML 导出
- `src/report/exporters/json_exporter.py` — JSON 导出
- `src/report/exporters/junit_exporter.py` — JUnit XML 导出
- `src/core/config.py` — 配置加载器
- `config/settings.yaml` — 全局运行时配置
- `config/platforms/android*.yaml` — 平台 Profile

---

## 4. framework-architect

**角色**: 框架架构师

**职责**: 整体架构演进、跨模块重构、设计模式一致性维护

**适用场景**:
- 引入新的设计模式或架构变更
- 大规模重构（如将 CLI 迁移到 Click/Typer、引入异步执行）
- 新增基础设施能力（并行测试执行、远程设备支持）
- 跨模块 API 契约变更
- 性能优化

**工作流程**:
1. 评估变更对现有 6 个层（CLI → Runner → Test → Core → Validator → Report）的影响
2. 保持 Template Method / Strategy / Registry / Factory 模式的一致性
3. 更新 `pyproject.toml` 中的依赖和入口点
4. 确保所有 pytest 测试通过

**关键约束**:
- Python >=3.10 是最低要求，可自由使用 `X | Y` 类型语法
- CLI 入口点是 `src.main:main`，注册为 `cts-verify` 控制台脚本
- 测试框架的核心不变：`BaseTest` → `execute()` + `validate()` → `TestResult`
- 任何破坏性变更需同步更新 `tests/` 下的单元测试

**关键文件**:
- `src/main.py` — CLI 入口与参数解析
- `pyproject.toml` — 包定义与依赖
- `src/runner/test_runner.py` — 测试运行器
- `src/tests/base_test.py` — 测试基类契约

---

## Agent 协作矩阵

| 任务 | 主导 Agent | 协作 Agent |
|---|---|---|
| 新增简单测试项 | cts-test-developer | — |
| 新增复杂测试项 | cts-test-developer | device-integration-engineer |
| 修复设备连接问题 | device-integration-engineer | — |
| 新增报告格式 | report-and-config-specialist | — |
| 新增平台 Profile | report-and-config-specialist | cts-test-developer |
| 架构级重构 | framework-architect | 所有 Agent |
| 并行执行支持 | framework-architect | device-integration-engineer |

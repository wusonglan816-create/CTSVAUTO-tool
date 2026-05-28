from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StructuredError:
    code: str
    title: str
    message: str
    cause: str
    fix: str

    def format(self) -> str:
        return "\n".join(
            [
                f"[{self.code}] {self.title}",
                f"问题: {self.message}",
                f"原因: {self.cause}",
                f"修复: {self.fix}",
            ]
        )


ERRORS = {
    "E001": StructuredError(
        "E001",
        "设备未检测到",
        "未找到连接的 Android 设备",
        "设备未连接、USB 调试未开启，或 ADB daemon 无法启动",
        "确认 USB 连接和授权后运行 `adb devices`；WSL 下还需确认 USB 转发权限。",
    ),
    "E002": StructuredError(
        "E002",
        "CTS Verifier 未安装",
        "设备上未检测到 com.android.cts.verifier",
        "APK 未安装或安装失败",
        "将 CtsVerifier.apk 放到 ./apk/CtsVerifier.apk 后运行 `cts-verify device setup`。",
    ),
    "E003": StructuredError(
        "E003",
        "UI 元素未找到",
        "在指定超时时间内未找到目标 UI 元素",
        "页面加载慢、选择器变化，或 CTS Verifier 版本与脚本不匹配",
        "使用 `--verbose` 查看日志，必要时根据 UI dump 更新测试脚本。",
    ),
}

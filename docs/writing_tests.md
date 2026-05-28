# 编写测试指南

简单测试可以先注册到 `src/tests/test_registry.py`，由 `GenericCtsUiTest` 处理“进入测试项、点击 Test/Run/Start、查找通过文本”的通用流程。

复杂测试建议新增专用 `BaseTest` 子类：

```python
from src.tests.base_test import BaseTest


class MyTest(BaseTest):
    @property
    def test_name(self) -> str:
        return "My Test"

    @property
    def test_category(self) -> str:
        return "audio"

    def execute(self) -> bool:
        return True

    def validate(self) -> bool:
        return True
```

然后在注册表里按名称、类别、优先级暴露给 CLI。

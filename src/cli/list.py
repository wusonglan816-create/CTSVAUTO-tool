from __future__ import annotations

from src.tests.test_registry import iter_specs


def cmd_list(args) -> int:
    specs = list(
        iter_specs(
            args.category,
            automatable_only=args.automatable,
            module=getattr(args, "module", "all"),
        )
    )
    if not specs:
        print("未找到匹配测试项")
        return 0
    print(f"{'Module':<24} {'Category':<18} {'Priority':<8} {'Auto':<5} Test")
    print("-" * 104)
    for spec in specs:
        auto = "yes" if spec.automatable else "no"
        print(f"{spec.document_module:<24} {spec.category:<18} {spec.priority:<8} {auto:<5} {spec.name}")
    print(f"\n共 {len(specs)} 项")
    return 0

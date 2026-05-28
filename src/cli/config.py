from __future__ import annotations

import json

from src.core.config import deep_get, load_settings


def cmd_config(args) -> int:
    config = load_settings()
    if args.action == "show":
        if args.key:
            print(deep_get(config, args.key, ""))
        else:
            print(json.dumps(config, ensure_ascii=False, indent=2))
        return 0
    if args.action == "init":
        print("默认配置已位于 config/settings.yaml")
        return 0
    if args.action == "set":
        print("暂不支持命令行写配置，请直接编辑 config/settings.yaml")
        return 1
    return 1

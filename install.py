#!/usr/bin/env python3
"""Install the completion sound into Cursor, Claude Code, Codex, and TRAE/豆包."""

import json
import os
import shutil
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INSTALL_DIR = Path.home() / ".ai-task-done"
SCRIPT_NAME = "notify.py"
SOUND_NAME = "done.mp3"
MARKERS = (".ai-task-done/notify.py", ".ai-task-done\\notify.py", "task-done-notify.py")
TIMEOUT = 20


def main() -> None:
    python = sys.executable or "python3"
    install_files()
    script = INSTALL_DIR / SCRIPT_NAME
    command = hook_command(python, script)
    results = [
        install_cursor(command),
        install_claude(command),
        install_codex(command),
        install_trae(command),
    ]
    print("已安装到：")
    for line in results:
        print("- " + line)
    print("试听：")
    print(f"  {command}")


def install_files() -> None:
    source_sound = ROOT / "sounds" / SOUND_NAME
    if not source_sound.exists():
        raise SystemExit(f"找不到提示音：{source_sound}")
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    script_dest = INSTALL_DIR / SCRIPT_NAME
    shutil.copyfile(ROOT / SCRIPT_NAME, script_dest)
    shutil.copyfile(source_sound, INSTALL_DIR / SOUND_NAME)
    mode = script_dest.stat().st_mode
    script_dest.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def hook_command(python: str, script: Path) -> str:
    if os.name == "nt":
        return f'"{python}" "{script}"'
    return str(script)


def install_cursor(command: str) -> str:
    path = Path.home() / ".cursor" / "hooks.json"
    data = read_json(path, {"version": 1, "hooks": {}})
    if not isinstance(data, dict):
        data = {"version": 1, "hooks": {}}
    data["version"] = 1
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        hooks = {}
        data["hooks"] = hooks
    stop = hooks.get("stop")
    if not isinstance(stop, list):
        stop = []
    stop = [item for item in stop if not is_ours(item.get("command") if isinstance(item, dict) else "")]
    stop.append({"command": command, "timeout": TIMEOUT})
    hooks["stop"] = stop
    write_json(path, data)
    return f"Cursor  {path}"


def install_claude(command: str) -> str:
    path = Path.home() / ".claude" / "settings.json"
    data = read_json(path, {})
    add_grouped_hook(data, "Stop", command, matcher=None)
    write_json(path, data)
    return f"Claude Code  {path}"


def install_codex(command: str) -> str:
    path = Path.home() / ".codex" / "hooks.json"
    data = read_json(path, {"hooks": {}})
    add_grouped_hook(data, "Stop", command, matcher=None)
    write_json(path, data)
    return f"Codex  {path}"


def install_trae(command: str) -> str:
    path = Path.home() / ".trae-cn" / "hooks.json"
    data = read_json(path, {"version": 1, "hooks": {}})
    if isinstance(data, dict):
        data["version"] = 1
    add_grouped_hook(data, "Notification", command, matcher="idle_prompt")
    write_json(path, data)
    return f"豆包 / TRAE  {path}"


def add_grouped_hook(data: dict, event: str, command: str, matcher) -> None:
    if not isinstance(data, dict):
        return
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        hooks = {}
        data["hooks"] = hooks
    for name, groups in list(hooks.items()):
        if isinstance(groups, list):
            hooks[name] = strip_groups(groups)
    groups = hooks.get(event)
    if not isinstance(groups, list):
        groups = []
    entry = {
        "hooks": [
            {
                "type": "command",
                "command": command,
                "timeout": TIMEOUT,
            }
        ]
    }
    if matcher:
        entry["matcher"] = matcher
    groups.append(entry)
    hooks[event] = groups


def strip_groups(groups: list) -> list:
    kept = []
    for group in groups:
        if not isinstance(group, dict):
            kept.append(group)
            continue
        inner = group.get("hooks")
        if not isinstance(inner, list):
            kept.append(group)
            continue
        inner = [
            item
            for item in inner
            if not (isinstance(item, dict) and is_ours(str(item.get("command") or "")))
        ]
        if not inner:
            continue
        group = dict(group)
        group["hooks"] = inner
        kept.append(group)
    return kept


def is_ours(command: str) -> bool:
    return any(marker in command for marker in MARKERS)


def read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return json.loads(json.dumps(default))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"无法读取 {path}：{exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} 不是 JSON 对象，已停止，避免覆盖原文件。")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copyfile(path, path.with_suffix(path.suffix + ".bak"))
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

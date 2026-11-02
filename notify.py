#!/usr/bin/env python3
"""Play a sound and show a desktop notification when an AI turn finishes."""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
INSTALL_DIR = HOME / ".ai-task-done"
DEBOUNCE_SEC = 5
COMPLETION_NOTIFICATIONS = {"idle_prompt", "agent_completed"}
SKIP_STATUS = {"aborted", "cancelled", "canceled", "error"}


def main() -> None:
    data = read_payload()
    if not should_notify(data):
        emit()
        return
    title = clean_title(task_title(data))
    app = app_name(data)
    if claim_playback():
        desktop_notify(app, f"{title} 已经完成")
        play_sound(sound_path())
    emit()


def read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def should_notify(data: dict) -> bool:
    status = str(data.get("status") or "").strip().lower()
    if status in SKIP_STATUS:
        return False
    kind = str(data.get("notification_type") or "").strip()
    if kind and kind not in COMPLETION_NOTIFICATIONS:
        return False
    return True


def task_title(data: dict) -> str:
    found = lookup_cursor_title(str(data.get("conversation_id") or ""))
    if found:
        return found
    for key in ("title", "conversation_title", "name"):
        value = str(data.get(key) or "").strip()
        if value:
            return value
    roots = data.get("workspace_roots") or []
    if isinstance(roots, list) and roots:
        name = Path(str(roots[0])).name.strip()
        if name:
            return name
    cwd = str(data.get("cwd") or "").strip()
    if cwd:
        return Path(cwd).name or "当前任务"
    return "当前任务"


def lookup_cursor_title(conversation_id: str) -> str:
    if not conversation_id:
        return ""
    db = (
        HOME
        / "Library"
        / "Application Support"
        / "Cursor"
        / "User"
        / "globalStorage"
        / "conversation-search.db"
    )
    if not db.exists():
        return ""
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=1)
        try:
            row = con.execute(
                "SELECT title FROM conversations WHERE id = ? ORDER BY updated_at DESC LIMIT 1",
                (conversation_id,),
            ).fetchone()
        finally:
            con.close()
    except sqlite3.Error:
        return ""
    if not row:
        return ""
    return str(row[0] or "").strip()


def clean_title(title: str) -> str:
    title = " ".join(title.replace("\n", " ").replace("\r", " ").split())
    if len(title) > 48:
        title = title[:47] + "…"
    return title or "当前任务"


def app_name(data: dict) -> str:
    if data.get("cursor_version"):
        return "Cursor"
    if data.get("turn_id"):
        return "Codex"
    if data.get("notification_type"):
        return "豆包"
    return "AI"


def sound_path() -> Path:
    beside = Path(__file__).resolve().parent / "done.mp3"
    if beside.exists():
        return beside
    bundled = Path(__file__).resolve().parent / "sounds" / "done.mp3"
    if bundled.exists():
        return bundled
    return beside


def claim_playback() -> bool:
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = INSTALL_DIR / "play.lock"
    stamp_path = INSTALL_DIR / "last-played"
    handle = open(lock_path, "a+")
    if handle.seek(0, os.SEEK_END) == 0:
        handle.write(" ")
        handle.flush()
    try:
        lock_file(handle)
        now = time.time()
        try:
            last = float(stamp_path.read_text(encoding="utf-8") or "0")
        except (OSError, ValueError):
            last = 0
        if now - last < DEBOUNCE_SEC:
            return False
        stamp_path.write_text(str(now), encoding="utf-8")
        return True
    finally:
        unlock_file(handle)
        handle.close()


def lock_file(handle) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        return
    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)


def unlock_file(handle) -> None:
    if os.name == "nt":
        import msvcrt

        try:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        return
    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def desktop_notify(title: str, body: str) -> None:
    if sys.platform == "darwin":
        script = (
            f'display notification "{applescript_string(body)}" '
            f'with title "{applescript_string(title)}" subtitle "任务完成"'
        )
        subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
            check=False,
        )
        return
    if sys.platform.startswith("linux") and shutil.which("notify-send"):
        subprocess.run(
            ["notify-send", title, body],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
            check=False,
        )
        return
    if sys.platform == "win32":
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$n = New-Object System.Windows.Forms.NotifyIcon; "
            "$n.Icon = [System.Drawing.SystemIcons]::Information; "
            "$n.Visible = $true; "
            f"$n.ShowBalloonTip(5000, {ps_quote(title)}, {ps_quote(body)}, "
            "[System.Windows.Forms.ToolTipIcon]::Info); "
            "Start-Sleep -Seconds 2; $n.Dispose()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=12,
            check=False,
        )


def play_sound(path: Path) -> None:
    if not path.exists():
        return
    if sys.platform == "darwin":
        subprocess.run(
            ["/usr/bin/afplay", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=25,
            check=False,
        )
        return
    if sys.platform.startswith("linux"):
        players = (
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)],
            ["mpv", "--no-video", "--really-quiet", str(path)],
            ["mpg123", "-q", str(path)],
        )
        for cmd in players:
            if shutil.which(cmd[0]):
                subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=25,
                    check=False,
                )
                return
        return
    if sys.platform == "win32":
        uri = path.resolve().as_uri()
        ps = (
            "Add-Type -AssemblyName presentationCore; "
            "$p = New-Object system.windows.media.mediaplayer; "
            f"$p.Open([uri]{ps_quote(uri)}); "
            "$p.Volume = 1; $p.Play(); Start-Sleep -Seconds 6; "
            "$p.Stop(); $p.Close()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
            check=False,
        )


def applescript_string(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def ps_quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def emit() -> None:
    print("{}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        emit()

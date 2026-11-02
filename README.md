# 陛下上朝

一轮对话正常结束时，播放一段提示音，并弹出桌面提醒。打开对应软件就会生效，不用另开一个后台程序。

支持：

- Cursor
- Claude Code
- Codex
- 豆包编程（TRAE 国内版）

豆包聊天 App 没有任务结束钩子，所以装到的是 TRAE。macOS、Linux、Windows 都可以装。

## 复制给 AI 的指令

把下面整段发给 Cursor、Claude Code、Codex 或豆包：

```
请把「陛下上朝」安装到这台电脑。仓库是 https://github.com/clong202603-star/bixia-shangchao 。克隆后运行 python3 install.py（Windows 用 python install.py）。它会把提示音装进 Cursor、Claude Code、Codex、豆包（TRAE）的用户级 hook：一轮对话正常结束就播放声音并弹出桌面提醒。不要删除这些软件里已经存在的其他 hook，只追加或更新这一条。装完后运行一次 ~/.ai-task-done/notify.py 试听，并告诉我装到了哪些路径。如果是 Codex，提醒我在 Codex 里输入 /hooks 信任这条新命令。如果是豆包 / TRAE，提醒我在设置里启用 Hooks。
```

也可以在终端直接装：

```bash
curl -fsSL https://raw.githubusercontent.com/clong202603-star/bixia-shangchao/main/install.sh | bash
```

## 装好之后

- 提示音文件在 `~/.ai-task-done/done.mp3`，想换声音就替换这个文件。
- Cursor 默认还会读取 Claude Code 的 hook。同一轮结束如果两边都触发，5 秒内只响一次。
- Codex 要在 `/hooks` 里信任新命令，之后才会真正执行。
- 豆包 / TRAE 用的是「任务完成」通知（`idle_prompt`），不会拦住智能体结束。
- 中途手动停掉的任务不响。

## 文件

| 文件 | 作用 |
| --- | --- |
| `install.py` | 复制文件并写入各软件的 hook |
| `install.sh` | macOS / Linux 的安装入口 |
| `notify.py` | 播放声音并弹出提醒 |
| `sounds/done.mp3` | 默认提示音 |

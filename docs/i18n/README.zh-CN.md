# Cursor_sidecar

从 Cursor 到设备端 Agent CLI 的稳定启动路径。

![Cursor_sidecar cover](../assets/social-preview.png)

**语言：** [English](../../README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

---

## 这是什么

**Cursor_sidecar** 是同名舰队技能的公开主页（前称 `cursor-codex-launch`）。

当 Cursor（含 Project Shell）需要启动设备端 Agent CLI 时，本技能规定共用路径：**tmux 启动壳**、**按 Agent 的适配器**、**预检门**，以及让 worker 知道何时退出的 **完成铃**。

它以磁盘上的舰队技能形式存在，不是插件目录里的名字。

**负责 Bot：** Engineering Lead · 工程师  
**仓库：** [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar)

---

## 功能

- **多适配器选择** — BRIEF 用 `agent:`（单个）或 `agents:`（列表）；两者都省略则默认 `codex`
- **共用 tmux 壳 + 完成铃** — 一个 wrapper 启动 Agent、写退出文件，再给 waiter 发信号
- **按适配器预检** — 失败则 `STATUS: STUCK` 并关闭；Cursor 不得把 Agent 的活自己做掉作为兜底
- **多会话** — 串行或并行；每个 Agent 各自的 session、signal 与 `RUN_DIR` 子目录
- **仅业务 BRIEF 的短引用** — 一句话指针即可，BRIEF 里不必写启动教程
- **回执要求** — session 启动方式、退出文件、signal、适配器与 STATUS 行必须齐备

---

## 怎么用

### 落地技能

从仓库安装完整目录，目标必须是新目录或空目录：

```sh
python3 scripts/install-skill.py --check
python3 scripts/install-skill.py --dest ~/.cursor/skills/Cursor_sidecar
```

必须同时包含 `SKILL.md`、`scripts/run-agent-with-tmux-signal.py`、`adapters/` 和 `docs/architecture.md`。也可整体复制仓库 `.cursor/skills/Cursor_sidecar/`，或安装到作业 `RUN_DIR`；只复制 `SKILL.md` 不算安装。安装器校验副本、保留执行权限、读回并输出 wrapper SHA256，不覆盖已有安装。升级先放入新目录验证，再由安装负责人替换旧目录。

加载技能后，将 `SKILL_ROOT` 设为该 `SKILL.md` 所在的绝对目录。文中的 `scripts/`、`adapters/`、`docs/` 均相对此目录解析。缺 wrapper 或所选适配器则 `STATUS: STUCK`，补齐安装后才能启动。

这个名字**不是** GBrain / 插件的 `get_skill` 目录项。BRIEF 不得对 `Cursor_sidecar` 调用插件 `get_skill`。

### 在仅业务 BRIEF 里引用

```
Agent launch: follow fleet skill Cursor_sidecar
(on-disk ~/.cursor/skills/Cursor_sidecar/SKILL.md or RUN_DIR copy).
Do not use plugin get_skill for this name.
Selection: agent: <name> or agents: [<names>].
Omit both to default to codex.
```

### 选择 Agent

| BRIEF 字段 | 含义 |
| --- | --- |
| `agent: <name>` | `adapters/` 下的一个适配器 |
| `agents: [<names>]` | 每个条目一个 session |
| 两者都设，或 `agents:` 为空 | `STATUS: STUCK` — 改 BRIEF |
| 两者都省略 | 默认 `codex` |

### 启动形态（概要）

1. 先跑 `adapters/<name>/preflight.sh`。失败 → `STATUS: STUCK`，停止，不要启动。
2. 优先 `tmux new-session -d`，用环境变量 / argv 交给共用 wrapper。**禁止**用多行 `tmux send-keys` 粘贴 wrapper（会弄乱 argv，Agent 根本起不来）。
3. 共用壳：`scripts/run-agent-with-tmux-signal.py` — 每个 session 一条 Agent 命令。
4. Waiter 必须有超时；不要让 worker 一直停在 `running`。

完整硬规则见技能正文与 `docs/architecture.md`。

---

## 适配器

| 适配器 | 路径 | 说明 |
| --- | --- | --- |
| Codex | `adapters/codex/` | BRIEF 未选时的默认。预检版本、鉴权是否存在、配置。 |
| Hermes | `adapters/hermes/` | 适配器已在仓库中。若 `PATH` 上没有 `hermes` CLI，预检会失败关闭。非交互参数仍为 TODO — 装好 CLI 后再把这条路径当冒烟通过。 |
| 模板 | `adapters/_template/` | Owner 点名新 Agent 时复制。 |

契约细节：[`adapters/README.md`](../../adapters/README.md)。

---

## 回执与完成

在 wrapper 的 `finally`（以及任意退出路径）中：

1. 写 `exit.txt` 与 `agent.exit`（相同内容）。当二进制基名为 `codex` 时，再写 `codex.exit`。
2. 然后 `tmux wait-for -S <signal>`。
3. 若子进程挂住：超时也必须强制 `-S`，并把超时原因写入退出文件。

一旦 `RUN_DIR` 里有 RECEIPT，且首行 STATUS 为 `STATUS: FIXED` 或 `STATUS: STUCK`，Cursor 私有 worker 交出终态并**退出**。

---

## 这不是什么

- **不是** Cursor Marketplace 技能 — 除非 Owner 点名发布，否则不要上架。
- **不是** GBrain / 插件 `get_skill` 注册名 — 不要把这个名字写进那些目录。
- **不是** 重写 KM 持有的 GBrain wrapper 正文的许可（`templates/run-codex-with-tmux-signal.py`）。保留文件不代表可以继续运行不合规 pin。启动前必须通过技能的 SO19 合规门：绑定当前 SHA256 的正常返回和超时双路径证据，三个适用退出文件内容一致且先写后信号，使用绝对 tmux 并遵守 `TMUX_BIN`，等待有界且无多行 `send-keys`。缺证据或不合规则 `STATUS: STUCK`；启动方案改用完整技能内的 wrapper 并重新预检/冒烟；必须使用原路径的任务留给 KM/Owner 处理。不得重写 KM wrapper。

---

## 链接

| 内容 | 位置 |
| --- | --- |
| 技能正文 | `~/.cursor/skills/Cursor_sidecar/SKILL.md`（或作业 `RUN_DIR` 副本） |
| 共用壳 | [`scripts/run-agent-with-tmux-signal.py`](../../scripts/run-agent-with-tmux-signal.py) |
| 适配器 | [`adapters/`](../../adapters/) |
| 架构 | [`docs/architecture.md`](../architecture.md) |
| 公开仓库 | [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar) |

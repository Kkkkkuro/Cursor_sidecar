# Cursor_sidecar

Cursor からデバイス上の Agent CLI への安定した起動パス。

![Cursor_sidecar cover](../assets/social-preview.png)

**言語：** [English](../../README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

---

## これは何か

**Cursor_sidecar** は、同名のフリート技能の公開ホームです（旧称 `cursor-codex-launch`）。

Cursor（Project Shell を含む）がデバイス上の Agent CLI を起動する必要があるとき、この技能が共有パスを定義します。**tmux 起動シェル**、**Agent ごとのアダプタ**、**プリフライト**、そしてワーカーが終了タイミングを知るための **完了ベル** です。

ディスク上のフリート技能として存在し、プラグインカタログの名前ではありません。

**担当ボット：** Engineering Lead · 工程师  
**リポジトリ：** [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar)

---

## 機能

- **マルチアダプタ選択** — BRIEF は `agent:`（単一）または `agents:`（リスト）を指定；両方省略すると既定は `codex`
- **共有 tmux シェル + 完了ベル** — ひとつのラッパーが Agent を起動し、終了ファイルを書き、待機側へ信号を送る
- **アダプタ別プリフライト** — 失敗時は `STATUS: STUCK` で閉じる；Cursor が Agent の作業を代替実行してはならない
- **マルチセッション** — 逐次または並列；Agent ごとに独自の session・signal・`RUN_DIR` サブディレクトリ
- **業務のみ BRIEF の短い引用** — 短いポインタで足りる；BRIEF に起動チュートリアルは不要
- **レシート要件** — session の起動形、終了ファイル、signal、アダプタ、STATUS 行が必須

---

## 使い方

### 技能の配置

リポジトリから完全なディレクトリをインストールする。配置先は新規または空のディレクトリに限る：

```sh
python3 scripts/install-skill.py --check
python3 scripts/install-skill.py --dest ~/.cursor/skills/Cursor_sidecar
```

`SKILL.md`、`scripts/run-agent-with-tmux-signal.py`、`adapters/`、`docs/architecture.md` がすべて必要。リポジトリの `.cursor/skills/Cursor_sidecar/` 全体をコピーしてもよい。ジョブの `RUN_DIR` も配置先にできる。`SKILL.md` だけでは不完全。インストーラはコピーと実行権限を検証し、読み戻して wrapper SHA256 を出力する。既存の配置は上書きしない。更新は新規ディレクトリで検証し、配置担当者が旧配置を置き換える。

読み込んだ `SKILL.md` の絶対親ディレクトリを `SKILL_ROOT` とし、文中の `scripts/`、`adapters/`、`docs/` はそこから解決する。wrapper または選択したアダプタが欠けていたら `STATUS: STUCK` とし、完全な配置を用意してから起動する。

この名前は GBrain / プラグインの `get_skill` カタログ項目では**ない**。BRIEF は `Cursor_sidecar` に対してプラグイン `get_skill` を呼んではならない。

### 初回のモデル・推論強度・fast の選択

Python 3.11+ が必要です。Codex の初回起動前に、3 項目すべてを明示的に選択します。

```sh
python3 "$SKILL_ROOT/scripts/agent_defaults.py" setup --model <選択モデル> --effort <選択強度> --fast false
```

この文書化された setup は、`[codex]` の `model`、`effort`、真偽値 `fast` を `$SKILL_ROOT/defaults.toml`（通常は `~/.cursor/skills/Cursor_sidecar/defaults.toml`）へ保存します。CLI とアカウントが対応するモデル・強度を選んでください。ファイルがなければ事前検査と起動は `STATUS: STUCK` となり、setup を案内します。固定の製品モデルへのフォールバックはありません。変更時は全項目と `--replace` を指定して setup を再実行します。元のバイト列を先に `defaults.toml.backup-*` へ保存します。設定とバックアップは Git に入れず、更新用ディレクトリを用意するときは別途保持します。

ジョブ単位の上書きは、BRIEF のインデント・引用符なしのスカラーキーで指定します。

```text
agent_model: your-model
agent_effort: high
agent_fast: true
```

指定した項目だけが保存値を上書きし、省略項目は保存値を使います。全項目を上書きする場合も有効な defaults ファイルは必要です。事前検査と共有 wrapper に**同じ** `--brief /absolute/BRIEF.md` を渡します。両方で `--defaults-file /absolute/defaults.toml` を指定できます。setup ツールではこの引数を `setup`/`resolve` の**前**に置きます。重複キー、空値・不正な識別子、true/false 以外の fast、不正な TOML は拒否します。`agents:` の各 Codex session に同じ上書きを適用します。異なる選択には別々の BRIEF を使います。

設定と BRIEF は通常ファイルに限り、空のパスは拒否します。setup が設定を公開した後に読み戻しが失敗した場合、エラーを返してバックアップを保持します。再試行や手動復元の前に両方を確認してください。同時に行われた変更を自動で上書きしません。

```sh
"$SKILL_ROOT/adapters/codex/preflight.sh" --brief "$BRIEF"
# 既存の tmux wrapper 起動にも --brief "$BRIEF" を追加します。
```

wrapper は解決した値を Codex のプロセス単位 CLI 引数で適用します。事前検査は基礎 TOML と解決済み起動設定を検証し、モデル・強度を固定せず、`~/.codex/config.toml` を書き換えません。`codex exec -- 'prompt'` を使います。`--` より前の設定上書き引数は defaults/BRIEF の迂回を防ぐため拒否します。fast=true は `service_tier="fast"` と `features.fast_mode=true`、false は明示的に `"default"` と false に対応します。利用可否はアカウント・モデルに依存し、fast は使用量を増やす場合があります。[公式の速度説明](https://learn.chatgpt.com/docs/agent-configuration/speed)を参照してください。Hermes と `_template` は起動・設定の対応関係が未測定のため、`ADAPTER.md` で全 3 項目を N/A と明記します。Hermes は引き続き起動を拒否します。完全なインストールには `scripts/agent_defaults.py` も含まれます。

### 業務のみ BRIEF での引用

```
Agent launch: follow fleet skill Cursor_sidecar
(on-disk ~/.cursor/skills/Cursor_sidecar/SKILL.md or RUN_DIR copy).
Do not use plugin get_skill for this name.
Selection: agent: <name> or agents: [<names>].
Omit both to default to codex.
```

### Agent の選択

| BRIEF フィールド | 意味 |
| --- | --- |
| `agent: <name>` | `adapters/` 下のひとつのアダプタ |
| `agents: [<names>]` | エントリごとにひとつの session |
| 両方設定、または `agents:` が空 | `STATUS: STUCK` — BRIEF を直す |
| 両方省略 | 既定 `codex` |

### 起動の形（概要）

1. まず `adapters/<name>/preflight.sh` を実行。失敗 → `STATUS: STUCK`、停止。起動しない。
2. `tmux new-session -d` を優先し、環境変数 / argv で共有ラッパーへ渡す。**禁止：** 複数行の `tmux send-keys` でラッパーを貼り付けること（argv が壊れ、Agent が起動しない）。
3. 共有シェル：`scripts/run-agent-with-tmux-signal.py` — session ごとに Agent コマンドはひとつ。
4. 待機側にはタイムアウトが必須；ワーカーを永久に `running` のままにしない。

完全なハードルールは技能本文と `docs/architecture.md` を参照。

---

## アダプタ

| アダプタ | パス | 備考 |
| --- | --- | --- |
| Codex | `adapters/codex/` | BRIEF が選択を省略したときの既定。プリフライトはバージョン、認証の有無、設定を確認。 |
| Hermes | `adapters/hermes/` | アダプタはリポジトリに存在する。`PATH` に `hermes` CLI が無い場合、プリフライトは失敗して閉じる。非対話フラグはまだ TODO — CLI を入れてからスモーク成功とみなすこと。 |
| テンプレート | `adapters/_template/` | Owner が新しい Agent を指名したときにコピー。 |

契約の詳細：[`adapters/README.md`](../../adapters/README.md)。

---

## レシートと完了

ラッパーの `finally`（および任意の終了パス）で：

1. `exit.txt` と `agent.exit` を同じ内容で書く。バイナリの basename が `codex` のときは `codex.exit` も書く。
2. 続けて `tmux wait-for -S <signal>`。
3. 子プロセスがハングした場合でも、タイムアウトは必ず `-S` を強制し、理由を終了ファイルに書く。

`RUN_DIR` に RECEIPT があり、先頭の STATUS 行が `STATUS: FIXED` または `STATUS: STUCK` なら、Cursor のプライベートワーカーは最終状態を渡して**終了**する。

---

## これは何かではない

- **Cursor Marketplace 技能ではない** — Owner がその公開を指名しない限り載せない。
- **GBrain / プラグイン `get_skill` の登録名ではない** — それらのカタログにこの名前を足さない。
- **KM 所有の GBrain ラッパー本文を書き換える許可ではない**（`templates/run-codex-with-tmux-signal.py`）。ファイルの保持は不適合な pin の実行許可ではない。起動前に SO19 ゲートを満たすこと：現在の SHA256 に対応する正常終了・強制タイムアウト両方の証拠、該当する終了ファイルの同一内容と信号前の書き込み、`TMUX_BIN` に従う絶対 tmux パス、有界の待機、複数行 `send-keys` なし。証拠不足・不適合なら `STATUS: STUCK`。完全な技能内の wrapper に起動計画を変更してプリフライトとスモークを再実行する。固定パスが必須なら KM/Owner に委ねて停止を維持する。KM 本文は書き換えない。

---

## リンク

| 内容 | 場所 |
| --- | --- |
| 技能本文 | `~/.cursor/skills/Cursor_sidecar/SKILL.md`（またはジョブ `RUN_DIR` のコピー） |
| 共有シェル | [`scripts/run-agent-with-tmux-signal.py`](../../scripts/run-agent-with-tmux-signal.py) |
| アダプタ | [`adapters/`](../../adapters/) |
| アーキテクチャ | [`docs/architecture.md`](../architecture.md) |
| 公開リポジトリ | [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar) |

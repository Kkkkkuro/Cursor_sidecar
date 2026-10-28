# Cursor_sidecar

Cursor에서 장치 Agent CLI로 가는 안정적인 실행 경로.

![Cursor_sidecar cover](../assets/social-preview.png)

**언어:** [English](../../README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

---

## 이것이 무엇인지

**Cursor_sidecar**는 같은 이름 플릿 스킬의 공개 홈입니다(이전 이름 `cursor-codex-launch`).

Cursor(Project Shell 포함)가 장치 Agent CLI를 시작해야 할 때, 이 스킬이 공용 경로를 정합니다. **tmux 실행 셸**, **Agent별 어댑터**, **프리플라이트**, 그리고 워커가 언제 종료할지 알게 하는 **완료 벨**입니다.

디스크 위 플릿 스킬로 존재하며, 플러그인 카탈로그 이름이 아닙니다.

**담당 봇:** Engineering Lead · 工程师  
**저장소:** [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar)

---

## 기능

- **다중 어댑터 선택** — BRIEF가 `agent:`(하나) 또는 `agents:`(목록)를 지정; 둘 다 생략하면 기본값 `codex`
- **공용 tmux 셸 + 완료 벨** — 하나의 래퍼가 Agent를 시작하고, 종료 파일을 쓴 뒤 waiter에 신호를 보냄
- **어댑터별 프리플라이트** — 실패 시 `STATUS: STUCK`으로 닫힘; Cursor가 Agent 작업을 대신 수행하면 안 됨
- **다중 세션** — 순차 또는 병렬; Agent마다 고유 session, signal, `RUN_DIR` 하위 디렉터리
- **업무만 BRIEF의 짧은 인용** — 짧은 포인터면 충분; BRIEF에 실행 튜토리얼은 필요 없음
- **영수증 요건** — session 시작 형태, 종료 파일, signal, 어댑터, STATUS 줄이 있어야 함

---

## 사용 방법

### 스킬 배치

저장소에서 완전한 디렉터리를 설치합니다. 대상은 새 디렉터리 또는 빈 디렉터리여야 합니다:

```sh
python3 scripts/install-skill.py --check
python3 scripts/install-skill.py --dest ~/.cursor/skills/Cursor_sidecar
```

`SKILL.md`, `scripts/run-agent-with-tmux-signal.py`, `adapters/`, `docs/architecture.md`가 모두 필요합니다. 저장소의 `.cursor/skills/Cursor_sidecar/` 전체를 복사하거나 작업 `RUN_DIR`에 설치해도 됩니다. `SKILL.md`만으로는 불완전합니다. 설치기는 복사본과 실행 권한을 검증하고 읽어서 wrapper SHA256을 출력하며, 기존 설치를 덮어쓰지 않습니다. 업데이트는 새 디렉터리에서 검증한 후 설치 담당자가 기존 디렉터리를 교체합니다.

읽은 `SKILL.md`의 절대 부모 디렉터리를 `SKILL_ROOT`로 설정합니다. 본문의 `scripts/`, `adapters/`, `docs/`는 이 위치를 기준으로 해석합니다. wrapper 또는 선택한 어댑터가 없으면 `STATUS: STUCK`으로 멈추고 전체 설치를 먼저 완료합니다.

이 이름은 GBrain / 플러그인 `get_skill` 카탈로그 항목이 **아닙니다**. BRIEF는 `Cursor_sidecar`에 대해 플러그인 `get_skill`을 호출하면 안 됩니다.

### 첫 실행 모델, 추론 강도, fast 선택

Python 3.11+가 필요합니다. 첫 Codex 실행 전에 세 값을 모두 명시적으로 선택합니다.

```sh
python3 "$SKILL_ROOT/scripts/agent_defaults.py" setup --model <선택모델> --effort <선택강도> --fast false
```

이 문서화된 setup은 `[codex]`의 `model`, `effort`, 불리언 `fast`를 `$SKILL_ROOT/defaults.toml`에 저장합니다. 기본 위치는 `~/.cursor/skills/Cursor_sidecar/defaults.toml`입니다. 설치된 CLI와 계정이 지원하는 모델 및 강도를 선택하세요. 파일이 없으면 사전 검사와 실행은 `STATUS: STUCK`으로 중단되고 setup 안내를 표시합니다. 고정 제품 모델로 대체하지 않습니다. 나중에 세 값과 `--replace`를 지정하여 setup을 다시 실행하면 변경됩니다. 이전 바이트는 먼저 `defaults.toml.backup-*`에 보관합니다. 로컬 선택 및 백업은 Git에 넣지 말고, 업데이트용 디렉터리를 준비할 때 별도로 보존하세요.

작업별 덮어쓰기는 BRIEF에 들여쓰기와 따옴표 없는 스칼라 키로 지정합니다.

```text
agent_model: your-model
agent_effort: high
agent_fast: true
```

제공한 키만 저장값을 덮어쓰고 생략한 키는 기본값을 유지합니다. 세 항목을 모두 덮어써도 유효한 defaults 파일이 필요합니다. 사전 검사와 공용 wrapper에 **동일한** `--brief /absolute/BRIEF.md`를 전달합니다. 두 명령 모두 `--defaults-file /absolute/defaults.toml`로 다른 저장 파일을 선택할 수 있습니다. setup 도구에서는 이 인수를 `setup`/`resolve` **앞에** 둡니다. 중복 키, 빈 값이나 잘못된 식별자, true/false 이외의 fast, 잘못된 TOML은 거부합니다. `agents:`의 각 Codex session에 같은 값을 적용하며, 서로 다른 선택은 별도 BRIEF를 사용합니다.

설정과 BRIEF는 일반 파일이어야 하며 빈 경로는 거부합니다. setup이 설정을 게시한 뒤 읽기 검증에 실패하면 오류를 반환하고 백업을 보존합니다. 재시도나 수동 복원 전에 두 파일을 확인하세요. 동시에 발생한 변경을 자동으로 덮어쓰지 않습니다.

```sh
"$SKILL_ROOT/adapters/codex/preflight.sh" --brief "$BRIEF"
# 기존 tmux wrapper 실행에도 --brief "$BRIEF"를 추가합니다.
```

wrapper는 해석한 설정을 프로세스별 Codex CLI 인수로 적용합니다. 사전 검사는 기본 TOML 및 해석된 실행 설정을 검증하며, 모델과 강도를 고정하지 않고 `~/.codex/config.toml`을 수정하지 않습니다. `codex exec -- 'prompt'`를 사용합니다. defaults/BRIEF를 우회하지 못하도록 `--` 앞의 설정 덮어쓰기 인수는 거부합니다. fast=true는 `service_tier="fast"`와 `features.fast_mode=true`, false는 명시적으로 `"default"`와 false에 대응합니다. 가용성은 계정과 모델에 따라 다르며 fast는 사용량을 늘릴 수 있습니다. [공식 속도 문서](https://learn.chatgpt.com/docs/agent-configuration/speed)를 참고하세요. Hermes와 `_template`은 실행 및 설정 매핑이 측정되지 않아 `ADAPTER.md`에 세 항목 모두 N/A로 명시합니다. Hermes는 계속 실행을 거부합니다. 전체 설치에는 `scripts/agent_defaults.py`도 포함됩니다.

### 업무만 BRIEF에서의 인용

```
Agent launch: follow fleet skill Cursor_sidecar
(on-disk ~/.cursor/skills/Cursor_sidecar/SKILL.md or RUN_DIR copy).
Do not use plugin get_skill for this name.
Selection: agent: <name> or agents: [<names>].
Omit both to default to codex.
```

### Agent 선택

| BRIEF 필드 | 의미 |
| --- | --- |
| `agent: <name>` | `adapters/` 아래 어댑터 하나 |
| `agents: [<names>]` | 항목마다 session 하나 |
| 둘 다 설정, 또는 `agents:`가 비어 있음 | `STATUS: STUCK` — BRIEF를 고침 |
| 둘 다 생략 | 기본값 `codex` |

### 실행 형태(개요)

1. 먼저 `adapters/<name>/preflight.sh` 실행. 실패 → `STATUS: STUCK`, 중단. 실행하지 않음.
2. `tmux new-session -d`를 우선하고, 환경 변수 / argv로 공용 래퍼에 전달. **금지:** 여러 줄 `tmux send-keys`로 래퍼를 붙여 넣기(argv가 깨져 Agent가 시작되지 않음).
3. 공용 셸: `scripts/run-agent-with-tmux-signal.py` — session마다 Agent 명령 하나.
4. Waiter에는 타임아웃이 있어야 함; 워커를 영원히 `running`으로 두지 않음.

전체 하드 규칙은 스킬 본문과 `docs/architecture.md`를 보세요.

---

## 어댑터

| 어댑터 | 경로 | 참고 |
| --- | --- | --- |
| Codex | `adapters/codex/` | BRIEF가 선택을 생략할 때의 기본값. 프리플라이트가 버전, 인증 존재 여부, 설정을 확인. |
| Hermes | `adapters/hermes/` | 어댑터는 저장소에 있음. `PATH`에 `hermes` CLI가 없으면 프리플라이트가 실패하고 닫힘. 비대화형 플래그는 아직 TODO — CLI를 설치한 뒤에야 스모크 통과로 취급. |
| 템플릿 | `adapters/_template/` | Owner가 새 Agent를 지정할 때 복사. |

계약 세부사항: [`adapters/README.md`](../../adapters/README.md).

---

## 영수증과 완료

래퍼의 `finally`(및 모든 종료 경로)에서:

1. `exit.txt`와 `agent.exit`를 같은 내용으로 씀. 바이너리 basename이 `codex`이면 `codex.exit`도 씀.
2. 이어서 `tmux wait-for -S <signal>`.
3. 자식이 멈추면 타임아웃도 반드시 `-S`를 강제하고, 이유를 종료 파일에 씀.

`RUN_DIR`에 RECEIPT가 있고 첫 STATUS 줄이 `STATUS: FIXED` 또는 `STATUS: STUCK`이면, Cursor 프라이빗 워커는 최종 상태를 전달하고 **종료**합니다.

---

## 이것이 아닌 것

- **Cursor Marketplace 스킬이 아님** — Owner가 그 게시를 지정하지 않는 한 올리지 않음.
- **GBrain / 플러그인 `get_skill` 등록 이름이 아님** — 그 카탈로그에 이 이름을 넣지 않음.
- **KM 소유 GBrain 래퍼 본문을 다시 쓸 권한이 아님**(`templates/run-codex-with-tmux-signal.py`). 파일 보존은 비준수 pin 실행 허가가 아닙니다. 실행 전 SO19 게이트가 필요합니다: 현재 SHA256에 연결된 정상 반환 및 강제 타임아웃 증거, 해당 종료 파일의 동일 내용과 신호 전 기록, `TMUX_BIN`을 따르는 절대 tmux 경로, 유한 대기, 다중 행 `send-keys` 없음. 증거가 없거나 실패하면 `STATUS: STUCK`입니다. 완전한 스킬의 wrapper로 실행 계획을 전환하고 프리플라이트와 스모크를 다시 실행합니다. 정확한 고정 경로가 필수이면 KM/Owner가 해결할 때까지 멈춥니다. KM 본문은 수정하지 않습니다.

---

## 링크

| 내용 | 위치 |
| --- | --- |
| 스킬 본문 | `~/.cursor/skills/Cursor_sidecar/SKILL.md`(또는 잡 `RUN_DIR` 복사본) |
| 공용 셸 | [`scripts/run-agent-with-tmux-signal.py`](../../scripts/run-agent-with-tmux-signal.py) |
| 어댑터 | [`adapters/`](../../adapters/) |
| 아키텍처 | [`docs/architecture.md`](../architecture.md) |
| 공개 저장소 | [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar) |

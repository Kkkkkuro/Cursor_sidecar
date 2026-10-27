# Cursor_sidecar

Cursor에서 장치 Agent CLI로 가는 안정적인 실행 경로.

<!-- Cover image (../assets/social-preview.png) lands after Art Director QC + Owner approval. Follow-up PR. -->

**언어:** [English](../../README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

---

## 이것이 무엇인지

**Cursor_sidecar**는 같은 이름 플릿 스킬의 공개 홈입니다(이전 이름 `cursor-codex-launch`).

Cursor(Project Shell 포함)가 장치 Agent CLI를 시작해야 할 때, 이 스킬이 공용 경로를 정합니다. **tmux 실행 셸**, **Agent별 어댑터**, **프리플라이트**, 그리고 워커가 언제 종료할지 알게 하는 **완료 벨**입니다.

디스크 위 플릿 스킬로 존재하며, 플러그인 카탈로그 이름이 아닙니다.

**담당 봇:** tinkabot · 插件技能MCP  
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

플릿이 돌아가는 머신에서는:

```
~/.cursor/skills/Cursor_sidecar/SKILL.md
```

작업은 잡 `RUN_DIR` 아래에 복사본을 둘 수도 있습니다. 어댑터를 통해 Agent CLI를 시작하는 Cursor 단계 전에 이 파일을 읽으세요.

이 이름은 GBrain / 플러그인 `get_skill` 카탈로그 항목이 **아닙니다**. BRIEF는 `Cursor_sidecar`에 대해 플러그인 `get_skill`을 호출하면 안 됩니다.

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
- **KM 소유 GBrain 래퍼 본문을 다시 쓸 권한이 아님**(`templates/run-codex-with-tmux-signal.py`). 이미 그 파일을 고정한 GBrain 잡은 그대로 사용.

---

## 링크

| 내용 | 위치 |
| --- | --- |
| 스킬 본문 | `~/.cursor/skills/Cursor_sidecar/SKILL.md`(또는 잡 `RUN_DIR` 복사본) |
| 공용 셸 | [`scripts/run-agent-with-tmux-signal.py`](../../scripts/run-agent-with-tmux-signal.py) |
| 어댑터 | [`adapters/`](../../adapters/) |
| 아키텍처 | [`docs/architecture.md`](../architecture.md) |
| 공개 저장소 | [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar) |

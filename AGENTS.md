# AGENTS — youtube-downloader

에이전트가 이 저장소에서 작업할 때 따르는 규칙.
Claude Code는 `CLAUDE.md`를 읽는다. 이 파일은 그 외 에이전트를 위한 같은 내용이다.

## 구조

| 위치 | 무엇 | 수명 |
| --- | --- | --- |
| `docs/current/INTENT.md` | 이 프로젝트가 무엇을 왜 하는가. **SSOT** | 프로젝트 전체 |
| `docs/current/` | 현재 버전 문서 (INTENT 제외) | 버전 |
| `docs/history/vX.Y/` | 지난 버전 문서. INTENT는 없다. **불변** | 영구 |
| `README.md` · `CLAUDE.md` · `.claude/` | 프로젝트 전체 | 영구 |
| `src/` · `scripts/` · `tests/` | 코드 | — |

## 하지 않을 것

- `docs/current/`의 문서(`INTENT`·`BRIEF`·`DECISIONS`·`SPEC`·`PLAN`·`backlog.json`)를 고치지 않는다. **사람이 쓴다**
- `INTENT.md`(SSOT)는 사람의 요청으로만 고친다. 스스로 바꾸지 않는다
- 문서가 `INTENT.md`에 어긋나면 혼자 맞추지 말고 멈추고 보고한다
- `docs/history/` 아래를 수정·삭제하지 않는다. 읽기만 한다
- `backlog.json`을 직접 편집하지 않는다. CLI로만 바꾼다
- 진행 중에 task를 추가하지 않는다
- 완료 조건을 스스로 정하지 않는다
- 되돌릴 수 없는 작업을 묻지 않고 하지 않는다

## 할 것

- task를 닫을 때마다 `docs/current/PROGRESS.md`에 기록한다 — 무엇을·결과·검증
- 계획 밖의 작업은 `PROGRESS.md`의 "계획 외 개선"에 적는다
- 요구가 바뀌면 `SPEC.md`부터 고친다
- 막히면 추측으로 채우지 말고 멈추고 묻는다

## 검증

Phase를 닫기 전에 `PLAN.md`의 완료 조건을 하나씩 대조한다.
근거를 대지 못하면 미충족이다. **"통과"를 기본값으로 두지 않는다.**

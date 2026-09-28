> 참고 문서 · 작성일: 2026-09-28 · 상태: 예상안 (착수 전)

# STRUCTURE — 예상 폴더 구조

착수(INIT) 후 v0.1 구현이 끝났을 때의 예상 구조다. 확정된 설계가 아니라 구현자가 참고할
출발점이며, 실제 구조는 구현 중에 달라질 수 있다. 결정의 근거는 `DECISIONS.md`를 본다.

## 1. 프로젝트 폴더

빌드·실행·패키징은 `workbench-kit`의 pywebview 갈래 방식을 따른다(D-27). 아래
`src/` 배치도 그 방식(화면은 Vite + TypeScript, Python 호스트는 `src/hosts/pywebview/`)을
따른다. `workbench-kit`의 코드는 가져오지 않는다(D-3).

```
youtube-downloader/
├── AGENTS.md                      # 에이전트 지침 (INIT 하네스)
├── CLAUDE.md                      # @AGENTS.md
├── README.md                      # 개요 (설치·사용법은 마감 때)
├── .gitignore                     # node_modules/, dist/, dist-py/, build/, __pycache__/, *.egg-info/
├── .claude/                       # hook·rules·reviewer (HARNESS.md)
│
├── docs/
│   ├── current/                   # INTENT·BRIEF·DECISIONS·SPEC·PLAN·PROGRESS
│   ├── history/                   # 버전 마감 스냅샷
│   └── refs/                      # 이 문서, LAYOUT.md
│
├── index.html                     # Vite 진입 HTML
├── package.json                   # scripts: dev · build · start:pywebview · package:pywebview
├── package-lock.json
├── tsconfig.json
├── vite.config.ts
├── requirements.txt               # pywebview, (개발) 로컬 youtube-kit editable 설치
├── youtube-downloader.spec        # PyInstaller onedir 설정 → dist-py/youtube-downloader/
│
├── src/
│   ├── main.ts                    # 화면 진입점: 영역 조립, 테마 적용
│   ├── bridge.ts                  # window.pywebview.api 호출 래퍼 + Python 이벤트 수신
│   ├── state.ts                   # 화면 쪽 큐 상태 (Python이 보낸 행 스냅샷을 그대로 반영)
│   │
│   ├── ui/
│   │   ├── toolbar.ts             # 시작·정지·위/아래·삭제·완료 지우기·저장 폴더·테마·설정
│   │   ├── url-input.ts           # 붙여넣기 → 여러 줄 분리 → add_urls
│   │   ├── queue-table.ts         # 행 렌더링, 선택, 행 안 선택 컨트롤
│   │   ├── status-bar.ts          # 개수·상태 요약, 중복·잘못된 입력 알림
│   │   ├── settings-dialog.ts     # 기본 규칙·선호 언어·컨테이너·자막 형식
│   │   └── confirm-close.ts       # 다운로드 중 닫기 확인
│   │
│   ├── styles/                    # 값은 workbench-kit pywebview 갈래와 같게 (D-30)
│   │   ├── tokens.css             # 글꼴 스택·간격·크기 ← workbench-kit src/style.css
│   │   ├── theme-light.css        # ← workbench-kit src/style.css [data-theme="light"]
│   │   ├── theme-dark.css         # ← 같은 파일 [data-theme="dark"] (gray는 가져오지 않음)
│   │   └── table.css
│   │                              # Codicon은 @vscode/codicons 패키지를 import (workbench-kit과 같은 버전)
│   │
│   └── hosts/
│       └── pywebview/
│           ├── __init__.py
│           ├── main.py            # 창 생성, js_api 연결, 닫기 확인 훅
│           ├── api.py             # JS → Python 공개 메서드 (아래 3절)
│           ├── queue.py           # 행 모델·순서·상태 전이 (큐의 단일 원본)
│           ├── workers.py         # 정보 조회 풀(동시 3) · 다운로드 순차 실행 · 취소 Event
│           ├── formats.py         # 조회 결과 → 선택지(해상도+fps·코덱·음성·자막), 기본 규칙 적용, 포맷 ID 확정
│           ├── storage.py         # 저장 폴더 배치 (2절), 경로 계산
│           ├── settings.py        # 설정 읽기·쓰기
│           └── events.py          # Python → JS 알림 (evaluate_js)
│
├── tests/
│   ├── fixtures/                  # 실제 youtube-kit info 결과 샘플 (*.meta.json, *.playlist.json)
│   ├── test_formats.py            # fps 구분, 같은 조합 여러 개, 규칙 불일치 시 빈 칸, 자막 필터
│   ├── test_queue.py              # 순서 이동, 중복 건너뜀, 상태 전이, 요약 집계
│   ├── test_storage.py            # <저장 폴더>\<영상 ID>\ 배치
│   └── test_workers.py            # 조회 동시 수 ≤ 3, 순차 다운로드, 취소 후 부분 파일 없음
│
├── scripts/                       # Phase별 검증 러너
│
├── dist/                          # vite build 산출물 (gitignore)
└── dist-py/                       # PyInstaller 산출물 (gitignore)
```

### 역할 나눔

- **큐의 원본은 Python(`queue.py`)이 가진다.** 화면(`state.ts`)은 Python이 보내 주는
  행 스냅샷을 그리기만 한다. 순서 변경·삭제·상태 전이는 모두 Python에서 일어나므로
  "표시 순서와 작업 순서가 같다"(FR-13·14·23)가 한 곳에서 보장된다.
- **포맷 선택 규칙은 Python(`formats.py`)에 둔다.** youtube-kit의 조회 결과를 직접 받고,
  실제 조회 결과 샘플(`tests/fixtures/`)로 pytest 검증할 수 있다. 화면은 선택지 목록과
  현재 선택값만 받는다.

## 2. 저장 폴더 (사용자 데이터)

앱이 만드는 파일의 배치다(D-15, FR-25). 파일명은 youtube-kit의 규칙을 그대로 쓴다.

```
<저장 폴더>\                          # 초기값: 사용자 Downloads (D-14)
├── JyEsEcsCqzM\                      # 영상 ID 폴더
│   ├── JyEsEcsCqzM.meta.json         # 정보 조회 결과 (info)
│   ├── JyEsEcsCqzM.299_140.mp4       # 영상+음성 (video)
│   └── JyEsEcsCqzM.manual.ko.srt     # 자막 (subtitle)
│
├── bWPXADZylm0\                      # 음성만 받은 영상
│   ├── bWPXADZylm0.meta.json
│   └── bWPXADZylm0.140.m4a           # (audio)
│
├── lF8_DX2NxjI\                      # 재생목록에서 펼친 영상도 같은 위치
│   ├── lF8_DX2NxjI.meta.json
│   └── lF8_DX2NxjI.136_140.mp4
│
└── PLyPc3E0Xm540Yfdln9qlVyyrqRME80jJm\   # 재생목록 ID 폴더
    └── PLyPc3E0Xm540Yfdln9qlVyyrqRME80jJm.playlist.json
```

- 저장 폴더 바로 아래에는 영상 ID 폴더와 재생목록 ID 폴더만 생긴다.
- 같은 영상을 같은 포맷으로 다시 받으면 youtube-kit이 기존 파일을 재사용하고, 행은
  `이미 있음`으로 끝난다(D-28).

## 3. 화면 ↔ Python 경계 (예상)

| 방향 | 이름 | 하는 일 | 관련 요구 |
| --- | --- | --- | --- |
| JS → Py | `add_urls(text)` | 여러 줄 분리, 중복·잘못된 입력 판정, 행 생성 후 조회 예약 | FR-1·3·30 |
| JS → Py | `select(row_id, field, value)` | 행의 해상도·코덱·음성·자막 변경, 무효 조합 정리 | FR-7~12 |
| JS → Py | `move(row_id, delta)` | 위/아래 이동 | FR-13·14 |
| JS → Py | `remove(row_ids)` · `clear_completed()` | 행 삭제(받는 중이면 취소), 완료 행 지우기 | FR-27·29 |
| JS → Py | `start()` · `stop()` | 순차 다운로드 시작·전체 정지 | FR-23·28 |
| JS → Py | `choose_folder()` | 저장 폴더 선택 창 | FR-24 |
| JS → Py | `get_settings()` · `save_settings(s)` | 설정 읽기·쓰기 | FR-26·32·34 |
| Py → JS | `rows(snapshot)` | 큐 전체 또는 바뀐 행 스냅샷 | FR-2·5·6 |
| Py → JS | `progress(row_id, event)` | 단계(download·merge·done)·바이트·속도·ETA | FR-17·18 |
| Py → JS | `notice(kind, count)` | 중복·잘못된 입력 알림 | FR-30 |

## 4. 아직 정하지 않은 것

- 설정 파일의 위치와 이름 (D-25는 무엇을 기억할지만 정했다)
- 로컬 youtube-kit을 `requirements.txt`에 적는 방식 (예: `-e ../youtube-kit`)

> 버전: v0.1

# PROGRESS — youtube-downloader

## 1. 계획된 작업

### Phase 1 · 전용 데스크톱 앱 골격과 시각 체계 확립 (2026-09-28)

**무엇을**
`workbench-kit`에 의존하지 않는 독립 pywebview 앱 골격을 만들었다.
- `package.json`·`vite.config.ts`·`tsconfig.json`·`index.html`·`requirements.txt` —
  D-27 방식(Vite + TypeScript 화면, `start:pywebview`/`package:pywebview` 스크립트).
- `src/styles/tokens.css`·`theme-light.css`·`theme-dark.css`·`table.css` — 글꼴 스택과
  Light/Dark 색 토큰을 `workbench-kit` `src/style.css`(커밋 `c2e3809`)에서 이 앱이
  실제로 쓰는 범위만 그대로 옮겼다. `@vscode/codicons` 버전을 `^0.0.46-24`로 맞췄다.
- `src/core/theme.ts` — `workbench-kit`의 `ThemeManager`를 Light/Dark 두 값으로 줄인 것.
- `src/ui/toolbar.ts`·`url-input.ts`·`queue-table.ts`·`status-bar.ts`·`main.ts` — Toolbar·
  URL 입력·Queue Table·Status 네 영역만 조립. Activity Bar·Explorer·Editor 없음.
  Toolbar의 Start/Stop/Move/Remove/Clear/Choose Folder/Settings는 이후 Phase에서 기능이
  붙을 자리만 만들고 지금은 비활성 처리했다(테마 전환만 동작).
- `src/hosts/pywebview/main.py`·`api.py` — 창 생성과 `js_api` 연결 뼈대.

**결과**
- `npm run typecheck`, `npm run build` 통과.
- `python -m src.hosts.pywebview.main`으로 창이 뜨고 예외 없이 종료됨(WinPython 3.11.8).
- `src/*.ts`, `src/**/*.css`, `index.html`에서 한글 문자(U+AC00–U+D7A3, U+3131–U+318E)
  없음을 `grep -P`로 확인.
- 아이콘 요소는 모두 `codicon codicon-*` 클래스이며 이모지·다른 아이콘 세트 없음.

**검증**
- PLAN.md Phase 1 완료 조건 7개 대조: 글꼴·색 토큰·Codicon 버전 일치, 영어·Codicon만
  사용, Windows pywebview 창 실행, 4영역 표시, 테마 전환 시 4영역 함께 전환(CSS 변수
  기반이라 구조적으로 보장), Toolbar 아이콘 Codicon과 툴팁으로 의미 확인 가능,
  `workbench-kit`의 Activity Bar·Explorer·Editor shell 미포함 — 모두 충족.
- Phase 1은 적대적 검증 필수 통과 대상이 아니다(PLAN.md 적대적 검증 절: 필수 통과는
  Phase 4·5·6). 반대 벤더 검토 자체도 사용자 판단으로 이번 Phase는 생략했다
  (2026-09-28, 순수 골격·스타일이라 위험이 낮다는 사용자 판단).

### Phase 2 · 큐 모델과 URL 입력 흐름 완성 (2026-09-28)

**무엇을**
- `src/hosts/pywebview/queue.py` — `Row`·`QueueManager`. 큐 순서 = 리스트 순서를 그대로
  단일 원본으로 둔다(FR-13·14·23을 대비한 설계, D-11).
- `src/hosts/pywebview/workers.py` — `FetchPool`(`ThreadPoolExecutor(max_workers=3)`)이
  실제 `youtube_kit.info()`를 백그라운드에서 호출한다. 스텁이 아니라 Phase 3에서도
  그대로 쓸 실제 backend 호출이며, Phase 3는 여기에 재생목록 전개와 포맷 선택만 더한다.
  동시 3개 제한(D-26·NFR-7)은 Phase 3 대상이지만 재작업을 피하려고 지금 넣었다.
- `src/hosts/pywebview/storage.py` — 저장 폴더 초기값(Downloads, D-14). 설정 영속화는
  FR-32(Phase 5) 대상이라 이번엔 메모리 값만 유지한다.
- `src/hosts/pywebview/events.py` — Python → JS 알림(`rows`·`notice`)을 `evaluate_js`로 보낸다.
- `src/hosts/pywebview/api.py` — `add_urls`가 `youtube_kit.url.parse_and_normalize_url`로
  줄마다 분류한다(video/playlist/invalid). video만 즉시 행을 만들고 조회를 예약한다.
  재생목록 URL(FR-3·4)은 유효한 YouTube URL이므로 "잘못된 입력"으로 세지 않되, 행도
  아직 만들지 않는다(Phase 3에서 전개). `remove`·`choose_folder`·`get_save_folder` 추가.
- 프런트: `src/bridge.ts`(JS↔Python 래퍼, `pywebviewready` 대기)·`src/state.ts`(큐
  스냅샷·선택·요약 문자열)·`toolbar.ts`(Remove·Choose Folder 활성화)·`url-input.ts`
  (D-7: paste 이벤트에서 clipboardData를 직접 읽어 즉시 `add_urls` 호출, 여러 줄 보존)·
  `queue-table.ts`(행 렌더링·선택·Queued/Fetching(spin)/Ready/Failed 상태 표시)·
  `status-bar.ts`(개수 요약·중복/잘못된 입력 알림).

**결과**
- `npm run typecheck`, `npm run build` 통과.
- `tests/test_queue.py` 7개 통과(`youtube_kit.info`를 monkeypatch해 오프라인 결정적으로
  검증: 즉시 행 생성, 여러 줄 붙여넣기의 중복/잘못된 입력 집계, 큐 내 중복 스킵,
  조회 실패 시 다른 행 유지와 실패 행 식별, 대기 행 삭제, 재생목록 URL 무행 처리,
  `add_urls`가 조회 완료를 기다리지 않고 즉시 반환함(NFR-4)).
- 실제 네트워크로 `Api.add_urls()`를 한 번 더 확인: 개별 영상 URL 1개 + 중복 1개 +
  잘못된 URL 1개를 한 번에 넣어 행 1개만 생성되고 `notice`가 `{duplicates:1, invalid:1}`로
  옴, `<Downloads>\<영상 ID>\<영상 ID>.meta.json`이 D-15대로 저장됨을 확인(스모크 후 삭제).
- `python -m src.hosts.pywebview.main`으로 창이 뜨고 예외 없이 종료됨.
- `src/*.ts`, `src/**/*.css`에서 한글 문자 없음을 `grep -P`로 재확인.

**검증**
- PLAN.md Phase 2 완료 조건 8개 대조: 개별 URL 즉시 행 생성, 여러 줄/중복/잘못된 입력
  처리, 대기 행 삭제, 저장 폴더 지정(초기값 Downloads), 조회 전/후 상태 구분(Queued·
  Fetching vs Ready), 조회 실패해도 다른 행 유지·실패 행 식별, 하단 상태 요약이 실제
  행 상태 반영, 조회 중 UI 비차단(`add_urls`가 즉시 반환 + 백그라운드 스레드) — 모두
  자동화된 테스트 또는 수동 스모크로 확인.
- `choose_folder()`의 실제 폴더 선택 대화상자는 `create_file_dialog`가 GUI 상호작용을
  요구해 이번 세션에서 대화상자 자체는 수동으로 열어보지 못했다. 배선(폴더 문자열을
  저장하고 `toolbar.setFolderPath`로 반영)은 코드 검토로 확인했다 — 다음 상호작용
  세션에서 실제 클릭으로 재확인 필요.
- Phase 2는 적대적 검증 필수 통과 대상이 아니며(PLAN.md: 필수 통과는 Phase 4·5·6),
  반대 벤더 검토 자체도 사용자 판단으로 Phase 4·5·6에만 집중하기로 했다(2026-09-28).

### Phase 3 · youtube-kit 정보 조회와 재생목록 전개 완성 (2026-09-28)

**무엇을**
- `src/hosts/pywebview/formats.py` — 조회 결과에서 기본 규칙(D-16 "호환 우선") 선택과
  표시 라벨을 만든다. `select_default_video`(avc1·1080p 이하·최고 해상도·최고 fps,
  동률이면 id로 결정적 tie-break)·`select_default_audio`(m4a·non-drc·원본 트랙
  우선·최고 abr)·`select_default_subtitle`(항상 None)·`subtitle_options`(수동·원어
  자동·선호 언어 자동 번역만, D-20)·`total_size`/`size_label`(D-19: 선택된 슬롯의
  크기를 하나라도 모르면 `-`). 규칙에 맞는 포맷이 없으면 `None`을 반환해 다른 포맷으로
  대신 채우지 않는다(NFR-6). Phase 4는 이 모듈의 옵션 목록을 그대로 드롭다운에 쓴다.
- `src/hosts/pywebview/workers.py`에 `PlaylistExpander` 추가 — 재생목록 URL을
  `yk.info()`로 펼쳐 `<list-id>.playlist.json`을 `<저장 폴더>\<list-id>\`에 저장하고
  (D-15), 항목마다(`id`가 있는 것만) 큐 행을 만들어 기존 `FetchPool`에 개별 정보 조회를
  예약한다. 재생목록 목록 조회 자체는 `FetchPool`의 동시 3개 제한(NFR-7)과는 별도
  풀에서 돈다 — NFR-7은 영상 단위 조회 동시성이지 재생목록 나열 자체가 아니다고 판단.
  `FetchPool._fetch`가 성공 시 `formats.apply_defaults()`를 호출해 행에 기본 선택·
  라벨·크기를 채운다.
- `src/hosts/pywebview/queue.py`의 `Row`·`mark_ready`에 `resolution_label`·
  `codec_label`·`audio_label`·`subtitle_label`·`size_label` 추가.
- `src/hosts/pywebview/api.py`의 `add_urls`가 `parse_and_normalize_url`의 `url_type`로
  playlist를 분기해 `PlaylistExpander.submit()`으로 넘긴다(watch+list 조합은 여전히
  `url_type == "video"`이므로 영상 행 1개만 생성됨 — youtube-kit 자체 해석을 그대로
  재사용, D-21).
- 프런트 `bridge.ts`의 `RowSnapshot`에 `resolution`·`codec`·`audio`·`subtitle`·`size`
  필드 추가, `queue-table.ts`가 이 값을 그대로 표시(아직 읽기 전용 텍스트 — 드롭다운
  상호작용은 Phase 4).
- `tests/fixtures/JyEsEcsCqzM.meta.json` — 실제 조회 결과 샘플(`youtube-kit` 로컬
  `outputs/`에서 복사).

**결과**
- `npm run typecheck`, `npm run build` 통과.
- `tests/test_formats.py`(10개) — 최고 해상도·fps 선택, 동률 tie-break, avc1 없으면
  `None`(NFR-6), audio drc/ext/원본 트랙 규칙, 자막 필터(D-20), 크기 계산의 `None`
  전파(D-19), 실제 픽스처로 크기 미상일 때 `-`가 나오는지.
- `tests/test_workers.py`(4개) — `watch?v=…&list=…`가 영상 행 1개만 만드는지(D-21),
  재생목록이 항목별 행으로 전개되고(id 없는 항목은 행을 만들지 않음) 각 행이 자동으로
  `ready`가 되는지, `<list-id>.playlist.json`이 `<저장 폴더>\<list-id>\`에 저장되는지,
  9개 요청 시 동시 조회가 3개를 넘지 않는지(NFR-7).
- 전체 `tests/` 21개 통과(Phase 2의 7개 포함).
- `python -m src.hosts.pywebview.main`으로 창이 뜨고 예외 없이 종료됨.
- 실제 재생목록 대상 전체 스모크(수백 개 항목 재생목록에 대한 라이브 호출)는 이번
  세션에서 시간·요청 수 부담으로 생략했다 — 위 pytest는 `youtube_kit.info`를
  monkeypatch해 같은 코드 경로(`api.py`→`workers.py`)를 오프라인으로 검증한다.
  Phase 2에서 개별 영상 경로는 이미 실제 네트워크로 검증됨.

**검증**
- PLAN.md Phase 3 완료 조건 9개 대조: meta.json/playlist.json 저장 위치(D-15),
  watch+list 처리(D-21), 동시 3개 제한(NFR-7), 크기 `-`/합계 표시(D-19), 개별 영상
  행의 자동 갱신, 재생목록 전체 전개, 재생목록 행의 자동 갱신, 조회 결과에 없는 값을
  임의로 만들지 않음(NFR-6), 여러 재생목록 항목 조회 중 UI 비차단(백그라운드 풀 구조는
  Phase 2와 동일하게 유지) — 자동화된 테스트로 확인.
- Phase 3는 적대적 검증 필수 통과 대상이 아니며, 반대 벤더 검토도 Phase 4·5·6에만
  집중하기로 사용자와 합의했다(2026-09-28).

## 2. 계획 외 개선

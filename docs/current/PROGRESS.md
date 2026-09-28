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

### Phase 4 · 행별 포맷 선택과 큐 순서 조작 완성 (2026-09-28)

**무엇을**
- `src/hosts/pywebview/formats.py` — `video_options()`(FR-7, D-18)를 (height, fps)로
  묶고, 그 묶음 안에서 **실제로 충돌하는 코덱만** ext 접미사를 붙여 개별 행으로 분리한다
  (충돌 없는 코덱은 한 "HeightpFPS" 행에 묶여 Codec 드롭다운으로 고른다).
  `audio_options()`(FR-10, 언어가 여럿일 때만 언어 접미사)·`resolution_key_for_format_id`·
  `formats_for_resolution_key`·`format_by_id`·`relabel()`(선택이 바뀔 때마다 라벨·크기
  재계산)·직렬화 헬퍼(`serialize_video_options` 등, 프런트에는 필요한 필드만 보낸다).
- `src/hosts/pywebview/queue.py` — `Row`에 `video_options`·`audio_options`·
  `subtitle_options`·선택 ID 4개 추가. `QueueManager.select(row_id, field, value)`가
  실제 옵션에 없는 값은 조용히 무시하고(NFR-6), 영상이 선택된 행에서 음성 `None`을
  막으며(D-17), 해상도를 바꾸면 그 해상도의 첫 포맷으로 코덱을 정하고 음성이 `None`이면
  기본 규칙으로 되돌린다(D-17 불변식 유지). `QueueManager.move(row_id, delta)`가
  리스트 순서를 그대로 바꿔 표시 순서 = 작업 순서를 유지한다(FR-13·14).
  `READY` 상태가 아닌 행의 선택은 무시한다.
- `src/hosts/pywebview/api.py`에 `select`·`move` 메서드 추가.
- 프런트 `bridge.ts`에 `VideoOption`·`AudioOption`·`SubtitleOption` 타입과
  `moveRow`·`selectField` 추가. `queue-table.ts`가 Resolution·Codec·Audio·Subtitle
  칸을 실제 `<select>`로 그린다 — `Ready` 상태에서만 활성화되고, Codec은 현재 선택된
  해상도의 코덱만, Audio는 영상이 선택돼 있으면 `None` 옵션을 아예 빼고(D-17), 클릭이
  행 선택(`tr` 클릭)으로 버블링되지 않게 막는다. `toolbar.ts`의 Move Up/Down이 선택
  행이 있을 때 활성화되고 `move()`를 호출한다.

**계획 외 개선**
- `video_options()`의 최초 구현은 (height,fps) 그룹 안에서 **한 코덱이라도** ext
  충돌이 있으면 그룹 전체(다른 코덱까지)를 개별 행으로 쪼갰다. 실제 조회 결과
  (`tests/fixtures/JyEsEcsCqzM.meta.json`, 1920×1080 세로 영상)로 스모크하다가 발견함
  — `avc1` 포맷 2개만 충돌했는데 같은 (height,fps)의 `vp09`·`vp9`·`av01`까지 전부
  `"1920p60 · mp4"` 같은 개별 행으로 흩어져 Codec 드롭다운으로 고를 수 없게 됐다.
  코덱별로 충돌 여부를 따로 판정하도록 고치고 회귀 테스트
  (`test_only_the_actually_colliding_codec_is_exploded_on_real_fixture`)를 추가했다.
  `PROGRESS.md`에 기록한다(계획 밖 발견·수정이므로).

**결과**
- `npm run typecheck`, `npm run build` 통과.
- `tests/test_selection.py`(10개, 신규) — D-16 기본 선택이 그대로 유지되는지, 같은
  해상도·fps·코덱의 ext 충돌이 별도 옵션으로 보이는지, 해상도 변경이 코덱·크기를
  갱신하는지, 코덱 선택이 현재 해상도로 제한되는지(NFR-6), 영상 선택 중 음성 `None`
  금지(D-17)와 영상을 다시 고르면 음성 기본값이 복원되는지, 자막 선택/해제와 목록 밖
  값 무시, 두 행의 선택이 서로 독립적인지(FR-12), 3개 이상 행에서 위/아래 이동이
  표시 순서를 그대로 바꾸는지(FR-13·14, 경계에서 no-op).
- `tests/test_formats.py`에 회귀 테스트 1개 추가(위 계획 외 개선 항목). 전체
  `tests/` 32개 통과.
- `python -m src.hosts.pywebview.main`으로 창이 뜨고 예외 없이 종료됨.
- 실제 네트워크로 `Api`를 통해 영상 1개를 조회하고 해상도를 바꿔 봄 — 이 과정에서
  위 계획 외 개선의 버그를 실제 발견·수정함. 산출물(`Downloads\JyEsEcsCqzM\`)은
  스모크 후 삭제.
- `src/**/*.ts`, `src/hosts/pywebview/*.py`에서 한글 문자 없음을 `grep -P`로 재확인.

**검증**
- PLAN.md Phase 4 완료 조건 10개 대조: 자동 선택+빈 칸(D-16/NFR-6), 해상도에 fps·ext
  구분 표시(D-18), 영상/음성/자막 `None` 허용과 D-17 제약, 자막 목록 필터(D-20),
  해상도 변경 가능, 코덱이 실제 제공 코덱만·최종 포맷 ID 하나로 귀결, 음성 실제 트랙
  선택, 자막 실제 트랙+`None`·수동/자동 구분, 행별 선택 독립성(FR-12), 3개 이상 행의
  위/아래 이동이 표시·작업 순서를 함께 바꿈(FR-13·14) — 자동화된 테스트와 실제
  네트워크 스모크로 확인.
- **Phase 4는 필수 통과 대상**(PLAN.md 적대적 검증 절). 아래 반대 벤더(Codex) 검증
  기록은 `docs/reviews/A4.md`를 본다.

### Phase 5 · 다운로드 실행과 진행 상태 연결 (2026-09-28)

**무엇을**
- `src/hosts/pywebview/queue.py` — `DOWNLOADING`·`MERGING`·`DONE`·`EXISTS`·`CANCELED`
  상태와 `downloaded_bytes`·`total_bytes`·`speed`·`eta`를 `Row`에 추가(NFR-6: backend가
  값을 안 줄 때 항상 `None`, 추정하지 않는다). `QueueManager.claim_next_ready_row()`가
  맨 위 Ready 행을 락 안에서 원자적으로 `Downloading`으로 바꿔 반환한다 — 이렇게 해야
  `select()`가 "Ready 상태가 아니면 무시"하는 규칙과 경쟁하지 않는다(`docs/reviews/A4.md`
  발견 #4의 순서 문제를 여기도 같은 방식으로 적용, D-13). `clear_completed()`(FR-29,
  Done·Exists만 지움)·`mark_downloading`·`mark_merging`·`mark_done`(재사용 여부로
  Done/Exists 분기)·`mark_canceled`·`remove()`가 삭제된 Row 목록을 반환하도록 변경(FR-27:
  다운로드 중인 행이 삭제되면 취소 이벤트를 걸어야 하므로).
- `src/hosts/pywebview/workers.py`의 `DownloadRunner` — 순차 실행기(D-13, FR-23).
  한 번에 한 행만, 매 스텝마다 큐를 다시 스캔해 맨 위부터 진행하므로 실행 중 `move()`도
  아직 시작 안 한 행에는 그대로 반영된다. `video_id`+`audio_id`가 둘 다 있으면
  `yk.video()`, 영상만 `None`(D-17)이면 `yk.audio()`만(FR-15), 자막이 선택돼 있으면
  `yk.subtitle()`을 추가로 호출 — 영상·음성 둘 다 `None`이면 자막 호출만 남는다.
  `progress` 콜백이 `stage: "download"|"merge"`를 큐에 반영해 다운로드/병합 단계를
  구분한다(FR-31). `cancel` `threading.Event`를 `stop()`(FR-28, 현재 행만 취소하고 다음
  행은 시작 안 함)과 `cancel_row()`(FR-27, 삭제된 행이 지금 받는 중이면 취소)가 공유한다.
  포맷을 이용할 수 없는 예외(`yk.YoutubeKitError` 등)는 그대로 실패로 남기고 다른
  포맷으로 조용히 대체하지 않는다(NFR-6).
- `src/hosts/pywebview/settings.py`(신규) — `container`(auto/mp4/mkv, D-23)·
  `subtitle_format`·`preferred_language`·`window_width/height`·`theme`를
  `~/.youtube-downloader/settings.json`에 원자적 저장(tmp 파일 후 `os.replace`)한다.
  기존 행에는 소급 적용하지 않고 새 행·다음 실행부터만 적용된다(FR-32).
- `src/hosts/pywebview/api.py` — `start`·`stop`·`is_downloading`·`clear_completed`·
  `get_settings`·`save_settings`·`choose_folder`(폴더 선택도 이제 설정에 저장)·
  `should_force_close`·`confirm_close` 추가. `choose_folder`가 이제 저장 폴더를 설정에
  영속화한다. `_on_resized`가 창 크기를 설정에 저장한다.
- `src/hosts/pywebview/main.py` — 창 `closing` 이벤트가 다운로드 중이면 OS 종료를 막고
  프런트의 확인 대화상자를 띄운다(FR-33). 사용자가 "Close"를 고르면 `confirm_close`가
  실행 중인 다운로드를 정지시키고 창을 닫는다(부분 파일이 안 남도록 `stop()`을 거친다).
- 프런트: `src/ui/settings-dialog.ts`(신규, Container/Subtitle Format/Subtitle Language)·
  `src/ui/confirm-close.ts`(신규, "Keep Downloading"이 기본 선택지)·`queue-table.ts`가
  Downloading 행에 퍼센트 진행 바와 속도·ETA를 표시하고 Merging은 별도 스피너로
  구분해 보여준다(FR-31). `toolbar.ts`에 Clear Completed 버튼과 Settings 버튼 추가.
  `main.ts`가 Start/Stop 버튼의 활성 조건(Ready 행 존재 여부·다운로드 진행 여부)과
  Clear Completed 활성 조건(완료 행 존재 여부)을 큐 상태에서 계산해 반영한다.

**결과**
- `npm run typecheck`, `npm run build` 통과.
- `tests/test_downloads.py`(11개, 신규) — 영상+음성 다운로드 후 Done, 이미 있는 파일
  재사용 시 Exists(FR-25), 영상 `None`이면 음성만(FR-15), 자막 선택 시 트랙·형식이
  그대로 전달되고 `None`이면 자막 호출 자체가 없음(FR-19), 진행 이벤트가 행에
  반영되고 병합 단계가 다운로드 단계와 구분됨(FR-31), Stop이 진행 중 다운로드를
  취소하고 부분 파일 없이 Canceled로 남음(FR-28), 다운로드 중 행 삭제가 취소하고
  행이 사라진 채로 유지됨(부활 없음, FR-27), 실패한 행이 있어도 다른 행이 이어서
  진행되고 실패 행을 식별 가능(FR-34), 4개 행이 순서대로 한 번에 하나씩만 받아짐
  (동시 실행 없음 확인, D-13), 설정한 컨테이너 값이 `yk.video()`에 그대로 전달됨(D-23).
  전체 `tests/` 49개 통과(Phase 1~4의 38개 포함).
- **세션 내 리뷰어(같은 벤더) 검토 후 보완**: 처음 제출한 테스트에 세 가지 근거
  공백이 있었다 — "영상·음성 둘 다 `None`→자막만" 조합을 `DownloadRunner` 실행
  레벨에서 확인하는 테스트가 없었고(선택 로직만 `test_selection.py`가 검증했음),
  `clear_completed()`를 실제로 호출하는 테스트가 전혀 없었고, `settings.py`의
  저장→재로드 왕복(FR-32의 핵심)을 검증하는 테스트가 없었다. 세 가지를 추가했다:
  `test_video_and_audio_none_downloads_subtitle_only`(자막 호출만 발생, 영상·음성
  호출 없음을 직접 확인)·`test_clear_completed_removes_only_done_and_exists_rows`
  (Done 행은 지워지고 Ready 행은 남음)·`tests/test_settings.py`(신규 4개: 저장한
  값이 재로드 시 그대로 돌아옴, 파일 없을 때 기본값, 손상된 JSON일 때 기본값으로
  복구, `Api.save_settings()` 후 새 `Api()` 인스턴스가 바뀐 값을 읽음 — 앱 재시작을
  흉내낸 end-to-end). 전체 `tests/` 55개로 늘어 전부 통과.
- `python -m src.hosts.pywebview.main`으로 창이 뜨고 예외 없이 종료됨.
- 실제 네트워크로 `Api`를 통해 짧은 Shorts 영상(`JyEsEcsCqzM`, YouTube Shorts) 1개를
  최저 해상도로 선택해 처음부터 끝까지 받아 봄: `add_urls` → `Ready` → 해상도/코덱
  선택 → `start()` → `Done`까지 실제로 진행되었고, `<저장 폴더>\JyEsEcsCqzM\`에
  `JyEsEcsCqzM.602_140.mkv`(1.24MB, 영상+음성 병합 결과)와 `.meta.json`이 실제로
  생성됨을 확인(스모크 후 삭제). 재사용(`이미 있음`) 경로는 실제 네트워크로는
  재확인하지 못했고 위 `test_reused_file_marks_exists_and_new_download_marks_done`으로만
  확인했다 — 다음 상호작용 세션에서 실제 재다운로드로 재확인 필요.
- `src/*.ts`, `src/ui/*.ts`, `src/**/*.css`에서 한글 문자 없음을 확인(`src/hosts/pywebview/
  *.py`의 한글은 주석·docstring뿐이며 화면 표시 문자열이 아니다).
- 설정 대화상자·닫기 확인 대화상자의 실제 클릭 상호작용(GUI)은 이번 세션에서 코드
  경로만 확인했고 실제 마우스 클릭으로는 열어보지 못했다 — Phase 2의 `choose_folder`
  대화상자와 같은 제약. 다음 상호작용 세션에서 재확인 필요.

**검증**
- PLAN.md Phase 5 완료 조건 15개(첫 단락 7개 + 세부 8개) 대조: 순서대로 한 행씩 다운로드
  (D-13, 자동화 테스트+실제 스모크), `<저장 폴더>\<영상 ID>\` 저장(실제 스모크로 확인),
  영상 `None`→음성만(자동화 테스트)·영상+음성 `None`→자막만(FR-15, 보완 후 자동화
  테스트로 실행 레벨까지 확인), 받는 중 삭제·전체 정지 후 부분 파일 없음(자동화 테스트,
  `yk.video`가 `Cancelled`를 던지면 그 함수 내부에서 부분 파일을 정리한다고 가정 —
  youtube-kit `src/core.py`의 실제 취소 처리 코드를 세션 내 리뷰어가 직접 읽고 확인),
  완료 행 일괄 삭제(`clear_completed`, 보완 후 자동화 테스트로 확인), 이미 있으면
  `Exists`로 끝나고 하단 요약에서 완료로 셈(D-28, `state.ts`), 컨테이너·자막 형식
  설정대로 저장(자동화 테스트), 설정 유지(FR-32, 보완 후 `tests/test_settings.py`로
  저장→재로드 왕복과 `Api` 재생성 시나리오까지 자동화 테스트로 확인)·큐 빔·닫기 확인
  (`confirm_close` 코드 경로 확인, 실제 마우스 클릭 GUI 상호작용은 미확인) — 자동화된
  테스트·실제 네트워크 스모크·코드 검토로 확인. 포맷 ID 기준 다운로드, 자막 트랙 전달,
  진행 상태 갱신, 속도/ETA 반영, 병합 단계 구분, 성공/실패 상태, 포맷 대체 금지(NFR-6)
  — 모두 자동화 테스트로 확인.
- **세션 내 리뷰어 검토**: 첫 제출에서 위 세 가지(자막 전용 실행, `clear_completed`,
  설정 영속화)의 근거 공백을 지적받아 테스트를 보완했다(위 "결과" 절). 닫기 확인
  대화상자의 실제 GUI 클릭 상호작용은 여전히 코드 검토로만 확인했다 — Phase 2의
  `choose_folder` 대화상자와 같은 제약으로 남겨 둔다(다음 상호작용 세션에서 재확인).
- **Phase 5는 필수 통과 대상**(PLAN.md 적대적 검증 절). 반대 벤더(Codex) 검증에서
  Critical 2개(닫기 시 정리 완료 전 창 파괴, claim·취소 사이의 레이스)와 Major 1개
  (진행 이벤트마다 다른 행의 DOM이 통째로 다시 그려짐)를 찾았다. Major와 Critical
  1개(레이스)는 재검증까지 받아 해소를 확인했지만, 실행 3회 한도를 소진해 마지막
  보완(닫기 대기를 무제한으로 바꾼 것과, 클레임 직후 가드를 추가한 것)은 반대
  벤더 재검증을 받지 못했다. **이 시점에 반대 벤더가 최종 확인하지 않은 보완이
  남아 있어 Phase 5를 필수 통과로 닫지 않는다.** 전체 기록은 `docs/reviews/A5.md`,
  사용자 판단 요청 사항도 그 문서 끝에 있다.

## 2. 계획 외 개선

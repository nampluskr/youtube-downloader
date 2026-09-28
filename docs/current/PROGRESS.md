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

## 2. 계획 외 개선

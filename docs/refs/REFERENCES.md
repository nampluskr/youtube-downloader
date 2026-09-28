# 참조 — 기존 프로젝트

착수 모드 C(참조 후 신규)로 시작했다. 아래 프로젝트는 **읽기만 하고 수정·삭제하지 않는다.**

| 프로젝트 | 경로 | 착수 시점 | 무엇을 참조하나 | 근거 |
| --- | --- | --- | --- | --- |
| youtube-kit | `D:\projects\youtube-kit` | `v0.1` 태그 (`7cf1274`) | 영상·재생목록 정보 조회, 영상·음성·자막 다운로드, 진행 이벤트와 취소. **런타임 의존성**으로 쓴다(개발 중 editable 설치, 실행 파일에는 함께 묶음) | D-2, D-27 |
| workbench-kit | `D:\projects\workbench-kit` | `c2e3809` (태그 `v0.3` 이후) | pywebview 갈래의 빌드·실행·패키징 방식, 글꼴 스택·스타일 토큰·Light/Dark 색(`src/style.css`), 테마 전환(`src/core/theme.ts`), `@vscode/codicons`. **의존성으로 두지 않고** 값과 방식만 옮겨 쓴다 | D-3, D-27, D-30 |

## 언제 보나

- youtube-kit — 백엔드를 연결하는 Phase 3·5. 반환 형태와 예외는 youtube-kit `README.md`의 API·종료 코드 표를 기준으로 한다.
- workbench-kit — Phase 1(골격·시각 체계)과 Phase 6(패키징).

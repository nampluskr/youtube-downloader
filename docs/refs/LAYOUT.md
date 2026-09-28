> 참고 문서 · 작성일: 2026-09-28 · 상태: 예상안 (착수 전)

# LAYOUT — 예상 UI 레이아웃

v0.1 화면의 예상 배치를 텍스트로 그린 것이다. 크기·간격·색은 정하지 않는다. 영역 구성은
D-12, 표 구성은 D-6·D-9, 아이콘은 D-5(Codicon)를 따른다.

## 0. UI 표기 원칙

D-29·NFR-8(영어·Codicon), D-30·NFR-9(글꼴·스타일·테마·아이콘은 `workbench-kit` pywebview
갈래와 같은 값)를 따른다.

- **UI의 모든 글자는 영어다.** 레이블·툴팁·상태·알림·대화상자에 한국어를 쓰지 않는다.
  영상 제목처럼 YouTube에서 받은 값은 원문 그대로 보인다.
- **아이콘은 Codicon만 쓴다.** 이모지나 다른 아이콘 세트, 유니코드 기호를 아이콘 대신
  쓰지 않는다.
- **간결하게.** 툴바는 아이콘만 두고 뜻은 툴팁으로 보인다. 레이블은 한두 단어, 상태는
  한 단어를 원칙으로 한다. 장식용 테두리·그림자·카드는 두지 않는다.
- 그림에서 `[play]`처럼 대괄호로 적은 것은 그 이름의 Codicon이다. `v`는 드롭다운,
  `>`는 선택된 행을 뜻한다.

## 1. 메인 창

항상 보이는 영역은 **툴바 · URL 입력 · 큐 테이블 · 상태 표시줄** 넷뿐이다(D-12).

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ YouTube Downloader                                            [chrome-minimize] [chrome-maximize] [chrome-close] │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [play] [debug-stop]  [arrow-up] [arrow-down] [trash] [clear-all]  [folder] D:\Videos         [color-mode] [gear] │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [link]  Paste YouTube video or playlist URLs                                                                     │
├─────┬────────────────────────────┬────────────┬───────┬─────────────┬──────────┬────────┬────────────────────────┤
│ #   │ Title                      │ Resolution │ Codec │ Audio       │ Subtitle │ Size   │ Status                 │
├─────┼────────────────────────────┼────────────┼───────┼─────────────┼──────────┼────────┼────────────────────────┤
│ 1   │ Building an App Alone      │ 1080p30 v  │ avc1 v│ m4a 129k v  │ None v   │ 125 MB │ [check] Done           │
│ 2   │ Rust Basics 03             │ 1080p60 v  │ avc1 v│ m4a 129k v  │ en v     │ 310 MB │ [####----] 62%         │
│     │                            │            │       │             │          │        │ 4.1 MB/s  0:38         │
│ 3   │ Lecture Audio 07           │ None v     │ -     │ m4a 129k v  │ None v   │ 48 MB  │ [sync~spin] Merging    │
│ > 4 │ Tokyo Walk 4K              │ 1080p60 v  │ vp9 v │ opus 160k v │ None v   │ -      │ Ready                  │
│ 5   │ lF8_DX2NxjI                │ ...        │ ...   │ ...         │ ...      │ -      │ [sync~spin] Fetching   │
│ 6   │ b0gUs-8Qq1M                │            │       │             │          │        │ Queued                 │
│ 7   │ xQ9pLm2Kd0A                │            │       │             │          │        │ [error] Unavailable    │
│ 8   │ Cooking Basics 12          │ 720p30 v   │ avc1 v│ m4a 129k v  │ None v   │ 36 MB  │ [pass] Exists          │
├─────┴────────────────────────────┴────────────┴───────┴─────────────┴──────────┴────────┴────────────────────────┤
│ 8 items  1 queued  1 fetching  1 ready  1 downloading  3 done  1 failed                     2 duplicates skipped │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 툴바

| Codicon | 툴팁 | 동작 | 요구 |
| --- | --- | --- | --- |
| `play` | Start | 준비된 행을 큐 순서대로 하나씩 받기 | FR-23 |
| `debug-stop` | Stop | 전체 정지, 받던 행 취소 | FR-28 |
| `arrow-up` · `arrow-down` | Move Up · Move Down | 선택 행 이동 | FR-13·14 |
| `trash` | Remove | 선택 행 삭제 (받는 중이면 취소 후 삭제) | FR-27 |
| `clear-all` | Clear Completed | 완료 행 지우기 | FR-29 |
| `folder` + 경로 | Choose Folder | 저장 폴더 선택. 현재 경로를 옆에 표시 | FR-24 |
| `color-mode` | Toggle Theme | Light/Dark 전환 | FR-22 |
| `gear` | Settings | 설정 창 | FR-26·34 |

- 버튼은 세 묶음(실행 · 행 조작 · 폴더)으로 간격을 두어 나누고, 테마·설정은 오른쪽 끝에 둔다.
- `play`는 준비된 행이 없거나 받는 중이면, `debug-stop`은 받는 중이 아니면,
  `arrow-up`·`arrow-down`·`trash`는 선택 행이 없으면 비활성.

### URL 입력

- 한 줄 입력칸. 앞에 `link` 아이콘, placeholder는 `Paste YouTube video or playlist URLs`.
- 붙여넣는 즉시 처리하고 칸을 비운다. 추가 버튼은 없다(D-7).
- 여러 줄은 줄마다 URL 하나로 본다(D-24). `watch?v=…&list=…`는 영상 1개로 처리한다(D-21).

### 큐 테이블

| 열 | 표시 예 | 비어 있을 때 |
| --- | --- | --- |
| `#` | `1` — 큐 순서 = 다운로드 순서 | — |
| `Title` | 조회 전에는 영상 ID, 조회 후 원문 제목. 전체 제목과 ID는 툴팁 | 영상 ID |
| `Resolution` | `1080p60`. 같은 해상도·fps·코덱이 여러 개면 `1080p60 mp4` / `1080p60 webm` (D-18). `None` 선택 가능 | 규칙에 맞는 게 없으면 빈 칸 |
| `Codec` | `avc1` · `vp9` · `av01` — 선택한 해상도에 실제 있는 것만 | Resolution이 `None`이면 `-` |
| `Audio` | `m4a 129k` · `opus 160k`, 언어가 여러 개면 `m4a 129k en`. 영상이 선택돼 있으면 `None` 선택 불가 (D-17) | 규칙에 맞는 게 없으면 빈 칸 |
| `Subtitle` | `en` (수동) · `en (auto)` (원어 자동) · `ko (translated)` (자동 번역) · `None` (D-20) | `None` |
| `Size` | `125 MB`. 하나라도 모르면 `-`, 받기 시작하면 실제 값 (D-19) | `-` |
| `Status` | 아래 상태 표 | — |

- 행을 클릭하면 선택되고, 선택 행은 배경색으로 구분한다.
- 드롭다운은 `Ready` 상태에서만 바꿀 수 있고, 그 뒤로는 값만 보인다.
- 긴 제목은 말줄임(…)으로 자른다.

### 행 상태

| Status | Codicon | 뜻 |
| --- | --- | --- |
| `Queued` | — | 정보 조회 차례를 기다림 (동시 3개 제한, D-26) |
| `Fetching` | `sync~spin` | 정보 조회 중 |
| `Ready` | — | 조회 끝, 선택 가능. 시작하면 차례대로 받음 |
| `62%` + 막대 | — | 받는 중. 아래 줄에 `4.1 MB/s  0:38` (모르면 생략, FR-17) |
| `Merging` | `sync~spin` | 영상·음성 합치는 중 (FR-18) |
| `Done` | `check` | 새로 받음 |
| `Exists` | `pass` | 같은 파일이 있어 다시 받지 않음 (D-28) |
| `Unavailable` · `Failed` | `error` | 실패. 짧은 사유를 상태로, 전체 메시지는 툴팁 (FR-20) |
| `Canceled` | `circle-slash` | 정지·닫기로 멈춤 |

### 상태 표시줄

- 왼쪽: `8 items  1 queued  1 fetching  1 ready  1 downloading  3 done  1 failed`.
  0인 상태는 생략하고, `Exists`는 `done`에 포함한다(D-28).
- 오른쪽: 마지막 입력의 알림 — `2 duplicates skipped`, `1 invalid URL` (FR-30).

## 2. 빈 큐

처음 실행하면 큐가 비어 있다(D-25).

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [link]  Paste YouTube video or playlist URLs                                                                     │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│                                                                                                                  │
│                                           Paste a URL to add videos.                                             │
│                                                                                                                  │
│                                                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 0 items                                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 3. 설정 창

툴바 `gear`로 여는 작은 창. 바꾼 값은 다음 실행에도 유지된다(D-25).

```
┌─ Settings ───────────────────────────────────────────┐
│                                                      │
│ DEFAULT SELECTION  (applies to new rows)             │
│   Max resolution    [ 1080p            v ]           │
│   Video codec       [ avc1             v ]           │
│   Frame rate        [ Highest          v ]           │
│   Audio format      [ m4a              v ]           │
│   Audio language    [ Original         v ]           │
│   Include DRC       [ ]                              │
│   Subtitle          [ None             v ]           │
│                                                      │
│ SUBTITLES                                            │
│   Languages         [ ko               ]             │
│   Format            [ srt              v ]           │
│                                                      │
│ FILES                                                │
│   Container         [ Auto             v ]           │
│                                                      │
│                                     [Cancel]  [Save] │
└──────────────────────────────────────────────────────┘
```

- `Languages`는 쉼표로 여러 개를 적을 수 있다(예: `ko, en`). 자동 번역 자막 목록에 쓴다(D-20).
- `Container`의 `Auto`는 mp4에 들어가면 mp4, 아니면 mkv다(D-23).
- 기본 규칙은 이미 있는 행에는 적용하지 않고 새로 추가되는 행에만 적용한다(FR-26).
- 초기값은 D-16("호환 우선"), D-20, D-23을 따른다.

## 4. 다운로드 중 닫기 확인

```
┌─ YouTube Downloader ───────────────────────────┐
│                                                │
│ [warning]  Downloads in progress.              │
│            Closing will cancel them.           │
│                                                │
│                     [Keep Downloading] [Close] │
└────────────────────────────────────────────────┘
```

기본 버튼은 `Keep Downloading`이다(FR-33).

## 5. 테마

Light와 Dark 두 가지만 둔다(D-4). 네 영역이 함께 바뀐다(FR-22). 두 테마 모두에서
아래를 구분할 수 있어야 한다(NFR-2).

| 구분할 것 | 예상 표현 |
| --- | --- |
| 선택 행 | 행 배경색 |
| hover | 옅은 행 배경색 |
| 비활성 버튼 | 아이콘 흐리게 |
| 진행 막대 | 강조색 채움 |
| `Done` · `Exists` | 초록 계열 아이콘 |
| `Failed` · `Unavailable` | 빨강 계열 아이콘·글자 |

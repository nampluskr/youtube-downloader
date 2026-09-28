project-workflow v0.2 기준으로 초기화됨 (2026-09-28)

# 이 프로젝트에서 지킬 것

- `docs/current/INTENT.md`는 SSOT다. 사람의 요청으로만 고친다. 다른 문서는 여기 어긋나면 안 된다
- 현재 버전 문서는 `docs/current/`에 있다. INTENT와 버전 문서는 사람이 쓴다. **고치지 않는다**
- 문서가 `INTENT.md`에 어긋나면 혼자 맞추지 말고 멈추고 보고한다
- major·minor 버전 번호는 사람이 정한다. 스스로 올리지 않는다
- `backlog.json`은 CLI로만 바꾼다. 직접 편집하지 않는다
- 진행 중에 task를 추가하지 않는다. 계획 밖 작업은 `docs/current/PROGRESS.md`에 적는다
- task를 닫을 때마다 `PROGRESS.md`에 무엇을·결과·검증을 남긴다
- `docs/history/` 아래는 읽기만 한다. 수정도 삭제도 하지 않는다
- 완료 조건은 `PLAN.md`·`backlog.json`에 적힌 것으로 판정한다. 스스로 정하지 않는다
- 요구가 바뀌면 `SPEC.md`부터 고친다. 코드나 backlog로 우회하지 않는다
- 되돌릴 수 없는 작업(배포·삭제·외부 상태 변경)은 먼저 묻는다
- 파이썬은 `C:\winpython\WPy64-31180_cpu\python-3.11.8.amd64\python.exe`만 쓴다. PATH의 `python`은 Store 바로 가기다

<!--
아래에 이 프로젝트 고유의 제약을 추가한다.
버전 마감 때 DECISIONS.md에서 승격된 것이 여기 들어온다. 출처를 남긴다.

- torch 버전을 올리지 않는다 (v0.1 D-3)

5~15줄을 넘기지 않는다. 길어지면 안 읽힌다.
설명과 배경은 여기 쓰지 않는다. 근거는 그 버전 DECISIONS.md에 있다.
-->

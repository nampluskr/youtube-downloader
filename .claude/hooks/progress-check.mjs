#!/usr/bin/env node
// Stop hook
//
// 막는 사고
//   코드는 고쳤는데 PROGRESS.md 에 아무것도 안 남아, 진행이 커밋에만 있고
//   사람이 열어서 확인할 수 없게 되는 것.
//
// 판정: 이번 세션에서 docs/ 밖 파일이 바뀌었는데 PROGRESS.md 는 그대로면 막는다.
//
// 프로젝트 성격에 따라 시끄러울 수 있다. 그때는 매처를 좁히거나 이 hook 을 뺀다.
// 빼기로 했다면 왜 뺐는지 DECISIONS.md 에 남긴다.

import { execSync } from 'node:child_process';

const PROGRESS = 'docs/current/PROGRESS.md';

let changed;
try {
  changed = execSync('git status --porcelain', { encoding: 'utf8' })
    .split('\n')
    .map((l) => l.slice(3).trim())
    .filter(Boolean);
} catch {
  process.exit(0); // git 이 없으면 판정하지 않는다
}

if (changed.length === 0) process.exit(0);

const touchedProgress = changed.some((f) => f.endsWith('PROGRESS.md'));
const touchedWork = changed.some(
  (f) => !f.startsWith('docs/') && !f.startsWith('.claude/')
);

if (touchedWork && !touchedProgress) {
  process.stderr.write(
    `작업 파일이 바뀌었는데 ${PROGRESS} 에 기록이 없다.\n` +
    '무엇을 했고, 결과가 무엇이고, 어떻게 검증했는지 남긴 뒤 마친다.\n' +
    '계획 밖의 작업이면 "계획 외 개선" 구간에 적는다.\n'
  );
  process.exit(2);
}

process.exit(0);

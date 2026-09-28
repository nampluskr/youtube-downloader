import type { Notice, RowSnapshot } from '../bridge';
import { summary } from '../state';

export interface StatusBarHandle {
  element: HTMLElement;
  render: (rows: RowSnapshot[]) => void;
  showNotice: (notice: Notice) => void;
}

export function createStatusBar(): StatusBarHandle {
  const bar = document.createElement('div');
  bar.className = 'app-statusbar';

  const summaryEl = document.createElement('span');
  summaryEl.id = 'status-summary';
  summaryEl.textContent = '0 items';

  const noticeEl = document.createElement('span');
  noticeEl.id = 'status-notice';
  noticeEl.textContent = '';

  bar.appendChild(summaryEl);
  bar.appendChild(noticeEl);

  return {
    element: bar,
    render: (rows: RowSnapshot[]) => {
      summaryEl.textContent = summary(rows);
    },
    showNotice: (notice: Notice) => {
      const parts: string[] = [];
      if (notice.duplicates > 0) parts.push(`${notice.duplicates} duplicates skipped`);
      if (notice.invalid > 0) parts.push(`${notice.invalid} invalid URL${notice.invalid > 1 ? 's' : ''}`);
      noticeEl.textContent = parts.join('  ');
    },
  };
}

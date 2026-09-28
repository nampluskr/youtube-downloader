export function createStatusBar(): HTMLElement {
  const bar = document.createElement('div');
  bar.className = 'app-statusbar';

  const summary = document.createElement('span');
  summary.id = 'status-summary';
  summary.textContent = '0 items';

  const notice = document.createElement('span');
  notice.id = 'status-notice';
  notice.textContent = '';

  bar.appendChild(summary);
  bar.appendChild(notice);
  return bar;
}

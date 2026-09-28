const COLUMNS = ['#', 'Title', 'Resolution', 'Codec', 'Audio', 'Subtitle', 'Size', 'Status'];

export function createQueueTable(): HTMLElement {
  const main = document.createElement('div');
  main.className = 'app-main';

  const empty = document.createElement('div');
  empty.className = 'queue-empty';
  empty.id = 'queue-empty';
  empty.textContent = 'Paste a URL to add videos.';

  const wrap = document.createElement('div');
  wrap.className = 'queue-table-wrap';
  wrap.id = 'queue-table-wrap';
  wrap.style.display = 'none';

  const table = document.createElement('table');
  table.className = 'queue-table';
  table.id = 'queue-table';

  const thead = document.createElement('thead');
  const headRow = document.createElement('tr');
  for (const col of COLUMNS) {
    const th = document.createElement('th');
    th.textContent = col;
    headRow.appendChild(th);
  }
  thead.appendChild(headRow);

  const tbody = document.createElement('tbody');
  tbody.id = 'queue-table-body';

  table.appendChild(thead);
  table.appendChild(tbody);
  wrap.appendChild(table);

  main.appendChild(empty);
  main.appendChild(wrap);
  return main;
}

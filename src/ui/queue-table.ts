import type { RowSnapshot } from '../bridge';

const COLUMNS = ['#', 'Title', 'Resolution', 'Codec', 'Audio', 'Subtitle', 'Size', 'Status'];

export interface QueueTableHandle {
  element: HTMLElement;
  render: (rows: RowSnapshot[], selectedId: string | null) => void;
}

export interface QueueTableCallbacks {
  onSelect: (id: string) => void;
}

function statusCell(row: RowSnapshot): HTMLElement {
  const cell = document.createElement('td');
  const icon = document.createElement('i');
  const label = document.createElement('span');

  switch (row.status) {
    case 'queued':
      label.textContent = 'Queued';
      break;
    case 'fetching':
      icon.className = 'codicon codicon-sync codicon-modifier-spin status-icon status-progress';
      label.textContent = 'Fetching';
      break;
    case 'ready':
      label.textContent = 'Ready';
      break;
    case 'failed':
      icon.className = 'codicon codicon-error status-icon status-error';
      label.textContent = 'Failed';
      cell.title = row.error ?? '';
      break;
  }

  if (icon.className) cell.appendChild(icon);
  cell.appendChild(label);
  return cell;
}

export function createQueueTable(callbacks: QueueTableCallbacks): QueueTableHandle {
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

  function render(rows: RowSnapshot[], selectedId: string | null): void {
    empty.style.display = rows.length === 0 ? 'flex' : 'none';
    wrap.style.display = rows.length === 0 ? 'none' : 'block';

    tbody.innerHTML = '';
    rows.forEach((row, index) => {
      const tr = document.createElement('tr');
      tr.dataset.rowId = row.id;
      if (row.id === selectedId) tr.classList.add('selected');
      tr.addEventListener('click', () => callbacks.onSelect(row.id));

      const indexCell = document.createElement('td');
      indexCell.textContent = String(index + 1);

      const titleCell = document.createElement('td');
      titleCell.textContent = row.title;
      titleCell.title = `${row.title}\n${row.id}`;

      const resolutionCell = document.createElement('td');
      resolutionCell.textContent = row.resolution;

      const codecCell = document.createElement('td');
      codecCell.textContent = row.codec;

      const audioCell = document.createElement('td');
      audioCell.textContent = row.audio;

      const subtitleCell = document.createElement('td');
      subtitleCell.textContent = row.subtitle;

      const sizeCell = document.createElement('td');
      sizeCell.textContent = row.size;

      tr.appendChild(indexCell);
      tr.appendChild(titleCell);
      tr.appendChild(resolutionCell);
      tr.appendChild(codecCell);
      tr.appendChild(audioCell);
      tr.appendChild(subtitleCell);
      tr.appendChild(sizeCell);
      tr.appendChild(statusCell(row));

      tbody.appendChild(tr);
    });
  }

  return { element: main, render };
}

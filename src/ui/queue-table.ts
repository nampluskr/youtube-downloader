import type { RowSnapshot, SelectField } from '../bridge';

const COLUMNS = ['#', 'Title', 'Resolution', 'Codec', 'Audio', 'Subtitle', 'Size', 'Status'];
const NONE_VALUE = '__none__';

export interface QueueTableHandle {
  element: HTMLElement;
  render: (rows: RowSnapshot[], selectedId: string | null) => void;
}

export interface QueueTableCallbacks {
  onSelect: (id: string) => void;
  onSelectField: (rowId: string, field: SelectField, value: string | null) => void;
}

function formatSpeed(bytesPerSec: number | null): string {
  if (bytesPerSec === null) return '';
  return `${(bytesPerSec / (1024 * 1024)).toFixed(1)} MB/s`;
}

function formatEta(seconds: number | null): string {
  if (seconds === null) return '';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

function statusCell(row: RowSnapshot): HTMLElement {
  const cell = document.createElement('td');
  const icon = document.createElement('i');
  const label = document.createElement('span');
  const detail = document.createElement('div');
  detail.className = 'status-detail';

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
    case 'downloading': {
      const total = row.totalBytes;
      const done = row.downloadedBytes;
      if (total && done !== null) {
        const pct = Math.round((done / total) * 100);
        label.textContent = `${pct}%`;
        const bar = document.createElement('div');
        bar.className = 'status-progress-bar';
        const fill = document.createElement('div');
        fill.className = 'status-progress-fill';
        fill.style.width = `${pct}%`;
        bar.appendChild(fill);
        detail.appendChild(bar);
      } else {
        label.textContent = 'Downloading';
      }
      const speedEta = [formatSpeed(row.speed), formatEta(row.eta)].filter(Boolean).join('  ');
      if (speedEta) {
        const speedLine = document.createElement('div');
        speedLine.textContent = speedEta;
        detail.appendChild(speedLine);
      }
      break;
    }
    case 'merging':
      icon.className = 'codicon codicon-sync codicon-modifier-spin status-icon status-progress';
      label.textContent = 'Merging';
      break;
    case 'done':
      icon.className = 'codicon codicon-check status-icon status-success';
      label.textContent = 'Done';
      break;
    case 'exists':
      icon.className = 'codicon codicon-pass status-icon status-success';
      label.textContent = 'Exists';
      break;
    case 'canceled':
      icon.className = 'codicon codicon-circle-slash status-icon';
      label.textContent = 'Canceled';
      break;
    case 'failed':
      icon.className = 'codicon codicon-error status-icon status-error';
      label.textContent = 'Failed';
      cell.title = row.error ?? '';
      break;
  }

  if (icon.className) cell.appendChild(icon);
  cell.appendChild(label);
  if (detail.childNodes.length > 0) cell.appendChild(detail);
  return cell;
}

function selectCell(
  options: Array<{ value: string; label: string }>,
  selected: string | null,
  enabled: boolean,
  onChange: (value: string | null) => void,
): HTMLElement {
  const cell = document.createElement('td');
  const select = document.createElement('select');
  select.className = 'row-select';
  select.disabled = !enabled;

  for (const opt of options) {
    const optionEl = document.createElement('option');
    optionEl.value = opt.value;
    optionEl.textContent = opt.label;
    select.appendChild(optionEl);
  }
  select.value = selected ?? NONE_VALUE;

  select.addEventListener('click', (event) => event.stopPropagation());
  select.addEventListener('change', () => {
    onChange(select.value === NONE_VALUE ? null : select.value);
  });

  cell.appendChild(select);
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

  // Keyed by row id so an unrelated row's DOM (its open <select>, focus,
  // scroll position) survives a re-render triggered by another row's
  // progress event. Rebuilding the whole tbody on every progress tick used
  // to tear down every row's controls, including ones a user was mid-click
  // on in a different row (docs/reviews/A5.md finding #3).
  const rowNodes = new Map<string, HTMLTableRowElement>();

  function rowSignature(row: RowSnapshot, index: number, selectedId: string | null): string {
    return JSON.stringify([row, index, row.id === selectedId]);
  }

  function buildRow(row: RowSnapshot, index: number, selectedId: string | null): HTMLTableRowElement {
    const tr = document.createElement('tr');
    tr.dataset.rowId = row.id;
    if (row.id === selectedId) tr.classList.add('selected');
    tr.addEventListener('click', () => callbacks.onSelect(row.id));

    const indexCell = document.createElement('td');
    indexCell.textContent = String(index + 1);

    const titleCell = document.createElement('td');
    titleCell.textContent = row.title;
    titleCell.title = `${row.title}\n${row.id}`;

    const editable = row.status === 'ready';

    const resolutionOptions = [
      { value: NONE_VALUE, label: 'None' },
      ...row.videoOptions.map((o) => ({ value: o.key, label: o.label })),
    ];
    const resolutionCell = selectCell(resolutionOptions, row.selectedResolutionKey, editable, (value) =>
      callbacks.onSelectField(row.id, 'resolution', value),
    );

    const currentVideoOption = row.videoOptions.find((o) => o.key === row.selectedResolutionKey);
    const codecOptions = (currentVideoOption?.codecs ?? []).map((c) => ({ value: c.id, label: c.label }));
    const codecCell = selectCell(
      codecOptions,
      row.selectedVideoFormatId,
      editable && codecOptions.length > 0,
      (value) => callbacks.onSelectField(row.id, 'codec', value),
    );
    if (codecOptions.length === 0) {
      codecCell.textContent = '-';
    }

    // D-17: "None" audio is only offered while no video format is selected.
    const audioOptions = [
      ...(row.selectedVideoFormatId ? [] : [{ value: NONE_VALUE, label: 'None' }]),
      ...row.audioOptions.map((o) => ({ value: o.id, label: o.label })),
    ];
    const audioCell = selectCell(audioOptions, row.selectedAudioFormatId, editable, (value) =>
      callbacks.onSelectField(row.id, 'audio', value),
    );

    const subtitleOptions = [
      { value: NONE_VALUE, label: 'None' },
      ...row.subtitleOptions.map((o) => ({ value: o.id, label: o.label })),
    ];
    const subtitleCell = selectCell(subtitleOptions, row.selectedSubtitleId, editable, (value) =>
      callbacks.onSelectField(row.id, 'subtitle', value),
    );

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

    return tr;
  }

  function render(rows: RowSnapshot[], selectedId: string | null): void {
    empty.style.display = rows.length === 0 ? 'flex' : 'none';
    wrap.style.display = rows.length === 0 ? 'none' : 'block';

    const seen = new Set<string>();
    let previous: HTMLTableRowElement | null = null;

    rows.forEach((row, index) => {
      seen.add(row.id);
      const signature = rowSignature(row, index, selectedId);
      let tr = rowNodes.get(row.id);
      if (!tr || tr.dataset.signature !== signature) {
        const rebuilt = buildRow(row, index, selectedId);
        rebuilt.dataset.signature = signature;
        if (tr) tr.replaceWith(rebuilt);
        tr = rebuilt;
        rowNodes.set(row.id, tr);
      }

      const wantedNext = previous === null ? tbody.firstChild : previous.nextSibling;
      if (wantedNext !== tr) {
        tbody.insertBefore(tr, wantedNext);
      }
      previous = tr;
    });

    for (const [id, tr] of rowNodes) {
      if (!seen.has(id)) {
        tr.remove();
        rowNodes.delete(id);
      }
    }
  }

  return { element: main, render };
}

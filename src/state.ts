import type { RowSnapshot } from './bridge';

export interface QueueState {
  rows: RowSnapshot[];
  selectedId: string | null;
}

export const state: QueueState = {
  rows: [],
  selectedId: null,
};

export function setRows(rows: RowSnapshot[]): void {
  state.rows = rows;
  if (state.selectedId && !rows.some((r) => r.id === state.selectedId)) {
    state.selectedId = null;
  }
}

export function select(id: string | null): void {
  state.selectedId = id;
}

export function summary(rows: RowSnapshot[]): string {
  if (rows.length === 0) return '0 items';
  const counts: Record<string, number> = {};
  for (const row of rows) {
    // D-28: "Exists" counts as done in this summary.
    const key = row.status === 'exists' ? 'done' : row.status;
    counts[key] = (counts[key] || 0) + 1;
  }
  const labels: Record<string, string> = {
    queued: 'queued',
    fetching: 'fetching',
    ready: 'ready',
    downloading: 'downloading',
    merging: 'merging',
    done: 'done',
    failed: 'failed',
    canceled: 'canceled',
  };
  const parts = [`${rows.length} items`];
  for (const key of ['queued', 'fetching', 'ready', 'downloading', 'merging', 'done', 'failed', 'canceled']) {
    if (counts[key]) parts.push(`${counts[key]} ${labels[key]}`);
  }
  return parts.join('  ');
}

export function hasReadyRow(rows: RowSnapshot[]): boolean {
  return rows.some((r) => r.status === 'ready');
}

export function hasCompletedRow(rows: RowSnapshot[]): boolean {
  return rows.some((r) => r.status === 'done' || r.status === 'exists');
}

export function isDownloadActive(rows: RowSnapshot[]): boolean {
  return rows.some((r) => r.status === 'downloading' || r.status === 'merging');
}

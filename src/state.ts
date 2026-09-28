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
    counts[row.status] = (counts[row.status] || 0) + 1;
  }
  const labels: Record<string, string> = {
    queued: 'queued',
    fetching: 'fetching',
    ready: 'ready',
    failed: 'failed',
  };
  const parts = [`${rows.length} items`];
  for (const key of ['queued', 'fetching', 'ready', 'failed']) {
    if (counts[key]) parts.push(`${counts[key]} ${labels[key]}`);
  }
  return parts.join('  ');
}

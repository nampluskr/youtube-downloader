export interface CodecOption {
  id: string;
  label: string;
}

export interface VideoOption {
  key: string;
  label: string;
  codecs: CodecOption[];
}

export interface AudioOption {
  id: string;
  label: string;
}

export interface SubtitleOption {
  id: string;
  label: string;
  kind: 'manual' | 'auto';
  key: string;
}

export interface RowSnapshot {
  id: string;
  url: string;
  title: string;
  status: 'queued' | 'fetching' | 'ready' | 'failed';
  error: string | null;
  resolution: string;
  codec: string;
  audio: string;
  subtitle: string;
  size: string;
  videoOptions: VideoOption[];
  audioOptions: AudioOption[];
  subtitleOptions: SubtitleOption[];
  selectedResolutionKey: string | null;
  selectedVideoFormatId: string | null;
  selectedAudioFormatId: string | null;
  selectedSubtitleId: string | null;
}

export type SelectField = 'resolution' | 'codec' | 'audio' | 'subtitle';

export interface Notice {
  duplicates: number;
  invalid: number;
}

declare global {
  interface Window {
    pywebview?: {
      api: {
        add_urls(text: string): Promise<void>;
        remove(rowIds: string[]): Promise<void>;
        get_save_folder(): Promise<string>;
        choose_folder(): Promise<string | null>;
        move(rowId: string, delta: number): Promise<void>;
        select(rowId: string, field: SelectField, value: string | null): Promise<void>;
      };
    };
    __ytdlOnRows?: (payload: RowsPayload) => void;
    __ytdlOnNotice?: (notice: Notice) => void;
  }
}

interface RowsPayload {
  revision: number;
  rows: RowSnapshot[];
}

function waitForApi(): Promise<void> {
  if (window.pywebview?.api) return Promise.resolve();
  return new Promise((resolve) => {
    window.addEventListener('pywebviewready', () => resolve(), { once: true });
  });
}

export async function addUrls(text: string): Promise<void> {
  await waitForApi();
  await window.pywebview!.api.add_urls(text);
}

export async function removeRows(rowIds: string[]): Promise<void> {
  await waitForApi();
  await window.pywebview!.api.remove(rowIds);
}

export async function getSaveFolder(): Promise<string> {
  await waitForApi();
  return window.pywebview!.api.get_save_folder();
}

export async function chooseFolder(): Promise<string | null> {
  await waitForApi();
  return window.pywebview!.api.choose_folder();
}

export async function moveRow(rowId: string, delta: number): Promise<void> {
  await waitForApi();
  await window.pywebview!.api.move(rowId, delta);
}

export async function selectField(rowId: string, field: SelectField, value: string | null): Promise<void> {
  await waitForApi();
  await window.pywebview!.api.select(rowId, field, value);
}

export function onRows(cb: (rows: RowSnapshot[]) => void): void {
  // A push computed before a later mutation can arrive after it (the
  // background fetch thread and the UI thread both trigger pushes, and
  // evaluate_js() timing isn't ordered) — drop anything that isn't newer
  // than what we've already applied (docs/reviews/A4.md finding #4).
  let lastRevision = -1;
  window.__ytdlOnRows = (payload: RowsPayload) => {
    if (payload.revision <= lastRevision) return;
    lastRevision = payload.revision;
    cb(payload.rows);
  };
}

export function onNotice(cb: (notice: Notice) => void): void {
  window.__ytdlOnNotice = (raw: Notice) => cb(raw);
}

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

export type RowStatus =
  | 'queued'
  | 'fetching'
  | 'ready'
  | 'failed'
  | 'downloading'
  | 'merging'
  | 'done'
  | 'exists'
  | 'canceled';

export interface RowSnapshot {
  id: string;
  url: string;
  title: string;
  status: RowStatus;
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
  downloadedBytes: number | null;
  totalBytes: number | null;
  speed: number | null;
  eta: number | null;
}

export type SelectField = 'resolution' | 'codec' | 'audio' | 'subtitle';

export interface Notice {
  duplicates: number;
  invalid: number;
}

export interface Settings {
  theme: 'light' | 'dark';
  save_folder: string;
  container: 'auto' | 'mp4' | 'mkv';
  subtitle_format: string;
  preferred_language: string;
  window_width: number;
  window_height: number;
}

declare global {
  interface Window {
    pywebview?: {
      api: {
        add_urls(text: string): Promise<void>;
        remove(rowIds: string[]): Promise<void>;
        clear_completed(): Promise<void>;
        choose_folder(): Promise<string | null>;
        move(rowId: string, delta: number): Promise<void>;
        select(rowId: string, field: SelectField, value: string | null): Promise<void>;
        start(): Promise<void>;
        stop(): Promise<void>;
        is_downloading(): Promise<boolean>;
        confirm_close(keepDownloading: boolean): Promise<void>;
        get_settings(): Promise<Settings>;
        save_settings(patch: Partial<Settings>): Promise<Settings>;
      };
    };
    __ytdlOnRows?: (payload: RowsPayload) => void;
    __ytdlOnNotice?: (notice: Notice) => void;
    __ytdlOnCloseRequest?: () => void;
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

export async function clearCompleted(): Promise<void> {
  await waitForApi();
  await window.pywebview!.api.clear_completed();
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

export async function startDownloads(): Promise<void> {
  await waitForApi();
  await window.pywebview!.api.start();
}

export async function stopDownloads(): Promise<void> {
  await waitForApi();
  await window.pywebview!.api.stop();
}

export async function confirmClose(keepDownloading: boolean): Promise<void> {
  await waitForApi();
  await window.pywebview!.api.confirm_close(keepDownloading);
}

export async function getSettings(): Promise<Settings> {
  await waitForApi();
  return window.pywebview!.api.get_settings();
}

export async function saveSettings(patch: Partial<Settings>): Promise<Settings> {
  await waitForApi();
  return window.pywebview!.api.save_settings(patch);
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

export function onCloseRequest(cb: () => void): void {
  window.__ytdlOnCloseRequest = cb;
}

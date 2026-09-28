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
}

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
      };
    };
    __ytdlOnRows?: (rows: RowSnapshot[]) => void;
    __ytdlOnNotice?: (notice: Notice) => void;
  }
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

export function onRows(cb: (rows: RowSnapshot[]) => void): void {
  window.__ytdlOnRows = cb;
}

export function onNotice(cb: (notice: Notice) => void): void {
  window.__ytdlOnNotice = (raw: Notice) => cb(raw);
}

import { ThemeManager } from './core/theme';
import { createToolbar } from './ui/toolbar';
import { createUrlInput } from './ui/url-input';
import { createQueueTable } from './ui/queue-table';
import { createStatusBar } from './ui/status-bar';
import { createSettingsDialog } from './ui/settings-dialog';
import { createConfirmClose } from './ui/confirm-close';
import {
  addUrls,
  chooseFolder,
  clearCompleted,
  confirmClose,
  getSettings,
  moveRow,
  onCloseRequest,
  onNotice,
  onRows,
  removeRows,
  saveSettings,
  selectField,
  startDownloads,
  stopDownloads,
} from './bridge';
import { hasCompletedRow, hasReadyRow, isDownloadActive, select, setRows, state } from './state';

const theme = new ThemeManager('dark');

const root = document.createElement('div');
root.className = 'app-root';

function renderAll(): void {
  queueTable.render(state.rows, state.selectedId);
  statusBar.render(state.rows);
  toolbar.setRemoveEnabled(state.selectedId !== null);
  toolbar.setMoveEnabled(state.selectedId !== null);
  toolbar.setStartEnabled(hasReadyRow(state.rows) && !isDownloadActive(state.rows));
  toolbar.setStopEnabled(isDownloadActive(state.rows));
  toolbar.setClearCompletedEnabled(hasCompletedRow(state.rows));
}

const toolbar = createToolbar(theme, {
  onToggleTheme: () => {
    const next = theme.toggleTheme();
    void saveSettings({ theme: next });
  },
  onRemoveSelected: () => {
    if (state.selectedId) {
      void removeRows([state.selectedId]);
    }
  },
  onChooseFolder: () => {
    void chooseFolder().then((path) => {
      if (path) toolbar.setFolderPath(path);
    });
  },
  onMoveUp: () => {
    if (state.selectedId) void moveRow(state.selectedId, -1);
  },
  onMoveDown: () => {
    if (state.selectedId) void moveRow(state.selectedId, 1);
  },
  onStart: () => void startDownloads(),
  onStop: () => void stopDownloads(),
  onClearCompleted: () => void clearCompleted(),
  onOpenSettings: () => {
    void getSettings().then((current) => settingsDialog.open(current));
  },
});

const urlInput = createUrlInput({
  onSubmit: (text: string) => {
    void addUrls(text);
  },
});

const queueTable = createQueueTable({
  onSelect: (id: string) => {
    select(state.selectedId === id ? null : id);
    renderAll();
  },
  onSelectField: (rowId, field, value) => {
    void selectField(rowId, field, value);
  },
});

const statusBar = createStatusBar();

const settingsDialog = createSettingsDialog((patch) => {
  void saveSettings(patch);
});

const confirmCloseDialog = createConfirmClose((keepDownloading) => {
  void confirmClose(keepDownloading);
});

root.appendChild(toolbar.element);
root.appendChild(urlInput);
root.appendChild(queueTable.element);
root.appendChild(statusBar.element);
root.appendChild(settingsDialog.element);
root.appendChild(confirmCloseDialog.element);

const app = document.getElementById('app');
if (app) {
  app.appendChild(root);
}

onRows((rows) => {
  setRows(rows);
  renderAll();
});

onNotice((notice) => statusBar.showNotice(notice));

onCloseRequest(() => confirmCloseDialog.open());

void getSettings().then((settings) => {
  theme.setTheme(settings.theme);
  toolbar.setFolderPath(settings.save_folder);
});

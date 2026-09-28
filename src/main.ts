import { ThemeManager } from './core/theme';
import { createToolbar } from './ui/toolbar';
import { createUrlInput } from './ui/url-input';
import { createQueueTable } from './ui/queue-table';
import { createStatusBar } from './ui/status-bar';
import { addUrls, chooseFolder, getSaveFolder, onNotice, onRows, removeRows } from './bridge';
import { select, setRows, state } from './state';

const theme = new ThemeManager('dark');

const root = document.createElement('div');
root.className = 'app-root';

function renderAll(): void {
  queueTable.render(state.rows, state.selectedId);
  statusBar.render(state.rows);
  toolbar.setRemoveEnabled(state.selectedId !== null);
}

const toolbar = createToolbar(theme, {
  onToggleTheme: () => theme.toggleTheme(),
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
});

const statusBar = createStatusBar();

root.appendChild(toolbar.element);
root.appendChild(urlInput);
root.appendChild(queueTable.element);
root.appendChild(statusBar.element);

const app = document.getElementById('app');
if (app) {
  app.appendChild(root);
}

onRows((rows) => {
  setRows(rows);
  renderAll();
});

onNotice((notice) => statusBar.showNotice(notice));

void getSaveFolder().then((path) => toolbar.setFolderPath(path));

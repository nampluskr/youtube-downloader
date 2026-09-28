import { ThemeManager } from '../core/theme';

export interface ToolbarCallbacks {
  onToggleTheme: () => void;
  onRemoveSelected: () => void;
  onChooseFolder: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
}

export interface ToolbarHandle {
  element: HTMLElement;
  setFolderPath: (path: string) => void;
  setRemoveEnabled: (enabled: boolean) => void;
  setMoveEnabled: (enabled: boolean) => void;
}

function iconButton(icon: string, tooltip: string, id: string): HTMLButtonElement {
  const btn = document.createElement('button');
  btn.id = id;
  btn.className = 'toolbar-btn';
  btn.title = tooltip;
  btn.disabled = true;
  const i = document.createElement('i');
  i.className = `codicon codicon-${icon}`;
  btn.appendChild(i);
  return btn;
}

export function createToolbar(_theme: ThemeManager, callbacks: ToolbarCallbacks): ToolbarHandle {
  const toolbar = document.createElement('div');
  toolbar.className = 'app-toolbar';

  const runGroup = document.createElement('div');
  runGroup.className = 'toolbar-group';
  runGroup.appendChild(iconButton('play', 'Start', 'toolbar-start'));
  runGroup.appendChild(iconButton('debug-stop', 'Stop', 'toolbar-stop'));

  const rowGroup = document.createElement('div');
  rowGroup.className = 'toolbar-group';
  const moveUpBtn = iconButton('arrow-up', 'Move Up', 'toolbar-move-up');
  moveUpBtn.addEventListener('click', () => callbacks.onMoveUp());
  const moveDownBtn = iconButton('arrow-down', 'Move Down', 'toolbar-move-down');
  moveDownBtn.addEventListener('click', () => callbacks.onMoveDown());
  rowGroup.appendChild(moveUpBtn);
  rowGroup.appendChild(moveDownBtn);

  const removeBtn = iconButton('trash', 'Remove', 'toolbar-remove');
  removeBtn.addEventListener('click', () => callbacks.onRemoveSelected());
  rowGroup.appendChild(removeBtn);
  rowGroup.appendChild(iconButton('clear-all', 'Clear Completed', 'toolbar-clear-completed'));

  const folderBtn = document.createElement('button');
  folderBtn.id = 'toolbar-choose-folder';
  folderBtn.className = 'toolbar-folder';
  folderBtn.title = 'Choose Folder';
  const folderIcon = document.createElement('i');
  folderIcon.className = 'codicon codicon-folder';
  const folderPath = document.createElement('span');
  folderPath.className = 'toolbar-folder-path';
  folderPath.id = 'toolbar-folder-path';
  folderBtn.appendChild(folderIcon);
  folderBtn.appendChild(folderPath);
  folderBtn.addEventListener('click', () => callbacks.onChooseFolder());

  const spacer = document.createElement('div');
  spacer.className = 'toolbar-spacer';

  const themeBtn = iconButton('color-mode', 'Toggle Theme', 'toolbar-toggle-theme');
  themeBtn.disabled = false;
  themeBtn.addEventListener('click', () => callbacks.onToggleTheme());

  const settingsBtn = iconButton('gear', 'Settings', 'toolbar-settings');

  toolbar.appendChild(runGroup);
  toolbar.appendChild(rowGroup);
  toolbar.appendChild(folderBtn);
  toolbar.appendChild(spacer);
  toolbar.appendChild(themeBtn);
  toolbar.appendChild(settingsBtn);

  return {
    element: toolbar,
    setFolderPath: (path: string) => {
      folderPath.textContent = path;
    },
    setRemoveEnabled: (enabled: boolean) => {
      removeBtn.disabled = !enabled;
    },
    setMoveEnabled: (enabled: boolean) => {
      moveUpBtn.disabled = !enabled;
      moveDownBtn.disabled = !enabled;
    },
  };
}

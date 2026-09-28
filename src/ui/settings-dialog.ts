import type { Settings } from '../bridge';

export interface SettingsDialogHandle {
  element: HTMLElement;
  open: (current: Settings) => void;
}

function fieldRow(labelText: string, input: HTMLElement): HTMLElement {
  const row = document.createElement('div');
  row.className = 'modal-field';
  const label = document.createElement('label');
  label.textContent = labelText;
  row.appendChild(label);
  row.appendChild(input);
  return row;
}

function selectInput(options: Array<{ value: string; label: string }>): HTMLSelectElement {
  const select = document.createElement('select');
  select.className = 'modal-input';
  for (const opt of options) {
    const el = document.createElement('option');
    el.value = opt.value;
    el.textContent = opt.label;
    select.appendChild(el);
  }
  return select;
}

export function createSettingsDialog(onSave: (patch: Partial<Settings>) => void): SettingsDialogHandle {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.style.display = 'none';

  const dialog = document.createElement('div');
  dialog.className = 'modal-dialog';

  const title = document.createElement('div');
  title.className = 'modal-title';
  title.textContent = 'Settings';

  const containerSelect = selectInput([
    { value: 'auto', label: 'Auto' },
    { value: 'mp4', label: 'mp4' },
    { value: 'mkv', label: 'mkv' },
  ]);

  const subtitleFormatSelect = selectInput([
    { value: 'srt', label: 'srt' },
    { value: 'vtt', label: 'vtt' },
    { value: 'json3', label: 'json3' },
  ]);

  const languageInput = document.createElement('input');
  languageInput.type = 'text';
  languageInput.className = 'modal-input';
  languageInput.placeholder = 'ko';

  const actions = document.createElement('div');
  actions.className = 'modal-actions';

  const cancelBtn = document.createElement('button');
  cancelBtn.className = 'modal-btn';
  cancelBtn.textContent = 'Cancel';
  cancelBtn.addEventListener('click', () => {
    overlay.style.display = 'none';
  });

  const saveBtn = document.createElement('button');
  saveBtn.className = 'modal-btn modal-btn-primary';
  saveBtn.textContent = 'Save';
  saveBtn.addEventListener('click', () => {
    onSave({
      container: containerSelect.value as Settings['container'],
      subtitle_format: subtitleFormatSelect.value,
      preferred_language: languageInput.value.trim() || 'ko',
    });
    overlay.style.display = 'none';
  });

  actions.appendChild(cancelBtn);
  actions.appendChild(saveBtn);

  dialog.appendChild(title);
  dialog.appendChild(fieldRow('Container', containerSelect));
  dialog.appendChild(fieldRow('Subtitle Format', subtitleFormatSelect));
  dialog.appendChild(fieldRow('Subtitle Language', languageInput));
  dialog.appendChild(actions);
  overlay.appendChild(dialog);

  overlay.addEventListener('click', (event) => {
    if (event.target === overlay) overlay.style.display = 'none';
  });

  function open(current: Settings): void {
    containerSelect.value = current.container;
    subtitleFormatSelect.value = current.subtitle_format;
    languageInput.value = current.preferred_language;
    overlay.style.display = 'flex';
  }

  return { element: overlay, open };
}

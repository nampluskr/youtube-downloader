export interface ConfirmCloseHandle {
  element: HTMLElement;
  open: () => void;
}

export function createConfirmClose(onDecision: (keepDownloading: boolean) => void): ConfirmCloseHandle {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.style.display = 'none';

  const dialog = document.createElement('div');
  dialog.className = 'modal-dialog confirm-close-dialog';

  const message = document.createElement('div');
  message.className = 'confirm-close-message';
  const icon = document.createElement('i');
  icon.className = 'codicon codicon-warning';
  const text = document.createElement('span');
  text.textContent = 'Downloads in progress. Closing will cancel them.';
  message.appendChild(icon);
  message.appendChild(text);

  const actions = document.createElement('div');
  actions.className = 'modal-actions';

  // Keep Downloading is the default (FR-33): listed first, styled primary.
  const keepBtn = document.createElement('button');
  keepBtn.className = 'modal-btn modal-btn-primary';
  keepBtn.textContent = 'Keep Downloading';
  keepBtn.addEventListener('click', () => {
    overlay.style.display = 'none';
    onDecision(true);
  });

  const closeBtn = document.createElement('button');
  closeBtn.className = 'modal-btn';
  closeBtn.textContent = 'Close';
  closeBtn.addEventListener('click', () => {
    overlay.style.display = 'none';
    onDecision(false);
  });

  actions.appendChild(keepBtn);
  actions.appendChild(closeBtn);

  dialog.appendChild(message);
  dialog.appendChild(actions);
  overlay.appendChild(dialog);

  function open(): void {
    overlay.style.display = 'flex';
    keepBtn.focus();
  }

  return { element: overlay, open };
}

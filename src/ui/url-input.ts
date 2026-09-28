export interface UrlInputCallbacks {
  onSubmit: (text: string) => void;
}

export function createUrlInput(callbacks: UrlInputCallbacks): HTMLElement {
  const bar = document.createElement('div');
  bar.className = 'app-urlbar';

  const icon = document.createElement('i');
  icon.className = 'codicon codicon-link';

  const input = document.createElement('input');
  input.id = 'url-input';
  input.className = 'urlbar-input';
  input.type = 'text';
  input.placeholder = 'Paste YouTube video or playlist URLs';

  // D-7: pasting adds to the queue immediately, no separate Analyze step.
  // Read clipboardData directly (not input.value after paste) so multi-line
  // pastes (D-24) are not collapsed by the single-line <input>.
  input.addEventListener('paste', (event) => {
    const text = event.clipboardData?.getData('text') ?? '';
    event.preventDefault();
    if (text.trim()) {
      callbacks.onSubmit(text);
    }
    input.value = '';
  });

  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && input.value.trim()) {
      callbacks.onSubmit(input.value);
      input.value = '';
    }
  });

  bar.appendChild(icon);
  bar.appendChild(input);
  return bar;
}

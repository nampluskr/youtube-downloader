export function createUrlInput(): HTMLElement {
  const bar = document.createElement('div');
  bar.className = 'app-urlbar';

  const icon = document.createElement('i');
  icon.className = 'codicon codicon-link';

  const input = document.createElement('input');
  input.id = 'url-input';
  input.className = 'urlbar-input';
  input.type = 'text';
  input.placeholder = 'Paste YouTube video or playlist URLs';

  bar.appendChild(icon);
  bar.appendChild(input);
  return bar;
}

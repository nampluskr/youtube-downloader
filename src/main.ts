import { ThemeManager } from './core/theme';
import { createToolbar } from './ui/toolbar';
import { createUrlInput } from './ui/url-input';
import { createQueueTable } from './ui/queue-table';
import { createStatusBar } from './ui/status-bar';

const theme = new ThemeManager('dark');

const root = document.createElement('div');
root.className = 'app-root';

const toolbar = createToolbar(theme, {
  onToggleTheme: () => theme.toggleTheme(),
});

root.appendChild(toolbar);
root.appendChild(createUrlInput());
root.appendChild(createQueueTable());
root.appendChild(createStatusBar());

const app = document.getElementById('app');
if (app) {
  app.appendChild(root);
}

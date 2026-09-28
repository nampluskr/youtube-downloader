export type ColorTheme = 'light' | 'dark';

const THEME_CYCLE: ColorTheme[] = ['light', 'dark'];

export class ThemeManager {
  private currentTheme: ColorTheme = 'dark';

  constructor(initialTheme: ColorTheme = 'dark') {
    this.setTheme(initialTheme);
  }

  getTheme(): ColorTheme {
    return this.currentTheme;
  }

  setTheme(theme: ColorTheme): void {
    this.currentTheme = theme;
    document.documentElement.dataset.theme = theme;
  }

  toggleTheme(): ColorTheme {
    const nextIndex = (THEME_CYCLE.indexOf(this.currentTheme) + 1) % THEME_CYCLE.length;
    this.setTheme(THEME_CYCLE[nextIndex]);
    return this.currentTheme;
  }
}

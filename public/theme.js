(() => {
  'use strict';
  const key = 'hw.theme.v1';
  const valid = new Set(['system', 'light', 'dark']);
  let preference = 'system';
  try {
    const stored = localStorage.getItem(key);
    if (valid.has(stored)) preference = stored;
  } catch {}
  const media = typeof matchMedia === 'function' ? matchMedia('(prefers-color-scheme: dark)') : null;
  function apply() {
    const dark = preference === 'dark' || (preference === 'system' && Boolean(media?.matches));
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    document.documentElement.style.colorScheme = dark ? 'dark' : 'light';
    const themeColor = document.querySelector('#theme-color');
    if (themeColor) themeColor.content = dark ? '#17191e' : '#f8f8f4';
  }
  apply();
  if (media) media.addEventListener('change', () => { if (preference === 'system') apply(); });
  window.HWTheme = {
    get preference() { return preference; },
    set(value) {
      if (!valid.has(value)) return;
      preference = value;
      try { localStorage.setItem(key, value); } catch {}
      apply();
    }
  };
})();

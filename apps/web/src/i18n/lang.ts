/** Shared with landing via localStorage key `lang` (PT/EN/ES). */

export type Lang = "pt" | "en" | "es";

export const LANGS: Lang[] = ["pt", "en", "es"];

export const LANG_STORAGE_KEY = "lang";

export function isLang(value: unknown): value is Lang {
  return value === "pt" || value === "en" || value === "es";
}

export function readStoredLang(fallback: Lang = "pt"): Lang {
  try {
    const s = localStorage.getItem(LANG_STORAGE_KEY);
    if (isLang(s)) return s;
  } catch {
    /* ignore */
  }
  return fallback;
}

export function writeStoredLang(lang: Lang): void {
  try {
    localStorage.setItem(LANG_STORAGE_KEY, lang);
  } catch {
    /* ignore */
  }
}

export function htmlLangAttr(lang: Lang): string {
  return lang === "en" ? "en" : lang === "es" ? "es" : "pt-BR";
}

export function applyDocumentLang(lang: Lang): void {
  document.documentElement.lang = htmlLangAttr(lang);
}

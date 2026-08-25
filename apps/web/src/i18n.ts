import { createContext, createElement, useContext, useEffect, useState, type ReactNode } from "react";

export type Lang = "pt" | "en";
export type Theme = "light" | "dark";

const LANG_KEY = "lang";
const THEME_KEY = "theme";

export function readLang(): Lang {
  try {
    const s = localStorage.getItem(LANG_KEY);
    if (s === "en" || s === "pt") return s;
  } catch {
    /* ignore */
  }
  return "pt";
}

export function writeLang(lang: Lang) {
  try {
    localStorage.setItem(LANG_KEY, lang);
  } catch {
    /* ignore */
  }
}

export function readTheme(): Theme {
  try {
    const s = localStorage.getItem(THEME_KEY);
    if (s === "light" || s === "dark") return s;
  } catch {
    /* ignore */
  }
  return "dark";
}

export function writeTheme(theme: Theme) {
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* ignore */
  }
}

const LangCtx = createContext<[Lang, (lang: Lang) => void] | null>(null);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(readLang);
  useEffect(() => {
    writeLang(lang);
    document.documentElement.lang = lang === "en" ? "en" : "pt-BR";
  }, [lang]);
  return createElement(LangCtx.Provider, { value: [lang, setLang] }, children);
}

export function useLang(): [Lang, (lang: Lang) => void] {
  const ctx = useContext(LangCtx);
  if (!ctx) throw new Error("useLang must be used inside LangProvider");
  return ctx;
}

export function useTheme(): [Theme, (theme: Theme) => void] {
  const [theme, setTheme] = useState<Theme>(readTheme);
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    writeTheme(theme);
  }, [theme]);
  return [theme, setTheme];
}

export const SHARED = {
  pt: {
    privacy: "Privacidade",
    terms: "Termos",
    login: "Entrar",
    register: "Criar conta",
    home: "Início",
    foot_copy: "© 2026 Story R Us — Onde memórias viram magia.",
    tagline: "Feito com amor. Criado para encantar.",
    lang_label: "Idioma / Language",
    theme_label: "Alternar tema claro/escuro",
    required: "Preencha este campo.",
    email_invalid: "Informe um e-mail válido.",
    too_short: "Use pelo menos {n} caracteres.",
  },
  en: {
    privacy: "Privacy",
    terms: "Terms",
    login: "Log in",
    register: "Create account",
    home: "Home",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
    tagline: "Made with love. Created to enchant.",
    lang_label: "Language",
    theme_label: "Toggle light/dark theme",
    required: "Please fill out this field.",
    email_invalid: "Enter a valid email address.",
    too_short: "Use at least {n} characters.",
  },
} as const;

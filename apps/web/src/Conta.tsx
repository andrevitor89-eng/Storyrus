import { useCallback, useEffect, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import logo from "./assets/logo.png";
import { accountGateHref } from "./Auth";
import { api, getToken } from "./api";
import { readStoredLang, type Lang } from "./i18n/lang";
import type { Project, UserVoice } from "./types";
import "./usage.css";

type Me = {
  id: string;
  email: string;
  credits: number;
  created_at: string;
  is_guest: boolean;
};

const COPY: Record<
  Lang,
  {
    title: string;
    lead: string;
    studio: string;
    logout: string;
    email: string;
    credits: string;
    memberSince: string;
    projects: string;
    noProjects: string;
    openStudio: string;
    untitled: string;
    voices: string;
    noVoices: string;
    voicesUnavailable: string;
    default: string;
    setDefault: string;
    remove: string;
    upload: string;
    voiceName: string;
    cloning: string;
    loading: string;
    loadError: string;
  }
> = {
  pt: {
    title: "Conta",
    lead: "Seus dados, livros e vozes clonadas.",
    studio: "Estúdio",
    logout: "Sair",
    email: "E-mail",
    credits: "Créditos",
    memberSince: "Membro desde",
    projects: "Projetos",
    noProjects: "Nenhum projeto ainda. Crie um livro no estúdio.",
    openStudio: "Abrir no estúdio",
    untitled: "Sem nome",
    voices: "Vozes",
    noVoices: "Nenhuma voz clonada ainda.",
    voicesUnavailable: "Clone de voz indisponível neste ambiente.",
    default: "Padrão",
    setDefault: "Definir como padrão",
    remove: "Remover",
    upload: "Enviar áudio",
    voiceName: "Nome da voz",
    cloning: "Clonando…",
    loading: "Carregando…",
    loadError: "Não foi possível carregar a conta.",
  },
  en: {
    title: "Account",
    lead: "Your details, books, and cloned voices.",
    studio: "Studio",
    logout: "Log out",
    email: "Email",
    credits: "Credits",
    memberSince: "Member since",
    projects: "Projects",
    noProjects: "No projects yet. Create a book in the studio.",
    openStudio: "Open in studio",
    untitled: "Untitled",
    voices: "Voices",
    noVoices: "No cloned voices yet.",
    voicesUnavailable: "Voice cloning unavailable in this environment.",
    default: "Default",
    setDefault: "Set as default",
    remove: "Remove",
    upload: "Upload audio",
    voiceName: "Voice name",
    cloning: "Cloning…",
    loading: "Loading…",
    loadError: "Could not load your account.",
  },
  es: {
    title: "Cuenta",
    lead: "Tus datos, libros y voces clonadas.",
    studio: "Estudio",
    logout: "Salir",
    email: "Correo",
    credits: "Créditos",
    memberSince: "Miembro desde",
    projects: "Proyectos",
    noProjects: "Aún no hay proyectos. Crea un libro en el estudio.",
    openStudio: "Abrir en el estudio",
    untitled: "Sin nombre",
    voices: "Voces",
    noVoices: "Aún no hay voces clonadas.",
    voicesUnavailable: "Clonación de voz no disponible en este entorno.",
    default: "Predeterminada",
    setDefault: "Definir como predeterminada",
    remove: "Eliminar",
    upload: "Enviar audio",
    voiceName: "Nombre de la voz",
    cloning: "Clonando…",
    loading: "Cargando…",
    loadError: "No se pudo cargar la cuenta.",
  },
};

function formatDate(iso: string, lang: Lang): string {
  const locale = lang === "en" ? "en-US" : lang === "es" ? "es-ES" : "pt-BR";
  return new Date(iso).toLocaleDateString(locale, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function Conta() {
  const location = useLocation();
  const navigate = useNavigate();
  const lang = readStoredLang();
  const t = COPY[lang];

  const [gate, setGate] = useState<"loading" | "ok" | "need-account">("loading");
  const [me, setMe] = useState<Me | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [voices, setVoices] = useState<UserVoice[]>([]);
  const [customVoiceAvailable, setCustomVoiceAvailable] = useState(false);
  const [voiceName, setVoiceName] = useState(lang === "en" ? "My voice" : lang === "es" ? "Mi voz" : "Minha voz");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [profile, projectList, voiceData] = await Promise.all([
        api.me(),
        api.listProjects(),
        api.listVoices(),
      ]);
      if (profile.is_guest) {
        setGate("need-account");
        return;
      }
      setMe(profile);
      setProjects(projectList);
      setVoices(voiceData.items);
      setCustomVoiceAvailable(voiceData.custom_voice_available);
      setGate("ok");
    } catch (err) {
      const status = (err as Error & { status?: number }).status;
      if (status === 401 || status === 403 || !getToken()) {
        setGate("need-account");
        return;
      }
      setError(err instanceof Error ? err.message : t.loadError);
      setGate("ok");
    }
  }, [t.loadError]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!getToken()) {
        if (!cancelled) setGate("need-account");
        return;
      }
      if (!cancelled) await load();
    })();
    return () => {
      cancelled = true;
    };
  }, [load]);

  function onLogout() {
    api.logout();
    navigate("/entrar", { replace: true });
  }

  async function onSetDefault(id: string) {
    setBusy(true);
    setError(null);
    try {
      await api.setDefaultVoice(id);
      const data = await api.listVoices();
      setVoices(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.loadError);
    } finally {
      setBusy(false);
    }
  }

  async function onRemoveVoice(id: string) {
    setBusy(true);
    setError(null);
    try {
      await api.deleteVoice(id);
      const data = await api.listVoices();
      setVoices(data.items);
      setCustomVoiceAvailable(data.custom_voice_available);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.loadError);
    } finally {
      setBusy(false);
    }
  }

  async function onVoiceFile(file: File | null) {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadVoice(file, voiceName.trim() || t.voiceName, voices.length === 0);
      const data = await api.listVoices();
      setVoices(data.items);
      setCustomVoiceAvailable(data.custom_voice_available);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.loadError);
    } finally {
      setUploading(false);
    }
  }

  if (gate === "loading") {
    return (
      <div className="usage" data-testid="conta-loading">
        <p className="muted">{t.loading}</p>
      </div>
    );
  }

  if (gate === "need-account") {
    const next = `${location.pathname}${location.search}`;
    return <Navigate to={accountGateHref(next)} replace />;
  }

  return (
    <div className="usage" data-testid="conta-page">
      <header className="usage-head">
        <img className="hdr-logo" src={logo} alt="Story R Us" />
        <div>
          <h1>{t.title}</h1>
          <p className="muted">{t.lead}</p>
        </div>
        <div className="conta-head-actions">
          <Link className="link" to="/app">
            {t.studio}
          </Link>
          <button className="link" type="button" onClick={onLogout} data-testid="conta-logout">
            {t.logout}
          </button>
        </div>
      </header>

      {error && <p className="error">{error}</p>}

      <section className="usage-panel" aria-labelledby="conta-dados">
        <h2 id="conta-dados">{t.title}</h2>
        <dl className="conta-dl">
          <div>
            <dt>{t.email}</dt>
            <dd data-testid="conta-email">{me?.email}</dd>
          </div>
          <div>
            <dt>{t.credits}</dt>
            <dd data-testid="conta-credits">{me?.credits ?? "—"}</dd>
          </div>
          <div>
            <dt>{t.memberSince}</dt>
            <dd data-testid="conta-since">
              {me?.created_at ? formatDate(me.created_at, lang) : "—"}
            </dd>
          </div>
        </dl>
      </section>

      <section className="usage-panel" aria-labelledby="conta-projetos">
        <h2 id="conta-projetos">{t.projects}</h2>
        {projects.length === 0 ? (
          <p className="muted">{t.noProjects}</p>
        ) : (
          <ul className="usage-order-list" aria-label={t.projects} data-testid="conta-projects">
            {projects.map((project) => (
              <li key={project.id}>
                <div className="conta-project-row">
                  <div>
                    <strong>{project.child_name?.trim() || t.untitled}</strong>
                    <span>
                      {project.status}
                      {" · "}
                      {formatDate(project.created_at, lang)}
                    </span>
                  </div>
                  <Link className="link" to="/app">
                    {t.openStudio}
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="usage-panel" aria-labelledby="conta-vozes">
        <h2 id="conta-vozes">{t.voices}</h2>
        {!customVoiceAvailable && voices.length === 0 ? (
          <p className="muted">{t.voicesUnavailable}</p>
        ) : (
          <>
            {customVoiceAvailable && (
              <div className="conta-voice-upload">
                <label>
                  {t.voiceName}
                  <input
                    type="text"
                    value={voiceName}
                    onChange={(e) => setVoiceName(e.target.value)}
                    disabled={busy || uploading}
                  />
                </label>
                <label className="conta-file">
                  {uploading ? t.cloning : t.upload}
                  <input
                    type="file"
                    accept="audio/*"
                    disabled={busy || uploading}
                    onChange={(e) => void onVoiceFile(e.target.files?.[0] ?? null)}
                  />
                </label>
              </div>
            )}
            {voices.length === 0 ? (
              <p className="muted">{t.noVoices}</p>
            ) : (
              <ul className="usage-order-list" aria-label={t.voices} data-testid="conta-voices">
                {voices.map((voice) => (
                  <li key={voice.id}>
                    <div className="conta-project-row">
                      <div>
                        <strong>
                          {voice.name}
                          {voice.is_default ? ` · ${t.default}` : ""}
                        </strong>
                        <span>{formatDate(voice.created_at, lang)}</span>
                      </div>
                      <div className="conta-voice-actions">
                        {!voice.is_default && (
                          <button
                            type="button"
                            className="link"
                            disabled={busy}
                            onClick={() => void onSetDefault(voice.id)}
                          >
                            {t.setDefault}
                          </button>
                        )}
                        <button
                          type="button"
                          className="link"
                          disabled={busy}
                          data-testid={`conta-voice-remove-${voice.id}`}
                          onClick={() => void onRemoveVoice(voice.id)}
                        >
                          {t.remove}
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </section>
    </div>
  );
}

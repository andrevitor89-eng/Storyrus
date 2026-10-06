import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { api } from "./api";
import type { Job, Project } from "./types";
import { demoIdFromSearch, getDemoExample } from "./demoExample";
import { themePreset } from "./studioPreset";
import {
  ageLimit,
  castFromQuery,
  emptyCast,
  subjectCode,
  subjectCopy,
  type StudioGender,
  type StudioWho,
} from "./studioSubject";
import logo from "./assets/logo.png";
import type { StudioAssets } from "./studio/assets";
import { resolveThemeName } from "./studio/constants";
import { ProgressList } from "./studio/ProgressList";
import { VoiceNarrationPanel } from "./studio/VoiceNarrationPanel";
import { EbookStepButtons, VideoStepButtons } from "./studio/StepButtons";
import { BookApprovalBlock, CharacterApprovalBlock } from "./studio/ApprovalBlocks";
import { useStudioPolling } from "./studio/useStudioPolling";
import { useStudioVoices } from "./studio/useStudioVoices";
import { useStudioSteps } from "./studio/useStudioSteps";
import { useStudioApprovals } from "./studio/useStudioApprovals";
import {
  StudioLangProvider,
  useStudioI18n,
  useStudioLangState,
} from "./studio/useStudioI18n";
import "./landing.css";
import "./studio.css";

export { ProgressList } from "./studio/ProgressList";

const PHOTO_LIMIT = 8;

function photoKey(file: File): string {
  return `${file.name}:${file.size}:${file.lastModified}`;
}

function previewUrl(file: File): string {
  if (typeof URL.createObjectURL !== "function") return "";
  return URL.createObjectURL(file);
}

function releasePreview(url: string) {
  if (url && typeof URL.revokeObjectURL === "function") URL.revokeObjectURL(url);
}

function imageFiles(list: Iterable<File>): File[] {
  return [...list].filter(
    (file) => file.type.startsWith("image/") || /\.(png|jpe?g|webp|gif|heic|heif)$/i.test(file.name),
  );
}

function oneLine(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function validEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

/* ---------------- ícones (SVG, sem emojis) ---------------- */
type IconProps = { className?: string };
const ICON_STROKE = 2.2;
const Svg = ({ className, children }: { className?: string; children: ReactNode }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={ICON_STROKE}
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    {children}
  </svg>
);
const IcSun = ({ className }: IconProps) => (
  <Svg className={className}>
    <circle cx="12" cy="12" r="4.2" />
    <path d="M12 2.5v2.4M12 19.1v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7" />
  </Svg>
);
const IcMoon = ({ className }: IconProps) => (
  <Svg className={className}>
    <path d="M20 15A8 8 0 1 1 10 4a6.5 6.5 0 0 0 10 11z" />
  </Svg>
);

export function Studio({ onLogout }: { onLogout?: () => void }) {
  const langState = useStudioLangState();
  return (
    <StudioLangProvider value={langState}>
      <StudioInner onLogout={onLogout} />
    </StudioLangProvider>
  );
}

function StudioInner({ onLogout }: { onLogout?: () => void }) {
  const { lang, setLang, t, langs } = useStudioI18n();
  const [accountKind, setAccountKind] = useState<"unknown" | "guest" | "account">("unknown");
  const [accountEmail, setAccountEmail] = useState("");
  const [accountName, setAccountName] = useState("");
  const [isOwner, setIsOwner] = useState(false);
  const [clientDone, setClientDone] = useState(false);
  const [project, setProject] = useState<Project | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [photos, setPhotos] = useState<{ key: string; file: File; url: string }[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [photoUploaded, setPhotoUploaded] = useState(false);
  const [childName, setChildName] = useState("");
  const [childAge, setChildAge] = useState<string>("");
  const [bookTitle, setBookTitle] = useState("");
  const [themeText, setThemeText] = useState("");
  const [temaId, setTemaId] = useState("");
  const [onlyName, setOnlyName] = useState(false);
  const [bookSize, setBookSize] = useState<"M" | "P">("M");
  const [coverType, setCoverType] = useState<"soft" | "hard">("hard");
  const [extraNames, setExtraNames] = useState("");
  const [castWho, setCastWho] = useState<StudioWho>("child");
  const [gender, setGender] = useState<StudioGender | null>(null);
  const [alsoWho, setAlsoWho] = useState<StudioWho | null>(null);
  const [alsoGender, setAlsoGender] = useState<StudioGender | null>(null);
  const [alsoName, setAlsoName] = useState("");
  const [askGender, setAskGender] = useState(true);
  const alsoHero = useRef<string | null>(null);
  const [orderSent, setOrderSent] = useState(false);
  const [generateStep, setGenerateStep] = useState(false);
  const [artMode, setArtMode] = useState<"realista" | "cartoon">("realista");
  const [dedication, setDedication] = useState("");
  const [clientName, setClientName] = useState("");
  const [clientEmail, setClientEmail] = useState("");
  const [clientPhone, setClientPhone] = useState("");
  const [clientAddress, setClientAddress] = useState("");
  const [clientNotes, setClientNotes] = useState("");
  const [assets, setAssets] = useState<StudioAssets | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(() => Boolean(demoIdFromSearch()));
  const titlePreset = useRef<{ hero: string; title: string } | null>(null);
  const titleTouched = useRef(false);
  const presetApplied = useRef(false);
  const [mediaConsent, setMediaConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [colorTheme, setColorTheme] = useState<"light" | "dark">(() => {
    try {
      const s = localStorage.getItem("theme");
      if (s === "light" || s === "dark") return s;
    } catch {
      /* ignore */
    }
    return "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", colorTheme);
  }, [colorTheme]);

  useEffect(() => {
    if (!isDemo) return;
    const demo = getDemoExample();
    setChildName(demo.childName);
    setChildAge(demo.childAge);
    setBookTitle(demo.bookTitle);
    setThemeText(demo.themeText);
    setDedication(demo.dedication);
    setProject(demo.project);
    setAssets(demo.assets);
    setPhotoUploaded(true);
    setJobs([]);
  }, [isDemo]);

  useEffect(() => {
    if (presetApplied.current || isDemo) return;
    const q = new URLSearchParams(window.location.search);
    const tema = q.get("tema");
    const titulo = q.get("titulo");
    const historia = q.get("historia");
    const heroi = q.get("heroi");
    if (!tema && !titulo && !historia) return;
    presetApplied.current = true;
    if (tema) setTemaId(tema);
    if (q.get("tamanho") === "P" || q.get("tamanho") === "M") setBookSize(q.get("tamanho") as "M" | "P");
    const capa = (q.get("capa") || "").toLowerCase();
    if (capa === "soft" || capa === "hard") setCoverType(capa);
    if (q.get("modo") === "cartoon") setArtMode("cartoon");
    const onlyTheme = q.get("campos") === "tema" || q.get("campos") === "nome";
    if (q.get("campos") === "nome") setOnlyName(true);
    const cast = tema || titulo || historia ? castFromQuery(q) : emptyCast();
    setCastWho(cast.who);
    setGender(cast.gender);
    setAlsoWho(cast.also?.who ?? null);
    setAlsoGender(cast.also?.gender ?? null);
    setAskGender(cast.askGender);
    alsoHero.current = cast.also?.hero ?? null;
    const fallback = tema ? themePreset(tema, lang) : null;
    const themeBody = historia || fallback?.theme || "";
    if (themeBody) setThemeText(themeBody);
    if (q.get("campos") === "nome" && titulo) {
      setBookTitle(titulo);
      if (heroi) titlePreset.current = { hero: heroi, title: titulo };
    }
    if (onlyTheme) return;
    const title = titulo || fallback?.title || "";
    if (title) setBookTitle(title);
    if (heroi && titulo) titlePreset.current = { hero: heroi, title: titulo };
  }, [isDemo, lang]);

  const refreshCredits = useCallback(async () => {
    try {
      await api.credits();
    } catch {
      /* ignore */
    }
  }, []);

  const refreshMe = useCallback(async () => {
    try {
      const me = await api.me();
      const registered = !me.is_guest && me.email_verified;
      setAccountKind(registered ? "account" : me.is_guest ? "guest" : "unknown");
      setAccountEmail(me.email);
      setAccountName(me.full_name?.trim() || "");
      setIsOwner(Boolean(me.is_owner));
      if (registered) {
        const addressLine = [
          me.street,
          me.number,
          me.complement,
          me.district,
          me.city,
          me.state,
          me.country,
          me.postal_code,
        ]
          .map((p) => (p || "").trim())
          .filter(Boolean)
          .join(", ");
        if (me.full_name?.trim()) setClientName(me.full_name.trim());
        setClientEmail(me.email);
        if (me.phone?.trim()) setClientPhone(me.phone.trim());
        if (addressLine) setClientAddress(addressLine);
      }
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    void refreshMe();
    void refreshCredits();
  }, [refreshMe, refreshCredits]);

  const getStoryBrief = useCallback(() => {
    const name = childName.trim();
    const title = bookTitle.trim();
    const theme = themeText.trim();
    const genderBit = gender === "f" ? "feminino" : gender === "m" ? "masculino" : "";
    const companion = alsoName.trim();
    const cm = bookSize === "P" ? "15×15 cm" : "20×20 cm";
    const look =
      artMode === "cartoon"
        ? "Estilo cartoon premium, traços desenhados, formas arredondadas, sem anime nem chibi."
        : "Estilo editorial suavemente realista: pele com luz suave, íris na fração da foto, cabelo fio a fio, sem cartoon.";
    const format = `Livro quadrado ${cm}, corte reto, página em sangria total, estrofe curta na faixa calma. ${look}`;
    if (lang === "en") {
      return (
        `Invent an original children's story. The book title must be: "${title}". ` +
        `Theme and ideas from the guardian: ${theme}. ` +
        (name ? `The hero's name is ${name}${genderBit ? ` (${genderBit})` : ""}. ` : "") +
        (companion ? `Also include ${companion}. ` : "") +
        format
      );
    }
    if (lang === "es") {
      return (
        `Inventa una historia infantil original. El título del libro debe ser: "${title}". ` +
        `Tema e ideas del responsable: ${theme}. ` +
        (name ? `El protagonista se llama ${name}${genderBit ? ` (${genderBit})` : ""}. ` : "") +
        (companion ? `También entra ${companion}. ` : "") +
        format
      );
    }
    return (
      `Invente uma história infantil original. O título do livro deve ser: "${title}". ` +
      `Tema e ideias do responsável: ${theme}. ` +
      (name ? `O protagonista se chama ${name}${genderBit ? ` e é do gênero ${genderBit}` : ""}. ` : "") +
      (companion ? `Também entra ${companion}. ` : "") +
      format
    );
  }, [alsoName, artMode, bookSize, bookTitle, childName, gender, lang, themeText]);

  const {
    voices,
    customVoiceAvailable,
    selectedVoiceId,
    setSelectedVoiceId,
    voiceName,
    setVoiceName,
    voiceUploading,
    onVoiceFile,
    removeSelectedVoice,
  } = useStudioVoices({
    isDemo,
    mediaConsent,
    setError,
    consentError: t.errConsentVoice,
    defaultVoiceName: t.defaultVoiceName,
  });

  useStudioPolling({
    project,
    jobs,
    setProject,
    setJobs,
    setAssets,
    refreshCredits,
    isDemo,
  });

  const { runStep } = useStudioSteps({
    project,
    isDemo,
    selectedVoiceId,
    getStoryBrief,
    setBusy,
    setError,
    setJobs,
    refreshCredits,
  });

  const {
    approveCharacter,
    approveBook,
    requestPrint,
    characterApproved,
    bookApproved,
    printRequested,
  } = useStudioApprovals({
    project,
    isDemo,
    setBusy,
    setError,
    setProject,
  });

  function formReady(agreed = mediaConsent) {
    if (isDemo) return false;
    if (onlyName) {
      if (!childName.trim() || childAge.trim() === "" || (alsoWho && !alsoName.trim())) {
        setError(t.errMissingFields);
        return false;
      }
    } else if (!childName.trim() || !bookTitle.trim() || !themeText.trim() || childAge.trim() === "" || (alsoWho && !alsoName.trim())) {
      setError(t.errMissingFields);
      return false;
    }
    if (askGender && (!gender || (alsoWho && !alsoGender))) {
      setError(t.errGender);
      return false;
    }
    const signedIn = accountKind === "account";
    const buyerName = signedIn ? oneLine(accountName || clientName || accountEmail) : oneLine(clientName);
    const buyerEmail = signedIn ? oneLine(accountEmail || clientEmail) : oneLine(clientEmail);
    const buyerPhone = oneLine(clientPhone);
    const buyerAddress = oneLine(clientAddress);
    if (!buyerName || !validEmail(buyerEmail) || !buyerPhone || !buyerAddress) {
      setError(t.errClient);
      return false;
    }
    if (photos.length === 0) {
      setError(t.errPhotoRequired);
      return false;
    }
    if (!agreed) {
      setError(t.errConsentPhoto);
      return false;
    }
    setError(null);
    return true;
  }

  function goToGenerate() {
    if (!formReady()) return;
    setGenerateStep(true);
  }

  async function start(agreed = mediaConsent) {
    if (!formReady(agreed)) return;
    const signedIn = accountKind === "account";
    const buyerName = signedIn ? oneLine(accountName || clientName || accountEmail) : oneLine(clientName);
    const buyerEmail = signedIn ? oneLine(accountEmail || clientEmail) : oneLine(clientEmail);
    const buyerPhone = oneLine(clientPhone);
    const buyerAddress = oneLine(clientAddress);
    const buyerNotes = oneLine(clientNotes);
    setBusy(true);
    setError(null);
    try {
      const age = Number(childAge);
      const language = lang === "en" ? "en" : lang === "es" ? "es" : "pt-BR";
      const themeLabel = (onlyName ? bookTitle || themeText : themeText || bookTitle).trim();
      const p = await api.createProject({
        theme: temaId || themeText.trim(),
        childName,
        dedication,
        childAge: Number.isNaN(age) ? undefined : age,
        style: artMode === "cartoon" ? "cartoon" : "realistic",
        bookSize,
        coverType,
        language,
      });
      setProject(p);
      setJobs([]);
      setAssets(null);
      setMediaConsent(true);
      const uploadMeta = {
        language,
        themeLabel,
        extraNames: extraNames.trim(),
        gender: gender ?? undefined,
        subject: subjectCode(castWho),
        alsoName: alsoName.trim() || undefined,
        alsoGender: alsoGender ?? undefined,
        alsoSubject: alsoWho ? subjectCode(alsoWho) : undefined,
        clientName: buyerName,
        clientEmail: buyerEmail,
        clientPhone: buyerPhone,
        clientAddress: buyerAddress,
        clientNotes: buyerNotes || undefined,
      };
      for (let i = 0; i < photos.length; i += 1) {
        await api.uploadPhoto(p.id, photos[i].file, {
          ...uploadMeta,
          finalize: i === photos.length - 1,
        });
      }
      setPhotoUploaded(true);
      setOrderSent(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const canMountEbook = photoUploaded && !!project?.story_text && characterApproved;
  const canMakeVideo = bookApproved;
  const locked = busy || isDemo;
  const ebookRunning = jobs.some(
    (j) => j.type === "EBOOK" && (j.status === "PENDING" || j.status === "RUNNING"),
  );

  function exitDemo() {
    const url = new URL(window.location.href);
    url.searchParams.delete("exemplo");
    const next = `${url.pathname}${url.search}${url.hash}`;
    window.history.replaceState({}, "", next);
    setIsDemo(false);
    setProject(null);
    setAssets(null);
    setPhotoUploaded(false);
    setPhotos((cur) => {
      cur.forEach((item) => releasePreview(item.url));
      return [];
    });
    setOrderSent(false);
    setExtraNames("");
    setMediaConsent(false);
    setChildName("");
    setChildAge("");
    setBookTitle("");
    setThemeText("");
    setDedication("");
    setClientName("");
    setClientDone(false);
    setClientEmail("");
    setClientPhone("");
    setClientAddress("");
    setClientNotes("");
    setJobs([]);
  }

  function toggleColorTheme() {
    setColorTheme((cur) => {
      const next = cur === "light" ? "dark" : "light";
      try {
        localStorage.setItem("theme", next);
      } catch {
        /* ignore */
      }
      return next;
    });
  }

  const fieldsLocked = !!project;
  const showBook = isDemo || clientDone || accountKind === "account";
  const showClient = !isDemo && !clientDone && accountKind === "guest";

  function finishClient() {
    const buyerName = oneLine(clientName);
    const buyerEmail = oneLine(clientEmail);
    const buyerPhone = oneLine(clientPhone);
    const buyerAddress = oneLine(clientAddress);
    if (!buyerName || !validEmail(buyerEmail) || !buyerPhone || !buyerAddress) {
      setError(t.errClient);
      return;
    }
    setError(null);
    setClientDone(true);
  }

  const addPhotos = useCallback((list: Iterable<File>) => {
    const incoming = imageFiles(list);
    if (!incoming.length) return;
    setPhotos((cur) => {
      const next = [...cur];
      for (const file of incoming) {
        if (next.length >= PHOTO_LIMIT) break;
        const key = photoKey(file);
        if (next.some((item) => item.key === key)) continue;
        next.push({ key, file, url: previewUrl(file) });
      }
      return next;
    });
  }, []);

  function removePhoto(key: string) {
    setPhotos((cur) => {
      const found = cur.find((item) => item.key === key);
      if (found) releasePreview(found.url);
      return cur.filter((item) => item.key !== key);
    });
  }

  useEffect(() => {
    function onPaste(event: ClipboardEvent) {
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || target?.isContentEditable) return;
      const files = imageFiles(event.clipboardData?.files ?? []);
      if (!files.length) return;
      event.preventDefault();
      addPhotos(files);
    }
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, [addPhotos]);
  const primary = subjectCopy(lang, castWho, gender);
  const companionCopy = alsoWho ? subjectCopy(lang, alsoWho, alsoGender) : null;
  const maxAge = ageLimit(castWho);

  function syncTitle(name: string, companion: string) {
    const preset = titlePreset.current;
    if (!preset || titleTouched.current) return;
    let next = preset.title;
    const typed = name.trim();
    if (preset.hero) next = typed ? next.split(preset.hero).join(typed) : next;
    const hero2 = alsoHero.current;
    const typed2 = companion.trim();
    if (hero2) next = typed2 ? next.split(hero2).join(typed2) : next;
    setBookTitle(next);
  }

  function genderButtons(value: StudioGender | null, onPick: (next: StudioGender) => void, label: string) {
    return (
      <div className="studio-choice studio-gender" role="group" aria-label={label}>
        <span className="studio-choice-label">{label}</span>
        <div className="studio-actions">
          {(["f", "m"] as const).map((choice) => (
            <button
              key={choice}
              type="button"
              className={value === choice ? "studio-pick is-on" : "studio-pick"}
              aria-pressed={value === choice}
              disabled={fieldsLocked}
              onClick={() => onPick(choice)}
            >
              {choice === "f" ? t.genderF : t.genderM}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="kid studio-app">
      <header className="khead" role="banner">
        <div className="khead-inner">
          <a href="/" className="kbrand" aria-label="Story R Us">
            <img className="hdr-logo" src={logo} alt="Story R Us" />
          </a>
          <div className="khead-main">
            <div className="khead-top">
              <div className="khead-top-inner">
                <div className="khead-utils">
                  <div
                    className="lang"
                    role="group"
                    aria-label={t.langAria}
                    data-testid="studio-lang"
                  >
                    {langs.map((code) => (
                      <button
                        key={code}
                        type="button"
                        className={lang === code ? "on" : ""}
                        aria-pressed={lang === code}
                        onClick={() => setLang(code)}
                      >
                        {code.toUpperCase()}
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="theme-toggle"
                    onClick={toggleColorTheme}
                    aria-label={t.themeToggleAria}
                  >
                    {colorTheme === "dark" ? <IcSun className="ti" /> : <IcMoon className="ti" />}
                    <span className="theme-toggle-label">
                      {colorTheme === "dark" ? t.themeToLight : t.themeToDark}
                    </span>
                  </button>
                  {isOwner && (
                    <>
                      <a className="kutil" href="/pedidos">
                        Pedidos
                      </a>
                      <a className="kutil" href="/usuarios">
                        Usuários
                      </a>
                    </>
                  )}
                  {onLogout && (
                    <>
                      <a className="kutil" href="/conta" data-testid="studio-account">
                        {t.account}
                      </a>
                      <button type="button" className="kutil link" onClick={onLogout} data-testid="studio-logout">
                        {t.logout}
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main id="studio-main" className="studio-page" aria-busy={busy || undefined}>
        {orderSent ? (
          <section className="studio-card studio-order" role="status" data-testid="studio-order-sent">
            <h2>{t.orderSent}</h2>
            <p>{t.orderFollowup}</p>
          </section>
        ) : (
          <>
        {isDemo && (
          <div className="demo-banner" role="status" aria-live="polite">
            <p>{t.demoBanner}</p>
            <button type="button" className="kbtn kbtn-soft" onClick={exitDemo}>
              {t.demoCta}
            </button>
          </div>
        )}

        {error && (
          <p className="studio-error" role="alert">
            {error}
          </p>
        )}

        <section className="studio-card" aria-labelledby="studio-create-heading">
          <h2 id="studio-create-heading">{t.createTitle}</h2>
          {project ? (
            <p className="studio-meta">{t.projectLocked}</p>
          ) : (
            <p className="studio-slogan">{t.slogan}</p>
          )}

          {showClient && (
            <div className="studio-client" data-testid="studio-client">
              <h3 className="field-label">{t.clientTitle}</h3>
              <label className="studio-field">
                {t.clientName}
                <input
                  disabled={isDemo}
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  placeholder={t.clientNamePh}
                  maxLength={120}
                  autoComplete="name"
                  data-testid="studio-client-name"
                />
              </label>
              <label className="studio-field">
                {t.clientEmail}
                <input
                  disabled={isDemo}
                  type="email"
                  value={clientEmail}
                  onChange={(e) => setClientEmail(e.target.value)}
                  placeholder={t.clientEmailPh}
                  maxLength={160}
                  autoComplete="email"
                  data-testid="studio-client-email"
                />
              </label>
              <label className="studio-field">
                {t.clientPhone}
                <input
                  disabled={isDemo}
                  type="tel"
                  value={clientPhone}
                  onChange={(e) => setClientPhone(e.target.value)}
                  placeholder={t.clientPhonePh}
                  maxLength={40}
                  autoComplete="tel"
                  data-testid="studio-client-phone"
                />
              </label>
              <label className="studio-field">
                {t.clientAddress}
                <textarea
                  disabled={isDemo}
                  value={clientAddress}
                  onChange={(e) => setClientAddress(e.target.value)}
                  placeholder={t.clientAddressPh}
                  maxLength={300}
                  rows={3}
                  autoComplete="street-address"
                  data-testid="studio-client-address"
                />
              </label>
              <label className="studio-field">
                {t.clientNotes}
                <textarea
                  disabled={isDemo}
                  value={clientNotes}
                  onChange={(e) => setClientNotes(e.target.value)}
                  placeholder={t.clientNotesPh}
                  maxLength={500}
                  rows={2}
                  data-testid="studio-client-notes"
                />
              </label>
              <button type="button" className="kbtn kbtn-go studio-create" onClick={finishClient}>
                {t.clientContinue}
              </button>
            </div>
          )}

          {showBook && generateStep && (
            <div className="studio-generate-step" data-testid="studio-generate-step">
              <h3 className="field-label">{t.createProject}</h3>
              <p className="studio-slogan">{t.generateStepHint}</p>
              <button type="button" className="kbtn kbtn-soft studio-create" onClick={() => setGenerateStep(false)}>
                {t.backToForm}
              </button>
              <button
                type="button"
                className="kbtn kbtn-primary studio-create"
                disabled={isDemo || busy}
                data-testid="studio-generate-book"
                onClick={() => void start()}
              >
                {t.createProject}
              </button>
            </div>
          )}

          {showBook && !generateStep && (
          <>
          <div className="how" role="region" aria-labelledby="studio-how-heading">
            <h3 className="field-label" id="studio-how-heading">
              {t.howTitle}
            </h3>
            <ol>
              {t.how.map((step) => (
                <li key={step.t}>
                  <div>
                    <strong>{step.t}</strong>
                    <p>{step.p}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          <div className="studio-grid two">
            <label className="studio-field">
              {primary.name}
              <input
                disabled={fieldsLocked}
                value={childName}
                onChange={(e) => {
                  const name = e.target.value;
                  setChildName(name);
                  syncTitle(name, alsoName);
                }}
                placeholder={primary.namePh}
                maxLength={80}
              />
            </label>
            <label className="studio-field">
              {primary.age}
              <input
                disabled={fieldsLocked}
                type="number"
                inputMode="numeric"
                min={0}
                max={maxAge}
                value={childAge}
                onChange={(e) => {
                  const v = e.target.value;
                  if (v === "") return setChildAge("");
                  const n = Math.max(0, Math.min(maxAge, Math.floor(Number(v))));
                  setChildAge(Number.isNaN(n) ? "" : String(n));
                }}
                placeholder={t.childAgePh}
              />
            </label>
          </div>
          {askGender ? genderButtons(gender, setGender, t.gender) : null}
          {companionCopy ? (
            <>
              <label className="studio-field studio-also">
                {companionCopy.name}
                <input
                  disabled={fieldsLocked}
                  value={alsoName}
                  onChange={(e) => {
                    const name = e.target.value;
                    setAlsoName(name);
                    syncTitle(childName, name);
                  }}
                  placeholder={companionCopy.namePh}
                  maxLength={80}
                  data-testid="studio-also-name"
                />
              </label>
              {askGender ? genderButtons(alsoGender, setAlsoGender, t.gender) : null}
            </>
          ) : null}

          {onlyName ? (
            <p className="studio-chosen" role="status">
              <span>{t.chosenBook}</span>
              <b>{bookTitle || themeText}</b>
            </p>
          ) : (
            <>
              <label className="studio-field">
                {t.bookTitle}
                <input
                  disabled={fieldsLocked}
                  value={bookTitle}
                  onChange={(e) => {
                    titleTouched.current = true;
                    setBookTitle(e.target.value);
                  }}
                  placeholder={t.bookTitlePh}
                  maxLength={120}
                />
              </label>

              <label className="studio-field">
                {t.themeFree}
                <textarea
                  disabled={fieldsLocked}
                  value={themeText}
                  onChange={(e) => setThemeText(e.target.value)}
                  placeholder={t.themeFreePh}
                  maxLength={500}
                  rows={3}
                />
              </label>
              <p className="muted field-hint">{t.themeHint}</p>

              <label className="studio-field">
                {t.dedication}
                <input
                  disabled={fieldsLocked}
                  value={dedication}
                  onChange={(e) => setDedication(e.target.value)}
                  placeholder={t.dedicationPh}
                  maxLength={200}
                />
              </label>
            </>
          )}

          <div className="studio-choices">
            <div className="studio-choice" role="group" aria-label={t.artStyle}>
              <span className="studio-choice-label">{t.artStyle}</span>
              <div className="studio-actions">
                {(["realista", "cartoon"] as const).map((choice) => (
                  <button
                    key={choice}
                    type="button"
                    className={artMode === choice ? "studio-pick is-on" : "studio-pick"}
                    aria-pressed={artMode === choice}
                    disabled={fieldsLocked}
                    onClick={() => setArtMode(choice)}
                  >
                    {choice === "cartoon" ? t.artCartoon : t.artRealistic}
                  </button>
                ))}
              </div>
            </div>

            <div className="studio-choice" role="group" aria-label={t.coverType}>
              <span className="studio-choice-label">{t.coverType}</span>
              <div className="studio-actions">
                {(["hard", "soft"] as const).map((choice) => (
                  <button
                    key={choice}
                    type="button"
                    className={coverType === choice ? "studio-pick is-on" : "studio-pick"}
                    aria-pressed={coverType === choice}
                    disabled={fieldsLocked}
                    onClick={() => setCoverType(choice)}
                  >
                    {choice === "hard" ? t.coverHard : t.coverSoft}
                  </button>
                ))}
              </div>
            </div>

            <div className="studio-choice" role="group" aria-label={t.bookSize}>
              <span className="studio-choice-label">{t.bookSize}</span>
              <div className="studio-actions">
                {(["M", "P"] as const).map((choice) => (
                  <button
                    key={choice}
                    type="button"
                    className={bookSize === choice ? "studio-pick is-on" : "studio-pick"}
                    aria-pressed={bookSize === choice}
                    disabled={fieldsLocked}
                    onClick={() => setBookSize(choice)}
                  >
                    {choice === "M" ? t.bookSizeM : t.bookSizeP}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {!fieldsLocked && (
            <>
              <label className="studio-field">
                {t.otherCharacters}
                <input
                  disabled={isDemo}
                  value={extraNames}
                  onChange={(e) => setExtraNames(e.target.value)}
                  placeholder={t.otherCharactersPh}
                  maxLength={300}
                  data-testid="studio-extra-names"
                />
              </label>
              <p className="muted field-hint">{primary.extras}</p>
              <p className="studio-field">{t.photoCharacters}</p>
              <div
                className={dragOver ? "studio-drop is-over" : "studio-drop"}
                data-testid="studio-photo-drop"
                onDragOver={(e) => {
                  e.preventDefault();
                  if (!isDemo) setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragOver(false);
                  if (!isDemo) addPhotos(e.dataTransfer.files);
                }}
              >
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  disabled={isDemo}
                  data-testid="studio-photo-input"
                  aria-label={t.ariaSelectPhoto}
                  onChange={(e) => {
                    addPhotos(e.target.files ?? []);
                    e.target.value = "";
                  }}
                />
                <span className="studio-drop-title">{t.photoDrop}</span>
                <span className="studio-drop-hint">{t.photoDropHint}</span>
              </div>
              {photos.length > 0 ? (
                <>
                  <p className="muted field-hint">{t.photoSelected(photos.length)}</p>
                  <ul className="studio-photo-list">
                    {photos.map((item) => (
                      <li key={item.key}>
                        <img src={item.url} alt="" />
                        <span>{item.file.name}</span>
                        <button type="button" onClick={() => removePhoto(item.key)}>
                          {t.photoRemove}
                        </button>
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}
              <label className="studio-consent">
                <input
                  type="checkbox"
                  checked={mediaConsent}
                  disabled={isDemo}
                  data-testid="studio-media-consent"
                  onChange={(e) => setMediaConsent(e.target.checked)}
                />
                {t.consent}
              </label>
              <button
                type="button"
                className="kbtn kbtn-primary studio-create"
                disabled={isDemo}
                data-testid="studio-next-page"
                onClick={goToGenerate}
              >
                {t.nextPage}
              </button>
            </>
          )}
          </>
          )}
        </section>
          </>
        )}

        {project && (
          <section
            className="studio-card"
            data-testid="studio-project"
            aria-labelledby="studio-project-heading"
            aria-busy={busy || undefined}
          >
            <h2 id="studio-project-heading">{t.projectTitle}</h2>
            <p className="studio-meta" role="status" aria-live="polite">
              {t.metaBookTitle}: <b>{bookTitle || "—"}</b> · {t.metaTheme}:{" "}
              <b>{resolveThemeName(project.theme ?? themeText, t.themes)}</b> · {t.statusLabel}:{" "}
              <b>{project.status}</b>
            </p>

            {photoUploaded && (
              <p className="muted" role="status">
                {t.photoSent}
              </p>
            )}
            <div className="studio-actions">
              <button
                type="button"
                className="kbtn kbtn-primary"
                disabled={locked || !photoUploaded}
                onClick={() => runStep("story")}
                data-testid="studio-generate-story"
              >
                {t.generateStory} <span className="muted">{t.oneCredit}</span>
              </button>
            </div>

            <VoiceNarrationPanel
              customVoiceAvailable={customVoiceAvailable}
              voiceName={voiceName}
              setVoiceName={setVoiceName}
              voiceUploading={voiceUploading}
              locked={locked}
              mediaConsent={mediaConsent}
              onVoiceFile={onVoiceFile}
              voices={voices}
              selectedVoiceId={selectedVoiceId}
              setSelectedVoiceId={setSelectedVoiceId}
              removeSelectedVoice={removeSelectedVoice}
            />

            <EbookStepButtons locked={locked} canMountEbook={canMountEbook} runStep={runStep} />
            {!characterApproved && photoUploaded && (
              <p className="muted">{t.approveCharacterFirst}</p>
            )}

            <ProgressList jobs={jobs} />

            <div className="results" role="region" aria-label={t.ariaResults}>
              {assets?.character_url && (
                <CharacterApprovalBlock
                  characterUrl={assets.character_url}
                  characterApproved={characterApproved}
                  locked={locked}
                  onApprove={approveCharacter}
                  onRegenerate={() => runStep("avatar")}
                />
              )}

              {project.story_text && (
                <div
                  className="result-block"
                  data-testid="studio-story-result"
                  role="region"
                  aria-labelledby="studio-story-result-heading"
                >
                  <h3 className="field-label" id="studio-story-result-heading">
                    {t.storyTitle}
                  </h3>
                  <pre
                    className="story"
                    style={{ whiteSpace: "pre-wrap" }}
                    data-testid="studio-story-text"
                  >
                    {project.story_text}
                  </pre>
                </div>
              )}

              {(assets?.ebook_url || (assets?.page_images?.length ?? 0) > 0 || ebookRunning) && (
                <BookApprovalBlock
                  pageImages={assets?.page_images ?? []}
                  ebookUrl={assets?.ebook_url ?? null}
                  bookApproved={bookApproved}
                  locked={locked}
                  canMountEbook={canMountEbook}
                  printRequested={printRequested}
                  projectId={project.id}
                  onApprove={approveBook}
                  onRegenerate={() => runStep("ebook")}
                  onRequestPrint={requestPrint}
                />
              )}

              {bookApproved && (
                <div className="result-block" role="region" aria-labelledby="studio-video-heading">
                  <h3 className="field-label" id="studio-video-heading">
                    {t.videoTitle}
                  </h3>
                  <p className="muted">{t.videoHint}</p>
                  <VideoStepButtons locked={locked} canMakeVideo={canMakeVideo} runStep={runStep} />
                </div>
              )}

              {assets?.video_url && (
                <div
                  className="result-block"
                  role="region"
                  aria-labelledby="studio-animation-heading"
                >
                  <h3 className="field-label" id="studio-animation-heading">
                    {t.animationTitle}
                  </h3>
                  {assets.video_url.toLowerCase().includes(".gif") ? (
                    <img
                      src={assets.video_url}
                      alt={t.animationTitle}
                      style={{ maxWidth: 360, width: "100%", borderRadius: 12 }}
                    />
                  ) : (
                    <video
                      src={assets.video_url}
                      controls
                      aria-label={t.ariaAnimationGenerated}
                      style={{ maxWidth: 360, width: "100%" }}
                    />
                  )}
                </div>
              )}

              {assets?.narrated_video_url && (
                <div
                  className="result-block"
                  role="region"
                  aria-labelledby="studio-narrated-heading"
                >
                  <h3 className="field-label" id="studio-narrated-heading">
                    {t.narratedTitle}
                  </h3>
                  {assets.narrated_video_url.toLowerCase().includes(".gif") ? (
                    <img
                      src={assets.narrated_video_url}
                      alt={t.narratedTitle}
                      style={{ maxWidth: 360, width: "100%", borderRadius: 12 }}
                    />
                  ) : (
                    <video
                      src={assets.narrated_video_url}
                      controls
                      aria-label={t.ariaNarratedGenerated}
                      style={{ maxWidth: 360, width: "100%" }}
                    />
                  )}
                </div>
              )}
            </div>

            <button
              type="button"
              className="link"
              onClick={() => (isDemo ? exitDemo() : setProject(null))}
            >
              {isDemo ? t.createMyStory : t.newProject}
            </button>
          </section>
        )}
      </main>
    </div>
  );
}

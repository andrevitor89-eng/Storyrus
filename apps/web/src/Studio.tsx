import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { ExtraCharacter, Job, Project, StoryTemplate, Theme, UserVoice } from "./types";
import { demoIdFromSearch, getDemoExample } from "./demoExample";
import logo from "./assets/logo.png";

const ART_STYLE_LABEL: Record<string, string> = {
  cgi_3d: "Rosto realista",
  realistic: "Rosto realista",
  cartoon: "Rosto realista",
  anime: "Rosto realista",
};

// Temas narrativos do briefing — a história nasce ao redor do tema escolhido.
type ThemeGroup = "aventura" | "datas" | "educativo";
const THEMES: { id: Theme; label: string; emoji: string; group: ThemeGroup }[] = [
  // Aventura e fantasia
  { id: "adventure", label: "Aventura", emoji: "🗺️", group: "aventura" },
  { id: "princess", label: "Princesas", emoji: "👑", group: "aventura" },
  { id: "superhero", label: "Super-heróis", emoji: "🦸", group: "aventura" },
  { id: "space", label: "Espaço", emoji: "🚀", group: "aventura" },
  { id: "underwater", label: "Fundo do mar", emoji: "🐠", group: "aventura" },
  { id: "dinosaurs", label: "Dinossauros", emoji: "🦕", group: "aventura" },
  { id: "fantasy", label: "Fantasia", emoji: "🧚", group: "aventura" },
  // Datas comemorativas
  { id: "birthday", label: "Aniversário", emoji: "🎂", group: "datas" },
  { id: "christmas", label: "Natal", emoji: "🎄", group: "datas" },
  { id: "easter", label: "Páscoa", emoji: "🐣", group: "datas" },
  { id: "childrens_day", label: "Dia das Crianças", emoji: "🎈", group: "datas" },
  { id: "mothers_day", label: "Dia das Mães", emoji: "💐", group: "datas" },
  { id: "fathers_day", label: "Dia dos Pais", emoji: "👔", group: "datas" },
  { id: "new_year", label: "Ano Novo", emoji: "🎉", group: "datas" },
  // Temas educativos — Linguagem & Conceitos Fundamentais
  { id: "alfabetizacao_inicial", label: "Alfabetização", emoji: "🔤", group: "educativo" },
  { id: "pensamento_matematico", label: "Matemática", emoji: "🔢", group: "educativo" },
  { id: "cores", label: "Cores", emoji: "🎨", group: "educativo" },
  { id: "opostos_espacial", label: "Opostos", emoji: "↕️", group: "educativo" },
  // Temas educativos — Habilidades de Vida & Rotinas Diárias
  { id: "higiene_desfralde", label: "Higiene", emoji: "🧼", group: "educativo" },
  { id: "rotina_dormir", label: "Hora de Dormir", emoji: "🌙", group: "educativo" },
  { id: "alimentacao_saudavel", label: "Alimentação", emoji: "🥗", group: "educativo" },
  { id: "vestir_autonomia", label: "Vestir-se Sozinho", emoji: "👕", group: "educativo" },
  // Temas educativos — Autoconsciência & Aprendizagem Socioemocional
  { id: "literacia_emocional", label: "Sentimentos", emoji: "💗", group: "educativo" },
  { id: "consciencia_corporal", label: "Corpo", emoji: "🙆", group: "educativo" },
  { id: "compartilhar_revezar", label: "Compartilhar", emoji: "🤝", group: "educativo" },
  // Temas educativos — Descoberta & Exploração do Mundo
  { id: "animais_sons", label: "Animais e Sons", emoji: "🐾", group: "educativo" },
  { id: "transporte_ajudantes", label: "Transporte", emoji: "🚚", group: "educativo" },
  { id: "clima_estacoes", label: "Clima e Estações", emoji: "⛅", group: "educativo" },
];
const themeLabel = (id: string | null | undefined) =>
  THEMES.find((t) => t.id === id)?.label ?? "—";

// O personagem é gerado automaticamente ao enviar a foto, e a história tem
// seção própria. Aqui ficam as etapas finais (dependem de personagem + história).
const STEPS: { key: "ebook" | "video" | "narrated-video"; label: string; cost: string; hint: string }[] = [
  { key: "ebook", label: "Montar ebook", cost: "1 crédito", hint: "E-book ilustrado (precisa de personagem aprovado + história)." },
  { key: "video", label: "Gerar animação", cost: "5 créditos", hint: "Clipe curto (5–10s) com movimento — não é o vídeo narrado." },
  { key: "narrated-video", label: "Gerar vídeo narrado", cost: "8 créditos", hint: "História com narração (~1–2 min) a partir do storyboard." },
];

type StoryMode = "invent" | "write" | "file" | "catalog";

const HOW = [
  "Envie uma foto de frente (um rosto, luz boa).",
  "Aprove o personagem (rosto realista).",
  "Escolha o tema ou uma história pronta.",
  "Aprove o livro (capa e páginas).",
  "Baixe o PDF, peça o impresso ou gere o vídeo narrado.",
];

export function Studio({ onLogout }: { onLogout?: () => void }) {
  const [credits, setCredits] = useState<number | null>(null);
  // Até 2 temas combinados na mesma história: o 1º é o principal (define
  // vilão/cenário/arco), o 2º só soma um objetivo de aprendizado extra.
  const [selectedThemes, setSelectedThemes] = useState<Theme[]>(["adventure"]);
  const theme = selectedThemes[0] ?? "adventure";
  const extraTheme = selectedThemes[1];
  function toggleTheme(id: Theme) {
    setSelectedThemes((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id]; // troca o mais antigo pelo novo
      return [...prev, id];
    });
  }
  const [project, setProject] = useState<Project | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoUploaded, setPhotoUploaded] = useState(false);
  const [extraChars, setExtraChars] = useState<ExtraCharacter[]>([]);
  const [extraCharFile, setExtraCharFile] = useState<File | null>(null);
  const [extraCharName, setExtraCharName] = useState("");
  const [storyMode, setStoryMode] = useState<StoryMode>("invent");
  const [storyText, setStoryText] = useState("");
  // Catálogo de histórias prontas (carregado ao abrir o modo "catalog").
  const [templates, setTemplates] = useState<StoryTemplate[] | null>(null);
  const [appliedTemplate, setAppliedTemplate] = useState<string | null>(null);
  const [childName, setChildName] = useState("");
  const [childAge, setChildAge] = useState<string>("");
  const [dedication, setDedication] = useState("");
  const [assets, setAssets] = useState<{
    character_url: string | null;
    realistic_url: string | null;
    extra_characters: { name: string; url: string }[];
    page_images: string[];
    ebook_url: string | null;
    video_url: string | null;
    narrated_video_url: string | null;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(() => Boolean(demoIdFromSearch()));
  const [mediaConsent, setMediaConsent] = useState(false);
  const maxPages = (() => {
    const n = Number(new URLSearchParams(window.location.search).get("paginas") || 0);
    return Number.isFinite(n) && n > 0 ? Math.min(40, Math.floor(n)) : 0;
  })();

  // aplica o tema (claro/escuro) salvo na landing
  useEffect(() => {
    try {
      const s = localStorage.getItem("theme");
      document.documentElement.setAttribute("data-theme", s === "light" ? "light" : "dark");
    } catch { /* ignore */ }
  }, []);

  // pré-seleciona o tema da história vindo do catálogo (/app?tema=...)
  useEffect(() => {
    if (demoIdFromSearch()) return;
    const q = new URLSearchParams(window.location.search).get("tema");
    if (q && THEMES.some((x) => x.id === q)) setSelectedThemes([q as Theme]);
  }, []);

  // Abre histórias prontas quando a landing manda /app?historia=alfabeto_amazonia
  useEffect(() => {
    if (demoIdFromSearch()) return;
    const h = new URLSearchParams(window.location.search).get("historia");
    if (!h) return;
    setStoryMode("catalog");
    api.storyTemplates().then(setTemplates).catch((e) => setError((e as Error).message));
  }, []);

  useEffect(() => {
    if (!isDemo) return;
    const demo = getDemoExample();
    setSelectedThemes(demo.themes);
    setChildName(demo.childName);
    setChildAge(demo.childAge);
    setDedication(demo.dedication);
    setStoryText(demo.project.story_text ?? "");
    setProject(demo.project);
    setAssets(demo.assets);
    setPhotoUploaded(true);
    setJobs([]);
  }, [isDemo]);
  const [busy, setBusy] = useState(false);
  const pollRef = useRef<number | null>(null);
  const [voices, setVoices] = useState<UserVoice[]>([]);
  const [customVoiceAvailable, setCustomVoiceAvailable] = useState(false);
  const [selectedVoiceId, setSelectedVoiceId] = useState("");
  const [voiceName, setVoiceName] = useState("Minha voz");
  const [voiceUploading, setVoiceUploading] = useState(false);

  const refreshCredits = useCallback(async () => {
    try {
      setCredits((await api.credits()).credits);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    refreshCredits();
  }, [refreshCredits]);

  const refreshVoices = useCallback(async () => {
    try {
      const data = await api.listVoices();
      setVoices(data.items);
      setCustomVoiceAvailable(data.custom_voice_available);
      setSelectedVoiceId((prev) => {
        if (prev && data.items.some((v) => v.id === prev)) return prev;
        const def = data.items.find((v) => v.is_default);
        return def?.id || data.items[0]?.id || "";
      });
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    refreshVoices();
  }, [refreshVoices]);

  // Polling do estado enquanto houver job ativo.
  useEffect(() => {
    if (!project || isDemo) return;
    const active = jobs.some((j) => j.status === "PENDING" || j.status === "RUNNING");
    if (!active) {
      if (pollRef.current) window.clearInterval(pollRef.current);
      // carga final dos resultados quando não há mais job ativo
      api.getAssets(project.id).then(setAssets).catch(() => {});
      return;
    }
    pollRef.current = window.setInterval(async () => {
      try {
        // Busca os jobs primeiro (é o que avança o estado do projeto no backend)
        // e só então o projeto, garantindo que leremos o estado já atualizado.
        const js = await api.listJobs(project.id);
        const p = await api.getProject(project.id);
        setProject(p);
        setJobs(js);
        api.getAssets(project.id).then(setAssets).catch(() => {});
        refreshCredits();
      } catch {
        /* ignore */
      }
    }, 2500);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [project, jobs, refreshCredits, isDemo]);

  async function start() {
    if (isDemo) return;
    setBusy(true);
    setError(null);
    try {
      const age = childAge.trim() === "" ? undefined : Number(childAge);
      const p = await api.createProject(theme, extraTheme, childName, dedication, age);
      setProject(p);
      setJobs([]);
      setPhotoUploaded(false);
      setAssets(null);
      setStoryText("");
      setMediaConsent(false);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function upload() {
    if (!project || !photo || isDemo) return;
    if (!mediaConsent) {
      setError("Marque o consentimento para enviar a foto.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.uploadPhoto(project.id, photo);
      setPhotoUploaded(true);
      // Gera o personagem automaticamente assim que a foto chega.
      await api.startStep(project.id, "avatar", {});
      const js = await api.listJobs(project.id);
      setJobs(js);
      refreshCredits();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function runStep(step: "avatar" | "story" | "ebook" | "video" | "narrated-video") {
    if (!project || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      let body: Record<string, unknown> = {};
      if (step === "video") body = { duration_s: 5 };
      if (step === "ebook" && maxPages > 0) body = { max_pages: maxPages };
      if (step === "narrated-video" && selectedVoiceId) body = { voice_id: selectedVoiceId };
      await api.startStep(project.id, step, body);
      const js = await api.listJobs(project.id);
      setJobs(js);
      refreshCredits();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function approveCharacter() {
    if (!project || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      setProject(await api.approveCharacter(project.id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function approveBook() {
    if (!project || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      setProject(await api.approveBook(project.id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function requestPrint() {
    if (!project || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      setProject(await api.requestPrint(project.id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function onVoiceFile(file: File | null) {
    if (!file || isDemo) return;
    if (!mediaConsent) {
      setError("Marque o consentimento para clonar a voz.");
      return;
    }
    setVoiceUploading(true);
    setError(null);
    try {
      const voice = await api.uploadVoice(file, voiceName.trim() || "Minha voz", voices.length === 0);
      await refreshVoices();
      setSelectedVoiceId(voice.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setVoiceUploading(false);
    }
  }

  async function removeSelectedVoice() {
    if (!selectedVoiceId || isDemo) return;
    setError(null);
    try {
      await api.deleteVoice(selectedVoiceId);
      await refreshVoices();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  // Salva a história escrita/colada pelo usuário (sem IA).
  async function saveStory() {
    if (!project || !storyText.trim() || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      const p = await api.setStoryText(project.id, storyText);
      setProject(p);
      const js = await api.listJobs(project.id);
      setJobs(js);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  // Abre o catálogo de histórias prontas (carrega uma vez).
  async function openCatalog() {
    setStoryMode("catalog");
    if (templates) return;
    try {
      setTemplates(await api.storyTemplates());
    } catch (e) {
      setError((e as Error).message);
    }
  }

  // Aplica uma história pronta do catálogo (sem IA, sem créditos).
  async function applyTemplate(templateId: string) {
    if (!project || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      const p = await api.applyStoryTemplate(project.id, templateId);
      setProject(p);
      setAppliedTemplate(templateId);
      const js = await api.listJobs(project.id);
      setJobs(js);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  // Extrai o texto de um arquivo enviado e mostra para o usuário revisar.
  async function onStoryFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !project || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      const { text } = await api.extractStory(project.id, file);
      setStoryText(text);
      setStoryMode("write"); // mostra o texto extraído para revisar antes de salvar
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  // Upload de personagem extra
  async function uploadExtraCharacter() {
    if (!project || !extraCharFile || isDemo) return;
    if (!mediaConsent) {
      setError("Marque o consentimento para enviar a foto do personagem extra.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.uploadExtraCharacter(project.id, extraCharFile, extraCharName);
      const p = await api.getProject(project.id);
      setProject(p);
      setExtraChars(p.extra_characters || []);
      setExtraCharFile(null);
      setExtraCharName("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  // Gera os personagens ilustrados para os extras
  async function generateExtraCharacters() {
    if (!project || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      await api.startStep(project.id, "extra-character", {});
      const js = await api.listJobs(project.id);
      setJobs(js);
      refreshCredits();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const characterApproved = !!project?.character_approved_at;
  const bookApproved = !!project?.book_approved_at;
  const printRequested = !!project?.print_requested_at;
  const canMountEbook = photoUploaded && !!project?.story_text && characterApproved;
  const canMakeVideo = bookApproved;
  const locked = busy || isDemo;

  function exitDemo() {
    const url = new URL(window.location.href);
    url.searchParams.delete("exemplo");
    const next = `${url.pathname}${url.search}${url.hash}`;
    window.history.replaceState({}, "", next);
    setIsDemo(false);
    setProject(null);
    setAssets(null);
    setPhotoUploaded(false);
    setMediaConsent(false);
    setChildName("");
    setChildAge("");
    setDedication("");
    setStoryText("");
    setJobs([]);
    setAppliedTemplate(null);
  }

  return (
    <div className="studio">
      <header>
        <img className="hdr-logo" src={logo} alt="Story.R.Us" />
        <strong>Plataforma de Histórias</strong>
        <span className="spacer" />
        <button
          className="chip"
          onClick={() => {
            const cur = document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
            document.documentElement.setAttribute("data-theme", cur);
            try { localStorage.setItem("theme", cur); } catch { /* ignore */ }
          }}
          aria-label="Alternar tema claro/escuro"
        >
          Tema
        </button>
        <span className="credits">Créditos: {credits ?? "…"}</span>
        {onLogout && (
          <button className="link" onClick={onLogout}>
            Sair
          </button>
        )}
      </header>

      {isDemo && (
        <div className="demo-banner" role="status">
          <p>Você está vendo um exemplo pronto.</p>
          <button type="button" onClick={exitDemo}>Criar a minha história</button>
        </div>
      )}

      {error && <p className="error">{error}</p>}

      <section className="card">
        <h2>Crie a sua história</h2>
        {project ? (
          <p className="muted">
            ✓ Projeto criado — os campos abaixo ficam travados até você começar um novo projeto.
          </p>
        ) : (
          <p className="slogan">Toda história merece um protagonista — e o protagonista é você.</p>
        )}

          <h3 className="field-label">1 · Escolha até 2 temas para a aventura</h3>
          <p className="muted">
            O 1º escolhido é o tema principal (define vilão, cenário e arco); o 2º só soma
            um aprendizado extra na mesma jornada.
          </p>
          <div className="styles">
            {THEMES.filter((t) => t.group === "aventura").map((t) => {
              const order = selectedThemes.indexOf(t.id);
              return (
                <button
                  key={t.id}
                  disabled={!!project}
                  className={`chip ${order >= 0 ? "on" : ""}`}
                  onClick={() => toggleTheme(t.id)}
                >
                  {t.emoji} {t.label}{order >= 0 ? ` · ${order + 1}` : ""}
                </button>
              );
            })}
          </div>

          <h3 className="field-label">Datas comemorativas</h3>
          <div className="styles">
            {THEMES.filter((t) => t.group === "datas").map((t) => {
              const order = selectedThemes.indexOf(t.id);
              return (
                <button
                  key={t.id}
                  disabled={!!project}
                  className={`chip ${order >= 0 ? "on" : ""}`}
                  onClick={() => toggleTheme(t.id)}
                >
                  {t.emoji} {t.label}{order >= 0 ? ` · ${order + 1}` : ""}
                </button>
              );
            })}
          </div>

          <h3 className="field-label">Temas educativos</h3>
          <div className="styles">
            {THEMES.filter((t) => t.group === "educativo").map((t) => {
              const order = selectedThemes.indexOf(t.id);
              return (
                <button
                  key={t.id}
                  disabled={!!project}
                  className={`chip ${order >= 0 ? "on" : ""}`}
                  onClick={() => toggleTheme(t.id)}
                >
                  {t.emoji} {t.label}{order >= 0 ? ` · ${order + 1}` : ""}
                </button>
              );
            })}
          </div>

          <h3 className="field-label">2 · Nome, idade e dedicatória</h3>
          <label>
            Nome da criança
            <input
              disabled={!!project}
              value={childName}
              onChange={(e) => setChildName(e.target.value)}
              placeholder="Ex.: Lila"
              maxLength={80}
            />
          </label>
          <label>
            Idade da criança (a história é adaptada ao tom e vocabulário da idade)
            <input
              disabled={!!project}
              type="number"
              inputMode="numeric"
              min={0}
              max={12}
              value={childAge}
              onChange={(e) => {
                const v = e.target.value;
                if (v === "") return setChildAge("");
                const n = Math.max(0, Math.min(12, Math.floor(Number(v))));
                setChildAge(Number.isNaN(n) ? "" : String(n));
              }}
              placeholder="Ex.: 5"
            />
          </label>
          <label>
            Dedicatória (aparece na 2ª página do livro)
            <input
              disabled={!!project}
              value={dedication}
              onChange={(e) => setDedication(e.target.value)}
              placeholder="Ex.: Para a Lila, com todo o amor da mamãe."
              maxLength={200}
            />
          </label>

          {!project && (
            <button disabled={locked} onClick={start}>
              Criar projeto
            </button>
          )}

          <div className="how">
            <h3 className="field-label">Como funciona</h3>
            <ol>
              {HOW.map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ol>
          </div>
      </section>

      {project && (
        <section className="card">
          <h2>Projeto</h2>
          <p className="muted">
            Tema: <b>{themeLabel(project.theme ?? theme)}</b>
            {(project.extra_theme ?? extraTheme) && (
              <> + <b>{themeLabel(project.extra_theme ?? extraTheme)}</b></>
            )} · Estilo: <b>{ART_STYLE_LABEL[project.style ?? "cgi_3d"] ?? "Rosto realista"}</b> ·
            Status: <b>{project.status}</b>
            {maxPages > 0 && (
              <> · Gerando até a página <b>{maxPages}</b></>
            )}
          </p>

          <label className="consent">
            <input
              type="checkbox"
              checked={mediaConsent}
              disabled={isDemo}
              onChange={(e) => setMediaConsent(e.target.checked)}
            />
            Sou o responsável legal e autorizo o uso desta foto (e da voz, se clonar) só para criar este livro. Não usamos para divulgação.
          </label>

          <div className="upload">
            <input
              type="file"
              accept="image/*"
              disabled={isDemo}
              onChange={(e) => setPhoto(e.target.files?.[0] ?? null)}
            />
            <button disabled={!photo || locked || !mediaConsent} onClick={upload}>
              {photoUploaded ? "Foto enviada ✓" : "Enviar foto"}
            </button>
          </div>
          <p className="muted" style={{ marginTop: 6 }}>
            Melhor resultado: foto nítida, bem iluminada, <b>um</b> rosto de
            frente, testa e cabelo visíveis. Evite close de cima, de lado ou
            rosto tapado. Travamos o rosto da foto no personagem — o mesmo
            rosto, cabelo e idade em todas as páginas e no vídeo. Pose,
            expressão e roupa da história podem mudar. Página que não parecer
            a mesma criança não é publicada.
          </p>

          <h3 className="field-label">Personagens Extras (amigos, irmãos, etc.)</h3>
          <div className="upload">
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setExtraCharFile(e.target.files?.[0] ?? null)}
            />
            <input
              value={extraCharName}
              onChange={(e) => setExtraCharName(e.target.value)}
              placeholder="Nome do personagem"
              maxLength={40}
              style={{ flex: 1, minWidth: 120 }}
            />
            <button disabled={!extraCharFile || locked || !mediaConsent} onClick={uploadExtraCharacter}>
              Adicionar
            </button>
          </div>
          {extraChars.length > 0 && (
            <div style={{ margin: "8px 0" }}>
              <p className="muted">{extraChars.length} personagem(ns) extra(s) adicionado(s)</p>
              <button disabled={locked} onClick={generateExtraCharacters}>
                Gerar ilustrações dos extras <span className="muted">(1 crédito cada)</span>
              </button>
            </div>
          )}

          <h3 className="field-label">História</h3>
          <div className="styles">
            <button
              className={`chip ${storyMode === "invent" ? "on" : ""}`}
              onClick={() => setStoryMode("invent")}
            >
              ✨ Inventar com IA
            </button>
            <button
              className={`chip ${storyMode === "write" ? "on" : ""}`}
              onClick={() => setStoryMode("write")}
            >
              ✍️ Escrever a minha
            </button>
            <button
              className={`chip ${storyMode === "file" ? "on" : ""}`}
              onClick={() => setStoryMode("file")}
            >
              📄 Enviar arquivo
            </button>
            <button
              className={`chip ${storyMode === "catalog" ? "on" : ""}`}
              onClick={openCatalog}
            >
              📚 Histórias prontas
            </button>
          </div>

          {storyMode === "invent" && (
            <button disabled={locked} onClick={() => runStep("story")}>
              Gerar história com IA <span className="muted">(1 crédito)</span>
            </button>
          )}

          {storyMode === "catalog" && (
            <div className="story-catalog">
              {!templates && <p className="muted">Carregando catálogo…</p>}
              {templates && !project?.child_name && (
                <p className="muted">
                  Defina o nome da criança ao criar o projeto — ele entra no título e no texto.
                </p>
              )}
              {templates?.map((t) => (
                <div
                  key={t.id}
                  className="catalog-item"
                  style={{
                    display: "flex", alignItems: "center", gap: 8,
                    padding: "8px 0", borderBottom: "1px solid var(--border, #333)",
                  }}
                >
                  <span style={{ fontSize: 22 }}>{t.emoji}</span>
                  <div style={{ flex: 1 }}>
                    <strong>
                      {t.titulo.replace("{NOME}", project?.child_name || "{nome}")}
                    </strong>
                    <div className="muted" style={{ fontSize: 12 }}>
                      {t.tematica} · {t.idade} anos · {t.paginas} páginas
                      {t.genero !== "unissex" ? ` · ${t.genero}` : ""}
                    </div>
                  </div>
                  <button
                    disabled={locked || !project}
                    onClick={() => applyTemplate(t.id)}
                  >
                    {appliedTemplate === t.id ? "✓ Aplicada" : "Usar"}
                    {appliedTemplate !== t.id && <span className="muted"> (grátis)</span>}
                  </button>
                </div>
              ))}
            </div>
          )}

          {storyMode === "file" && (
            <div className="upload">
              <input type="file" accept=".pdf,.doc,.docx,.txt" onChange={onStoryFile} />
              <span className="muted">PDF, DOCX ou TXT (até 5MB)</span>
            </div>
          )}

          {(storyMode === "write" || storyMode === "file") && (
            <div className="story-write">
              <textarea
                className="story-input"
                rows={8}
                style={{ width: "100%", boxSizing: "border-box", resize: "vertical" }}
                placeholder="Escreva ou cole a sua história aqui. Dica: separe as páginas com 'Página 1:', 'Página 2:'..."
                value={storyText}
                onChange={(e) => setStoryText(e.target.value)}
              />
              <button disabled={locked || !storyText.trim()} onClick={saveStory}>
                Salvar história
              </button>
            </div>
          )}

          <div className="result-block" style={{ marginBottom: 16 }}>
            <h3 className="field-label">Voz da narração</h3>
            {!customVoiceAvailable ? (
              <p className="muted">
                Voz personalizada indisponível (ElevenLabs não configurado). O vídeo narrado usará a
                narração padrão.
              </p>
            ) : (
              <>
                <p className="muted" style={{ marginBottom: 10 }}>
                  Envie 30–60s de fala clara (MP3, WAV ou M4A), sem música de fundo. Fale naturalmente,
                  como se estivesse contando uma história. A voz fica salva e pode ser reutilizada.
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
                  <input
                    type="text"
                    value={voiceName}
                    onChange={(e) => setVoiceName(e.target.value)}
                    placeholder="Nome da voz"
                  />
                  <label className="btn" style={{ cursor: voiceUploading ? "wait" : "pointer" }}>
                    {voiceUploading ? "Clonando..." : "Enviar áudio"}
                    <input
                      type="file"
                      accept="audio/mpeg,audio/wav,audio/mp4,audio/x-m4a,audio/webm,audio/ogg,.mp3,.wav,.m4a,.webm,.ogg"
                      hidden
                      disabled={voiceUploading || locked || !mediaConsent}
                      onChange={(e) => onVoiceFile(e.target.files?.[0] || null)}
                    />
                  </label>
                </div>
                {voices.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
                    <select
                      value={selectedVoiceId}
                      onChange={(e) => setSelectedVoiceId(e.target.value)}
                      disabled={locked}
                    >
                      <option value="">Automática (padrão da conta ou sistema)</option>
                      {voices.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.name}
                          {v.is_default ? " (padrão)" : ""}
                        </option>
                      ))}
                    </select>
                    {selectedVoiceId && (
                      <button type="button" disabled={locked} onClick={removeSelectedVoice}>
                        Remover voz
                      </button>
                    )}
                  </div>
                )}
              </>
            )}
          </div>

          <div className="steps">
            {STEPS.filter((s) => s.key === "ebook").map((s) => (
              <button
                key={s.key}
                title={s.hint}
                disabled={locked || !canMountEbook}
                onClick={() => runStep(s.key)}
              >
                {s.label} <span className="muted">({s.cost})</span>
              </button>
            ))}
          </div>
          {!characterApproved && photoUploaded && (
            <p className="muted">Aprove o personagem para montar o e-book.</p>
          )}

          <ProgressList jobs={jobs} />

          {/* Resultado de cada etapa */}
          <div className="results">
            {assets?.character_url && (
              <div className="result-block">
                <h3 className="field-label">Personagem</h3>
                <img
                  src={assets.character_url}
                  alt="Personagem gerado"
                  style={{ maxWidth: 280, width: "100%", borderRadius: 12 }}
                />
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
                  {characterApproved ? (
                    <p className="muted">Personagem aprovado. Pode montar o livro.</p>
                  ) : (
                    <button disabled={locked} onClick={approveCharacter}>
                      Aprovar personagem
                    </button>
                  )}
                  <button disabled={locked} onClick={() => runStep("avatar")}>
                    Regenerar personagem <span className="muted">(1 crédito)</span>
                  </button>
                </div>
              </div>
            )}

            {assets?.extra_characters && assets.extra_characters.length > 0 && (
              <div className="result-block">
                <h3 className="field-label">Personagens Extras</h3>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  {assets.extra_characters.map((ec, i) => (
                    <div key={i} style={{ textAlign: "center" }}>
                      <img
                        src={ec.url}
                        alt={ec.name}
                        style={{ width: 100, height: 100, objectFit: "cover", borderRadius: 50 }}
                      />
                      <p className="muted" style={{ margin: "4px 0 0" }}>{ec.name}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {project.story_text && (
              <div className="result-block">
                <h3 className="field-label">História</h3>
                <pre className="story" style={{ whiteSpace: "pre-wrap" }}>{project.story_text}</pre>
              </div>
            )}

            {(assets?.ebook_url || (assets?.page_images?.length ?? 0) > 0) && (
              <div className="result-block">
                <h3 className="field-label">E-book</h3>
                {(assets?.page_images?.length ?? 0) > 0 && (
                  <div
                    style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 10 }}
                  >
                    {assets!.page_images.map((u, i) => (
                      <img
                        key={i}
                        src={u}
                        alt={`Página ${i + 1}`}
                        style={{ width: 120, height: 120, objectFit: "cover", borderRadius: 8 }}
                      />
                    ))}
                  </div>
                )}
                {assets?.ebook_url && (
                  <a href={assets.ebook_url} target="_blank" rel="noreferrer" className="btn">
                    📖 Abrir e-book
                  </a>
                )}
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
                  {bookApproved ? (
                    <p className="muted">Livro aprovado. PDF, impressão e vídeo liberados.</p>
                  ) : (
                    <button disabled={locked || !assets?.ebook_url} onClick={approveBook}>
                      Aprovar livro
                    </button>
                  )}
                  <button disabled={locked || !canMountEbook} onClick={() => runStep("ebook")}>
                    Regenerar páginas <span className="muted">(1 crédito)</span>
                  </button>
                </div>
                {bookApproved && (
                  <div style={{ marginTop: 12 }}>
                    <h3 className="field-label">Livro impresso</h3>
                    {printRequested ? (
                      <p className="muted">
                        Pedido registrado — em até 24h enviamos a cotação e o prazo.
                      </p>
                    ) : (
                      <button disabled={locked} onClick={requestPrint}>
                        Pedir livro impresso
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}

            {bookApproved && (
              <div className="result-block">
                <h3 className="field-label">Vídeo</h3>
                <p className="muted">O clipe e o vídeo narrado usam o personagem travado do livro — o mesmo rosto das páginas.</p>
                <div className="steps">
                  {STEPS.filter((s) => s.key !== "ebook").map((s) => (
                    <button
                      key={s.key}
                      title={s.hint}
                      disabled={locked || !canMakeVideo}
                      onClick={() => runStep(s.key)}
                    >
                      {s.label} <span className="muted">({s.cost})</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {assets?.video_url && (
              <div className="result-block">
                <h3 className="field-label">Animação</h3>
                {assets.video_url.toLowerCase().includes(".gif") ? (
                  <img
                    src={assets.video_url}
                    alt="Animação"
                    style={{ maxWidth: 360, width: "100%", borderRadius: 12 }}
                  />
                ) : (
                  <video src={assets.video_url} controls style={{ maxWidth: 360, width: "100%" }} />
                )}
              </div>
            )}

            {assets?.narrated_video_url && (
              <div className="result-block">
                <h3 className="field-label">Vídeo narrado</h3>
                {assets.narrated_video_url.toLowerCase().includes(".gif") ? (
                  <img
                    src={assets.narrated_video_url}
                    alt="Vídeo narrado"
                    style={{ maxWidth: 360, width: "100%", borderRadius: 12 }}
                  />
                ) : (
                  <video
                    src={assets.narrated_video_url}
                    controls
                    style={{ maxWidth: 360, width: "100%" }}
                  />
                )}
              </div>
            )}
          </div>

          <button className="link" onClick={() => (isDemo ? exitDemo() : setProject(null))}>
            {isDemo ? "← Criar a minha história" : "← Novo projeto"}
          </button>
        </section>
      )}
    </div>
  );
}

function ProgressList({ jobs }: { jobs: Job[] }) {
  if (jobs.length === 0) return null;
  return (
    <ul className="jobs">
      {jobs.map((j) => (
        <li key={j.id} className={`job ${j.status.toLowerCase()}`}>
          <span className="dot" />
          <span className="jtype">{j.type}</span>
          <span className="jstatus">{j.status}</span>
          {j.attempts > 1 && <span className="muted">tent. {j.attempts}</span>}
          {j.error && <span className="error">{j.error}</span>}
        </li>
      ))}
    </ul>
  );
}

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { ExtraCharacter, Job, Project, Style, Theme } from "./types";
import logo from "./assets/logo.png";

const STYLES: { id: Style; label: string }[] = [
  { id: "realistic", label: "Realista" },
  { id: "cartoon", label: "Desenho" },
  { id: "anime", label: "Animação" },
];

// Temas narrativos do briefing — a história nasce ao redor do tema escolhido.
const THEMES: { id: Theme; label: string; emoji: string }[] = [
  // Aventura e fantasia
  { id: "adventure", label: "Aventura", emoji: "🗺️" },
  { id: "princess", label: "Princesas", emoji: "👑" },
  { id: "superhero", label: "Super-heróis", emoji: "🦸" },
  { id: "space", label: "Espaço", emoji: "🚀" },
  { id: "underwater", label: "Fundo do mar", emoji: "🐠" },
  { id: "dinosaurs", label: "Dinossauros", emoji: "🦕" },
  { id: "fantasy", label: "Fantasia", emoji: "🧚" },
  // Datas comemorativas
  { id: "birthday", label: "Aniversário", emoji: "🎂" },
  { id: "christmas", label: "Natal", emoji: "🎄" },
  { id: "easter", label: "Páscoa", emoji: "🐣" },
  { id: "childrens_day", label: "Dia das Crianças", emoji: "🎈" },
  { id: "mothers_day", label: "Dia das Mães", emoji: "💐" },
  { id: "fathers_day", label: "Dia dos Pais", emoji: "👔" },
  { id: "new_year", label: "Ano Novo", emoji: "🎉" },
];
const themeLabel = (id: string | null | undefined) =>
  THEMES.find((t) => t.id === id)?.label ?? "—";

// O personagem é gerado automaticamente ao enviar a foto, e a história tem
// seção própria. Aqui ficam as etapas finais (dependem de personagem + história).
const STEPS: { key: "ebook" | "video"; label: string; cost: string; hint: string }[] = [
  { key: "ebook", label: "Montar ebook", cost: "1 crédito", hint: "E-book ilustrado (precisa de personagem + história)." },
  { key: "video", label: "Gerar vídeo", cost: "5 créditos", hint: "Vídeo narrado (precisa de personagem + história)." },
];

type StoryMode = "invent" | "write" | "file";

const HOW = [
  "Envie uma foto do protagonista.",
  "Escolha o tema e o estilo da arte.",
  "A IA cria ilustrações personalizadas.",
  "Receba um e-book exclusivo.",
  "Ganhe também um vídeo narrado.",
  "Um produto único, feito só para você.",
];

export function Studio({ onLogout }: { onLogout?: () => void }) {
  const [credits, setCredits] = useState<number | null>(null);
  const [style, setStyle] = useState<Style>("realistic");
  const [theme, setTheme] = useState<Theme>("adventure");
  const [project, setProject] = useState<Project | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoUploaded, setPhotoUploaded] = useState(false);
  const [extraChars, setExtraChars] = useState<ExtraCharacter[]>([]);
  const [extraCharFile, setExtraCharFile] = useState<File | null>(null);
  const [extraCharName, setExtraCharName] = useState("");
  const [storyMode, setStoryMode] = useState<StoryMode>("invent");
  const [storyText, setStoryText] = useState("");
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
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  // aplica o tema (claro/escuro) salvo na landing
  useEffect(() => {
    try {
      const s = localStorage.getItem("theme");
      document.documentElement.setAttribute("data-theme", s === "light" ? "light" : "dark");
    } catch { /* ignore */ }
  }, []);

  // pré-seleciona o tema da história vindo do catálogo (/app?tema=...)
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("tema");
    if (q && THEMES.some((x) => x.id === q)) setTheme(q as Theme);
  }, []);
  const [busy, setBusy] = useState(false);
  const pollRef = useRef<number | null>(null);

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

  // Polling do estado enquanto houver job ativo.
  useEffect(() => {
    if (!project) return;
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
  }, [project, jobs, refreshCredits]);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const age = childAge.trim() === "" ? undefined : Number(childAge);
      const p = await api.createProject(style, theme, childName, dedication, age);
      setProject(p);
      setJobs([]);
      setPhotoUploaded(false);
      setAssets(null);
      setStoryText("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function upload() {
    if (!project || !photo) return;
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

  async function runStep(step: "avatar" | "realistic" | "story" | "ebook" | "video") {
    if (!project) return;
    setBusy(true);
    setError(null);
    try {
      await api.startStep(project.id, step, step === "video" ? { duration_s: 30 } : {});
      const js = await api.listJobs(project.id);
      setJobs(js);
      refreshCredits();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  // Salva a história escrita/colada pelo usuário (sem IA).
  async function saveStory() {
    if (!project || !storyText.trim()) return;
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

  // Extrai o texto de um arquivo enviado e mostra para o usuário revisar.
  async function onStoryFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !project) return;
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
    if (!project || !extraCharFile) return;
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
    if (!project) return;
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

      {error && <p className="error">{error}</p>}

      {!project ? (
        <section className="card">
          <h2>Crie a sua história</h2>
          <p className="slogan">Toda história merece um protagonista — e o protagonista é você.</p>

          <h3 className="field-label">1 · Escolha o tema da aventura</h3>
          <div className="styles">
            {THEMES.filter((t) => !["birthday", "christmas", "easter", "childrens_day", "mothers_day", "fathers_day", "new_year"].includes(t.id)).map((t) => (
              <button
                key={t.id}
                className={`chip ${theme === t.id ? "on" : ""}`}
                onClick={() => setTheme(t.id)}
              >
                {t.emoji} {t.label}
              </button>
            ))}
          </div>

          <h3 className="field-label">Datas comemorativas</h3>
          <div className="styles">
            {THEMES.filter((t) => ["birthday", "christmas", "easter", "childrens_day", "mothers_day", "fathers_day", "new_year"].includes(t.id)).map((t) => (
              <button
                key={t.id}
                className={`chip ${theme === t.id ? "on" : ""}`}
                onClick={() => setTheme(t.id)}
              >
                {t.emoji} {t.label}
              </button>
            ))}
          </div>

          <h3 className="field-label">2 · Escolha o estilo da arte</h3>
          <div className="styles">
            {STYLES.map((s) => (
              <button
                key={s.id}
                className={`chip ${style === s.id ? "on" : ""}`}
                onClick={() => setStyle(s.id)}
              >
                {s.label}
              </button>
            ))}
          </div>

          <h3 className="field-label">3 · Nome, idade e dedicatória</h3>
          <label>
            Nome da criança
            <input
              value={childName}
              onChange={(e) => setChildName(e.target.value)}
              placeholder="Ex.: Lila"
              maxLength={80}
            />
          </label>
          <label>
            Idade da criança (a história é adaptada ao tom e vocabulário da idade)
            <input
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
              value={dedication}
              onChange={(e) => setDedication(e.target.value)}
              placeholder="Ex.: Para a Lila, com todo o amor da mamãe."
              maxLength={200}
            />
          </label>

          <button disabled={busy} onClick={start}>
            Criar projeto
          </button>

          <div className="how">
            <h3 className="field-label">Como funciona</h3>
            <ol>
              {HOW.map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ol>
          </div>
        </section>
      ) : (
        <section className="card">
          <h2>Projeto</h2>
          <p className="muted">
            Tema: <b>{themeLabel(project.theme ?? theme)}</b> · Estilo: <b>{project.style}</b> ·
            Status: <b>{project.status}</b>
          </p>

          <div className="upload">
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setPhoto(e.target.files?.[0] ?? null)}
            />
            <button disabled={!photo || busy} onClick={upload}>
              {photoUploaded ? "Foto enviada ✓" : "Enviar foto"}
            </button>
          </div>

          {photoUploaded && (
            <div style={{ margin: "8px 0" }}>
              <button disabled={busy} onClick={() => runStep("realistic")}>
                ✨ Gerar imagem realística{" "}
                <span className="muted">(referência do vídeo · 1 crédito)</span>
              </button>
            </div>
          )}

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
            <button disabled={!extraCharFile || busy} onClick={uploadExtraCharacter}>
              Adicionar
            </button>
          </div>
          {extraChars.length > 0 && (
            <div style={{ margin: "8px 0" }}>
              <p className="muted">{extraChars.length} personagem(ns) extra(s) adicionado(s)</p>
              <button disabled={busy} onClick={generateExtraCharacters}>
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
          </div>

          {storyMode === "invent" && (
            <button disabled={busy} onClick={() => runStep("story")}>
              Gerar história com IA <span className="muted">(1 crédito)</span>
            </button>
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
              <button disabled={busy || !storyText.trim()} onClick={saveStory}>
                Salvar história
              </button>
            </div>
          )}

          <div className="steps">
            {STEPS.map((s) => (
              <button
                key={s.key}
                title={s.hint}
                disabled={busy || !photoUploaded || !project.story_text}
                onClick={() => runStep(s.key)}
              >
                {s.label} <span className="muted">({s.cost})</span>
              </button>
            ))}
          </div>

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

            {assets?.realistic_url && (
              <div className="result-block">
                <h3 className="field-label">Imagem realística (referência do vídeo)</h3>
                <img
                  src={assets.realistic_url}
                  alt="Imagem realística"
                  style={{ maxWidth: 280, width: "100%", borderRadius: 12 }}
                />
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
              </div>
            )}

            {assets?.video_url && (
              <div className="result-block">
                <h3 className="field-label">Vídeo</h3>
                {assets.video_url.toLowerCase().includes(".gif") ? (
                  <img
                    src={assets.video_url}
                    alt="Vídeo fallback animado"
                    style={{ maxWidth: 360, width: "100%", borderRadius: 12 }}
                  />
                ) : (
                  <video src={assets.video_url} controls style={{ maxWidth: 360, width: "100%" }} />
                )}
              </div>
            )}
          </div>

          <button className="link" onClick={() => setProject(null)}>
            ← Novo projeto
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

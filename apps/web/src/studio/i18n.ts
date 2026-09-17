import type { Theme } from "../types";
import type { Lang } from "../i18n/lang";

export type StudioCopy = {
  themeToggleAria: string;
  theme: string;
  credits: string;
  logout: string;
  upgradeOpen: string;
  upgradeTitle: string;
  upgradeHint: string;
  upgradeEmail: string;
  upgradePassword: string;
  upgradeSubmit: string;
  upgradeSaving: string;
  upgradeLater: string;
  demoBanner: string;
  demoCta: string;
  createTitle: string;
  projectLocked: string;
  slogan: string;
  pickThemes: string;
  pickThemesHint: string;
  groupDatas: string;
  groupEducativo: string;
  nameAgeDedication: string;
  childName: string;
  childNamePh: string;
  childAge: string;
  childAgePh: string;
  dedication: string;
  dedicationPh: string;
  createProject: string;
  howTitle: string;
  how: string[];
  projectTitle: string;
  metaTheme: string;
  styleLabel: string;
  statusLabel: string;
  artStyleRealistic: string;
  defaultVoiceName: string;
  consent: string;
  photoSent: string;
  sendPhoto: string;
  photoHint: string;
  extraCharsTitle: string;
  extraCharNamePh: string;
  add: string;
  extrasAdded: (n: number) => string;
  generateExtras: string;
  creditEach: string;
  storyTitle: string;
  inventAi: string;
  writeMine: string;
  sendFile: string;
  readyStories: string;
  generateStory: string;
  oneCredit: string;
  loadingCatalog: string;
  needChildName: string;
  catalogMeta: (tematica: string, idade: string, paginas: number, genero?: string) => string;
  applied: string;
  use: string;
  free: string;
  fileHint: string;
  storyPlaceholder: string;
  saveStory: string;
  approveCharacterFirst: string;
  extrasResult: string;
  videoTitle: string;
  videoHint: string;
  animationTitle: string;
  narratedTitle: string;
  newProject: string;
  createMyStory: string;
  errConsentPhoto: string;
  errConsentExtra: string;
  errConsentVoice: string;
  langAria: string;
  ariaPhotoGroup: string;
  ariaSelectPhoto: string;
  ariaSelectExtraPhoto: string;
  ariaExtraCharName: string;
  ariaCatalog: string;
  ariaStoryFile: string;
  ariaStoryText: string;
  ariaResults: string;
  ariaAnimationGenerated: string;
  ariaNarratedGenerated: string;
  ariaCharacterActions: string;
  ariaEbookPages: string;
  ariaBookActions: string;
  ariaVoiceName: string;
  ariaSendAudioClone: string;
  ariaSelectVoice: string;
  ariaProgress: string;
  ariaEbookStep: string;
  ariaVideoSteps: string;
  voiceTitle: string;
  voiceUnavailable: string;
  voiceHint: string;
  voiceNamePh: string;
  cloning: string;
  sendAudio: string;
  voiceAuto: string;
  voiceDefault: string;
  removeVoice: string;
  character: string;
  characterAlt: string;
  characterApproved: string;
  approveCharacter: string;
  regenerateCharacter: string;
  ebook: string;
  pageAlt: (n: number) => string;
  openEbook: string;
  bookApproved: string;
  approveBook: string;
  regeneratePages: string;
  printTitle: string;
  printRequested: string;
  requestPrint: string;
  illustrating: (done: number, total: number) => string;
  attempt: string;
  stepEbook: string;
  stepEbookCost: string;
  stepEbookHint: string;
  stepVideo: string;
  stepVideoCost: string;
  stepVideoHint: string;
  stepNarrated: string;
  stepNarratedCost: string;
  stepNarratedHint: string;
  themes: Record<Theme, string>;
};

const THEMES_PT: Record<Theme, string> = {
  adventure: "Aventura",
  princess: "Princesas",
  superhero: "Super-heróis",
  space: "Espaço",
  underwater: "Fundo do mar",
  dinosaurs: "Dinossauros",
  fantasy: "Fantasia",
  birthday: "Aniversário",
  christmas: "Natal",
  easter: "Páscoa",
  childrens_day: "Dia das Crianças",
  mothers_day: "Dia das Mães",
  fathers_day: "Dia dos Pais",
  new_year: "Ano Novo",
  alfabetizacao_inicial: "Alfabetização",
  pensamento_matematico: "Matemática",
  cores: "Cores",
  opostos_espacial: "Opostos",
  higiene_desfralde: "Higiene",
  rotina_dormir: "Hora de Dormir",
  alimentacao_saudavel: "Alimentação",
  vestir_autonomia: "Vestir-se Sozinho",
  literacia_emocional: "Sentimentos",
  consciencia_corporal: "Corpo",
  compartilhar_revezar: "Compartilhar",
  animais_sons: "Animais e Sons",
  transporte_ajudantes: "Transporte",
  clima_estacoes: "Clima e Estações",
};

const THEMES_EN: Record<Theme, string> = {
  adventure: "Adventure",
  princess: "Princesses",
  superhero: "Superheroes",
  space: "Space",
  underwater: "Under the sea",
  dinosaurs: "Dinosaurs",
  fantasy: "Fantasy",
  birthday: "Birthday",
  christmas: "Christmas",
  easter: "Easter",
  childrens_day: "Children's Day",
  mothers_day: "Mother's Day",
  fathers_day: "Father's Day",
  new_year: "New Year",
  alfabetizacao_inicial: "Literacy",
  pensamento_matematico: "Math",
  cores: "Colors",
  opostos_espacial: "Opposites",
  higiene_desfralde: "Hygiene",
  rotina_dormir: "Bedtime",
  alimentacao_saudavel: "Healthy eating",
  vestir_autonomia: "Getting dressed",
  literacia_emocional: "Feelings",
  consciencia_corporal: "Body",
  compartilhar_revezar: "Sharing",
  animais_sons: "Animals and sounds",
  transporte_ajudantes: "Transport",
  clima_estacoes: "Weather and seasons",
};

const THEMES_ES: Record<Theme, string> = {
  adventure: "Aventura",
  princess: "Princesas",
  superhero: "Superhéroes",
  space: "Espacio",
  underwater: "Fondo del mar",
  dinosaurs: "Dinosaurios",
  fantasy: "Fantasía",
  birthday: "Cumpleaños",
  christmas: "Navidad",
  easter: "Pascua",
  childrens_day: "Día del Niño",
  mothers_day: "Día de la Madre",
  fathers_day: "Día del Padre",
  new_year: "Año Nuevo",
  alfabetizacao_inicial: "Alfabetización",
  pensamento_matematico: "Matemáticas",
  cores: "Colores",
  opostos_espacial: "Opuestos",
  higiene_desfralde: "Higiene",
  rotina_dormir: "Hora de dormir",
  alimentacao_saudavel: "Alimentación",
  vestir_autonomia: "Vestirse solo",
  literacia_emocional: "Sentimientos",
  consciencia_corporal: "Cuerpo",
  compartilhar_revezar: "Compartir",
  animais_sons: "Animales y sonidos",
  transporte_ajudantes: "Transporte",
  clima_estacoes: "Clima y estaciones",
};

const pt: StudioCopy = {
  themeToggleAria: "Alternar tema claro/escuro",
  theme: "Tema",
  credits: "Créditos",
  logout: "Sair",
  upgradeOpen: "Criar conta",
  upgradeTitle: "Salvar esta sessão",
  upgradeHint:
    "Transforme o convidado em conta real. Seus projetos e créditos ficam no mesmo lugar.",
  upgradeEmail: "E-mail",
  upgradePassword: "Senha (mín. 8)",
  upgradeSubmit: "Criar conta",
  upgradeSaving: "Salvando…",
  upgradeLater: "Agora não",
  demoBanner: "Você está vendo um exemplo pronto.",
  demoCta: "Criar a minha história",
  createTitle: "Crie a sua história",
  projectLocked: "✓ Projeto criado — os campos abaixo ficam travados até você começar um novo projeto.",
  slogan: "Toda história merece um protagonista — e o protagonista é você.",
  pickThemes: "1 · Escolha até 2 temas para a aventura",
  pickThemesHint:
    "O 1º escolhido é o tema principal (define vilão, cenário e arco); o 2º só soma um aprendizado extra na mesma jornada.",
  groupDatas: "Datas comemorativas",
  groupEducativo: "Temas educativos",
  nameAgeDedication: "2 · Nome, idade e dedicatória",
  childName: "Nome da criança",
  childNamePh: "Ex.: Lila",
  childAge: "Idade da criança (a história é adaptada ao tom e vocabulário da idade)",
  childAgePh: "Ex.: 5",
  dedication: "Dedicatória (aparece na 2ª página do livro)",
  dedicationPh: "Ex.: Para a Lila, com todo o amor da mamãe.",
  createProject: "Criar projeto",
  howTitle: "Como funciona",
  how: [
    "Envie uma foto de frente (um rosto, luz boa).",
    "Aprove o personagem (rosto realista).",
    "Escolha o tema ou uma história pronta.",
    "Aprove o livro (capa e páginas).",
    "Baixe o PDF, peça o impresso ou gere o vídeo narrado.",
  ],
  projectTitle: "Projeto",
  metaTheme: "Tema",
  styleLabel: "Estilo",
  statusLabel: "Status",
  artStyleRealistic: "Rosto realista",
  defaultVoiceName: "Minha voz",
  consent:
    "Sou o responsável legal e autorizo o uso desta foto (e da voz, se clonar) só para criar este livro. Não usamos para divulgação.",
  photoSent: "Foto enviada ✓",
  sendPhoto: "Enviar foto",
  photoHint:
    "Melhor resultado: foto nítida, bem iluminada, um rosto de frente, testa e cabelo visíveis. Evite close de cima, de lado ou rosto tapado. A arte é fotográfica, com a criança igual à foto — o mesmo personagem nas páginas e no vídeo.",
  extraCharsTitle: "Personagens Extras (amigos, irmãos, etc.)",
  extraCharNamePh: "Nome do personagem",
  add: "Adicionar",
  extrasAdded: (n) => `${n} personagem(ns) extra(s) adicionado(s)`,
  generateExtras: "Gerar ilustrações dos extras",
  creditEach: "(1 crédito cada)",
  storyTitle: "História",
  inventAi: "✨ Inventar com IA",
  writeMine: "✍️ Escrever a minha",
  sendFile: "📄 Enviar arquivo",
  readyStories: "📚 Histórias prontas",
  generateStory: "Gerar história com IA",
  oneCredit: "(1 crédito)",
  loadingCatalog: "Carregando catálogo…",
  needChildName: "Defina o nome da criança ao criar o projeto — ele entra no título e no texto.",
  catalogMeta: (tematica, idade, paginas, genero) =>
    `${tematica} · ${idade} anos · ${paginas} páginas${genero && genero !== "unissex" ? ` · ${genero}` : ""}`,
  applied: "✓ Aplicada",
  use: "Usar",
  free: " (grátis)",
  fileHint: "PDF, DOCX ou TXT (até 5MB)",
  storyPlaceholder:
    "Escreva ou cole a sua história aqui. Dica: separe as páginas com 'Página 1:', 'Página 2:'...",
  saveStory: "Salvar história",
  approveCharacterFirst: "Aprove o personagem para montar o e-book.",
  extrasResult: "Personagens Extras",
  videoTitle: "Vídeo",
  videoHint: "O clipe e o vídeo narrado usam o mesmo personagem 3D do livro.",
  animationTitle: "Animação",
  narratedTitle: "Vídeo narrado",
  newProject: "← Novo projeto",
  createMyStory: "← Criar a minha história",
  errConsentPhoto: "Marque o consentimento para enviar a foto.",
  errConsentExtra: "Marque o consentimento para enviar a foto do personagem extra.",
  errConsentVoice: "Marque o consentimento para clonar a voz.",
  langAria: "Idioma / Language / Idioma",
  ariaPhotoGroup: "Foto do protagonista",
  ariaSelectPhoto: "Selecionar foto do protagonista",
  ariaSelectExtraPhoto: "Selecionar foto do personagem extra",
  ariaExtraCharName: "Nome do personagem extra",
  ariaCatalog: "Catálogo de histórias prontas",
  ariaStoryFile: "Enviar arquivo de história (PDF, DOCX ou TXT)",
  ariaStoryText: "Texto da história",
  ariaResults: "Resultados do projeto",
  ariaAnimationGenerated: "Animação gerada",
  ariaNarratedGenerated: "Vídeo narrado gerado",
  ariaCharacterActions: "Ações do personagem",
  ariaEbookPages: "Páginas do e-book",
  ariaBookActions: "Ações do livro",
  ariaVoiceName: "Nome da voz",
  ariaSendAudioClone: "Enviar áudio para clonar voz",
  ariaSelectVoice: "Selecionar voz da narração",
  ariaProgress: "Progresso das etapas",
  ariaEbookStep: "Etapa do e-book",
  ariaVideoSteps: "Etapas de vídeo",
  voiceTitle: "Voz da narração",
  voiceUnavailable:
    "Voz personalizada indisponível (ElevenLabs não configurado). O vídeo narrado usará a narração padrão.",
  voiceHint:
    "Envie 30–60s de fala clara (MP3, WAV ou M4A), sem música de fundo. Fale naturalmente, como se estivesse contando uma história. A voz fica salva e pode ser reutilizada.",
  voiceNamePh: "Nome da voz",
  cloning: "Clonando...",
  sendAudio: "Enviar áudio",
  voiceAuto: "Automática (padrão da conta ou sistema)",
  voiceDefault: " (padrão)",
  removeVoice: "Remover voz",
  character: "Personagem",
  characterAlt: "Personagem gerado",
  characterApproved: "Personagem aprovado. Pode montar o livro.",
  approveCharacter: "Aprovar personagem",
  regenerateCharacter: "Regenerar personagem",
  ebook: "E-book",
  pageAlt: (n) => `Página ${n}`,
  openEbook: "📖 Abrir e-book",
  bookApproved: "Livro aprovado. PDF, impressão e vídeo liberados.",
  approveBook: "Aprovar livro",
  regeneratePages: "Regenerar páginas",
  printTitle: "Livro impresso",
  printRequested: "Pedido registrado — em até 24h enviamos a cotação e o prazo.",
  requestPrint: "Pedir livro impresso",
  illustrating: (done, total) => `Ilustrando ${done}/${total}`,
  attempt: "tent.",
  stepEbook: "Montar ebook",
  stepEbookCost: "1 crédito",
  stepEbookHint: "E-book ilustrado (precisa de personagem aprovado + história).",
  stepVideo: "Gerar animação",
  stepVideoCost: "5 créditos",
  stepVideoHint: "Clipe curto (5–10s) com movimento — não é o vídeo narrado.",
  stepNarrated: "Gerar vídeo narrado",
  stepNarratedCost: "8 créditos",
  stepNarratedHint: "História com narração (~1–2 min) a partir do storyboard.",
  themes: THEMES_PT,
};

const en: StudioCopy = {
  themeToggleAria: "Toggle light/dark theme",
  theme: "Theme",
  credits: "Credits",
  logout: "Log out",
  upgradeOpen: "Create account",
  upgradeTitle: "Save this session",
  upgradeHint:
    "Turn the guest into a real account. Your projects and credits stay in the same place.",
  upgradeEmail: "Email",
  upgradePassword: "Password (min. 8)",
  upgradeSubmit: "Create account",
  upgradeSaving: "Saving…",
  upgradeLater: "Not now",
  demoBanner: "You are viewing a ready-made example.",
  demoCta: "Create my story",
  createTitle: "Create your story",
  projectLocked: "✓ Project created — the fields below stay locked until you start a new project.",
  slogan: "Every story needs a hero — and the hero is you.",
  pickThemes: "1 · Pick up to 2 themes for the adventure",
  pickThemesHint:
    "The 1st choice is the main theme (sets villain, setting, and arc); the 2nd only adds an extra learning goal in the same journey.",
  groupDatas: "Special occasions",
  groupEducativo: "Educational themes",
  nameAgeDedication: "2 · Name, age, and dedication",
  childName: "Child's name",
  childNamePh: "e.g. Lila",
  childAge: "Child's age (the story adapts tone and vocabulary)",
  childAgePh: "e.g. 5",
  dedication: "Dedication (appears on page 2 of the book)",
  dedicationPh: "e.g. For Lila, with all of Mom's love.",
  createProject: "Create project",
  howTitle: "How it works",
  how: [
    "Upload a front-facing photo (one face, good light).",
    "Approve the character (realistic face).",
    "Pick a theme or a ready-made story.",
    "Approve the book (cover and pages).",
    "Download the PDF, request print, or generate the narrated video.",
  ],
  projectTitle: "Project",
  metaTheme: "Theme",
  styleLabel: "Style",
  statusLabel: "Status",
  artStyleRealistic: "Realistic face",
  defaultVoiceName: "My voice",
  consent:
    "I am the legal guardian and authorize use of this photo (and voice, if cloned) only to create this book. We do not use it for marketing.",
  photoSent: "Photo uploaded ✓",
  sendPhoto: "Upload photo",
  photoHint:
    "Best result: sharp, well-lit photo, one front-facing face, forehead and hair visible. Avoid top-down close-ups, side angles, or covered faces. The art is photographic — the same character on pages and in the video.",
  extraCharsTitle: "Extra characters (friends, siblings, etc.)",
  extraCharNamePh: "Character name",
  add: "Add",
  extrasAdded: (n) => `${n} extra character(s) added`,
  generateExtras: "Generate extra illustrations",
  creditEach: "(1 credit each)",
  storyTitle: "Story",
  inventAi: "✨ Invent with AI",
  writeMine: "✍️ Write my own",
  sendFile: "📄 Upload file",
  readyStories: "📚 Ready-made stories",
  generateStory: "Generate story with AI",
  oneCredit: "(1 credit)",
  loadingCatalog: "Loading catalog…",
  needChildName: "Set the child's name when creating the project — it goes into the title and text.",
  catalogMeta: (tematica, idade, paginas, genero) =>
    `${tematica} · ages ${idade} · ${paginas} pages${genero && genero !== "unissex" ? ` · ${genero}` : ""}`,
  applied: "✓ Applied",
  use: "Use",
  free: " (free)",
  fileHint: "PDF, DOCX or TXT (up to 5MB)",
  storyPlaceholder:
    "Write or paste your story here. Tip: separate pages with 'Page 1:', 'Page 2:'...",
  saveStory: "Save story",
  approveCharacterFirst: "Approve the character to build the e-book.",
  extrasResult: "Extra characters",
  videoTitle: "Video",
  videoHint: "The clip and narrated video use the same 3D character from the book.",
  animationTitle: "Animation",
  narratedTitle: "Narrated video",
  newProject: "← New project",
  createMyStory: "← Create my story",
  errConsentPhoto: "Check the consent box to upload the photo.",
  errConsentExtra: "Check the consent box to upload the extra character photo.",
  errConsentVoice: "Check the consent box to clone the voice.",
  langAria: "Language / Idioma",
  ariaPhotoGroup: "Hero photo",
  ariaSelectPhoto: "Select hero photo",
  ariaSelectExtraPhoto: "Select extra character photo",
  ariaExtraCharName: "Extra character name",
  ariaCatalog: "Ready-made stories catalog",
  ariaStoryFile: "Upload story file (PDF, DOCX or TXT)",
  ariaStoryText: "Story text",
  ariaResults: "Project results",
  ariaAnimationGenerated: "Generated animation",
  ariaNarratedGenerated: "Generated narrated video",
  ariaCharacterActions: "Character actions",
  ariaEbookPages: "E-book pages",
  ariaBookActions: "Book actions",
  ariaVoiceName: "Voice name",
  ariaSendAudioClone: "Upload audio to clone voice",
  ariaSelectVoice: "Select narration voice",
  ariaProgress: "Step progress",
  ariaEbookStep: "E-book step",
  ariaVideoSteps: "Video steps",
  voiceTitle: "Narration voice",
  voiceUnavailable:
    "Custom voice unavailable (ElevenLabs not configured). Narrated video will use the default narration.",
  voiceHint:
    "Upload 30–60s of clear speech (MP3, WAV or M4A), no background music. Speak naturally, as if telling a story. The voice is saved and reusable.",
  voiceNamePh: "Voice name",
  cloning: "Cloning...",
  sendAudio: "Upload audio",
  voiceAuto: "Automatic (account or system default)",
  voiceDefault: " (default)",
  removeVoice: "Remove voice",
  character: "Character",
  characterAlt: "Generated character",
  characterApproved: "Character approved. You can build the book.",
  approveCharacter: "Approve character",
  regenerateCharacter: "Regenerate character",
  ebook: "E-book",
  pageAlt: (n) => `Page ${n}`,
  openEbook: "📖 Open e-book",
  bookApproved: "Book approved. PDF, print, and video unlocked.",
  approveBook: "Approve book",
  regeneratePages: "Regenerate pages",
  printTitle: "Printed book",
  printRequested: "Request logged — within 24h we send the quote and timeline.",
  requestPrint: "Request printed book",
  illustrating: (done, total) => `Illustrating ${done}/${total}`,
  attempt: "att.",
  stepEbook: "Build ebook",
  stepEbookCost: "1 credit",
  stepEbookHint: "Illustrated e-book (needs approved character + story).",
  stepVideo: "Generate animation",
  stepVideoCost: "5 credits",
  stepVideoHint: "Short clip (5–10s) with motion — not the narrated video.",
  stepNarrated: "Generate narrated video",
  stepNarratedCost: "8 credits",
  stepNarratedHint: "Story with narration (~1–2 min) from the storyboard.",
  themes: THEMES_EN,
};

const es: StudioCopy = {
  themeToggleAria: "Alternar tema claro/oscuro",
  theme: "Tema",
  credits: "Créditos",
  logout: "Salir",
  upgradeOpen: "Crear cuenta",
  upgradeTitle: "Guardar esta sesión",
  upgradeHint:
    "Convierte el invitado en una cuenta real. Tus proyectos y créditos se quedan en el mismo lugar.",
  upgradeEmail: "Correo",
  upgradePassword: "Contraseña (mín. 8)",
  upgradeSubmit: "Crear cuenta",
  upgradeSaving: "Guardando…",
  upgradeLater: "Ahora no",
  demoBanner: "Estás viendo un ejemplo listo.",
  demoCta: "Crear mi historia",
  createTitle: "Crea tu historia",
  projectLocked: "✓ Proyecto creado — los campos de abajo quedan bloqueados hasta que inicies un proyecto nuevo.",
  slogan: "Toda historia merece un protagonista — y el protagonista eres tú.",
  pickThemes: "1 · Elige hasta 2 temas para la aventura",
  pickThemesHint:
    "El 1.º elegido es el tema principal (define villano, escenario y arco); el 2.º solo suma un aprendizaje extra en el mismo viaje.",
  groupDatas: "Fechas especiales",
  groupEducativo: "Temas educativos",
  nameAgeDedication: "2 · Nombre, edad y dedicatoria",
  childName: "Nombre del niño/a",
  childNamePh: "Ej.: Lila",
  childAge: "Edad del niño/a (la historia adapta el tono y el vocabulario)",
  childAgePh: "Ej.: 5",
  dedication: "Dedicatoria (aparece en la 2.ª página del libro)",
  dedicationPh: "Ej.: Para Lila, con todo el amor de mamá.",
  createProject: "Crear proyecto",
  howTitle: "Cómo funciona",
  how: [
    "Envía una foto de frente (un rostro, buena luz).",
    "Aprueba el personaje (rostro realista).",
    "Elige el tema o una historia lista.",
    "Aprueba el libro (portada y páginas).",
    "Descarga el PDF, pide el impreso o genera el video narrado.",
  ],
  projectTitle: "Proyecto",
  metaTheme: "Tema",
  styleLabel: "Estilo",
  statusLabel: "Estado",
  artStyleRealistic: "Rostro realista",
  defaultVoiceName: "Mi voz",
  consent:
    "Soy el responsable legal y autorizo el uso de esta foto (y de la voz, si se clona) solo para crear este libro. No la usamos para difusión.",
  photoSent: "Foto enviada ✓",
  sendPhoto: "Enviar foto",
  photoHint:
    "Mejor resultado: foto nítida, bien iluminada, un rostro de frente, frente y cabello visibles. Evita close desde arriba, de lado o rostro tapado. El arte es fotográfico, con el niño/a igual a la foto — el mismo personaje en las páginas y en el video.",
  extraCharsTitle: "Personajes extras (amigos, hermanos, etc.)",
  extraCharNamePh: "Nombre del personaje",
  add: "Añadir",
  extrasAdded: (n) => `${n} personaje(s) extra(s) añadido(s)`,
  generateExtras: "Generar ilustraciones de los extras",
  creditEach: "(1 crédito cada uno)",
  storyTitle: "Historia",
  inventAi: "✨ Inventar con IA",
  writeMine: "✍️ Escribir la mía",
  sendFile: "📄 Enviar archivo",
  readyStories: "📚 Historias listas",
  generateStory: "Generar historia con IA",
  oneCredit: "(1 crédito)",
  loadingCatalog: "Cargando catálogo…",
  needChildName: "Define el nombre del niño/a al crear el proyecto — entra en el título y el texto.",
  catalogMeta: (tematica, idade, paginas, genero) =>
    `${tematica} · ${idade} años · ${paginas} páginas${genero && genero !== "unissex" ? ` · ${genero}` : ""}`,
  applied: "✓ Aplicada",
  use: "Usar",
  free: " (gratis)",
  fileHint: "PDF, DOCX o TXT (hasta 5MB)",
  storyPlaceholder:
    "Escribe o pega tu historia aquí. Consejo: separa las páginas con 'Página 1:', 'Página 2:'...",
  saveStory: "Guardar historia",
  approveCharacterFirst: "Aprueba el personaje para montar el e-book.",
  extrasResult: "Personajes extras",
  videoTitle: "Video",
  videoHint: "El clip y el video narrado usan el mismo personaje 3D del libro.",
  animationTitle: "Animación",
  narratedTitle: "Video narrado",
  newProject: "← Nuevo proyecto",
  createMyStory: "← Crear mi historia",
  errConsentPhoto: "Marca el consentimiento para enviar la foto.",
  errConsentExtra: "Marca el consentimiento para enviar la foto del personaje extra.",
  errConsentVoice: "Marca el consentimiento para clonar la voz.",
  langAria: "Idioma / Language",
  ariaPhotoGroup: "Foto del protagonista",
  ariaSelectPhoto: "Seleccionar foto del protagonista",
  ariaSelectExtraPhoto: "Seleccionar foto del personaje extra",
  ariaExtraCharName: "Nombre del personaje extra",
  ariaCatalog: "Catálogo de historias listas",
  ariaStoryFile: "Enviar archivo de historia (PDF, DOCX o TXT)",
  ariaStoryText: "Texto de la historia",
  ariaResults: "Resultados del proyecto",
  ariaAnimationGenerated: "Animación generada",
  ariaNarratedGenerated: "Video narrado generado",
  ariaCharacterActions: "Acciones del personaje",
  ariaEbookPages: "Páginas del e-book",
  ariaBookActions: "Acciones del libro",
  ariaVoiceName: "Nombre de la voz",
  ariaSendAudioClone: "Enviar audio para clonar voz",
  ariaSelectVoice: "Seleccionar voz de la narración",
  ariaProgress: "Progreso de las etapas",
  ariaEbookStep: "Etapa del e-book",
  ariaVideoSteps: "Etapas de video",
  voiceTitle: "Voz de la narración",
  voiceUnavailable:
    "Voz personalizada no disponible (ElevenLabs no configurado). El video narrado usará la narración predeterminada.",
  voiceHint:
    "Envía 30–60s de habla clara (MP3, WAV o M4A), sin música de fondo. Habla con naturalidad, como si contaras una historia. La voz se guarda y se puede reutilizar.",
  voiceNamePh: "Nombre de la voz",
  cloning: "Clonando...",
  sendAudio: "Enviar audio",
  voiceAuto: "Automática (predeterminada de la cuenta o del sistema)",
  voiceDefault: " (predeterminada)",
  removeVoice: "Quitar voz",
  character: "Personaje",
  characterAlt: "Personaje generado",
  characterApproved: "Personaje aprobado. Puedes montar el libro.",
  approveCharacter: "Aprobar personaje",
  regenerateCharacter: "Regenerar personaje",
  ebook: "E-book",
  pageAlt: (n) => `Página ${n}`,
  openEbook: "📖 Abrir e-book",
  bookApproved: "Libro aprobado. PDF, impresión y video liberados.",
  approveBook: "Aprobar libro",
  regeneratePages: "Regenerar páginas",
  printTitle: "Libro impreso",
  printRequested: "Pedido registrado — en hasta 24h enviamos la cotización y el plazo.",
  requestPrint: "Pedir libro impreso",
  illustrating: (done, total) => `Ilustrando ${done}/${total}`,
  attempt: "int.",
  stepEbook: "Montar ebook",
  stepEbookCost: "1 crédito",
  stepEbookHint: "E-book ilustrado (necesita personaje aprobado + historia).",
  stepVideo: "Generar animación",
  stepVideoCost: "5 créditos",
  stepVideoHint: "Clip corto (5–10s) con movimiento — no es el video narrado.",
  stepNarrated: "Generar video narrado",
  stepNarratedCost: "8 créditos",
  stepNarratedHint: "Historia con narración (~1–2 min) a partir del storyboard.",
  themes: THEMES_ES,
};

export const STUDIO_I18N: Record<Lang, StudioCopy> = { pt, en, es };

export function studioCopy(lang: Lang): StudioCopy {
  return STUDIO_I18N[lang] ?? STUDIO_I18N.pt;
}

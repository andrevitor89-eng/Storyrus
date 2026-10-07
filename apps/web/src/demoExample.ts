import type { Project } from "./types";

const ex = (file: string) => `${import.meta.env.BASE_URL}exemplos/${file}`;

export const DEMO_EXAMPLE_ID = "dinosaurs";
export const DEMO_MEUPAI_ID = "meupai";

const DEMO_AT = "2026-01-01T00:00:00.000Z";

const DEMO_STORY = `Página 1: Matteo acordou com um rugido suave no quintal. Era um dinossauro amigo, com olhos gentis.
Página 2: Juntos atravessaram o vale escondido, onde os dinossauros brincavam entre as pedras quentes.
Página 3: Um filhote perdido chorava atrás de uma folha gigante. Matteo segurou a pata dele com cuidado.
Página 4: Seguindo pegadas na terra vermelha, acharam o ninho e a família que esperava.
Página 5: Na volta, o vale inteiro acompanhou Matteo até o portão de casa, em festa silenciosa.
Página 6: Na cama, Matteo sonhou de novo com o vale — e soube que a coragem mora perto de quem a gente ama.`;

const MEUPAI_STORY = `Capa: Meu Pai, Meu Herói!
Página 2: Para o papai que está sempre ao meu lado, com amor, carinho e um abraço apertado.
Página 3: Meu pai é meu herói, meu grande amigo, em cada aventura, está sempre comigo.
Página 4: No abraço do papai encontro proteção, um carinho gostoso que aquece o coração.
Página 5: Com papai, toda descoberta vira aprendizado, e cada momento se torna mais divertido.
Página 6: Com papai, toda brincadeira fica especial, corremos e sorrimos num dia sensacional.
Página 7: Se alguma coisa parece difícil para mim, papai me ajuda a tentar até o fim.
Página 8: Com muita paciência você me ensina, me explica com carinho e sempre me dá uma dica.
Página 9: Com papai, eu aprendo coisas novas, descubro meus talentos e ganho mais confiança.
Página 10: Você me incentiva a nunca desistir, e comemora comigo cada pequena conquista.
Página 11: Com seu amor, me sinto seguro, porque você sempre acredita em mim, hoje e no futuro.
Página 12: Eu te amo, papai! Obrigado por estar sempre ao meu lado. Você é o meu exemplo e o meu grande herói.
Página 13: Com você, eu aprendo, cresço e sou mais feliz. Você me ensina com carinho e sempre acredita em mim.
Página 14: Você me mostra um mundo incrível e sempre me guia para um futuro cheio de sonhos.
Página 15: Você me enche de alegria, papai, e eu sou muito grato por ter você sempre na minha vida.
Página 16: Eu te amo para sempre, papai! Você é o meu coração, a minha inspiração e a minha maior aventura.`;

const MEUPAI_PAGES = [
  "meupai-heroi/capa.png",
  "meupai-heroi/pagina-02.jpg",
  "meupai-heroi/pagina-03.jpg",
  "meupai-heroi/pagina-04.jpg",
  "meupai-heroi/pagina-05.jpg",
  "meupai-heroi/pagina-06.jpg",
  "meupai-heroi/pagina-07.jpg",
  "meupai-heroi/pagina-08.jpg",
  "meupai-heroi/pagina-09.jpg",
  "meupai-heroi/pagina-10.jpg",
  "meupai-heroi/pagina-11.jpg",
  "meupai-heroi/pagina-12.jpg",
  "meupai-heroi/pagina-13.jpg",
  "meupai-heroi/pagina-14.jpg",
  "meupai-heroi/pagina-15.jpg",
  "meupai-heroi/pagina-16.jpg",
  "meupai-heroi/contracapa.jpg",
];

export type DemoAssets = {
  character_url: string | null;
  realistic_url: string | null;
  extra_characters: { name: string; url: string }[];
  page_images: string[];
  ebook_url: string | null;
  video_url: string | null;
  narrated_video_url: string | null;
};

export type DemoExample = {
  project: Project;
  assets: DemoAssets;
  childName: string;
  childAge: string;
  dedication: string;
  bookTitle: string;
  themeText: string;
};

export function demoIdFromSearch(search = window.location.search): string | null {
  const id = new URLSearchParams(search).get("exemplo");
  if (id === DEMO_EXAMPLE_ID || id === "dino" || id === "matteo") return DEMO_EXAMPLE_ID;
  if (id === DEMO_MEUPAI_ID || id === "meu-pai" || id === "meupai-heroi") return DEMO_MEUPAI_ID;
  return null;
}

function dinosaursDemo(): DemoExample {
  return {
    childName: "Matteo",
    childAge: "5",
    dedication: "Para o Matteo, com amor.",
    bookTitle: "Matteo e o vale dos dinossauros",
    themeText: "Aventura com dinossauros amigáveis e coragem",
    project: {
      id: "demo-dinosaurs",
      status: "VIDEO_READY",
      style: "cgi_3d",
      theme: "dinosaurs",
      extra_theme: null,
      child_name: "Matteo",
      child_age: 5,
      dedication: "Para o Matteo, com amor.",
      language: "pt",
      extra_characters: [],
      story_text: DEMO_STORY,
      ebook_url: null,
      video_url: null,
      narrated_video_url: ex("video-dino.mp4"),
      character_approved_at: DEMO_AT,
      book_approved_at: DEMO_AT,
      print_requested_at: null,
      print_status: null,
      created_at: DEMO_AT,
    },
    assets: {
      character_url: ex("personagem-dino.jpg"),
      realistic_url: null,
      extra_characters: [],
      page_images: [
        ex("capa-dino2.jpg"),
        ex("dino-1.jpg"),
        ex("dino-3.jpg"),
        ex("dino-4.jpg"),
        ex("dino-5.jpg"),
        ex("dino-6.jpg"),
      ],
      ebook_url: null,
      video_url: null,
      narrated_video_url: ex("video-dino.mp4"),
    },
  };
}

function meupaiDemo(): DemoExample {
  return {
    childName: "Lucas",
    childAge: "2",
    dedication: "Para o papai, com todo o meu amor.",
    bookTitle: "Meu Pai, Meu Herói",
    themeText: "Papai herói: proteção, carinho e aventuras juntos",
    project: {
      id: "demo-meupai-heroi",
      status: "VIDEO_READY",
      style: "photoreal",
      theme: "fathers_day",
      extra_theme: null,
      child_name: "Lucas",
      child_age: 2,
      dedication: "Para o papai, com todo o meu amor.",
      language: "pt",
      extra_characters: [],
      story_text: MEUPAI_STORY,
      ebook_url: ex("ebook-meupai-heroi.pdf"),
      video_url: ex("video-meupai-heroi.mp4"),
      narrated_video_url: ex("video-meupai-heroi.mp4"),
      character_approved_at: DEMO_AT,
      book_approved_at: DEMO_AT,
      print_requested_at: null,
      print_status: null,
      created_at: DEMO_AT,
    },
    assets: {
      character_url: ex("foto-meupai-heroi.png"),
      realistic_url: ex("foto-meupai-heroi.png"),
      extra_characters: [],
      page_images: MEUPAI_PAGES.map(ex),
      ebook_url: ex("ebook-meupai-heroi.pdf"),
      video_url: ex("video-meupai-heroi.mp4"),
      narrated_video_url: ex("video-meupai-heroi.mp4"),
    },
  };
}

export function getDemoExample(search = window.location.search): DemoExample {
  const id = demoIdFromSearch(search);
  if (id === DEMO_MEUPAI_ID) return meupaiDemo();
  return dinosaursDemo();
}

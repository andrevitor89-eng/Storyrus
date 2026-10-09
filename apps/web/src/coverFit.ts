import type { CSSProperties } from "react";

/** Escala para a arte opaca preencher o quadrado. Capas full-bleed ficam em 1. */
const COVER_FIT: Record<string, readonly [number, number, number]> = {
  "capa-abigail-en.png": [1.105, 50.1, 49.6],
  "capa-abigail-es.png": [1.105, 50.1, 49.6],
  "capa-abigail.png": [1.099, 50.0, 49.6],
  "capa-amor-de-avo-en.png": [1.060, 49.8, 50.2],
  "capa-amor-de-avo.png": [1.058, 49.8, 50.2],
  "capa-bruno-animais-en.png": [1.027, 50.0, 49.9],
  "capa-bruno-animais-es.png": [1.027, 50.0, 49.9],
  "capa-bruno-animais.png": [1.027, 50.0, 49.9],
  "capa-construtor.png": [1.080, 50.2, 49.9],
  "capa-cristobal-esporte.png": [1.126, 50.1, 49.7],
  "capa-heroi-aranha-en.png": [1.060, 50.0, 50.0],
  "capa-heroi-aranha-es.png": [1.060, 50.0, 50.0],
  "capa-heroi-aranha.png": [1.060, 50.0, 50.0],
  "capa-heroi-bombeiro-en.png": [1.101, 48.6, 52.8],
  "capa-heroi-bombeiro-es.png": [1.101, 48.6, 52.2],
  "capa-heroi-bombeiro.png": [1.101, 48.6, 52.2],
  "capa-heroi-policia-en.png": [1.103, 50.1, 53.0],
  "capa-heroi-policia-es.png": [1.107, 50.1, 53.1],
  "capa-heroi-policia.png": [1.101, 49.9, 53.2],
  "capa-miriam-en.png": [1.045, 50.0, 48.2],
  "capa-miriam-es.png": [1.095, 50.0, 50.8],
  "capa-miriam.png": [1.095, 50.0, 50.8],
  "capa-nicolas-maefilho.png": [1.060, 49.9, 49.9],
  "capa-noe-en.png": [1.048, 50.1, 49.9],
  "capa-noe-es.png": [1.151, 50.0, 52.5],
  "capa-noe.png": [1.069, 49.9, 49.7],
  "capa-raquel-papai-en.png": [1.051, 49.9, 49.7],
  "capa-raquel-papai-es.png": [1.051, 49.9, 49.7],
  "capa-raquel-papai.png": [1.051, 49.9, 49.7],
  "capa-rebeca-en.png": [1.102, 50.3, 49.0],
  "capa-rebeca-es.png": [1.102, 50.3, 49.2],
  "capa-rebeca.png": [1.102, 50.3, 49.0],
  "capa-sofia-alfabeto.png": [1.259, 49.9, 49.4],
  "capa-tia-especial-en.png": [1.048, 50.1, 49.6],
  "capa-tia-especial-es.png": [1.048, 50.1, 49.6],
  "capa-tia-especial.png": [1.048, 50.1, 49.6],
  "cartoon-capa-amordetia.png": [1.193, 45.4, 46.8],
  "cartoon-capa-lucas.png": [1.075, 50.2, 50.6],
  "cartoon-capa-mako.png": [1.121, 50.3, 49.9],
};

export function coverFitStyle(file: string): CSSProperties | undefined {
  const fit = COVER_FIT[file];
  if (!fit) return undefined;
  const [scale, ox, oy] = fit;
  return {
    "--cover-fit": String(Math.round(scale * 1.012 * 1000) / 1000),
    "--cover-ox": `${ox}%`,
    "--cover-oy": `${oy}%`,
  } as CSSProperties;
}

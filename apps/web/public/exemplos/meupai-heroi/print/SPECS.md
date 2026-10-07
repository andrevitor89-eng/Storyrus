# Especificações de impressão — Meu Pai, Meu Herói

Extraídas das bases da gráfica + perfil **FOGRA32L** (ISOcofuncoated).

> Nota: as bases PDF/X enviadas pela gráfica declaram OutputIntent
> `Coated FOGRA39 (ISO 12647-2:2004)`. O pacote de arte foi gerado em
> **FOGRA32L** conforme solicitado. Confirme com a gráfica se o miolo/capa
> devem seguir FOGRA32 ou FOGRA39.

## Perfil de cor

| Item | Valor |
|---|---|
| Espaço | CMYK |
| Perfil | `FOGRA32L.icc` — ISOcofuncoated (FOGRA32L) |
| Condição | Continuous forms, papel tipo 4 uncoated white, 54 L/cm |
| Resolução | **300 dpi** |
| Formato do livro | **20 × 20 cm** (corte) |

## Miolo (`BASE_INDICACOES_MIOLO.pdf`)

Spread de 2 páginas (esquerda + direita).

| Zona | Cor na base | Tamanho (spread) | Por página |
|---|---|---|---|
| Sangra | vermelho | 410 × 210 mm | 205 × 210 mm* |
| Corte | verde | 400 × 200 mm | **200 × 200 mm** |
| Segurança | azul | — | **190 × 190 mm** |
| Dobra | rosa tracejado | centro | — |

\* Sangra = 5 mm em cada lado do corte.

Arquivos gerados: `miolo/NN-*.tif` em **210 × 210 mm @ 300 dpi** (2480 × 2480 px),
imagem preenchendo a sangra (conteúdo importante dentro de 190 × 190).

## Capa convencional / mole (`BASE_INDICACOES_CAPA_CONVENCIONAL.pdf`)

Aberta: contracapa | vinco | capa.

| Zona | Tamanho |
|---|---|
| Sangra | **410 × 210 mm** |
| Corte | **400 × 200 mm** (200 + 200) |
| Segurança | **190 × 190 mm** por face |
| Vinco | centro (dobra da lombada) |

Arquivo: `capa-mole/capa-mole-fogra32.tif` e PDF correspondente.

## Capa dura (`BASE_INDICACOES_CAPA_DURA.pdf` + `BASE_CAPA_DURA.ai`)

| Zona | Tamanho |
|---|---|
| Sangra (arquivo da base) | **443 × 235 mm** |
| Tamanho final | **413 × 205 mm** |
| Lombada | **5 × 205 mm** |
| Cada face (contracapa / capa) | **204 × 205 mm** |
| Segurança | **194 × 195 mm** aprox. por face |
| Sangria de envelopamento | **15 mm** em cada lado |

Arquivo: `capa-dura/capa-dura-fogra32.tif` e PDF correspondente.
A base `.ai` (`BASE_CAPA_DURA.ai`) tem exatamente 443 × 235 mm.

## Bases versionadas

Em `print/bases/`:

- `BASE_CAPA_DURA.ai`
- `BASE_INDICACOES_CAPA_CONVENCIONAL.pdf`
- `BASE_INDICACOES_CAPA_DURA.pdf`
- `BASE_INDICACOES_MIOLO.pdf`

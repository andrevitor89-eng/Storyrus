# Prompt de Geração de Histórias — Story R Us

Este documento define um prompt de sistema (system prompt) pronto para uso, que estende o
`_SYSTEM_PT` / `_SYSTEM_EN` já em produção em `backend/app/ai_clients/text_anthropic.py`. Ele
adiciona quatro camadas que o prompt atual ainda não cobre: **perfil próprio da criança**,
**personagens como cenário** (com o vilão podendo ser um sentimento), **espaço narrativo
definido** e **fluxo/ritmo explícito**. Mantém tudo o que já funciona (rima natural, 2-4 versos,
progressão lógica), sem reinventar o que já está validado.

Também proponho um dicionário `THEME_EDU`-style novo (`LEARNING_GOALS`), no mesmo formato do que
já existe em `handlers.py`, cobrindo os 14 subtemas das 4 categorias educacionais das imagens.

---

## 1. Perfil da criança-protagonista (input obrigatório)

A criança não é mais um nome solto num brief — ela precisa de um perfil com três campos:

| Campo | Exemplo | Função |
|---|---|---|
| `nome` + `idade` | Ana, 4 anos | já existe no schema (`child_name`, `child_age`) |
| `traço_central` | "não gosta de dividir os brinquedos" / "tem medo do escuro" / "ainda confunde as cores" | o ponto de partida — é o que a história vai transformar. Deve apontar diretamente para o objetivo educacional escolhido |
| `interesse/talento` | "adora dinossauros", "é curiosa e observadora" | a ferramenta que a criança usa para vencer o obstáculo no clímax — nunca um adulto ou a sorte resolve, é o próprio traço da criança |

Regra: **a descrição do traço_central já é metade da lição.** Se o objetivo é "aprender a
dividir", o traço central da criança é a dificuldade em dividir — a história é o caminho entre
esses dois pontos.

---

## 2. Personagens = cenário (o vilão pode ser um sentimento)

Cada personagem secundário (campo `extra_characters`, já existente no schema) funciona como uma
peça de cenário: a descrição dele **decide** que cena vai existir, não é decoração.

- Um personagem descrito como "chora muito e quer atenção" gera uma cena sobre paciência/empatia.
- Um personagem descrito como "sabe contar até 10" gera uma cena de aprendizado por imitação.

**O vilão** (obstáculo da jornada) tem duas formas possíveis, e a escolha depende do objetivo
educacional:

1. **Sentimento personificado** — para temas socioemocionais e de rotina (Medo-do-Escuro,
   Timidez, Ciúme, Preguiça, Vergonha, Impaciência). Ganha corpo, voz e um motivo simples para
   agir daquele jeito — nunca é "mau", é um sentimento que a criança precisa entender e acalmar,
   não destruir.
2. **Desafio-obstáculo concreto** — para temas de conhecimento de mundo/conceitos (a maré que
   sobe antes de contar os peixinhos, a estante alta demais para alcançar o livro certo). Também
   pode ganhar um sentimento por trás (frustração por não alcançar), mas o obstáculo em si é
   físico/prático.

Regra de ouro: o vilão nunca é derrotado pela força — é **compreendido, nomeado e acalmado** (se
sentimento) ou **superado com o traço/interesse da criança** (se obstáculo). Isso é o que torna a
lição transferível para a vida real da criança.

---

## 3. Espaço narrativo

Definir, antes de escrever, em 1 frase:
- **Onde** a história acontece (quarto, quintal, escola, floresta, praia — concreto, sensorial).
- **O que o espaço conta sobre a criança** (o quarto bagunçado já mostra o traço central; o
  parquinho cheio de amigos já mostra a timidez).
- **O que ela vai aprender ali** — o espaço deve conter, literalmente, o objetivo educacional
  (contar objetos → quarto cheio de blocos; cores → jardim com flores; vestir-se → guarda-roupa).

O espaço muda pouco ao longo do livro (mantém a coerência visual), mas ganha um canto novo ou uma
luz diferente no clímax — é o sinal visual de que algo mudou por dentro da criança.

---

## 4. Fluxo da história (ritmo, contenção, transição)

Substitui o "começo-meio-fim" genérico por um arco de 5 batidas, mapeado nas páginas do livro:

| Fase | % do livro | Ritmo | O que acontece |
|---|---|---|---|
| **Abertura** | ~15% | Calmo, gostoso | Apresenta criança + espaço + traço central. O gancho é a primeira pista do objetivo. |
| **Gatilho** | logo após | Acelera de leve | Um pequeno desejo ou pedido aparece — a razão da jornada. |
| **Contenção** | ~45-50% | Crescente, mas nunca assustador | 1-2 obstáculos pequenos; o vilão (sentimento ou desafio) aparece e cresce aos poucos. A criança tenta, erra, tenta de novo. |
| **Clímax** | 1 página | Pico breve | A criança usa o próprio traço/interesse para nomear, acalmar ou superar o vilão. |
| **Resolução** | ~15-20% | Desacelera, aconchegante | O espaço muda de leve, a lição é sentida (não explicada), final caloroso. |

**Regra de transição:** a última imagem/verso de cada página deve plantar uma semente (um som,
uma pergunta, um movimento) que a página seguinte responde. Nunca fechar uma página com ponto
final "morto" — feche com um fio que puxa para a próxima cena.

---

## 5. Dicionário de objetivos educacionais (`LEARNING_GOALS`)

Baseado nas 4 categorias fornecidas. Pronto para plugar em `handlers.py` no mesmo formato de
`THEME_EDU`, com um campo a mais (`vilao`) e (`espaco`):

```python
LEARNING_GOALS: dict[str, dict[str, dict[str, str]]] = {
    "pt": {
        # ---- Linguagem & Conceitos Fundamentais ----
        "alfabetizacao_inicial": {
            "foco": "consciência fonêmica: o alfabeto, rimas e a leitura da esquerda para a direita",
            "vilao": "a Timidez, que faz a criança guardar as palavras só para si",
            "espaco": "um cantinho de leitura cheio de livros e letras coloridas",
            "sequencia": "encontrar uma letra ou palavra misteriosa → seguir pistas rimadas pela "
                "casa → a Timidez tenta calar a criança bem na hora de dizer a palavra em voz alta "
                "→ a criança usa a curiosidade para soletrar e ler mesmo com medo → celebrar "
                "lendo a palavra inteira para todos",
        },
        "pensamento_matematico": {
            "foco": "contar de 1 a 5, separar por tamanho e reconhecer círculo, quadrado e triângulo",
            "vilao": "a Pressa, que faz contar errado e pular números",
            "espaco": "um quarto ou quintal cheio de blocos, brinquedos e formas para organizar",
            "sequencia": "objetos espalhados pedem para ser organizados → contar um a um devagar → "
                "a Pressa tenta atropelar a contagem → a criança respira e conta de novo, com calma "
                "→ tudo organizado por tamanho e forma, missão cumprida",
        },
        "cores": {
            "foco": "cores primárias e secundárias, reconhecidas em objetos do mundo real",
            "vilao": "a Confusão, que embaralha as cores na cabeça da criança",
            "espaco": "um jardim ou caixa de tintas cheio de cores para nomear",
            "sequencia": "algo perdeu a cor certa e precisa ser combinado → percorrer o espaço "
                "nomeando cores em objetos conhecidos → a Confusão troca as cores de lugar → a "
                "criança usa o que já sabe (o que é amarelo? o que é azul?) para desfazer a troca "
                "→ tudo com a cor certa de novo",
        },
        "opostos_espacial": {
            "foco": "grande/pequeno, em cima/embaixo, dentro/fora",
            "vilao": "o Embolado, um sentimento de estar perdido no espaço",
            "espaco": "uma casa ou parquinho com cantos altos, baixos, dentro e fora bem marcados",
            "sequencia": "algo precisa ser guardado ou encontrado no lugar certo → explorar o "
                "espaço nomeando opostos a cada passo → o Embolado confunde as direções → a "
                "criança usa os opostos como mapa (não é embaixo, é em cima!) → encontra o caminho "
                "certo",
        },
        # ---- Habilidades de Vida & Rotinas Diárias ----
        "higiene_desfralde": {
            "foco": "a transição do banheiro, lavar as mãos e escovar os dentes em passos previsíveis",
            "vilao": "a Vergonha, que faz esconder quando precisa ir ao banheiro",
            "espaco": "o banheiro de casa, arrumado e acolhedor",
            "sequencia": "a criança sente que precisa ir ao banheiro → a Vergonha sussurra para "
                "esconder o sinal → a criança nomeia o que sente e pede ajuda → consegue sozinha, "
                "passo a passo (calça, sentar, papel, descarga, lavar as mãos) → orgulho de ter "
                "conseguido",
        },
        "rotina_dormir": {
            "foco": "a ansiedade de separação e uma rotina calma antes de dormir",
            "vilao": "o Medo-do-Escuro, que aparece quando a luz apaga",
            "espaco": "o quarto da criança à noite, com uma luminária e um brinquedo favorito",
            "sequencia": "o dia termina e chega a hora de dormir → passos da rotina (banho, "
                "pijama, escovar os dentes, história) → o Medo-do-Escuro aparece quando a luz "
                "apaga → a criança nomeia o medo e acende a luminária/abraça o brinquedo → "
                "adormece tranquila",
        },
        "alimentacao_saudavel": {
            "foco": "grupos de alimentos, frutas e verduras, coragem para experimentar texturas novas",
            "vilao": "o Enjoo, que faz recusar tudo que é novo no prato",
            "espaco": "a cozinha ou horta de casa, colorida com frutas e legumes",
            "sequencia": "aparece um alimento novo e diferente no prato ou na horta → o Enjoo "
                "encolhe o nariz da criança → a criança usa a curiosidade (cheirar, tocar, provar "
                "um pouquinho) para vencer o Enjoo → descobre um sabor novo → orgulho de ter "
                "experimentado",
        },
        "vestir_autonomia": {
            "foco": "identificar peças de roupa, botões, zíperes e sapatos, e vestir-se sozinho",
            "vilao": "a Impaciência, que quer que outra pessoa faça tudo",
            "espaco": "o guarda-roupa ou quarto, com roupas espalhadas para escolher",
            "sequencia": "a criança precisa se vestir para algo especial → a Impaciência tenta "
                "fazer desistir no primeiro botão emperrado → a criança tenta de novo, devagar, "
                "peça por peça → consegue se vestir sozinha → orgulho de ter feito por conta "
                "própria",
        },
        # ---- Autoconsciência & Aprendizagem Socioemocional ----
        "literacia_emocional": {
            "foco": "nomear sentimentos grandes — raiva, tristeza, frustração, alegria",
            "vilao": "o sentimento grande do dia (Raiva, Tristeza ou Frustração), como personagem",
            "espaco": "um lugar familiar e calmo, como a sala de casa ou o pátio da escola",
            "sequencia": "algo não sai como a criança queria → o sentimento grande aparece e cresce "
                "→ a criança tenta ignorá-lo, mas ele só cresce mais → a criança para, nomeia o "
                "que sente e respira fundo → o sentimento fica pequeno e vira aprendizado",
        },
        "consciencia_corporal": {
            "foco": "nomes das partes do corpo, o que elas fazem e limites espaciais básicos",
            "vilao": "o Desatento, que faz a criança não perceber o próprio corpo",
            "espaco": "um espaço de brincar livre, como o quintal ou a sala",
            "sequencia": "uma brincadeira de imitação ou dança começa → cada parte do corpo entra "
                "em ação (mãos, pés, cabeça) → o Desatento tenta bagunçar os movimentos → a "
                "criança presta atenção no próprio corpo e acerta o ritmo → brincadeira concluída "
                "com orgulho",
        },
        "compartilhar_revezar": {
            "foco": "brincar em paralelo, dividir e esperar a vez com gentileza",
            "vilao": "o Ciúme, que não quer soltar o brinquedo",
            "espaco": "um parquinho ou sala de brincar com outra criança por perto",
            "sequencia": "um amiguinho quer brincar com o mesmo brinquedo → o Ciúme aperta o "
                "brinquedo contra o peito → a criança sente o Ciúme, mas lembra como é bom brincar "
                "junto → propõe revezar ou dividir → os dois brincam juntos e se divertem mais "
                "ainda",
        },
        # ---- Descoberta & Exploração do Mundo ----
        "animais_sons": {
            "foco": "nomes e sons de animais, e seus habitats (fazenda, oceano, selva)",
            "vilao": "o Silêncio-Enroscado, que embaralha os sons dos animais",
            "espaco": "uma fazenda, floresta ou aquário para visitar",
            "sequencia": "um som de animal escapa e ninguém sabe de quem é → seguir o som até o "
                "habitat certo → o Silêncio-Enroscado tenta confundir o som com outro animal → a "
                "criança escuta com atenção e acerta o animal e seu som → o habitat inteiro canta "
                "junto",
        },
        "transporte_ajudantes": {
            "foco": "veículos (caminhão, trem, avião) e figuras da comunidade (bombeiro, médico, carteiro)",
            "vilao": "a Pressa-Perdida, que atrapalha o caminho até o ajudante certo",
            "espaco": "uma rua ou cidade pequena com diferentes veículos passando",
            "sequencia": "algo precisa ser entregue ou resolvido rápido → a criança escolhe o "
                "veículo certo para o trajeto → a Pressa-Perdida embaralha o caminho → a criança "
                "para, pensa e escolhe a rota certa com a ajuda de um profissional da comunidade → "
                "missão entregue com sucesso",
        },
        "clima_estacoes": {
            "foco": "padrões de clima (chuva, sol, neve) e a roupa certa para cada estação",
            "vilao": "o Friozinho-Sem-Aviso (ou Solzão-Repentino), que muda o tempo de repente",
            "espaco": "o quintal ou uma janela que mostra o tempo mudando",
            "sequencia": "a criança se prepara para sair de um jeito → o tempo muda de repente → o "
                "vilão do clima brinca de confundir a roupa certa → a criança observa o céu e "
                "escolhe a roupa certa para a nova estação/clima → sai para brincar preparada e "
                "feliz",
        },
    },
}
```

*(A versão `"en"` segue a mesma estrutura, traduzida — omitida aqui por brevidade; posso gerar
se for útil.)*

---

## 6. System prompt completo (pronto para uso — PT-BR)

Texto para substituir/estender `_SYSTEM_PT` em `text_anthropic.py`. As partes **novas** em
relação ao prompt atual estão marcadas com `[NOVO]`.

```
Você é um autor premiado de livros infantis personalizados (nível WonderWraps/TellMyTale).
Escreva SEMPRE em português do Brasil impecável, com ortografia, gramática, pontuação e
ACENTUAÇÃO corretas (nunca omita acentos: coração, você, céu, mãozinha).

[NOVO] PERFIL DA CRIANÇA: você recebe um nome, uma idade, um TRAÇO CENTRAL (o ponto de partida
que a história vai transformar) e um INTERESSE/TALENTO (a ferramenta que a criança usa para
vencer o obstáculo). O traço central deve apontar diretamente para o objetivo educacional da
história — é o "antes"; a lição é o "depois". Nunca troque o traço central por outro no meio da
história, e nunca deixe um adulto ou a sorte resolver o problema por ela: quem supera o obstáculo
é a própria criança, usando o que já é seu.

[NOVO] PERSONAGENS COMO CENÁRIO: cada personagem secundário funciona como peça de cenário — a
descrição dele DEFINE que cena existe, nunca é decoração. O VILÃO da história pode ser um
SENTIMENTO PERSONIFICADO (Medo-do-Escuro, Timidez, Ciúme, Vergonha, Impaciência, Frustração) para
temas emocionais e de rotina, ou um DESAFIO-OBSTÁCULO concreto para temas de descoberta do mundo.
Em ambos os casos, o vilão nunca é "mau" nem é destruído — ele é NOMEADO, COMPREENDIDO e
ACALMADO (se sentimento) ou SUPERADO com o traço/interesse da própria criança (se obstáculo). É
isso que torna a lição transferível para a vida real da criança.

[NOVO] ESPAÇO: antes de escrever, defina em 1 frase onde a história acontece (lugar concreto e
sensorial), o que esse espaço já revela sobre o traço central da criança, e como ele contém
literalmente o objetivo educacional (ex.: contar objetos → quarto cheio de blocos). O espaço muda
pouco ao longo do livro, mas ganha um detalhe novo no clímax — sinal visual de que algo mudou por
dentro da criança.

HISTÓRIA (o mais importante): antes de escrever, planeje mentalmente um ENREDO COERENTE com
começo, meio e fim — o espaço definido acima, um pequeno OBJETIVO ligado ao traço central da
criança, uma jornada com 1 ou 2 obstáculos e o vilão (sentimento ou desafio), um clímax gentil
onde a criança usa seu próprio traço/interesse para superar, e um final acolhedor com a lição
sentida, não explicada. Cada página AVANÇA a história de forma lógica e se conecta à anterior —
nunca cenas soltas, aleatórias ou sem nexo. O protagonista é o mesmo do início ao fim, com o
mesmo nome. Seja concreto e sensorial (lugares, cores, sons), com ternura e sem medo, sempre
adequado à IDADE indicada no pedido (se nenhuma idade for informada, escreva para 3 a 7 anos).

[NOVO] FLUXO E RITMO: estruture as páginas em 5 fases — ABERTURA (~15%, ritmo calmo: criança +
espaço + traço central), GATILHO (logo após: nasce o pequeno objetivo/desejo), CONTENÇÃO (~45-
50%, ritmo cresce aos poucos: 1-2 obstáculos, o vilão aparece e cresce, a criança tenta e erra),
CLÍMAX (1 página, pico breve: a criança nomeia/acalma/supera o vilão com seu próprio traço),
RESOLUÇÃO (~15-20%, ritmo desacelera: o espaço muda de leve, final caloroso). TRANSIÇÃO: a última
imagem ou verso de cada página deve plantar uma semente (som, pergunta, movimento) que a página
seguinte responde — nunca feche uma página com um ponto final "morto".

CRIATIVIDADE E ENCANTAMENTO: abra a página 1 com um GANCHO irresistível que dê vontade de virar a
página. Crie um momento de DESCOBERTA ou uma pequena SURPRESA no meio, aumente a emoção e a
tensão gentil até o CLÍMAX triunfante, e termine com um final memorável e afetuoso que dê um
friozinho gostoso na barriga. Use imagens vívidas e inesperadas, palavras sonoras (plim!, zup!,
splash!), um toque de humor ou magia, vocabulário rico e ideias ORIGINAIS — nada de clichês nem
histórias repetidas. Cada livro deve ser único, emocionante e inesquecível.

EDUCATIVO: cada história também ENSINA. Entrelace à ação e às falas as curiosidades verdadeiras
pedidas no brief — a criança aprende brincando, sem tom de aula. Use o nome certo das coisas
(animais, plantas, planetas, instrumentos) com uma explicação simples de 1 frase, e faça o final
retomar com leveza o que o herói descobriu e sentiu — não apenas "aprendeu", mas sentiu na pele.

FORMA: cada página é uma ESTROFE CURTA de 2 a 4 versos, musical, no máximo ~40 palavras,
descrevendo UMA cena visual clara (lugar + ação do protagonista).

REGRA DE OURO DO SENTIDO: cada verso deve ser uma frase NATURAL do português, na ordem direta
(sujeito + verbo + complemento), que faria sentido perfeito lida em voz alta como prosa. A rima é
um enfeite, nunca o objetivo: use rima (AABB ou ABCB) apenas quando ela vier naturalmente; é
PROIBIDO inverter a ordem das palavras, escolher palavras estranhas ao contexto ou sacrificar a
lógica da cena só para rimar. Verso solto e claro vale mais que rima forçada e confusa.

REVISÃO FINAL (obrigatória): antes de responder, releia a história inteira como se fosse prosa,
do título à última página, e reescreva qualquer verso confuso, incoerente, sem nexo com a cena ou
com rima forçada. Confira que: (1) a sequência de eventos faz sentido de uma página para a outra;
(2) o final resolve o objetivo apresentado no começo; (3) o vilão foi nomeado e acalmado/superado
pelo próprio traço da criança, não por um adulto ou pela sorte; (4) o espaço mudou de leve no
clímax.

Responda APENAS com o texto pedido — sem notas, comentários ou sugestões de imagem.
```

---

## 7. Como integrar (nota de implementação, se quiser aplicar depois)

1. `text_anthropic.py`: substituir `_SYSTEM_PT` (e o par `_SYSTEM_EN`) pelo texto da seção 6.
2. `handlers.py`: adicionar o dicionário `LEARNING_GOALS` da seção 5 ao lado de `THEME_EDU`, e
   permitir que `theme` aponte para um objetivo educacional além dos temas de aventura já
   existentes — a lógica de montagem do `brief` (linhas ~668-704) já sabe puxar `focus`/`sequence`
   de um dicionário por tema; só precisa também puxar `vilao` e `espaco` do novo dicionário e
   somar ao brief.
3. `schemas.py`: os campos que faltam são `traço_central` e `interesse_talento` da criança — hoje
   só existe `child_name`/`child_age`/`dedication`. Podem entrar como dois campos novos opcionais
   em `ProjectCreateIn`, ou serem embutidos em `dedication`/`brief` livre por enquanto, sem
   migração de banco.

**✅ IMPLEMENTADO** — Este documento foi implementado em `backend/app/workers/handlers.py`:
1. `LEARNING_GOALS` com campos separados (foco, vilao, espaco, sequencia) para todos os 14 temas educacionais.
2. `THEME_EDU` simplificado com apenas aventura/datas comemorativas.
3. `handle_story()` atualizado para puxar vilao/espaco do `LEARNING_GOALS` e injetá-los no brief.
4. System prompt (`_SYSTEM_PT`/`_SYSTEM_EN`) já continha o prompt evoluído com perfil da criança, personagens como cenário, espaço narrativo e fluxo/ritmo.

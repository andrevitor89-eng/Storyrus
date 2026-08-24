import { SHARED, useLang, type Lang } from "./i18n";
import { SimpleShell } from "./SiteChrome";

type Block = { h: string; p: string[] };

const PRIVACY: Record<Lang, { title: string; updated: string; blocks: Block[] }> = {
  pt: {
    title: "Política de Privacidade",
    updated: "Atualizado em 24 de agosto de 2026",
    blocks: [
      {
        h: "O que é este serviço",
        p: [
          "A Story R Us cria histórias e livros ilustrados personalizados a partir de uma foto e de alguns dados que você envia. Esta página descreve o que o produto faz hoje — sem promessas que o código e o material público do site não sustentam.",
        ],
      },
      {
        h: "O que coletamos",
        p: [
          "Conta (se você se cadastrar): e-mail e senha.",
          "Dados da criança: nome e faixa etária, usados para personalizar o texto da história.",
          "Foto da criança: usada para gerar o personagem ilustrado e as páginas do livro (e o vídeo, se você pedir).",
          "Outros campos que você preencher no estúdio, como dedicatória, tema e estilo.",
        ],
      },
      {
        h: "Como usamos a foto",
        p: [
          "A foto serve para preparar o livro (e o vídeo) do seu filho. Não usamos a imagem para divulgação, anúncio ou marketing.",
          "Para gerar o personagem e as ilustrações, a foto passa pelo nosso pipeline de IA. Hoje isso inclui um provedor de imagem (personagem e cenas), um provedor de texto (história) e, se você pedir vídeo, um provedor de vídeo. Esses provedores processam o necessário para entregar o que você solicitou — não para campanhas nossas.",
          "Não vendemos a foto e não a usamos para promover o serviço com o rosto da criança.",
        ],
      },
      {
        h: "Dados de crianças",
        p: [
          "O fluxo é feito para um adulto (pai, mãe ou responsável) criar um livro em que a criança é a protagonista. Não pedimos que a criança abra a conta.",
          "Nome, idade e foto são dados de criança: usamos só para personalizar o pedido que você fez.",
        ],
      },
      {
        h: "Armazenamento e acesso",
        p: [
          "Arquivos e resultados ficam no armazenamento do serviço. Quando o produto opera com links assinados, o acesso a esses arquivos é de duração limitada.",
          "Esta página não inventa um prazo automático de exclusão, porque o produto não documenta um. Se quiser apagar conta, foto ou livro, use os canais do próprio site — vamos tratar o pedido com o que o sistema permitir no momento.",
        ],
      },
      {
        h: "Compartilhamento",
        p: [
          "Não compartilhamos seus dados para marketing. Há processamento por provedores de IA e de infraestrutura (hospedagem e armazenamento) necessários para gerar e entregar o livro.",
        ],
      },
      {
        h: "O que esta página não afirma",
        p: [
          "Não afirmamos certificação LGPD/GDPR, encarregado nomeado, técnica de criptografia específica nem prazos de retenção que o material público do produto não descreve.",
        ],
      },
      {
        h: "Contato",
        p: [
          "Não publicamos um e-mail de privacidade neste site. Use a conta no serviço ou os canais indicados no próprio site quando existirem.",
        ],
      },
    ],
  },
  en: {
    title: "Privacy Policy",
    updated: "Updated 24 August 2026",
    blocks: [
      {
        h: "What this service is",
        p: [
          "Story R Us creates personalized illustrated stories and books from a photo and a few details you send. This page describes what the product does today — without claims the public site and code cannot support.",
        ],
      },
      {
        h: "What we collect",
        p: [
          "Account (if you register): email and password.",
          "Child details: name and age band, used to personalize the story text.",
          "A photo of the child: used to generate the illustrated character and book pages (and a video, if you ask for one).",
          "Other studio fields you fill in, such as a dedication, theme and art style.",
        ],
      },
      {
        h: "How we use the photo",
        p: [
          "The photo is used to prepare your child's book (and video). We do not use the image for advertising, promotion or marketing.",
          "To generate the character and illustrations, the photo goes through our AI pipeline. Today that includes an image provider (character and scenes), a text provider (story) and, if you request video, a video provider. Those providers process what is needed to deliver what you asked for — not for our campaigns.",
          "We do not sell the photo and we do not use it to promote the service with the child's face.",
        ],
      },
      {
        h: "Children's data",
        p: [
          "The flow is meant for an adult (parent or guardian) to create a book in which the child is the hero. We do not ask the child to open the account.",
          "Name, age and photo are a child's personal data: we use them only to personalize the order you placed.",
        ],
      },
      {
        h: "Storage and access",
        p: [
          "Files and results are kept in the service storage. When the product uses signed links, access to those files is time-limited.",
          "This page does not invent an automatic deletion deadline, because the product does not document one. If you want an account, photo or book deleted, use the channels on this site — we will handle the request with whatever the system allows at the time.",
        ],
      },
      {
        h: "Sharing",
        p: [
          "We do not share your data for marketing. There is processing by AI and infrastructure providers (hosting and storage) needed to generate and deliver the book.",
        ],
      },
      {
        h: "What this page does not claim",
        p: [
          "We do not claim LGPD/GDPR certification, a named data-protection officer, a specific encryption scheme, or retention periods that the product's public material does not describe.",
        ],
      },
      {
        h: "Contact",
        p: [
          "We do not publish a privacy email on this site. Use the in-product account or whatever contact channels the site itself provides.",
        ],
      },
    ],
  },
};

const TERMS: Record<Lang, { title: string; updated: string; blocks: Block[] }> = {
  pt: {
    title: "Termos de uso",
    updated: "Atualizado em 24 de agosto de 2026",
    blocks: [
      {
        h: "O serviço",
        p: [
          "A Story R Us oferece a criação de uma história ilustrada personalizada (e, se disponível, vídeo) a partir de uma foto e de dados que você informa. Preços, prazos e formatos exibidos na vitrine podem mudar; o que vale para cada pedido é o que estiver indicado no fluxo no momento da compra.",
        ],
      },
      {
        h: "Quem pode usar",
        p: [
          "O cadastro e o pedido são para um adulto. Se a história é sobre uma criança, você declara ser pai, mãe ou responsável (ou ter autorização) para enviar a foto, o nome e a idade.",
        ],
      },
      {
        h: "Foto e direitos",
        p: [
          "Você só deve enviar foto de quem tem o direito de usar para este fim. A imagem é usada para gerar o personagem e o livro — não para divulgação nossa.",
          "O conteúdo gerado é um produto personalizado para o seu pedido. Não prometemos semelhança fotográfica perfeita nem resultado idêntico a qualquer exemplo da vitrine.",
        ],
      },
      {
        h: "Conta",
        p: [
          "Se você criar uma conta, é responsável por guardar a senha. O estúdio também pode funcionar como convidado, conforme a configuração atual da API.",
        ],
      },
      {
        h: "Limites",
        p: [
          "O serviço depende de provedores de IA e de infraestrutura. Falhas, filas ou recusas de conteúdo (por exemplo, moderação) podem acontecer. Esta página não inventa garantia de reembolso, SLA ou disponibilidade 24h que o produto não documenta.",
        ],
      },
      {
        h: "Mudanças",
        p: [
          "Podemos atualizar estes termos quando o produto mudar. A data no topo indica a versão publicada neste site.",
        ],
      },
    ],
  },
  en: {
    title: "Terms of use",
    updated: "Updated 24 August 2026",
    blocks: [
      {
        h: "The service",
        p: [
          "Story R Us offers a personalized illustrated story (and, when available, video) from a photo and details you provide. Prices, timing and formats on the storefront may change; what applies to each order is what the flow shows when you buy.",
        ],
      },
      {
        h: "Who may use it",
        p: [
          "Sign-up and ordering are for an adult. If the story is about a child, you state that you are a parent or guardian (or have permission) to send the photo, name and age.",
        ],
      },
      {
        h: "Photos and rights",
        p: [
          "Only upload a photo you have the right to use for this purpose. The image is used to generate the character and the book — not for our advertising.",
          "Generated content is a personalized product for your order. We do not promise a perfect photographic likeness or a result identical to any storefront example.",
        ],
      },
      {
        h: "Account",
        p: [
          "If you create an account, you are responsible for keeping the password. The studio may also work as a guest, depending on the current API setup.",
        ],
      },
      {
        h: "Limits",
        p: [
          "The service depends on AI and infrastructure providers. Failures, queues or content refusals (for example, moderation) can happen. This page does not invent a refund policy, SLA or 24/7 uptime that the product does not document.",
        ],
      },
      {
        h: "Changes",
        p: [
          "We may update these terms when the product changes. The date at the top is the version published on this site.",
        ],
      },
    ],
  },
};

function LegalDoc({ kind }: { kind: "privacy" | "terms" }) {
  const [lang] = useLang();
  const doc = kind === "privacy" ? PRIVACY[lang] : TERMS[lang];
  return (
    <SimpleShell>
      <article className="legal-doc">
        <p className="page-kicker">{kind === "privacy" ? SHARED[lang].privacy : SHARED[lang].terms}</p>
        <h1>{doc.title}</h1>
        <p className="legal-updated">{doc.updated}</p>
        {doc.blocks.map((b) => (
          <section key={b.h}>
            <h2>{b.h}</h2>
            {b.p.map((para) => <p key={para}>{para}</p>)}
          </section>
        ))}
      </article>
    </SimpleShell>
  );
}

export function Privacy() {
  return <LegalDoc kind="privacy" />;
}

export function Terms() {
  return <LegalDoc kind="terms" />;
}

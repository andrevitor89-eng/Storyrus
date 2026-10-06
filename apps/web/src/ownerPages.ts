export type OwnerPage = {
  path: "/gastos" | "/pedidos" | "/usuarios";
  file: string;
  title: string;
  description: string;
};

export const OWNER_PAGES: readonly OwnerPage[] = [
  {
    path: "/gastos",
    file: "gastos.html",
    title: "Gastos — Story R Us",
    description: "Painel privado de custos da plataforma.",
  },
  {
    path: "/pedidos",
    file: "pedidos.html",
    title: "Pedidos — Story R Us",
    description: "Painel privado dos livros enviados com foto.",
  },
  {
    path: "/usuarios",
    file: "usuarios.html",
    title: "Usuários — Story R Us",
    description: "Painel privado das contas cadastradas.",
  },
];

export function applyOwnerPageMeta(html: string, page: OwnerPage): string {
  const url = `https://storyrus.ai${page.path}`;
  let next = html;
  next = next.replace(/<title>[\s\S]*?<\/title>/i, `<title>${page.title}</title>`);
  next = next.replace(/(property="og:title"\s+content=")[^"]*(")/i, `$1${page.title}$2`);
  next = next.replace(/(property="og:description"\s+content=")[^"]*(")/i, `$1${page.description}$2`);
  next = next.replace(/(property="og:url"\s+content=")[^"]*(")/i, `$1${url}$2`);
  next = next.replace(/(rel="canonical"\s+href=")[^"]*(")/i, `$1${url}$2`);
  next = next.replace(/(name="description"\s+content=")[^"]*(")/i, `$1${page.description}$2`);
  next = next.replace(/(name="twitter:title"\s+content=")[^"]*(")/i, `$1${page.title}$2`);
  next = next.replace(/(name="twitter:description"\s+content=")[^"]*(")/i, `$1${page.description}$2`);
  if (!/name="robots"/i.test(next)) {
    next = next.replace(/<head>/i, `<head>\n    <meta name="robots" content="noindex, nofollow" />`);
  }
  return next;
}

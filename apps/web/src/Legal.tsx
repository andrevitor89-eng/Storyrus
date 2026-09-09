import { Link } from "react-router-dom";
import logo from "./assets/logo.png";
import "./landing.css";

const CONTACT = "Storyrus@outlook.com";

export function Legal({ kind }: { kind: "privacy" | "terms" }) {
  const privacy = kind === "privacy";
  return (
    <div className="kid legal-page">
      <header className="knav">
        <Link to="/" className="kbrand"><img src={logo} alt="Story R Us" /></Link>
        <nav className="klinks">
          <Link to="/" className="kbtn kbtn-go">Início</Link>
        </nav>
      </header>
      <main className="ksection" style={{ maxWidth: 720, margin: "0 auto", textAlign: "left" }}>
        <h1 className="ktitle">{privacy ? "Privacidade" : "Termos de uso"}</h1>
        {privacy ? (
          <>
            <p className="ksub" style={{ textAlign: "left" }}>
              A Story R Us cria livros ilustrados a partir de uma foto que você envia.
              Este texto descreve o que fazemos com esses dados hoje.
            </p>
            <h2>O que coletamos</h2>
            <p>Nome, idade e dedicatória da criança, a foto enviada, e o conteúdo gerado (personagem, páginas, PDF, vídeo e, se você clonar, um sample de voz).</p>
            <h2>Para que usamos</h2>
            <p>Só para criar e entregar o livro e os vídeos do seu projeto. Não vendemos dados e não usamos a foto do cliente para divulgação.</p>
            <h2>Exemplos da página inicial</h2>
            <p>As fotos e vídeos em /exemplos são demonstrações da plataforma, separados do que você envia no estúdio.</p>
            <h2>Conta de convidado</h2>
            <p>Sem cadastro, o navegador recebe um token isolado. Cada visitante vê só os próprios projetos.</p>
            <h2>Retenção</h2>
            <p>Os arquivos ficam no armazenamento do projeto enquanto a conta existir. Para apagar dados, escreva para {CONTACT}.</p>
            <h2>Crianças</h2>
            <p>O envio da foto deve ser feito pelo responsável legal, que autoriza o uso apenas para este livro.</p>
          </>
        ) : (
          <>
            <p className="ksub" style={{ textAlign: "left" }}>
              Ao usar storyrus.ai você concorda com estes termos.
            </p>
            <h2>O serviço</h2>
            <p>Geramos histórias e ilustrações com IA. O resultado pode variar. Você revisa a prévia antes de baixar o PDF ou pedir cotação do impresso.</p>
            <h2>Responsável legal</h2>
            <p>Só envie foto de criança se você for o responsável e autorizar o uso para criar este livro.</p>
            <h2>Créditos</h2>
            <p>Etapas pagas consomem créditos da conta. Impressão é sob consulta, não um checkout automático.</p>
            <h2>Propriedade</h2>
            <p>Você pode usar o livro gerado para uso pessoal e familiar. Não redistribua o software nem abuse da API.</p>
            <h2>Contato</h2>
            <p>{CONTACT}</p>
          </>
        )}
        <p style={{ marginTop: 28 }}><Link to="/" className="kbtn kbtn-primary">Voltar à página inicial</Link></p>
      </main>
    </div>
  );
}

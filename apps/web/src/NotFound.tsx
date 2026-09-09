import { Link } from "react-router-dom";
import logo from "./assets/logo.png";
import "./landing.css";

export function NotFound() {
  return (
    <div className="kid legal-page">
      <header className="knav">
        <Link to="/" className="kbrand"><img src={logo} alt="Story R Us" /></Link>
      </header>
      <main className="ksection" style={{ textAlign: "center" }}>
        <h1 className="ktitle">Página não encontrada</h1>
        <p className="ksub">Esse endereço não existe. Volte à página inicial ou abra o estúdio.</p>
        <p style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
          <Link to="/" className="kbtn kbtn-primary">Início</Link>
          <Link to="/app" className="kbtn kbtn-soft">Criar minha história</Link>
        </p>
      </main>
    </div>
  );
}

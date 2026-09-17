type CharacterProps = {
  characterUrl: string;
  characterApproved: boolean;
  locked: boolean;
  onApprove: () => void;
  onRegenerate: () => void;
};

export function CharacterApprovalBlock({
  characterUrl,
  characterApproved,
  locked,
  onApprove,
  onRegenerate,
}: CharacterProps) {
  return (
    <div className="result-block">
      <h3 className="field-label">Personagem</h3>
      <img
        src={characterUrl}
        alt="Personagem gerado"
        style={{ maxWidth: 280, width: "100%", borderRadius: 12 }}
      />
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
        {characterApproved ? (
          <p className="muted">Personagem aprovado. Pode montar o livro.</p>
        ) : (
          <button disabled={locked} onClick={onApprove}>
            Aprovar personagem
          </button>
        )}
        <button disabled={locked} onClick={onRegenerate}>
          Regenerar personagem <span className="muted">(1 crédito)</span>
        </button>
      </div>
    </div>
  );
}

type BookProps = {
  pageImages: string[];
  ebookUrl: string | null;
  bookApproved: boolean;
  locked: boolean;
  canMountEbook: boolean;
  printRequested: boolean;
  onApprove: () => void;
  onRegenerate: () => void;
  onRequestPrint: () => void;
};

export function BookApprovalBlock({
  pageImages,
  ebookUrl,
  bookApproved,
  locked,
  canMountEbook,
  printRequested,
  onApprove,
  onRegenerate,
  onRequestPrint,
}: BookProps) {
  return (
    <div className="result-block">
      <h3 className="field-label">E-book</h3>
      {pageImages.length > 0 && (
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 10 }}>
          {pageImages.map((u, i) => (
            <img
              key={i}
              src={u}
              alt={`Página ${i + 1}`}
              loading="lazy"
              style={{ width: 120, height: 120, objectFit: "cover", borderRadius: 8 }}
            />
          ))}
        </div>
      )}
      {ebookUrl && (
        <a href={ebookUrl} target="_blank" rel="noreferrer" className="btn">
          📖 Abrir e-book
        </a>
      )}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
        {bookApproved ? (
          <p className="muted">Livro aprovado. PDF, impressão e vídeo liberados.</p>
        ) : (
          <button disabled={locked || !ebookUrl} onClick={onApprove}>
            Aprovar livro
          </button>
        )}
        <button disabled={locked || !canMountEbook} onClick={onRegenerate}>
          Regenerar páginas <span className="muted">(1 crédito)</span>
        </button>
      </div>
      {bookApproved && (
        <div style={{ marginTop: 12 }}>
          <h3 className="field-label">Livro impresso</h3>
          {printRequested ? (
            <p className="muted">Pedido registrado — em até 24h enviamos a cotação e o prazo.</p>
          ) : (
            <button disabled={locked} onClick={onRequestPrint}>
              Pedir livro impresso
            </button>
          )}
        </div>
      )}
    </div>
  );
}

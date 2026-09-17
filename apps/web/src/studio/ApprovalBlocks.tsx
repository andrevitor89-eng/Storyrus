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
    <div className="result-block" role="region" aria-labelledby="studio-character-heading">
      <h3 className="field-label" id="studio-character-heading">Personagem</h3>
      <img
        src={characterUrl}
        alt="Personagem gerado"
        style={{ maxWidth: 280, width: "100%", borderRadius: 12 }}
      />
      <div
        style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}
        role="group"
        aria-label="Ações do personagem"
      >
        {characterApproved ? (
          <p className="muted" role="status">
            Personagem aprovado. Pode montar o livro.
          </p>
        ) : (
          <button type="button" disabled={locked} onClick={onApprove}>
            Aprovar personagem
          </button>
        )}
        <button type="button" disabled={locked} onClick={onRegenerate}>
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
    <div className="result-block" role="region" aria-labelledby="studio-ebook-heading">
      <h3 className="field-label" id="studio-ebook-heading">E-book</h3>
      {pageImages.length > 0 && (
        <div
          style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 10 }}
          aria-label="Páginas do e-book"
        >
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
      <div
        style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}
        role="group"
        aria-label="Ações do livro"
      >
        {bookApproved ? (
          <p className="muted" role="status">
            Livro aprovado. PDF, impressão e vídeo liberados.
          </p>
        ) : (
          <button type="button" disabled={locked || !ebookUrl} onClick={onApprove}>
            Aprovar livro
          </button>
        )}
        <button type="button" disabled={locked || !canMountEbook} onClick={onRegenerate}>
          Regenerar páginas <span className="muted">(1 crédito)</span>
        </button>
      </div>
      {bookApproved && (
        <div style={{ marginTop: 12 }} role="region" aria-labelledby="studio-print-heading">
          <h3 className="field-label" id="studio-print-heading">Livro impresso</h3>
          {printRequested ? (
            <p className="muted" role="status">
              Pedido registrado — em até 24h enviamos a cotação e o prazo.
            </p>
          ) : (
            <button type="button" disabled={locked} onClick={onRequestPrint}>
              Pedir livro impresso
            </button>
          )}
        </div>
      )}
    </div>
  );
}

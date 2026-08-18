type ShotKind = "good" | "multi" | "side";

function ShotArt({ kind }: { kind: ShotKind }) {
  const face = "#f4c19a",
    hair = "#6b4a2b",
    eye = "#3a2b1c",
    mouth = "#a15a3a";
  if (kind === "multi") {
    return (
      <svg className="shot-svg" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden>
        <rect width="120" height="120" fill="#e7ecf4" />
        <g>
          <rect x="24" y="76" width="20" height="26" rx="10" fill="#8fb4dd" />
          <circle cx="34" cy="58" r="16" fill={face} />
          <path d="M19 57q0-18 15-18t15 18q0-9-15-9t-15 9Z" fill="#7a5230" />
          <circle cx="29" cy="57" r="2.1" fill={eye} />
          <circle cx="39" cy="57" r="2.1" fill={eye} />
        </g>
        <g>
          <rect x="76" y="76" width="20" height="26" rx="10" fill="#8ccdb0" />
          <circle cx="86" cy="58" r="16" fill={face} />
          <circle cx="81" cy="57" r="2.1" fill={eye} />
          <circle cx="91" cy="57" r="2.1" fill={eye} />
        </g>
        <g>
          <rect x="47" y="72" width="26" height="34" rx="12" fill="#e79a9a" />
          <circle cx="60" cy="52" r="19" fill="#eab98f" />
          <circle cx="54" cy="51" r="2.4" fill={eye} />
          <circle cx="66" cy="51" r="2.4" fill={eye} />
        </g>
      </svg>
    );
  }
  if (kind === "side") {
    return (
      <svg className="shot-svg" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden>
        <rect width="120" height="120" fill="#e7ecf4" />
        <rect x="50" y="88" width="16" height="18" rx="8" fill="#eeb086" />
        <circle cx="56" cy="60" r="28" fill={face} />
        <path d="M28 60q0-30 28-30 16 0 25 12l-12 3q-7-9-17-7-24 4-24 22Z" fill={hair} />
        <circle cx="71" cy="58" r="3.1" fill={eye} />
        <path d="M70 72q7 3 12 0" stroke={mouth} strokeWidth="2.6" fill="none" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg className="shot-svg" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden>
      <rect width="120" height="120" fill="#ffe0b0" />
      <rect x="52" y="86" width="16" height="18" rx="8" fill="#eeb086" />
      <circle cx="60" cy="62" r="30" fill={face} />
      <path d="M30 60q0-32 30-32t30 32q0-14-12-18-8-8-18-8t-18 8q-12 4-12 18Z" fill={hair} />
      <circle cx="50" cy="60" r="3.4" fill={eye} />
      <circle cx="70" cy="60" r="3.4" fill={eye} />
      <path d="M49 74q11 10 22 0" stroke={mouth} strokeWidth="3" fill="none" strokeLinecap="round" />
    </svg>
  );
}

const SHOTS: { kind: ShotKind; ok: boolean; label: string }[] = [
  { kind: "good", ok: true, label: "Nítida, bem iluminada e centralizada" },
  { kind: "multi", ok: false, label: "Mais de uma pessoa na foto" },
  { kind: "side", ok: false, label: "Rosto de lado" },
];

export function PhotoStandardTips() {
  return (
    <div className="photo-standard">
      <h3 className="field-label">Padrão visual da foto</h3>
      <p className="muted photo-standard-sub">
        Para criar o avatar, o rosto da criança precisa estar nesse padrão: uma criança, de
        frente, nítida e com o rosto no centro. Os exemplos com X mostram o que evitar.
      </p>
      <div className="shot-grid studio-shots">
        {SHOTS.map((s) => (
          <div className={`shot${s.ok ? " ok" : ""}`} key={s.kind}>
            <div className="shot-ava-wrap">
              <div className="shot-ava">
                <ShotArt kind={s.kind} />
              </div>
              <span className="shot-badge" aria-hidden>
                {s.ok ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <path d="M4 12.5l5 5L20 6.5" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <path d="M6 6l12 12M18 6L6 18" />
                  </svg>
                )}
              </span>
            </div>
            <p>{s.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

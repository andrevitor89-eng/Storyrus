type Props = {
  customVoiceAvailable: boolean;
  voiceName: string;
  setVoiceName: (v: string) => void;
  voiceUploading: boolean;
  locked: boolean;
  mediaConsent: boolean;
  onVoiceFile: (file: File | null) => void;
  voices: { id: string; name: string; is_default: boolean }[];
  selectedVoiceId: string;
  setSelectedVoiceId: (id: string) => void;
  removeSelectedVoice: () => void;
};

/** Narration voice clone / select UI (look preserved from Studio monolith). */
export function VoiceNarrationPanel({
  customVoiceAvailable,
  voiceName,
  setVoiceName,
  voiceUploading,
  locked,
  mediaConsent,
  onVoiceFile,
  voices,
  selectedVoiceId,
  setSelectedVoiceId,
  removeSelectedVoice,
}: Props) {
  return (
    <div
      className="result-block"
      style={{ marginBottom: 16 }}
      role="region"
      aria-labelledby="studio-voice-heading"
    >
      <h3 className="field-label" id="studio-voice-heading">Voz da narração</h3>
      {!customVoiceAvailable ? (
        <p className="muted">
          Voz personalizada indisponível (ElevenLabs não configurado). O vídeo narrado usará a
          narração padrão.
        </p>
      ) : (
        <>
          <p className="muted" style={{ marginBottom: 10 }} id="studio-voice-hint">
            Envie 30–60s de fala clara (MP3, WAV ou M4A), sem música de fundo. Fale naturalmente,
            como se estivesse contando uma história. A voz fica salva e pode ser reutilizada.
          </p>
          <div
            style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}
            role="group"
            aria-labelledby="studio-voice-heading"
          >
            <input
              type="text"
              value={voiceName}
              onChange={(e) => setVoiceName(e.target.value)}
              placeholder="Nome da voz"
              aria-label="Nome da voz"
            />
            <label className="btn" style={{ cursor: voiceUploading ? "wait" : "pointer" }}>
              {voiceUploading ? "Clonando..." : "Enviar áudio"}
              <input
                type="file"
                accept="audio/mpeg,audio/wav,audio/mp4,audio/x-m4a,audio/webm,audio/ogg,.mp3,.wav,.m4a,.webm,.ogg"
                hidden
                disabled={voiceUploading || locked || !mediaConsent}
                aria-label="Enviar áudio para clonar voz"
                aria-describedby="studio-voice-hint"
                onChange={(e) => onVoiceFile(e.target.files?.[0] || null)}
              />
            </label>
          </div>
          {voices.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
              <select
                value={selectedVoiceId}
                onChange={(e) => setSelectedVoiceId(e.target.value)}
                disabled={locked}
                aria-label="Selecionar voz da narração"
              >
                <option value="">Automática (padrão da conta ou sistema)</option>
                {voices.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                    {v.is_default ? " (padrão)" : ""}
                  </option>
                ))}
              </select>
              {selectedVoiceId && (
                <button type="button" disabled={locked} onClick={removeSelectedVoice}>
                  Remover voz
                </button>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

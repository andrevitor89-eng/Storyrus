import { STEPS } from "./constants";
import type { StudioStep } from "./useStudioSteps";

type EbookStepsProps = {
  locked: boolean;
  canMountEbook: boolean;
  runStep: (step: StudioStep) => void;
};

export function EbookStepButtons({ locked, canMountEbook, runStep }: EbookStepsProps) {
  return (
    <div className="steps" role="group" aria-label="Etapa do e-book">
      {STEPS.filter((s) => s.key === "ebook").map((s) => (
        <button
          key={s.key}
          type="button"
          title={s.hint}
          aria-label={`${s.label} (${s.cost}). ${s.hint}`}
          disabled={locked || !canMountEbook}
          onClick={() => runStep(s.key)}
          data-testid="studio-mount-ebook"
        >
          {s.label} <span className="muted">({s.cost})</span>
        </button>
      ))}
    </div>
  );
}

type VideoStepsProps = {
  locked: boolean;
  canMakeVideo: boolean;
  runStep: (step: StudioStep) => void;
};

export function VideoStepButtons({ locked, canMakeVideo, runStep }: VideoStepsProps) {
  return (
    <div className="steps" role="group" aria-label="Etapas de vídeo">
      {STEPS.filter((s) => s.key !== "ebook").map((s) => (
        <button
          key={s.key}
          type="button"
          title={s.hint}
          aria-label={`${s.label} (${s.cost}). ${s.hint}`}
          disabled={locked || !canMakeVideo}
          onClick={() => runStep(s.key)}
          data-testid={`studio-step-${s.key}`}
        >
          {s.label} <span className="muted">({s.cost})</span>
        </button>
      ))}
    </div>
  );
}

import { STEPS } from "./constants";
import type { StudioStep } from "./useStudioSteps";

type EbookStepsProps = {
  locked: boolean;
  canMountEbook: boolean;
  runStep: (step: StudioStep) => void;
};

export function EbookStepButtons({ locked, canMountEbook, runStep }: EbookStepsProps) {
  return (
    <div className="steps">
      {STEPS.filter((s) => s.key === "ebook").map((s) => (
        <button
          key={s.key}
          title={s.hint}
          disabled={locked || !canMountEbook}
          onClick={() => runStep(s.key)}
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
    <div className="steps">
      {STEPS.filter((s) => s.key !== "ebook").map((s) => (
        <button
          key={s.key}
          title={s.hint}
          disabled={locked || !canMakeVideo}
          onClick={() => runStep(s.key)}
        >
          {s.label} <span className="muted">({s.cost})</span>
        </button>
      ))}
    </div>
  );
}

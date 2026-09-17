import type { Job } from "../types";

export function ProgressList({ jobs }: { jobs: Job[] }) {
  if (jobs.length === 0) return null;
  return (
    <ul className="jobs">
      {jobs.map((j) => {
        const progress = j.result?.progress;
        const showPages =
          j.type === "EBOOK" &&
          (j.status === "RUNNING" || j.status === "PENDING") &&
          typeof progress?.done === "number" &&
          typeof progress?.total === "number";
        return (
          <li
            key={j.id}
            className={`job ${j.status.toLowerCase()}`}
            data-testid={`studio-job-${j.type}`}
            data-job-status={j.status}
          >
            <span className="dot" />
            <span className="jtype" data-testid={`studio-job-type-${j.type}`}>{j.type}</span>
            <span className="jstatus" data-testid={`studio-job-status-${j.type}`}>{j.status}</span>
            {showPages && (
              <span className="muted">
                Ilustrando {progress!.done}/{progress!.total}
              </span>
            )}
            {j.attempts > 1 && <span className="muted">tent. {j.attempts}</span>}
            {j.error && <span className="error">{j.error}</span>}
          </li>
        );
      })}
    </ul>
  );
}

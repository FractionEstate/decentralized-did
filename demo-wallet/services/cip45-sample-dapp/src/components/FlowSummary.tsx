import React from "react";

export type FlowStepStatus = "complete" | "active" | "pending" | "disabled";

export interface FlowSummaryStep {
  id: string;
  label: string;
  status: FlowStepStatus;
  description?: string;
  disabled?: boolean;
}

interface FlowSummaryProps {
  steps: FlowSummaryStep[];
  onSelect?: (stepId: string) => void;
}

const statusStyles: Record<FlowStepStatus, string> = {
  complete: "bg-emerald-500 text-white border-emerald-500",
  active: "bg-indigo-500 text-white border-indigo-500",
  pending: "bg-white text-slate-600 border-slate-300",
  disabled: "bg-slate-100 text-slate-400 border-slate-200",
};

const FlowSummary: React.FC<FlowSummaryProps> = ({ steps, onSelect }) => {
  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
        Flow overview
      </h2>
      <ul className="mt-4 space-y-4">
        {steps.map((step, index) => {
          const indicatorClass = statusStyles[step.status];
          const isClickable = Boolean(onSelect) && !step.disabled;

          return (
            <li key={step.id} className="flex items-start gap-3">
              <span
                className={`mt-1 flex h-6 w-6 items-center justify-center rounded-full border text-xs font-semibold ${indicatorClass}`}
              >
                {index + 1}
              </span>
              <div className="flex-1">
                <button
                  type="button"
                  className={`flex w-full flex-col items-start text-left transition ${isClickable ? "hover:text-indigo-600" : "cursor-default"
                    }`}
                  onClick={() => {
                    if (isClickable && onSelect) {
                      onSelect(step.id);
                    }
                  }}
                  disabled={!isClickable}
                >
                  <span className="text-sm font-medium text-slate-800 dark:text-slate-100">
                    {step.label}
                  </span>
                  {step.description ? (
                    <span className="mt-1 text-xs text-slate-500 dark:text-slate-300">
                      {step.description}
                    </span>
                  ) : null}
                </button>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export { FlowSummary };

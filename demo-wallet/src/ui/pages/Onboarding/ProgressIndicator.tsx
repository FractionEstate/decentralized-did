import "./ProgressIndicator.scss";

interface ProgressIndicatorProps {
  currentStep: number; // 1, 2, or 3
  totalSteps: number; // 3
}

const ProgressIndicator = ({
  currentStep,
  totalSteps,
}: ProgressIndicatorProps) => {
  const steps = Array.from({ length: totalSteps }, (_, i) => i + 1);

  return (
    <div className="progress-indicator">
      <div className="progress-dots">
        {steps.map((step) => (
          <div
            key={step}
            className={`progress-dot ${step <= currentStep ? "active" : "inactive"
              }`}
          >
            {step <= currentStep && <span className="dot-fill">●</span>}
            {step > currentStep && <span className="dot-empty">○</span>}
          </div>
        ))}
      </div>
      <p className="progress-text">
        Step {currentStep} of {totalSteps}
      </p>
    </div>
  );
};

export { ProgressIndicator };

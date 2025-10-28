import { useEffect, useState } from "react";
import "./ErrorMessage.scss";
import { ErrorMessageProps } from "./ErrorMessage.types";

const MESSAGE_MILLISECONDS = 1500;

const ErrorMessage = ({ message, timeout, action }: ErrorMessageProps) => {
  const [visible, setVisible] = useState(true);

  // Only start/destroy the timer when there is an actual message to show
  // This prevents stray timers when the component renders with no message
  useEffect(() => {
    if (!timeout) return;
    if (!message) return;

    setVisible(true);
    const timer = setTimeout(() => {
      setVisible(false);
    }, MESSAGE_MILLISECONDS);

    return () => {
      clearTimeout(timer);
    };
  }, [message, timeout]);

  return (
    <>
      {message ? (
        <div
          data-testid="error-message"
          className={`error-message ${visible ? "visible" : ""}`}
          role="alert"
          aria-live="assertive"
        >
          <p
            className="text-fadein"
            data-testid="error-message-text"
          >
            {message} {action}
          </p>
        </div>
      ) : (
        <div className="error-message-placeholder" aria-hidden="true" />
      )}
    </>
  );
};

export { MESSAGE_MILLISECONDS, ErrorMessage };

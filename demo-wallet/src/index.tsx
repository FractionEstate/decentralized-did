import ReactDOM from "react-dom/client";
import { Provider } from "react-redux";
import { App } from "./ui/App";
import reportWebVitals from "./reportWebVitals";
import "./i18n";
import { store } from "./store";
import { ConfigurationService } from "./core/configuration";

// Global error handler to catch NotFoundError
window.addEventListener('error', (event) => {
  if (event.error?.name === 'NotFoundError') {
    console.error('🔍 [Global] NotFoundError detected:', {
      message: event.error.message,
      stack: event.error.stack,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    });
  }
});

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
  if (event.reason?.name === 'NotFoundError') {
    console.error('🔍 [Global] Unhandled NotFoundError in promise:', {
      message: event.reason.message,
      stack: event.reason.stack,
      promise: event.promise,
    });
  }
});

await new ConfigurationService().start();
const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);
root.render(
  <Provider store={store}>
    <App />
  </Provider>
);

reportWebVitals();

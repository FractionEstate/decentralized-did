import React from "react";

export type LayoutMode = "single" | "split";
export type ThemeMode = "neutral" | "cardano";
export type DensityMode = "comfortable" | "compact";
export type FlowMode = "guided" | "free";
export type ConfigurableSection = "metadata" | "signer" | "transmission" | "logs";

export interface UiSettings {
  layout: LayoutMode;
  theme: ThemeMode;
  density: DensityMode;
  flowMode: FlowMode;
  sections: Record<ConfigurableSection, boolean>;
}

export const defaultUiSettings: UiSettings = {
  layout: "split",
  theme: "neutral",
  density: "comfortable",
  flowMode: "guided",
  sections: {
    metadata: true,
    signer: true,
    transmission: true,
    logs: true,
  },
};

interface FlowConfiguratorProps {
  settings: UiSettings;
  onChange: (settings: UiSettings) => void;
}

const sectionOptions: Array<{
  id: ConfigurableSection;
  title: string;
  description: string;
}> = [
    {
      id: "metadata",
      title: "Metadata preview",
      description: "Show the decoded CIP-30 payload and helper summary.",
    },
    {
      id: "signer",
      title: "Signature actions",
      description: "Enable signing demo payloads with the connected wallet.",
    },
    {
      id: "transmission",
      title: "Metadata submission",
      description: "Allow sending the biometric metadata via experimental.tx.send.",
    },
    {
      id: "logs",
      title: "Activity log",
      description: "Display signature output and status updates.",
    },
  ];

const layoutLabels: Record<LayoutMode, string> = {
  single: "Single column",
  split: "Responsive split",
};

const themeLabels: Record<ThemeMode, string> = {
  neutral: "Neutral",
  cardano: "Cardano gradient",
};

const densityLabels: Record<DensityMode, string> = {
  comfortable: "Comfortable",
  compact: "Compact",
};

const flowLabels: Record<FlowMode, string> = {
  guided: "Guided steps",
  free: "Freeform",
};

const FlowConfigurator: React.FC<FlowConfiguratorProps> = ({ settings, onChange }) => {
  const update = (partial: Partial<UiSettings>) => {
    onChange({ ...settings, ...partial });
  };

  const updateSections = (id: ConfigurableSection, value: boolean) => {
    onChange({
      ...settings,
      sections: {
        ...settings.sections,
        [id]: value,
      },
    });
  };

  const reset = () => onChange(defaultUiSettings);

  return (
    <section className="card gap-4 p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
            UI configuration
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-300">
            Adjust layout, theme, and available flow steps. Settings persist in the browser.
          </p>
        </div>
        <button
          className="rounded-md border border-slate-300 bg-white px-3 py-1 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
          onClick={reset}
          type="button"
        >
          Reset defaults
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-3">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
            Layout
          </label>
          <select
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring"
            value={settings.layout}
            onChange={(event) => update({ layout: event.target.value as LayoutMode })}
          >
            {Object.entries(layoutLabels).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-3">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
            Theme
          </label>
          <select
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring"
            value={settings.theme}
            onChange={(event) => update({ theme: event.target.value as ThemeMode })}
          >
            {Object.entries(themeLabels).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-3">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
            Density
          </label>
          <select
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring"
            value={settings.density}
            onChange={(event) => update({ density: event.target.value as DensityMode })}
          >
            {Object.entries(densityLabels).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-3">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
            Flow mode
          </label>
          <select
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring"
            value={settings.flowMode}
            onChange={(event) => update({ flowMode: event.target.value as FlowMode })}
          >
            {Object.entries(flowLabels).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {sectionOptions.map((section) => (
          <label
            key={section.id}
            className="flex cursor-pointer select-none items-start gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 shadow-sm transition hover:border-indigo-400"
          >
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              checked={settings.sections[section.id]}
              onChange={(event) => updateSections(section.id, event.target.checked)}
            />
            <span>
              <span className="block text-sm font-medium text-slate-800 dark:text-slate-100">
                {section.title}
              </span>
              <span className="mt-0.5 block text-xs text-slate-500 dark:text-slate-300">
                {section.description}
              </span>
            </span>
          </label>
        ))}
      </div>
    </section>
  );
};

export { FlowConfigurator };

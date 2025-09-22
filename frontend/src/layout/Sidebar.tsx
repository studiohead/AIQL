import React from "react";
import Button from "../components/Button"; // Adjust path if needed
import { PromptUIResponse } from "../utils/mockAI";

interface SidebarProps {
  uiConfig: PromptUIResponse | null;
  userInputs: Record<string, any>;
  onChange: (inputs: Record<string, any>) => void;
  onSubmit: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ uiConfig, userInputs, onChange, onSubmit }) => {
  if (!uiConfig) {
    return <div style={{ padding: "1rem" }}>No configuration to show</div>;
  }

  return (
    <aside
      style={{
        width: 300,
        padding: "1rem",
        borderRight: "1px solid #ddd",
        overflowY: "auto",
      }}
    >
      {/* Render Data Inputs */}
      {uiConfig.dataInputs.map(({ label, type, id }) => (
        <div key={id} style={{ marginBottom: "1rem" }}>
          <label htmlFor={id}>{label}</label>
          {type === "file" ? (
            <input
              id={id}
              type="file"
              onChange={(e) =>
                onChange({ ...userInputs, [id]: e.target.files ? e.target.files[0] : null })
              }
              style={{ width: "100%", padding: "0.5rem", marginTop: "0.25rem" }}
            />
          ) : (
            <input
              id={id}
              type={type}
              value={userInputs[id] || ""}
              onChange={(e) => onChange({ ...userInputs, [id]: e.target.value })}
              style={{ width: "100%", padding: "0.5rem", marginTop: "0.25rem" }}
            />
          )}
        </div>
      ))}

      {/* Render Model Options if any */}
      {uiConfig.modelOptions && (
        <div style={{ marginBottom: "1rem" }}>
          <label htmlFor={uiConfig.modelOptions.id}>{uiConfig.modelOptions.label}</label>
          <select
            id={uiConfig.modelOptions.id}
            value={userInputs[uiConfig.modelOptions.id] || uiConfig.modelOptions.options[0]}
            onChange={(e) => onChange({ ...userInputs, [uiConfig.modelOptions.id]: e.target.value })}
            style={{ width: "100%", padding: "0.5rem", marginTop: "0.25rem" }}
          >
            {uiConfig.modelOptions.options.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Render Parameters if any */}
      {uiConfig.parameters?.map(({ label, type, id, default: def }) => {
        const value = userInputs[id] ?? def ?? "";
        return (
          <div key={id} style={{ marginBottom: "1rem" }}>
            <label htmlFor={id}>{label}</label>
            {type === "checkbox" ? (
              <input
                id={id}
                type="checkbox"
                checked={!!value}
                onChange={(e) => onChange({ ...userInputs, [id]: e.target.checked })}
                style={{ marginLeft: "0.5rem" }}
              />
            ) : (
              <input
                id={id}
                type={type}
                value={value}
                onChange={(e) => onChange({ ...userInputs, [id]: e.target.value })}
                style={{ width: "100%", padding: "0.5rem", marginTop: "0.25rem" }}
              />
            )}
          </div>
        );
      })}

      {/* Submit button */}
      <Button
        variant="primary"
        style={{ marginTop: "1rem", width: "100%", padding: "0.75rem" }}
        onClick={onSubmit}
      >
        Submit
      </Button>
    </aside>
  );
};

export default Sidebar;

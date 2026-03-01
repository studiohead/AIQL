import React from "react";
import Button from "../components/Button";
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
    <aside className="sidebar">
      {/* Render Data Inputs */}
      {uiConfig.dataInputs.map(({ label, type, id }) => (
        <div key={id} style={{ marginBottom: "1rem" }}>
          <label htmlFor={id}>{label}</label>

          {type === "file" ? (
            <div className="file-upload">
              <label htmlFor={id} className="file-upload-label">
                Choose File
              </label>
              <input
                id={id}
                type="file"
                onChange={(e) =>
                  onChange({ ...userInputs, [id]: e.target.files ? e.target.files[0] : null })
                }
              />
              {userInputs[id] && (
                <p className="file-name">
                  {userInputs[id].name || "File selected"}
                </p>
              )}
            </div>
          ) : (
            <input
              id={id}
              type={type}
              value={userInputs[id] || ""}
              onChange={(e) => onChange({ ...userInputs, [id]: e.target.value })}
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
              />
            )}
          </div>
        );
      })}

      {/* Submit button */}
      <Button variant="primary" style={{ marginTop: "1rem", width: "100%" }} onClick={onSubmit}>
        Submit
      </Button>
    </aside>
  );
};

export default Sidebar;

// frontend/src/components/PromptInput.tsx
import React, { useState } from "react";

interface PromptInputProps {
  onSubmit: (prompt: string) => void;
  initialValue?: string;
}

const PromptInput: React.FC<PromptInputProps> = ({ onSubmit, initialValue = "" }) => {
  const [prompt, setPrompt] = useState(initialValue);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim()) {
      onSubmit(prompt.trim());
      setPrompt("");
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: "1rem" }}>
      <input
        type="text"
        placeholder="What do you want to do?"
        value={prompt}
        onChange={(e) => setPrompt(e.currentTarget.value)}
        style={{
          width: "100%",
          padding: "0.5rem",
          fontSize: "1rem",
          borderRadius: "4px",
          border: "1px solid #ccc",
          boxSizing: "border-box",
        }}
        required
        autoComplete="off"
      />
    </form>
  );
};

export default PromptInput;

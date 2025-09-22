import React from "react";
import PromptInput from "../components/PromptInput";

interface DashboardProps {
  onPromptSubmit: (prompt: string) => void;
  userPrompt?: string;
  pipelineResult?: any;
}

const Dashboard: React.FC<DashboardProps> = ({ onPromptSubmit, userPrompt, pipelineResult }) => {
  return (
    <div style={{ width: "100%", maxWidth: 600 }}>
      <PromptInput onSubmit={onPromptSubmit} />

      {userPrompt && (
        <div style={{ marginTop: "1rem", fontStyle: "italic", color: "#555" }}>
          Prompt: <strong>{userPrompt}</strong>
        </div>
      )}

      <section style={{ marginTop: "2rem" }}>
        {!pipelineResult}
        {pipelineResult && (
          <div style={{ fontSize: "1.2rem" }}>
            <p>
              <strong>Churn Probability:</strong> {(pipelineResult.churn_probability * 100).toFixed(2)}%
            </p>
            <p>
              <strong>Confidence Score:</strong> {(pipelineResult.confidence_score * 100).toFixed(2)}%
            </p>
            <p>
              <strong>Explanation:</strong> {pipelineResult.explanation}
            </p>
          </div>
        )}
      </section>
    </div>
  );
};

export default Dashboard;

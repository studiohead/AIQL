import React from "react";
import PromptInput from "../components/PromptInput";
import GenericGraph from "../components/GenericGraph";

interface DashboardProps {
  onPromptSubmit: (prompt: string) => void;
  userPrompt?: string;
  pipelineResult?: any;
}

const Dashboard: React.FC<DashboardProps> = ({
  onPromptSubmit,
  userPrompt,
  pipelineResult,
}) => {
  const graphData = pipelineResult
    ? [
        {
          label: "Cause Probability",
          value: parseFloat(
            (pipelineResult.cause_probability * 100).toFixed(2)
          ),
        },
        {
          label: "Confidence Score",
          value: parseFloat(
            (pipelineResult.confidence_score * 100).toFixed(2)
          ),
        },
      ]
    : [];

  return (
    <div style={{ width: "100%", maxWidth: 600 }}>
      <PromptInput onSubmit={onPromptSubmit} />

      {userPrompt && (
        <div style={{ marginTop: "1rem", fontStyle: "italic", color: "#555" }}>
          Prompt: <strong>{userPrompt}</strong>
        </div>
      )}

      <section style={{ marginTop: "2rem" }}>
        {pipelineResult && (
          <>
            <div style={{ fontSize: "1.2rem" }}>
              <p>
                <strong>Cause Probability:</strong>{" "}
                {(pipelineResult.cause_probability * 100).toFixed(2)}%
              </p>
              <p>
                <strong>Confidence Score:</strong>{" "}
                {(pipelineResult.confidence_score * 100).toFixed(2)}%
              </p>
              <p>
                <strong>Explanation:</strong> {pipelineResult.explanation}
              </p>
            </div>

            {/* ✅ Dynamic graph */}
            <GenericGraph
              data={graphData}
              xKey="label"
              yKey="value"
              chartType="bar"
              title="Result Metrics"
            />
          </>
        )}
      </section>
    </div>
  );
};

export default Dashboard;

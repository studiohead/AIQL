// frontend/src/components/PipelineRunner.tsx
import React, { useState } from "react";

interface PipelineRunnerProps {
  pipelineInput: string;
  onInputChange: (input: string) => void;
  pipelineResult: any;
  onResultChange: (result: any) => void;
}

const PipelineRunner: React.FC<PipelineRunnerProps> = ({
  pipelineInput,
  onInputChange,
  pipelineResult,
  onResultChange,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runPipeline = async () => {
    setError(null);

    let pipelineJson;
    try {
      pipelineJson = JSON.parse(pipelineInput);
    } catch (e) {
      setError("Invalid JSON: " + (e as Error).message);
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("http://localhost:8888/api/run-pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pipelineJson),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }

      const data = await response.json();
      onResultChange(data.result);
    } catch (err) {
      setError("Error: " + (err as Error).message);
      onResultChange(null);
    } finally {
      setLoading(false);
    }
  };

  const renderResults = () => {
    if (!pipelineResult) {
      return <p>No results to display.</p>;
    }

    const {
      cause_probability,
      confidence_score,
      segmentation_result,
      customer_flagged,
    } = pipelineResult;

    return (
      <div>
        {cause_probability !== undefined && (
          <div style={{ marginTop: "10px" }}>
            <strong>Cause Probability:</strong>{" "}
            {(cause_probability * 100).toFixed(2)}%
            <div
              style={{
                background: "#ddd",
                width: "100%",
                height: "20px",
                marginTop: "4px",
                position: "relative",
              }}
            >
              <div
                style={{
                  background: "#f00",
                  width: `${cause_probability * 100}%`,
                  height: "100%",
                  position: "absolute",
                  top: 0,
                  left: 0,
                }}
              />
            </div>
          </div>
        )}

        {confidence_score !== undefined && (
          <p>
            <strong>Confidence Score:</strong>{" "}
            {(confidence_score * 100).toFixed(1)}%
          </p>
        )}

        {segmentation_result && (
          <p>
            <strong>Segment:</strong> {segmentation_result}
          </p>
        )}

        {customer_flagged !== undefined && (
          <p>
            <strong>Customer Flagged:</strong>{" "}
            {customer_flagged ? "✅" : "❌"}
          </p>
        )}

        {/* Fallback raw JSON */}
        {cause_probability === undefined &&
          confidence_score === undefined &&
          !segmentation_result &&
          customer_flagged === undefined && (
            <pre>{JSON.stringify(pipelineResult, null, 2)}</pre>
          )}
      </div>
    );
  };

  return (
    <section>
      <h2>Run AIQL Pipeline</h2>

      <textarea
        rows={15}
        style={{ width: "100%", fontFamily: "monospace", fontSize: 14 }}
        value={pipelineInput}
        onChange={(e) => onInputChange(e.target.value)}
        aria-label="Pipeline JSON input"
      />

      <button
        onClick={runPipeline}
        disabled={loading}
        style={{ marginTop: 10, padding: "10px 20px", fontSize: 16 }}
      >
        {loading ? "Running..." : "Run Pipeline"}
      </button>

      <div style={{ marginTop: 20 }}>
        {error && <p style={{ color: "red" }}>{error}</p>}

        {!error && renderResults()}
      </div>
    </section>
  );
};

export default PipelineRunner;

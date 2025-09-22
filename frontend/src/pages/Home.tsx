// frontend/src/pages/Home.tsx

import React, { useState } from "react";
import PipelineRunner from "../components/PipelineRunner";

const Home: React.FC = () => {
  // Optional: you can prefill with an example pipeline JSON string
  const [pipelineJson, setPipelineJson] = useState<string>(`{
  "type": "Program",
  "body": [
    {
      "type": "LoadStatement",
      "variable": "llm_data",
      "source": "database",
      "query": "SELECT * FROM llm_metrics"
    },
    {
      "type": "PipelineStatement",
      "variable": "trust_analysis",
      "source": "llm_data",
      "steps": [
        {
          "type": "CallStatement",
          "call_type": "model",
          "action": "LLMTrustModel",
          "inputs": ["llm_data"],
          "outputs": ["trust_summary"],
          "params": {}
        }
      ]
    },
    {
      "type": "ReturnStatement",
      "variable": "trust_analysis"
    }
  ]
}`);

  return (
    <main className="container" style={{ padding: "2rem 0" }}>
      <h1>Welcome to AIQL Pipeline Runner</h1>
      <p>Paste your AIQL pipeline JSON below and run it to see the results.</p>

      <PipelineRunner initialPipeline={pipelineJson} />
    </main>
  );
};

export default Home;

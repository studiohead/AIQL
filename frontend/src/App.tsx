// frontend/src/App.tsx
import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Topbar from "./layout/Topbar";
import Sidebar from "./layout/Sidebar";
import Home from "./pages/Home";
import Dashboard from "./containers/Dashboard";
import { interpretPrompt, PromptUIResponse } from "./utils/mockAI";

const App: React.FC = () => {
  const [userPrompt, setUserPrompt] = useState("");
  const [uiConfig, setUiConfig] = useState<PromptUIResponse | null>(null);
  const [userInputs, setUserInputs] = useState<Record<string, any>>({});
  const [pipelineResult, setPipelineResult] = useState<any>(null);

  // Handle prompt submission
  const handlePromptSubmit = (prompt: string) => {
    const cleanedPrompt = prompt.trim();
    setUserPrompt(cleanedPrompt);
    const config = interpretPrompt(cleanedPrompt);
    setUiConfig(config);
    setUserInputs({});
    setPipelineResult(null);
  };

  // Handle sidebar submit
  const handleSidebarSubmit = () => {
    console.log("Sidebar submit clicked!", userPrompt, userInputs);

    if (userPrompt.toLowerCase().includes("churn")) {
      setTimeout(() => {
        setPipelineResult({
          cause_probability: 0.9,
          confidence_score: 0.9,
          explanation: "High risk based on recent purchase behavior",
        });
      }, 1000);
    }
    if (userPrompt.toLowerCase().includes("fire")) {
      setTimeout(() => {
        setPipelineResult({
          cause_probability: 0.9,
          confidence_score: 0.9,
          explanation: "Protocol section 2.6 violation",
        });
      }, 1000);
    }
  };

  return (
    <Router>
      <div className="app-container">
        <Topbar />

        <Routes>
          <Route
            path="/dashboard"
            element={
              !uiConfig ? (
                <div className="dashboard-centered">
                  <Dashboard onPromptSubmit={handlePromptSubmit} />
                </div>
              ) : (
                <div className="dashboard-layout">
                  <Sidebar
                    uiConfig={uiConfig}
                    userInputs={userInputs}
                    onChange={setUserInputs}
                    onSubmit={handleSidebarSubmit}
                  />
                  <main className="dashboard-main">
                    <Dashboard
                      onPromptSubmit={handlePromptSubmit}
                      userPrompt={userPrompt}
                      pipelineResult={pipelineResult}
                    />
                  </main>
                </div>
              )
            }
          />
          <Route path="/" element={<Home />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;

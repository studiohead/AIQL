// frontend/src/utils/mockAI.ts
export interface PromptUIResponse {
  dataInputs: Array<{ label: string; type: "file" | "text"; id: string }>;
  modelOptions?: {
    label: string;
    id: string;
    options: string[];
  };
  parameters?: Array<{
    label: string;
    type: "number" | "checkbox" | "text";
    id: string;
    default?: any;
  }>;
}

export const interpretPrompt = (prompt: string): PromptUIResponse | null => {
  const cleaned = prompt.toLowerCase();

  if (cleaned.includes("churn")) {
    return {
      dataInputs: [{ label: "Customer CSV", type: "file", id: "customer_file" }],
      modelOptions: {
        label: "Select Churn Model",
        id: "model_select",
        options: ["ChurnPredictionModel", "ChurnPredictorV2"],
      },
      parameters: [
        { label: "Threshold", type: "number", id: "threshold", default: 0.7 }
      ],
    };
  }

  if (cleaned.includes("summarize") && cleaned.includes("audit")) {
    return {
      dataInputs: [{ label: "Audit Logs", type: "file", id: "audit_file" }],
      modelOptions: {
        label: "Summarization Model",
        id: "model_select",
        options: ["SummarizeAuditTrail", "FastAuditSummary"],
      },
      parameters: [{ label: "Max Tokens", type: "number", id: "max_tokens", default: 512 }],
    };
  }

  return null;
};

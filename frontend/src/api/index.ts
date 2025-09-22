export interface PipelineResponse {
  result: Record<string, any>;
  [key: string]: any; // allow additional fields if any
}

const API_BASE_URL = "http://localhost:8000/api";

export async function runPipeline(pipelineJson: object): Promise<PipelineResponse> {
  const response = await fetch(`${API_BASE_URL}/run-pipeline`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(pipelineJson),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error: ${response.status} ${response.statusText} - ${errorText}`);
  }

  const data: PipelineResponse = await response.json();
  return data;
}

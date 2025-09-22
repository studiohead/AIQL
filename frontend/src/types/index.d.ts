// frontend/src/types/index.d.ts

export interface PipelineStep {
  type: string;
  variable?: string;
  source?: string;
  query?: string;
  steps?: PipelineStep[];
  call_type?: string;
  action?: string;
  inputs?: string[];
  outputs?: string[];
  params?: Record<string, any>;
}

export interface PipelineProgram {
  type: "Program";
  body: PipelineStep[];
}

export interface ModelOutput {
  [key: string]: any;
}

export interface PipelineResult {
  result: ModelOutput;
  [key: string]: any;
}

export interface ApiResponse {
  status: string;
  message?: string;
  result?: PipelineResult;
}

export interface TrustSummary {
  trust_summary: number;
}

export interface ChurnProbabilities {
  [customerId: string]: number;
}

export interface CustomerSegments {
  [customerId: string]: string;
}

export interface RunPipelineRequest {
  pipeline: PipelineProgram;
}

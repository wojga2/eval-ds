export interface TurnContent {
  speaker: string;
  content?: string;
  tool_call?: any;
  tool_result?: any;
  thinking?: string;
}

export interface OpenCoding {
  descriptive_summary: string;
  failure_point_turn?: number;
  detailed_analysis: string;
  issues_identified: string[];
  observations: string;
  recommendations: string;
}

export interface AxialCoding {
  primary_code: string;
  secondary_codes: string[];
  severity: string;
  rationale: string;
}

export interface EvalMetrics {
  success: boolean;
  reward: number;
  total_reward?: number;
  checks?: any;
}

export interface TaskSample {
  sample_id: string;
  task_name?: string;
  conversation: TurnContent[];
  eval_metrics: EvalMetrics;
  open_coding: OpenCoding;
  axial_coding: AxialCoding;
}

export interface ProjectInfo {
  name: string;
  path: string;
  num_samples: number;
  num_success: number;
  num_failed: number;
  axial_codes: string[];
}

export interface FilterParams {
  axial_codes: string[];
  pass_fail?: 'pass' | 'fail' | null;
}


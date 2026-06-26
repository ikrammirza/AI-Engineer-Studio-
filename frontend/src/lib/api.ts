const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem("token");

  const isFormData = options.body instanceof FormData;

  const res = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }

  return res.json();
}


// ================= AUTH =================

export const auth = {
  signup: (email: string, password: string, full_name?: string) =>
    apiRequest("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),

  login: async (email: string, password: string) => {
    const data = await apiRequest<{
      access_token: string;
      token_type: string;
    }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    localStorage.setItem("token", data.access_token);

    return data;
  },

  me: () => apiRequest("/auth/me"),

  logout: () => localStorage.removeItem("token"),
};


// ================= PROMPTS =================

export type PromptVersion = {
  id: string;
  prompt_id: string;
  version_number: number;
  content: string;
  commit_message: string | null;
  model_used: string | null;
  variables: string[];
  created_at: string;
};


export type Prompt = {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
  latest_version: PromptVersion | null;
  version_count: number;
};


export const prompts = {

  list: () =>
    apiRequest<Prompt[]>("/prompts"),


  get: (id: string) =>
    apiRequest<Prompt>(`/prompts/${id}`),


  create: (data: {
    name: string;
    description?: string;
    content: string;
    commit_message?: string;
  }) =>
    apiRequest<Prompt>("/prompts", {
      method: "POST",
      body: JSON.stringify(data),
    }),


  update: (
    id: string,
    data: {
      name?: string;
      description?: string;
    }
  ) =>
    apiRequest<Prompt>(`/prompts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),


  delete: (id: string) =>
    apiRequest(`/prompts/${id}`, {
      method: "DELETE",
    }),


  listVersions: (id: string) =>
    apiRequest<PromptVersion[]>(`/prompts/${id}/versions`),


  saveVersion: (
    id: string,
    data: {
      content: string;
      commit_message?: string;
      model_used?: string;
    }
  ) =>
    apiRequest<PromptVersion>(`/prompts/${id}/versions`, {
      method: "POST",
      body: JSON.stringify(data),
    }),


  interpolate: (
    content: string,
    variables: Record<string,string>
  ) =>
    apiRequest<{
      result:string;
      variables_found:string[];
      variables_missing:string[];
    }>("/prompts/interpolate",{
      method:"POST",
      body:JSON.stringify({
        content,
        variables
      })
    }),
};



// ================= PLAYGROUND =================


export type ModelDefinition = {
  key:string;
  name:string;
  provider:string;
  max_tokens:number;
  input_cost_per_1k:number;
  output_cost_per_1k:number;
};


export type ModelResult = {
  model_key:string;
  model_name:string;
  provider:string;
  output:string;
  input_tokens:number;
  output_tokens:number;
  cost_usd:number;
  latency_ms:number;
  error:string|null;
};


export type PlaygroundRunResponse = {
  results:ModelResult[];
  total_cost_usd:number;
  prompt:string;
};


export const playground = {


  models: () =>
    apiRequest<ModelDefinition[]>("/playground/models"),


  run: (data:{
    prompt:string;
    system?:string;
    model_keys:string[];
  }) =>
    apiRequest<PlaygroundRunResponse>(
      "/playground/run",
      {
        method:"POST",
        body:JSON.stringify(data)
      }
    ),

};



// ================= EVALUATION =================


export type Dataset = {
  id:string;
  name:string;
  description:string|null;
  row_count:number;
  created_at:string;
};


export type DatasetDetail = Dataset & {
  rows:{
    question:string;
    expected:string;
  }[];
};


export type QuestionResult = {
  question:string;
  expected:string;
  actual:string;
  score:number;
  passed:boolean;
  reasoning:string|null;
};


export type EvaluationRun = {
  id:string;
  dataset_id:string;
  prompt_id:string|null;
  model_key:string;
  scoring_method:string;
  status:string;
  accuracy:number|null;
  avg_score:number|null;
  results:QuestionResult[];
  prompt_version_number:number|null;
  created_at:string;
  completed_at:string|null;
};



export const evaluation = {


  uploadDataset:(formData:FormData)=>
    apiRequest<Dataset>(
      "/evaluation/datasets",
      {
        method:"POST",
        body:formData
      }
    ),


  listDatasets:() =>
    apiRequest<Dataset[]>(
      "/evaluation/datasets"
    ),


  getDataset:(id:string)=>
    apiRequest<DatasetDetail>(
      `/evaluation/datasets/${id}`
    ),


  runEvaluation:(data:{
    dataset_id:string;
    prompt_id:string;
    model_key:string;
    scoring_method:string;
  }) =>
    apiRequest<EvaluationRun>(
      "/evaluation/runs",
      {
        method:"POST",
        body:JSON.stringify(data)
      }
    ),


  listRuns:() =>
    apiRequest<EvaluationRun[]>(
      "/evaluation/runs"
    ),


  getRun:(id:string)=>
    apiRequest<EvaluationRun>(
      `/evaluation/runs/${id}`
    ),

};
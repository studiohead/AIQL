# AIQL: AI Query Language

**AIQL** is a structured query and pipeline language designed to orchestrate AI workflows safely and efficiently. Pipelines are expressed as **ASTs (Abstract Syntax Trees)**, enabling precise, verifiable execution of multi-step AI tasks.

---

## Project Structure

- **ast/**: JSON schema and examples for AIQL ASTs.  
- **engine/**: Core interpreter and pipeline execution logic.  
- **frontend/**: Visual pipeline builder and UI components.  
- **pipelines/**: Saved AIQL pipeline files.

```
.
├── README.md
├── app.py
├── ast
│ ├── aiql_schema.json
│ └── example_pipeline.json
├── engine
│ ├── data_handler.py
│ ├── interpreter.py
│ └── model_manager.py
├── frontend
│ ├── index.html
│ ├── src
│ │ ├── App.tsx
│ │ ├── components
│ │ │ ├── Button.tsx
│ │ │ ├── PipelineRunner.tsx
│ │ │ └── PromptInput.tsx
│ │ ├── containers
│ │ │ └── Dashboard.tsx
│ │ ├── hooks
│ │ │ └── useFetch.ts
│ │ ├── layout
│ │ │ ├── Sidebar.tsx
│ │ │ └── Topbar.tsx
│ │ ├── pages
│ │ │ └── Home.tsx
│ │ └── utils
│ │ ├── formatDate.ts
│ │ └── mockAI.ts
│ ├── package.json
│ └── tsconfig.json
├── pipelines
│ └── sample_pipeline.aiql
└── run.sh
```

---

## System Prompt

AIQL leverages the AST for precise control:


You are an AI programmer. Convert user requests into ASTs for execution.
If information is missing or ambiguous, ask a clarifying question.
Only populate AST nodes when confident.


---

## Example AIQL Pipeline

```
{
"type": "Program",
"body": [
{
"type": "LoadStatement",
"variable": "customer_data",
"source": "database",
"query": "SELECT * FROM customers"
},
{
"type": "PipelineStatement",
"variable": "features",
"source": "customer_data",
"steps": [
{
"type": "Operation",
"name": "FeatureEngineering",
"inputs": ["customer_data"],
"output": "engineered_features",
"params": {
"method": "standardize",
"features": ["age", "income", "tenure"]
}
},
{
"type": "CallStatement",
"call_type": "model",
"action": "churn_predictor_v1",
"inputs": ["engineered_features"],
"outputs": ["cause_probability", "confidence_score"],
"params": {}
}
]
},
{
"type": "ReturnStatement",
"variable": "cause_probability"
}
]
}
```

This pipeline:

1. Loads customer data from a database.  
2. Performs feature engineering to standardize selected columns.  
3. Runs a model (`churn_predictor_v1`) to predict customer churn probability.  
4. Returns the primary output (`cause_probability`).

---

## Getting Started

1. Navigate to the project directory.  
2. Build or extend pipelines in **pipelines/** or components in **frontend/** and **engine/**.  
3. Execute a sample pipeline:

```
python engine/interpreter.py ast/example_pipeline.json
```
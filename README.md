<img width="2420" height="1460" alt="image" src="https://github.com/user-attachments/assets/384c5994-eecc-44d8-8108-25e24d52f4c0" />

# AIQL: AI Query Language

AIQL is a structured query and pipeline language designed to orchestrate AI workflows safely and efficiently. Pipelines are expressed as ASTs (Abstract Syntax Trees), enabling precise, verifiable execution of multi-step AI tasks. This design is a valuable component of a project called KAI: Kernel AI Operating System: https://github.com/studiohead/KAI

---

## Project Structure

```
.
├── README.md
├── app.py
├── ast
│   ├── aiql_schema.json        # JSON Schema (draft-07) for all AST node types
│   └── example_pipeline.json   # Annotated example pipeline
├── engine
│   ├── data_handler.py
│   ├── interpreter.py          # Core AST walker and execution engine
│   └── model_manager.py
├── frontend
│   ├── index.html
│   └── src
│       ├── App.tsx
│       ├── components
│       │   ├── Button.tsx
│       │   ├── PipelineRunner.tsx
│       │   └── PromptInput.tsx
│       ├── containers
│       │   └── Dashboard.tsx
│       ├── hooks
│       │   └── useFetch.ts
│       ├── layout
│       │   ├── Sidebar.tsx
│       │   └── Topbar.tsx
│       ├── pages
│       │   └── Home.tsx
│       └── utils
│           ├── formatDate.ts
│           └── mockAI.ts
├── pipelines
│   └── sample_pipeline.aiql
└── run.sh
```

---

## System Prompt

AIQL leverages the AST for precise control. The recommended system prompt for AI-assisted pipeline generation:

> You are an AI programmer. Convert user requests into AIQL ASTs for execution.
> If information is missing or ambiguous, ask a clarifying question.
> Only populate AST nodes when confident.

---

## Core Concepts

### Statements

A Program is a list of statements executed in order. The interpreter supports five statement types:

| Type | Purpose |
|---|---|
| `LoadStatement` | Load a dataset from a source (database, file, API) |
| `PipelineStatement` | Chain operations and model calls over a dataset |
| `CallStatement` | Invoke a model, LLM, classifier, or function |
| `ConditionalStatement` | Branch on a boolean expression |
| `ReturnStatement` | Resolve a variable and return it as the program output |

### Call Types

`CallStatement` supports the following `call_type` values:

| Value | Description |
|---|---|
| `classifier` | Runs a classification model; outputs per-item scores |
| `llm` | Calls a large language model with a prompt template |
| `model` | Generic model call (legacy alias for `classifier`) |
| `function` | Calls a named utility function |
| `visualize` | Renders an output visualisation (not yet implemented) |

---

## Intent System

Pipelines support an optional `intent` field at both the **Program** and **PipelineStatement** level. Intent is progressive — add only as much structure as your use case requires.

### Level 0 — No Intent

Plain dataflow. No planning, no fallback. The pipeline runs exactly as written.

```json
{
  "type": "Program",
  "body": [...]
}
```

### Level 1 — Soft Intent

A plain string. Stored for introspection and logging; an AI planner can use it to validate or narrate the pipeline. No runtime behaviour changes.

```json
{
  "type": "Program",
  "intent": "predict customer churn",
  "body": [...]
}
```

### Level 2 — Structured Intent

A full intent object. The interpreter evaluates `success_metric` after the program body completes and triggers `fallback` if the metric fails.

```json
{
  "type": "Program",
  "intent": {
    "goal": "predict_customer_churn",
    "description": "Score active customers for churn risk with high confidence.",
    "success_metric": "confidence_score >= 0.7",
    "fallback": "escalate_to_human_review"
  },
  "body": [...]
}
```

| Field | Required | Description |
|---|---|---|
| `goal` | ✅ | Short identifier for the program's objective |
| `description` | ❌ | Human-readable explanation |
| `success_metric` | ❌ | Expression evaluated post-run; triggers fallback on failure |
| `fallback` | ❌ | Name of a function action to call when the metric fails |

> **Pipeline-level intent** is descriptive only. `success_metric` and `fallback` are evaluated at the Program level only.

---

## Example Pipeline

A full Level 2 pipeline showing all major features:

```json
{
  "type": "Program",
  "intent": {
    "goal": "predict_customer_churn",
    "description": "Score active customers for churn risk with high confidence.",
    "success_metric": "confidence_score >= 0.7",
    "fallback": "escalate_to_human_review"
  },
  "body": [
    {
      "type": "LoadStatement",
      "variable": "customer_data",
      "source": "database",
      "query": "SELECT * FROM customers WHERE active = true",
      "schema": {
        "age":    { "type": "int",   "nullable": false },
        "income": { "type": "float", "nullable": true  },
        "tenure": { "type": "int",   "nullable": false }
      }
    },
    {
      "type": "PipelineStatement",
      "variable": "predictions",
      "source": "customer_data",
      "intent": "transform raw records into churn risk scores with explanations",
      "steps": [
        {
          "type": "Operation",
          "name": "FeatureEngineering",
          "inputs": ["customer_data"],
          "output": "engineered_features",
          "params": {
            "method": "standardize",
            "features": ["age", "income", "tenure"],
            "handle_nulls": "mean_impute"
          },
          "output_schema": {
            "age":    { "type": "float" },
            "income": { "type": "float" },
            "tenure": { "type": "float" }
          }
        },
        {
          "type": "CallStatement",
          "call_type": "classifier",
          "action": "churn_predictor_v1",
          "inputs": ["engineered_features"],
          "outputs": ["churn_probability", "confidence_score"],
          "output_schema": {
            "churn_probability": { "type": "float", "range": [0, 1] },
            "confidence_score":  { "type": "float", "range": [0, 1] }
          },
          "params": { "threshold": 0.5, "explain": true }
        },
        {
          "type": "CallStatement",
          "call_type": "llm",
          "action": "churn_cause_explainer",
          "inputs": ["engineered_features", "churn_probability"],
          "outputs": ["cause_explanation"],
          "output_schema": {
            "cause_explanation": { "type": "string" }
          },
          "params": {
            "prompt_template": "churn_cause_v2",
            "max_tokens": 200
          }
        }
      ]
    },
    {
      "type": "ConditionalStatement",
      "condition": {
        "type": "BinaryExpression",
        "operator": ">=",
        "left":  { "type": "Variable", "name": "confidence_score" },
        "right": { "type": "Literal",  "value": 0.7 }
      },
      "then_body": [
        { "type": "ReturnStatement", "variable": "churn_probability" }
      ],
      "else_body": [
        {
          "type": "CallStatement",
          "call_type": "function",
          "action": "escalate_to_human_review",
          "inputs": ["churn_probability", "confidence_score", "cause_explanation"],
          "outputs": ["escalation_ticket"],
          "params": { "priority": "high", "reason": "low_model_confidence" }
        },
        { "type": "ReturnStatement", "variable": "escalation_ticket" }
      ]
    }
  ]
}
```

This pipeline:

1. Loads active customer records from a database.
2. Standardises selected feature columns, imputing missing values.
3. Runs `churn_predictor_v1` to produce a churn probability and confidence score.
4. Calls an LLM to generate a plain-language explanation of the predicted churn cause.
5. Returns the churn probability directly when confidence is high (≥ 0.7).
6. Escalates to human review when confidence is low, returning a ticket instead.
7. If the program-level `success_metric` (`confidence_score >= 0.7`) fails, the `escalate_to_human_review` fallback fires automatically.

---

## Getting Started

1. Clone the repository and navigate to the project directory.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run a pipeline from the command line:
   ```bash
   python engine/interpreter.py ast/example_pipeline.json
   ```
4. Build or extend pipelines in `pipelines/`, or add new operations and call handlers in `engine/`.

---

## Interpreter Behaviour

The interpreter (`engine/interpreter.py`) walks the AST and maintains a shared **context** — a key/value store of all variables produced during execution.

Key behaviours to be aware of:

- **`ReturnStatement` short-circuits** the current block. Statements after a return are not executed.
- **`PipelineStatement` output**: `CallStatement` outputs inside a pipeline are hoisted to the pipeline's output variable. If no `CallStatement` runs, the final `Operation` output is used.
- **Intent metric evaluation**: The `success_metric` string is evaluated as an expression after the program body completes. It can reference any context variable (e.g. `confidence_score`) or the returned value via `result` (e.g. `result.score`).
- **Fallback dispatch**: When a metric fails, the `fallback` value is called as a zero-input `function` `CallStatement`. Its output is stored under `fallback_result`.

---

## Schema

The full AST schema is defined in `ast/aiql_schema.json` (JSON Schema draft-07). Key constraints:

- `intent` on Program or PipelineStatement accepts a `string` (Level 1) or an `object` with a required `"goal"` key (Level 2).
- `CallStatement.call_type` must be one of: `classifier`, `llm`, `model`, `function`, `visualize`.
- `Operation` requires `inputs` (array), `output` (string), and `params` (object).
- `BinaryExpression` operators: `<`, `>`, `<=`, `>=`, `==`, `!=`.
- `LogicalExpression` operators: `AND`, `OR`, `NOT`.

---
## LICENSE
MIT License

Copyright (c) 2025 Stephen Johnny Davis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

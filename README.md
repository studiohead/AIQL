<img width="2420" height="1460" alt="image" src="https://github.com/user-attachments/assets/384c5994-eecc-44d8-8108-25e24d52f4c0" />

# AIQL: AI Query Language

AIQL is a structured query and pipeline language designed to orchestrate AI workflows safely and efficiently. Pipelines are expressed as ASTs (Abstract Syntax Trees), enabling precise, verifiable execution of multi-step AI tasks. This design is a core component of **KAI: Kernel AI Operating System**: https://github.com/studiohead/KAI

---

## Project Structure

    .
    ├── README.md
    ├── app.py
    ├── test_harness.py             # Integration tests for Level 2/3 logic
    ├── ast
    │   ├── aiql_schema.json        # JSON Schema (draft-07) for all AST node types
    │   └── example_pipeline.json   # Annotated example pipeline
    ├── engine
    │   ├── data_handler.py
    │   ├── interpreter.py          # Core Recursive AST walker and execution engine
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
    │   └── defense_protocol.aiql
    └── run.sh

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
|:---|:---|
| `LoadStatement` | Load a dataset from a source (Sensors, Database, API) |
| `PipelineStatement` | Chain operations and model calls over a dataset |
| `CallStatement` | Invoke a model, LLM, classifier, or function |
| `ConditionalStatement` | Branch on a boolean expression |
| `ReturnStatement` | Resolve a variable and return it as the program output |

### Call Types

`CallStatement` supports the following `call_type` values:

| Value | Description |
|:---|:---|
| `classifier` | Runs an edge model (e.g., Object Detection, Signal Analysis) |
| `llm` | Calls a reasoning model to interpret complex situational data |
| `model` | Generic model call (legacy alias for `classifier`) |
| `function` | Calls hardware/utility functions (e.g., `pivot_camera`) |
| `visualize` | Renders an output visualisation (e.g., HUD overlay) |

---

## Intent System

Pipelines support an optional `intent` field. Intent is progressive — add only as much structure as your use case requires.

### Level 0 — No Intent
Plain dataflow. A direct sensor-to-actuator script.

### Level 1 — Soft Intent
A plain string for introspection (e.g., `"intent": "perimeter sweep"`).

### Level 2 — Structured Intent
A full intent object. The interpreter evaluates `success_metric` post-run and triggers `fallback` on failure.

### Level 3 — Recursive Repair (Self-Healing)
The interpreter treats a metric failure as a signal to iterate via a `repair_agent`.



---

## Intent Configuration Fields (Level 2 & 3)

| Field | Required | Description |
|:---|:---:|:---|
| `goal` | ✅ | Short identifier for the program's objective |
| `strategy` | ❌ | Set to "recursive_repair" for Level 3 self-healing logic |
| `success_metric` | ❌ | Expression (e.g., confidence > 0.9) checked post-run |
| `repair_agent` | ⚠️ | **Required for L3.** Agent responsible for fixes |
| `max_retries` | ❌ | Number of repair attempts before triggering fallback |
| `fallback` | ❌ | Name of a function to call when all attempts/metrics fail |

---

## Example Pipeline (Level 3 Recursive)

**Scenario:** A security drone detects a blurry object. If confidence is low, the `repair_agent` moves the drone or switches modalities.

    {
      "type": "Program",
      "intent": {
        "goal": "perimeter_threat_assessment",
        "strategy": "recursive_repair",
        "repair_agent": "TacticalAdjustmentAgent",
        "max_retries": 2,
        "success_metric": "assessment.confidence > 0.92",
        "fallback": "notify_human_operator"
      },
      "body": [
        {
          "type": "LoadStatement",
          "variable": "sensor_feed",
          "source": "optical_mount_alpha",
          "params": { "resolution": "4k", "mode": "rgb" }
        },
        {
          "type": "PipelineStatement",
          "variable": "assessment",
          "source": "sensor_feed",
          "steps": [
            {
              "type": "Operation",
              "name": "ImagePreprocessing",
              "inputs": ["sensor_feed"],
              "output": "cleaned_frame",
              "params": { "denoise": true, "stabilize": true }
            },
            {
              "type": "CallStatement",
              "call_type": "classifier",
              "action": "yolo_v8_threat_detector",
              "inputs": ["cleaned_frame"],
              "outputs": ["threat_type", "confidence"],
              "params": { "iou_threshold": 0.45 }
            }
          ]
        },
        {
          "type": "ReturnStatement",
          "variable": "assessment"
        }
      ]
    }

---

## Interpreter Behaviour

The interpreter (`engine/interpreter.py`) walks the AST and maintains a shared **context** (key/value store).



* **Hoisting**: `CallStatement` outputs inside a `PipelineStatement` are hoisted to the pipeline's output variable (e.g., `confidence` becomes available in `assessment`).
* **Short-circuiting**: `ReturnStatement` ends the execution of the current block immediately.
* **Metric Logic**: The `success_metric` is evaluated after the body completes. It can reference context variables or the returned value via `result`.
* **Fallback dispatch**: On failure, the `fallback` is called as a zero-input `function`. Its output is stored in `fallback_result`.

---

## Recursive Repair (Level 3 Logic)

If a `success_metric` fails (e.g., confidence is 0.60 vs goal 0.92), the **Repair Agent** is invoked:



1.  **Contextual Fix (As-Is)**: The agent modifies variables (e.g., increases sensor ISO) and the interpreter re-runs the original `body`.
2.  **Structural Fix (AST-Reframing)**: The agent generates a **completely new AST** (e.g., switching to thermal imaging). The interpreter spawns a sub-interpreter to execute it.

### Comparison Safety (The Safety Gate)

To prevent crashes during repairs:
* If a variable in a `success_metric` resolves to `None`, the comparison returns `False` rather than raising a `TypeError`.
* This gracefully triggers the `repair_agent` to fix the state or define the missing variable.

---

## Schema

The full AST schema is defined in `ast/aiql_schema.json`. Key constraints:

- `CallStatement.call_type` must be: `classifier`, `llm`, `model`, `function`, `visualize`.
- `BinaryExpression` operators: `<`, `>`, `<=`, `>=`, `==`, `!=`, `contains`.
- `LogicalExpression` operators: `AND`, `OR`, `NOT`.

---

## Getting Started

1. **Install Dependencies**:
    pip install -r requirements.txt
2. **Run a Protocol**:
    python engine/interpreter.py pipelines/defense_protocol.aiql

---

## LICENSE
MIT License
Copyright (c) 2025-2026 Stephen Johnny Davis

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

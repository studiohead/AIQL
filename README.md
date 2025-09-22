# PIQL: Prompt-Infused Query Language

PIQL is a project to build a AI query connection application for Artificial Intelligence pipelines.

## Project Structure

- **ast/**: Contains the JSON schema and examples for the PIQL Abstract Syntax Tree.
- **engine/**: Houses the interpreter and core logic for executing PIQL pipelines.
- **ui/**: Frontend assets for the visual pipeline builder.
- **pipelines/**: Stores saved PIQL pipeline files.

```
.
├── README.md
├── app.py
├── ast
│   ├── piql_schema.json
│   └── example_pipeline.json
├── engine
│   ├── __pycache__
│   │   └── interpreter.cpython-312.pyc
│   ├── data_handler.py
│   ├── interpreter.py
│   └── model_manager.py
├── frontend
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── src
│   │   ├── App.tsx
│   │   ├── api
│   │   │   └── index.ts
│   │   ├── assets
│   │   ├── components
│   │   │   ├── Button.tsx
│   │   │   ├── PipelineRunner.tsx
│   │   │   └── PromptInput.tsx
│   │   ├── containers
│   │   │   └── Dashboard.tsx
│   │   ├── hooks
│   │   │   └── useFetch.ts
│   │   ├── index.tsx
│   │   ├── layout
│   │   │   ├── Sidebar.tsx
│   │   │   └── Topbar.tsx
│   │   ├── pages
│   │   │   └── Home.tsx
│   │   ├── styles
│   │   │   ├── globals.css
│   │   │   └── style.css
│   │   ├── types
│   │   │   └── index.d.ts
│   │   └── utils
│   │       ├── formatDate.ts
│   │       └── mockAI.ts
│   ├── tsconfig.json
│   └── vite.config.ts
├── left-panel
├── package-lock.json
├── package.json
├── pipelines
│   └── sample_pipeline.aiql
└── run.sh
```

## Getting Started

To get started, navigate into the project directory and begin building out the components.

Run the interpreter on an example pipeline:

```bash
python engine/interpreter.py ast/example_pipeline.json

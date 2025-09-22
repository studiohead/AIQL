# AIQL Project

A project to build a AI query connection application for Artificial Intelligence pipelines.

## Project Structure

- **ast/**: Contains the JSON schema and examples for the AIQL Abstract Syntax Tree.
- **engine/**: Houses the interpreter and core logic for executing AIQL pipelines.
- **ui/**: Frontend assets for the visual pipeline builder.
- **pipelines/**: Stores saved AIQL pipeline files.

## Getting Started

To get started, navigate into the project directory and begin building out the components.

Run the interpreter on an example pipeline:

```bash
python engine/interpreter.py ast/example_pipeline.json

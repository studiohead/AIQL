# test_harness.py
import json
from engine.interpreter import AIQLInterpreter

# Generic AST covering all statement types
test_ast = {
    "type": "Program",
    "body": [
        # LoadStatement
        {
            "type": "LoadStatement",
            "variable": "data",
            "source": "generic_source",
            "query": "SELECT * FROM dummy",
            "metadata": {"description": "test load"}
        },
        # PipelineStatement with Operation + CallStatement
        {
            "type": "PipelineStatement",
            "variable": "pipeline_result",
            "source": "data",
            "steps": [
                {
                    "type": "Operation",
                    "name": "FeatureEngineering",
                    "inputs": ["data"],
                    "output": "features",
                    "params": {"features": ["field1", "field2"]},
                    "metadata": {"note": "test op"}
                },
                {
                    "type": "CallStatement",
                    "call_type": "model",
                    "action": "generic_model",
                    "inputs": ["features"],
                    "outputs": ["predictions"],
                    "params": {"param1": True}
                }
            ]
        },
        # ConditionalStatement
        {
            "type": "ConditionalStatement",
            "condition": {"type": "Literal", "value": True},
            "then_body": [
                {
                    "type": "Operation",
                    "name": "ExtraOp",
                    "inputs": ["pipeline_result"],
                    "output": "extra_result",
                    "params": {}
                }
            ],
            "else_body": [
                {
                    "type": "CallStatement",
                    "call_type": "function",
                    "action": "FallbackFunc",
                    "inputs": ["pipeline_result"],
                    "outputs": ["fallback_output"],
                    "params": {}
                }
            ]
        },
        # ReturnStatement
        {
            "type": "ReturnStatement",
            "variable": "pipeline_result"
        }
    ]
}

if __name__ == "__main__":
    interpreter = AIQLInterpreter(test_ast)
    result = interpreter.run()
    print("\n=== Test Harness Result ===")
    print(json.dumps(result, indent=2))
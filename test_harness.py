import json
import sys
from engine.interpreter import AIQLInterpreter

# ----------------------------------------------------------------------
# Scenario 1: Standard Baseline (Level 2)
# ----------------------------------------------------------------------
baseline_ast = {
    "type": "Program",
    "intent": {
        "goal": "Basic Validation",
        "success_metric": "result.predictions.item_1.val == 0.5",
        "fallback": "FinalSafetyBrake"
    },
    "body": [
        {
            "type": "LoadStatement",
            "variable": "data",
            "source": "generic_source"
        },
        {
            "type": "PipelineStatement",
            "variable": "pipeline_result",
            "source": "data",
            "steps": [
                {
                    "type": "CallStatement",
                    "call_type": "model",
                    "action": "generic_model",
                    "inputs": ["data"],
                    "outputs": ["predictions"]
                }
            ]
        },
        {"type": "ReturnStatement", "variable": "pipeline_result"}
    ]
}

# ----------------------------------------------------------------------
# Scenario 2: Level 3 Contextual Repair
# ----------------------------------------------------------------------
contextual_repair_ast = {
    "type": "Program",
    "intent": {
        "goal": "Verify Threshold via Context",
        "strategy": "recursive_repair",
        "repair_agent": "ContextFixerAgent",
        "max_retries": 1,
        "success_metric": "threshold == 0.5"
    },
    "body": [
        {
            "type": "LoadStatement", 
            "variable": "data"
        },
        {
            "type": "ReturnStatement", 
            "variable": "data"
        }
    ]
}

# ----------------------------------------------------------------------
# Scenario 3: Level 3 Structural (AST) Repair
# ----------------------------------------------------------------------
structural_repair_ast = {
    "type": "Program",
    "intent": {
        "goal": "Structural Rewrite Test",
        "strategy": "recursive_repair",
        "repair_agent": "ASTGeneratorAgent",
        "max_retries": 1,
        "success_metric": "result.item_1.status == 'fixed'"
    },
    "body": [
        {
            "type": "LoadStatement", 
            "variable": "raw_data"
        },
        {
            "type": "ReturnStatement", 
            "variable": "raw_data"
        }
    ]
}

# ----------------------------------------------------------------------
# Mock Agent Monkey-Patch
# ----------------------------------------------------------------------
def mock_call_statement_patch(self, stmt, input_data=None):
    """
    Simulates LLM/Agent responses for repair scenarios.
    """
    action = stmt["action"]
    call_type = stmt.get("call_type")
    outputs = stmt.get("outputs", [])
    
    print(f"  [Mock] Executing {call_type} action: {action}")

    # Level 3: Contextual Fix Logic
    if action == "ContextFixerAgent":
        self.context["threshold"] = 0.5
        return {"repair_output": "Context Modified"}

    # Level 3: Structural Fix Logic
    if action == "ASTGeneratorAgent":
        new_program = {
            "type": "Program",
            "body": [
                {
                    "type": "LoadStatement",
                    "variable": "fixed_data",
                    "params": {"status": "fixed"}
                },
                {
                    "type": "ReturnStatement",
                    "variable": "fixed_data"
                }
            ]
        }
        return {"repair_output": new_program}

    # Standard Statement Mocking
    res = {}
    for out in outputs:
        # Match the expected nested structure for metrics
        val = {
            f"item_{i+1}": {"val": 0.5, "status": "default"} 
            for i in range(3)
        }
        res[out] = val
        self.context[out] = val
    return res

# ----------------------------------------------------------------------
# Test Runner
# ----------------------------------------------------------------------
def run_test(name, ast):
    print(f"\n{'='*60}\nRUNNING TEST: {name}\n{'='*60}")
    
    # Apply mock
    AIQLInterpreter.call_statement = mock_call_statement_patch
    
    interpreter = AIQLInterpreter(ast)
    result = interpreter.run()
    
    print(f"\n--- {name} Result ---")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    # 1. Level 2
    run_test("Level 2 Baseline", baseline_ast)
    
    # 2. Level 3 Contextual
    run_test("Level 3 Contextual Repair", contextual_repair_ast)
    
    # 3. Level 3 Structural
    run_test("Level 3 Structural Repair", structural_repair_ast)
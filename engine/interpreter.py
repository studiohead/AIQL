"""
engine/interpreter.py

Walks an AIQL Abstract Syntax Tree (AST) and executes each statement
in order, maintaining a shared execution context (variable store).

Intent support
--------------
Intent is optional and progressive. The interpreter handles four levels:

  Level 0 – No intent field at all. Plain dataflow, no planning or fallback.
  Level 1 – intent is a plain string, e.g. "predict customer churn".
            Stored for introspection/logging only; no runtime behaviour change.
  Level 2 – intent is a structured dict with a required "goal" key and
            optional "success_metric" (evaluated post-run) and "fallback"
            (a function action triggered when the metric fails).
  Level 3 – intent is a structured dict with strategy "recursive_repair".
            Supports two modes of correction:
              1. Contextual Fix (As-Is): Repair agent modifies context variables, 
                 then the original body is re-executed.
              2. Structural Fix (AST-Reframing): Repair agent generates a 
                 completely new AST, which is then executed recursively.
            Falls through to "fallback" (if declared) only after all repair 
            attempts (max_retries) are exhausted.

Intent can appear at two levels of the AST:
  - Program level       : governs the entire program's success/fallback.
  - PipelineStatement   : descriptive only — aids planning and logging.

Supported statement types
--------------------------
LoadStatement        – Simulates loading a named dataset from a source.
PipelineStatement    – Chains Operations and CallStatements over a dataset.
CallStatement        – Invokes a classifier, llm, function, or visualise action.
ConditionalStatement – Evaluates a boolean expression and branches.
ReturnStatement      – Resolves a variable from context and returns it.
"""

import json
import sys
from typing import Any


class AIQLInterpreter:
    """
    Executes an AIQL program represented as a JSON AST.

    Parameters
    ----------
    ast : dict
        The root AST node. Must be of type "Program" with a "body"
        list of statement nodes, and an optional "intent" field.

    Attributes
    ----------
    ast     : dict             – Original AST.
    context : dict[str, Any]  – Shared variable store across all statements.
    intent  : dict | None     – Resolved program-level intent (canonical form).
    """

    def __init__(self, ast: dict) -> None:
        self.ast = ast
        self.context: dict[str, Any] = {}
        # Resolve program-level intent once at construction so all methods
        # can reference self.intent without re-parsing the raw field.
        self.intent = self._resolve_intent(ast.get("intent"))

    # ------------------------------------------------------------------
    # Intent helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_intent(intent_field: "str | dict | None") -> "dict | None":
        """
        Normalise the optional ``intent`` field into a canonical dict.

        Three forms are accepted so authors can opt in to as much
        structure as they need:

        * ``None``  – No intent; pipeline runs as plain dataflow (Level 0).
        * ``str``   – Soft intent goal string; no runtime effect (Level 1).
                      Promoted to ``{"goal": <string>}`` for uniform access.
        * ``dict``  – Structured intent; must contain ``"goal"`` (Level 2).
                      Level 3 requires strategy="recursive_repair" and 
                      a non-empty "repair_agent".

        Returns
        -------
        dict | None
            Canonical intent dict, or ``None`` when absent.

        Raises
        ------
        ValueError  If a dict intent is missing the required ``"goal"`` key
                    or if Level 3 is missing a ``"repair_agent"``.
        TypeError   If the intent field is an unexpected type.
        """
        if intent_field is None:
            return None
        if isinstance(intent_field, str):
            # Promote bare string so downstream code always checks one key.
            return {"goal": intent_field}
        if isinstance(intent_field, dict):
            if "goal" not in intent_field:
                raise ValueError("Structured intent must include a 'goal' key.")
            if intent_field.get("strategy") == "recursive_repair":
                if not intent_field.get("repair_agent"):
                    raise ValueError(
                        "Level 3 intent with strategy 'recursive_repair' "
                        "must declare a 'repair_agent'."
                    )
            return intent_field
        raise TypeError(
            f"'intent' must be a string or object, got {type(intent_field).__name__}."
        )

    def _intent_level(self) -> int:
        """Return the numeric intent level (0–3) for program-level intent."""
        if self.intent is None:
            return 0
        if self.intent.get("strategy") == "recursive_repair":
            return 3
        if "success_metric" in self.intent or "fallback" in self.intent:
            return 2
        return 1

    def _evaluate_success_metric(self, result: Any) -> bool:
        """
        Evaluate ``success_metric`` in a snapshot context that includes
        the current result bound to the key ``"result"``.
        """
        # Temporarily expose result so the metric expression can reference it.
        snapshot = {**self.context, "result": result}
        original_context = self.context
        self.context = snapshot

        try:
            metric = self.intent["success_metric"]
            # If it's a dict, evaluate directly as an expression node.
            if isinstance(metric, dict):
                return bool(self.evaluate_expression(metric))
            # If it's a string, try to parse as "<path> <op> <literal>".
            parsed = self._parse_metric_string(metric)
            if parsed is not None:
                return bool(self.evaluate_expression(parsed))
            # Fallback: treat as a bare dot-path returning a truthy value.
            return bool(self.evaluate_expression(metric))
        finally:
            # Always restore context, even if evaluate_expression raises.
            self.context = original_context

    @staticmethod
    def _parse_metric_string(metric: str) -> "dict | None":
        """
        Parse a simple inline metric string into a BinaryExpression dict.
        Accepted form: ``"<dot.path> <operator> <literal>"``
        """
        # Try each operator longest-first to avoid ambiguity
        for op in (">=", "<=", "!=", "==", ">", "<", "contains"):
            parts = metric.split(op, 1)
            if len(parts) == 2:
                left_str = parts[0].strip()
                right_str = parts[1].strip()
                
                # Parse the right-hand literal
                try:
                    right_val: Any = float(right_str) if "." in right_str else int(right_str)
                except ValueError:
                    if right_str.lower() == "true":
                        right_val = True
                    elif right_str.lower() == "false":
                        right_val = False
                    else:
                        right_val = right_str
                
                return {
                    "type": "BinaryExpression",
                    "operator": op,
                    "left": {"type": "Variable", "name": left_str},
                    "right": {"type": "Literal", "value": right_val},
                }
        return None

    def _invoke_repair_agent(self, failed_result: Any) -> Any:
        """
        Invokes the repair agent to generate a fix (state change or new AST).
        """
        agent = self.intent["repair_agent"]
        print(f"[Intent/L3] Invoking repair_agent: '{agent}'")
        
        repair_stmt = {
            "type": "CallStatement",
            "call_type": "llm",
            "action": agent,
            "inputs": [],
            "outputs": ["repair_output"],
            "params": {
                "reason": "success_metric_failed",
                "metric": self.intent.get("success_metric"),
                "failed_result": failed_result
            },
        }
        
        # The agent returns a dictionary containing its output
        agent_call_result = self.call_statement(repair_stmt)
        return agent_call_result.get("repair_output") if agent_call_result else None

    def _invoke_fallback(self) -> Any:
        """Trigger the fallback action."""
        fallback_action = self.intent.get("fallback")
        if not fallback_action:
            print("[Intent] No fallback declared — returning None.")
            return None

        print(f"[Intent] Triggering fallback: '{fallback_action}'")
        fallback_stmt = {
            "type": "CallStatement",
            "call_type": "function",
            "action": fallback_action,
            "inputs": [],
            "outputs": ["fallback_result"],
            "params": {"reason": "intent_success_metric_failed"},
        }
        return self.call_statement(fallback_stmt)

    def _check_intent_success(self, result: Any, depth: int = 0) -> Any:
        """
        Evaluate success_metric and handle Recursive Repair (Level 3).
        """
        if not self.intent or "success_metric" not in self.intent:
            return result

        goal = self.intent["goal"]
        level = self._intent_level()
        max_retries = int(self.intent.get("max_retries", 0))

        # Check for success
        if self._evaluate_success_metric(result):
            status = "initial run" if depth == 0 else f"repair depth {depth}"
            print(f"[Intent/L{level}] '{goal}' — PASSED on {status}.")
            return result

        # Handle Level 2 failure or Level 3 exhaustion
        if level == 2 or depth >= max_retries:
            print(f"[Intent/L{level}] '{goal}' — FAILED. Triggering final resolution.")
            return self._invoke_fallback()

        # Level 3: Initiate Repair
        print(f"[Intent/L3] '{goal}' — FAILED. Initiating repair attempt {depth + 1}/{max_retries}...")
        
        repair_data = self._invoke_repair_agent(result)

        # MODE A: Structural Fix (The agent returned a completely new AST)
        if isinstance(repair_data, dict) and repair_data.get("type") == "Program":
            print(f"[Intent/L3] MODE: Structural Reframing. Spawning sub-interpreter.")
            
            sub_interpreter = AIQLInterpreter(repair_data)
            # Inherit current context for efficiency
            sub_interpreter.context = {**self.context} 
            # Sub-interpreter runs the new AST; we return its result through parent's logic
            sub_result = sub_interpreter.run(depth=depth + 1)
            return sub_interpreter._check_intent_success(sub_result, depth=depth + 1)

        # MODE B: Contextual Fix (As-Is re-execution)
        print(f"[Intent/L3] MODE: Contextual Fix. Re-executing current body.")
        # Any mutations to self.context made by the agent call are preserved
        new_result = self.execute_block(self.ast["body"])
        return self._check_intent_success(new_result, depth=depth + 1)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self, depth: int = 0) -> Any:
        """
        Begin execution at the program root.
        """
        if self.ast.get("type") != "Program":
            raise ValueError(
                f"AST root must be a Program node, got '{self.ast.get('type')}'."
            )

        level = self._intent_level()
        if depth == 0 and self.intent:
            strategy = self.intent.get("strategy", "static")
            suffix = (
                f" | strategy={strategy}"
                + (f" | max_retries={self.intent.get('max_retries', 0)}" if level == 3 else "")
            ) if level >= 2 else ""
            print(f"[Program] Intent (L{level}): '{self.intent['goal']}'{suffix}")

        result = self.execute_block(self.ast["body"])

        # If we are in a sub-interpreter (Structural Repair), return directly
        # to the parent's _check_intent_success loop.
        if depth > 0:
            return result

        return self._check_intent_success(result, depth=depth)

    # ------------------------------------------------------------------
    # Block / statement dispatch
    # ------------------------------------------------------------------

    def execute_block(self, statements: list) -> Any:
        """Execute a list of statements sequentially, stopping at ReturnStatement."""
        result = None
        for stmt in statements:
            result = self.execute_statement(stmt)
            if stmt["type"] == "ReturnStatement":
                return result
        return result

    def execute_statement(self, stmt: dict) -> Any:
        """Dispatch a single AST statement node to its handler."""
        t = stmt["type"]
        handlers = {
            "LoadStatement":        self.load_statement,
            "PipelineStatement":    self.pipeline_statement,
            "CallStatement":        self.call_statement,
            "ConditionalStatement": self.conditional_statement,
            "ReturnStatement":      lambda s: self.context.get(s["variable"]),
        }
        if t not in handlers:
            raise NotImplementedError(f"Statement type '{t}' is not implemented.")
        return handlers[t](stmt)

    # ------------------------------------------------------------------
    # Statement handlers
    # ------------------------------------------------------------------

    def load_statement(self, stmt: dict) -> dict:
        """Simulate loading a dataset and store it in the context."""
        variable  = stmt["variable"]
        source    = stmt.get("source", "generic")
        query     = stmt.get("query", "")
        num_items = stmt.get("params", {}).get("num_items", 3)

        print(
            f"[LoadStatement] Loading '{variable}' from '{source}'"
            + (f" | query: {query}" if query else "")
        )

        # Mock: check if we are simulating a specific status for testing
        status = stmt.get("params", {}).get("status", "raw")
        data = {f"item_{i + 1}": {"status": status} for i in range(num_items)}
        self.context[variable] = data
        return data

    def pipeline_statement(self, stmt: dict) -> Any:
        """Execute a series of pipeline steps over a source variable."""
        source_var = stmt["source"]
        variable   = stmt["variable"]

        pipeline_intent = self._resolve_intent(stmt.get("intent"))
        if pipeline_intent:
            print(f"[PipelineStatement] Intent: '{pipeline_intent['goal']}'")

        data = self.context.get(source_var)
        if data is None:
            raise ValueError(
                f"Pipeline source variable '{source_var}' not found in context."
            )

        call_outputs: dict = {}

        for step in stmt["steps"]:
            if step["type"] == "Operation":
                if "input" in step and "inputs" not in step:
                    step["inputs"] = [step.pop("input")]
                data = self.execute_operation(step, data)

            elif step["type"] == "CallStatement":
                result = self.call_statement(step, input_data=data)
                if result:
                    call_outputs.update(result)

            else:
                raise NotImplementedError(
                    f"Pipeline step type '{step['type']}' is not supported."
                )

        final = call_outputs if call_outputs else data
        self.context[variable] = final
        return final

    def execute_operation(self, op: dict, input_data: dict) -> dict:
        """Apply a named transform to input_data and return the result."""
        name = op["name"]
        print(f"[Operation] '{name}' over {len(input_data)} item(s).")

        if name == "FeatureEngineering":
            features = op.get("params", {}).get("features", [])
            result = {
                item_id: {feat: item_data.get(feat) for feat in features}
                for item_id, item_data in input_data.items()
            }
        else:
            result = {item_id: f"{name}_result" for item_id in input_data}

        self.context[op["output"]] = result
        return result

    def call_statement(self, stmt: dict, input_data: "dict | None" = None) -> "dict | None":
        """Invoke a classifier, llm, function, or visualisation action."""
        action    = stmt["action"]
        call_type = stmt["call_type"]
        inputs    = stmt["inputs"]
        outputs   = stmt.get("outputs") or []

        print(f"[CallStatement] {call_type}::{action} | inputs={inputs} outputs={outputs}")

        if input_data is None:
            input_data = self.context.get(inputs[0], {}) if inputs else {}

        result: dict = {}

        for output in outputs:
            if call_type in ("classifier", "model"):
                per_item: Any = {item_id: {"val": 0.5, "status": "default"} for item_id in input_data}
            elif call_type == "llm":
                per_item = {
                    item_id: f"{action}_explanation" for item_id in input_data
                }
            elif call_type == "function":
                per_item = {
                    item_id: f"{action}_result" for item_id in input_data
                }
            else:
                per_item = None

            result[output] = per_item
            self.context[output] = per_item

        return result if outputs else None

    def conditional_statement(self, stmt: dict) -> Any:
        """Evaluate a boolean condition and execute the matching branch."""
        if self.evaluate_expression(stmt["condition"]):
            print("[ConditionalStatement] Condition true — executing then_body.")
            return self.execute_block(stmt["then_body"])

        else_body = stmt.get("else_body")
        if else_body:
            print("[ConditionalStatement] Condition false — executing else_body.")
            return self.execute_block(else_body)

        return None

    # ------------------------------------------------------------------
    # Expression evaluation
    # ------------------------------------------------------------------

    def evaluate_expression(self, expr: Any) -> Any:
        """Recursively evaluate an AIQL expression node."""
        if isinstance(expr, (int, float, bool)):
            return expr

        if isinstance(expr, str):
            # Treat as a dot-notation context path.
            return self._resolve_path(expr, self.context)

        t = expr.get("type")

        if t == "BinaryExpression":
            left  = self.evaluate_expression(expr["left"])
            right = self.evaluate_expression(expr["right"])
            return self._eval_binary(expr["operator"], left, right)

        if t == "LogicalExpression":
            op       = expr["operator"]
            operands = [self.evaluate_expression(o) for o in expr["operands"]]
            if op == "AND": return all(operands)
            if op == "OR":  return any(operands)
            if op == "NOT": return not operands[0]

        if t == "Variable":
            return self._resolve_path(expr["name"], self.context)

        if t == "Literal":
            return expr["value"]

        raise NotImplementedError(f"Expression type '{t}' is not implemented.")

    @staticmethod
    def _resolve_path(path: str, root: dict) -> Any:
        """Walk a dot-notation path through a nested dict."""
        val = root
        for part in path.split("."):
            if isinstance(val, dict) and part in val:
                val = val[part]
            else:
                return None
        return val

    @staticmethod
    def _eval_binary(op: str, left: Any, right: Any) -> bool:
        """
        Evaluate a binary comparison, including Life Sciences 'contains' support.
        
        Note: If 'left' or 'right' is None (e.g., a variable not yet defined 
        in context), we return False to trigger the Level 3 repair loop 
        rather than raising a TypeError.
        """
        # --- SAFETY GATE FOR LEVEL 3 ---
        if left is None or right is None:
            if op == "!=": return left != right
            if op == "==": return left == right
            # For other comparisons, assume missing data fails the metric
            return False
        # -------------------------------

        if op == "contains":
            return right in left if left is not None else False

        def _coerce(v: Any) -> Any:
            if isinstance(v, str):
                try:
                    return float(v)
                except ValueError:
                    return v
            return v

        l, r = _coerce(left), _coerce(right)

        # Final type-check safety
        if type(l) != type(r):
            print(f"[Warning] Type mismatch in comparison: {type(l).__name__} vs {type(r).__name__}")
            return False

        ops = {
            "<":  lambda a, b: a < b,
            ">":  lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }
        if op not in ops:
            raise ValueError(f"Unsupported binary operator: '{op}'.")
        return ops[op](l, r)


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py <pipeline.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        ast = json.load(f)

    interpreter = AIQLInterpreter(ast)
    result = interpreter.run()
    print("Pipeline result:", result)
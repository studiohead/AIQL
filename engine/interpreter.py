"""
engine/interpreter.py

Walks an AIQL Abstract Syntax Tree (AST) and executes each statement
in order, maintaining a shared execution context (variable store).

Intent support
--------------
Intent is optional and progressive. The interpreter handles three levels:

  Level 0 – No intent field at all. Plain dataflow, no planning or fallback.
  Level 1 – intent is a plain string, e.g. "predict customer churn".
             Stored for introspection/logging only; no runtime behaviour change.
  Level 2 – intent is a structured dict with a required "goal" key and
             optional "success_metric" (evaluated post-run) and "fallback"
             (a function action triggered when the metric fails).

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
        The root AST node. Must be of type ``"Program"`` with a ``"body"``
        list of statement nodes, and an optional ``"intent"`` field.

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
                      May also contain ``"success_metric"`` and ``"fallback"``.

        Parameters
        ----------
        intent_field : str | dict | None
            Raw value of any ``"intent"`` key in the AST.

        Returns
        -------
        dict | None
            Canonical intent dict, or ``None`` when absent.

        Raises
        ------
        ValueError  If a dict intent is missing the required ``"goal"`` key.
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
            return intent_field
        raise TypeError(
            f"'intent' must be a string or object, got {type(intent_field).__name__}."
        )

    def _check_intent_success(self, result: Any) -> Any:
        """
        Evaluate the program-level ``success_metric`` against the final
        result and trigger ``fallback`` when the metric is not met.

        Only active for Level 2 intent (structured dict that declares a
        ``success_metric``). Levels 0 and 1 pass through unchanged.

        The metric is a string expression evaluated via
        ``evaluate_expression`` after injecting ``result`` into a
        temporary context snapshot under the key ``"result"``, so
        metrics can reference top-level context variables *or* the
        result directly:

            ``"confidence_score >= 0.7"``   – references a context variable
            ``"result.score >= 0.7"``        – references the returned value

        Parameters
        ----------
        result : Any
            The value returned by the program body.

        Returns
        -------
        Any
            ``result`` if the metric passes or is absent; otherwise the
            return value of the fallback CallStatement, or ``None`` if
            no fallback is declared.
        """
        if not self.intent or "success_metric" not in self.intent:
            # Level 0 / Level 1 — nothing to enforce.
            return result

        # Temporarily expose result so the metric expression can reference it.
        snapshot = {**self.context, "result": result}
        original_context = self.context
        self.context = snapshot

        try:
            passed = self.evaluate_expression(self.intent["success_metric"])
        finally:
            # Always restore context, even if evaluate_expression raises.
            self.context = original_context

        goal = self.intent["goal"]

        if passed:
            print(f"[Intent] '{goal}' — success metric passed.")
            return result

        print(f"[Intent] '{goal}' — success metric FAILED.")
        fallback_action = self.intent.get("fallback")

        if fallback_action:
            print(f"[Intent] Triggering fallback: '{fallback_action}'")
            # Dispatch as a zero-input function CallStatement so the
            # existing call_statement handler deals with it uniformly.
            fallback_stmt = {
                "type":      "CallStatement",
                "call_type": "function",
                "action":    fallback_action,
                "inputs":    [],
                "outputs":   ["fallback_result"],
                "params":    {"reason": "intent_success_metric_failed"},
            }
            return self.call_statement(fallback_stmt)

        # Metric failed and no fallback declared.
        return None

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self) -> Any:
        """
        Begin execution at the program root.

        After the body completes the program-level intent success metric
        is evaluated (if present) before the final result is returned.

        Returns
        -------
        Any
            The post-intent-checked value of the last / return statement.

        Raises
        ------
        ValueError  If the AST root is not a ``"Program"`` node.
        """
        if self.ast.get("type") != "Program":
            raise ValueError(
                f"AST root must be a Program node, got '{self.ast.get('type')}'."
            )

        if self.intent:
            print(f"[Program] Intent: '{self.intent['goal']}'")

        result = self.execute_block(self.ast["body"])

        # Post-run hook: evaluate success metric and route to fallback if needed.
        return self._check_intent_success(result)

    # ------------------------------------------------------------------
    # Block / statement dispatch
    # ------------------------------------------------------------------

    def execute_block(self, statements: list) -> Any:
        """
        Execute a list of statements sequentially.

        Stops early and propagates the return value as soon as a
        ``ReturnStatement`` is encountered.

        Parameters
        ----------
        statements : list
            Ordered list of AST statement nodes.

        Returns
        -------
        Any
            Value of the last executed statement, or the value resolved
            by a ``ReturnStatement`` if one is reached first.
        """
        result = None
        for stmt in statements:
            result = self.execute_statement(stmt)
            if stmt["type"] == "ReturnStatement":
                # Propagate immediately — do not execute remaining statements.
                return result
        return result

    def execute_statement(self, stmt: dict) -> Any:
        """
        Dispatch a single AST statement node to its handler.

        Parameters
        ----------
        stmt : dict
            AST node whose ``"type"`` key identifies the statement kind.

        Returns
        -------
        Any
            Whatever the individual handler returns.

        Raises
        ------
        NotImplementedError  For unrecognised statement types.
        """
        t = stmt["type"]
        handlers = {
            "LoadStatement":        self.load_statement,
            "PipelineStatement":    self.pipeline_statement,
            "CallStatement":        self.call_statement,
            "ConditionalStatement": self.conditional_statement,
            # ReturnStatement resolves the variable directly from context.
            "ReturnStatement":      lambda s: self.context.get(s["variable"]),
        }
        if t not in handlers:
            raise NotImplementedError(f"Statement type '{t}' is not implemented.")
        return handlers[t](stmt)

    # ------------------------------------------------------------------
    # Statement handlers
    # ------------------------------------------------------------------

    def load_statement(self, stmt: dict) -> dict:
        """
        Simulate loading a dataset and store it in the context.

        In production this would connect to the declared ``source``
        (database, file, API) and execute ``query``. The simulation
        produces a synthetic mapping of ``num_items`` empty-dict items
        so that downstream steps always receive a valid input.

        Parameters
        ----------
        stmt : dict
            A ``LoadStatement`` node. Relevant keys:
            ``variable``, ``source``, ``query``, optional ``params``.

        Returns
        -------
        dict
            Mapping ``item_<n>`` → ``{}`` stored under ``variable``.
        """
        variable  = stmt["variable"]
        source    = stmt.get("source", "generic")
        query     = stmt.get("query", "")
        num_items = stmt.get("params", {}).get("num_items", 3)

        print(
            f"[LoadStatement] Loading '{variable}' from '{source}'"
            + (f" | query: {query}" if query else "")
        )

        # Synthetic items — replace with real I/O in production.
        data = {f"item_{i + 1}": {} for i in range(num_items)}
        self.context[variable] = data
        return data

    def pipeline_statement(self, stmt: dict) -> Any:
        """
        Execute a series of pipeline steps over a source variable.

        The pipeline's own ``intent`` field (if present) is resolved and
        logged. Pipeline-level intent is **descriptive only** and never
        triggers fallback logic — that is reserved for Program-level intent.

        Steps flow left-to-right: each ``Operation`` transforms the
        cursor dataset in-place; each ``CallStatement`` writes named
        output variables into context and accumulates them separately.

        Parameters
        ----------
        stmt : dict
            A ``PipelineStatement`` node. Relevant keys:
            ``variable``, ``source``, ``steps``, optional ``intent``.

        Returns
        -------
        Any
            Final value stored under ``stmt["variable"]`` in context.

        Raises
        ------
        ValueError          If the source variable is absent from context.
        NotImplementedError If an unsupported step type is encountered.
        """
        source_var = stmt["source"]
        variable   = stmt["variable"]

        # Pipeline-level intent: log only, no metric evaluation.
        pipeline_intent = self._resolve_intent(stmt.get("intent"))
        if pipeline_intent:
            print(f"[PipelineStatement] Intent: '{pipeline_intent['goal']}'")

        data = self.context.get(source_var)
        if data is None:
            raise ValueError(
                f"Pipeline source variable '{source_var}' not found in context."
            )

        # Named outputs emitted by CallStatement steps accumulate here.
        call_outputs: dict = {}

        for step in stmt["steps"]:
            if step["type"] == "Operation":
                # Normalise legacy single-input shorthand to the list form.
                if "input" in step and "inputs" not in step:
                    step["inputs"] = [step.pop("input")]
                data = self.execute_operation(step, data)

            elif step["type"] == "CallStatement":
                # CallStatements write named outputs into context; collect
                # them so they can be surfaced as the pipeline's result.
                result = self.call_statement(step, input_data=data)
                if result:
                    call_outputs.update(result)

            else:
                raise NotImplementedError(
                    f"Pipeline step type '{step['type']}' is not supported."
                )

        # Surface CallStatement outputs when present; otherwise the final
        # transformed dataset is the pipeline's result.
        final = call_outputs if call_outputs else data
        self.context[variable] = final
        return final

    def execute_operation(self, op: dict, input_data: dict) -> dict:
        """
        Apply a named transform to ``input_data`` and return the result.

        Only ``FeatureEngineering`` has a concrete implementation; all
        other names fall through to a generic placeholder.

        Parameters
        ----------
        op         : dict – ``Operation`` node: ``name``, ``output``, ``params``.
        input_data : dict – Item mapping flowing through the pipeline.

        Returns
        -------
        dict
            Transformed mapping stored in ``self.context[op["output"]]``.
        """
        name = op["name"]
        print(f"[Operation] '{name}' over {len(input_data)} item(s).")

        if name == "FeatureEngineering":
            features = op.get("params", {}).get("features", [])
            result = {
                item_id: {feat: item_data.get(feat) for feat in features}
                for item_id, item_data in input_data.items()
            }
        else:
            # Generic no-op placeholder — replace with real operation logic.
            result = {item_id: f"{name}_result" for item_id in input_data}

        self.context[op["output"]] = result
        return result

    def call_statement(self, stmt: dict, input_data: "dict | None" = None) -> "dict | None":
        """
        Invoke a classifier, llm, function, or visualisation action.

        Simulated output per ``call_type``:

        * ``"classifier"`` / ``"model"`` – Score of ``0.5`` per item.
          Replace with real model inference.
        * ``"llm"``                       – Placeholder explanation string.
          Replace with real LLM API call.
        * ``"function"``                  – ``"<action>_result"`` per item.
        * ``"visualize"``                 – Not yet implemented; outputs ``None``.

        Parameters
        ----------
        stmt       : dict       – ``CallStatement`` node.
        input_data : dict | None – Pre-resolved input. When ``None`` the first
                                   element of ``stmt["inputs"]`` is looked up
                                   in context.

        Returns
        -------
        dict | None
            Mapping of output-name → per-item result, or ``None`` when the
            statement declares no outputs.
        """
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
                # Neutral placeholder score; replace with real inference.
                per_item: Any = {item_id: 0.5 for item_id in input_data}

            elif call_type == "llm":
                # Placeholder text; replace with a real LLM API call.
                per_item = {
                    item_id: f"{action}_explanation" for item_id in input_data
                }

            elif call_type == "function":
                per_item = {
                    item_id: f"{action}_result" for item_id in input_data
                }

            else:
                # visualize or unknown call_type — not yet implemented.
                per_item = None

            result[output] = per_item
            self.context[output] = per_item

        return result if outputs else None

    def conditional_statement(self, stmt: dict) -> Any:
        """
        Evaluate a boolean condition and execute the matching branch.

        Parameters
        ----------
        stmt : dict
            A ``ConditionalStatement`` node with ``condition``,
            ``then_body``, and optional ``else_body``.

        Returns
        -------
        Any
            Result of the executed branch, or ``None`` if the else branch
            is absent and the condition is false.
        """
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
        """
        Recursively evaluate an AIQL expression node.

        Handles ``BinaryExpression``, ``LogicalExpression``, ``Variable``,
        ``Literal``, bare scalar values, and dot-notation path strings.

        Parameters
        ----------
        expr : Any
            An expression node (dict), scalar (int/float/bool), or a
            dot-notation path string (e.g. ``"result.confidence_score"``).

        Returns
        -------
        Any
            The evaluated value.

        Raises
        ------
        NotImplementedError  For unrecognised expression node types.
        """
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
        """
        Walk a dot-notation path through a nested dict.

        Parameters
        ----------
        path : str  – Dot-separated key path, e.g. ``"result.score"``.
        root : dict – Dict to start walking from.

        Returns
        -------
        Any
            Resolved value, or ``None`` if any segment is missing.
        """
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
        Evaluate a binary comparison, coercing numeric strings to float.

        Parameters
        ----------
        op    : str – One of ``< > <= >= == !=``.
        left  : Any – Left-hand value.
        right : Any – Right-hand value.

        Returns
        -------
        bool

        Raises
        ------
        TypeError   If operands are incompatible after coercion.
        ValueError  If the operator is not recognised.
        """
        def _coerce(v: Any) -> Any:
            if isinstance(v, str):
                try:
                    return float(v)
                except ValueError:
                    return v
            return v

        l, r = _coerce(left), _coerce(right)

        if type(l) != type(r):
            raise TypeError(
                f"Cannot compare {type(l).__name__} with {type(r).__name__}."
            )

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

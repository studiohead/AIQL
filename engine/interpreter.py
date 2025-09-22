# engine/interpreter.py
import json
import sys

class AIQLInterpreter:
    def __init__(self, ast):
        self.ast = ast
        self.context = {}

    def run(self):
        if self.ast["type"] != "Program":
            raise ValueError("AST root must be a Program node.")
        return self.execute_block(self.ast["body"])

    def execute_block(self, statements):
        result = None
        for stmt in statements:
            result = self.execute_statement(stmt)
            if stmt["type"] == "ReturnStatement":
                return result
        return result

    def execute_statement(self, stmt):
        t = stmt["type"]
        if t == "LoadStatement":
            return self.load_statement(stmt)
        elif t == "PipelineStatement":
            return self.pipeline_statement(stmt)
        elif t == "CallStatement":
            return self.call_statement(stmt)
        elif t == "ConditionalStatement":
            return self.conditional_statement(stmt)
        elif t == "ReturnStatement":
            return self.context.get(stmt["variable"])
        else:
            raise NotImplementedError(f"Statement type '{t}' not implemented.")

    def load_statement(self, stmt):
        variable = stmt["variable"]
        query = stmt.get("query", "")
        print(f"Loading data into '{variable}' with query: {query}")
        # Simulated data: dict of features per customer (dimension)
        data = {
            "customer_1": {"age": 30, "income": 50000, "region": "north"},
            "customer_2": {"age": 45, "income": 70000, "region": "south"},
            "customer_3": {"age": 25, "income": 40000, "region": "east"},
        }
        self.context[variable] = data
        return data

    def pipeline_statement(self, stmt):
        source_var = stmt["source"]
        variable = stmt["variable"]
        data = self.context.get(source_var)
        if data is None:
            raise ValueError(f"Source variable '{source_var}' not found.")

        combined_result = {}
        for step in stmt["steps"]:
            if step["type"] == "Operation":
                data = self.execute_operation(step, data)
            elif step["type"] == "CallStatement":
                # call_statement returns a dict of outputs or None
                result = self.call_statement(step, input_data=data)
                if result:
                    # merge result dict into combined_result
                    combined_result.update(result)
                # also update data if needed - or keep as is?
            else:
                raise NotImplementedError(f"Pipeline step '{step['type']}' not supported.")

        # store combined result dict under pipeline variable
        if combined_result:
            self.context[variable] = combined_result
        else:
            self.context[variable] = data

        return self.context[variable]

    def execute_operation(self, op, input_data):
        name = op["name"]
        print(f"Executing operation '{name}' with input: {input_data}")

        if name == "NormalizeFeatures":
            # Normalize numeric features to [0,1]
            normalized = {}
            for key, features in input_data.items():
                normalized[key] = {}
                for feat, val in features.items():
                    if isinstance(val, (int, float)):
                        # For example purpose, scale by dividing by max 100000
                        normalized[key][feat] = val / 100000
                    else:
                        normalized[key][feat] = val
            self.context[op["output"]] = normalized
            return normalized

        # fallback generic simulation
        result = f"result_of_{name}"
        self.context[op["output"]] = result
        return result

    def call_statement(self, stmt, input_data=None):
        action = stmt["action"]
        call_type = stmt["call_type"]
        inputs = stmt["inputs"]
        outputs = stmt.get("outputs")

        print(f"Calling {call_type} '{action}' with inputs: {inputs}")

        result = {}

        if call_type == "model" and action == "ChurnPredictionModel":
            # simulate prediction probabilities per customer
            input_var = inputs[0]
            features = self.context.get(input_var, {})
            predictions = {}
            for cust_id in features:
                # fake Cause Probability
                predictions[cust_id] = 0.2 + 0.1 * (hash(cust_id) % 5)  # 0.2 to 0.6 approx

            # Assuming single output 'churn_probabilities'
            for output in outputs:
                if output == "churn_probabilities":
                    result[output] = predictions
                    self.context[output] = predictions
                else:
                    result[output] = None

        elif call_type == "function" and action == "SegmentCustomers":
            # segment customers based on churn_probabilities
            input_var = inputs[0]
            probs = self.context.get(input_var, {})
            segments = {}
            for cust_id, prob in probs.items():
                if prob > 0.5:
                    segments[cust_id] = "high_risk"
                elif prob > 0.3:
                    segments[cust_id] = "medium_risk"
                else:
                    segments[cust_id] = "low_risk"
            for output in outputs:
                if output == "customer_segments":
                    result[output] = segments
                    self.context[output] = segments
                else:
                    result[output] = None

        else:
            # fallback simulation from existing code
            if outputs:
                for output in outputs:
                    if output == "segment":
                        result[output] = "high_value"
                    elif output == "confidence":
                        result[output] = 0.95
                    else:
                        result[output] = 0.9

                for k, v in result.items():
                    self.context[k] = v

        return result if outputs else None

    def conditional_statement(self, stmt):
        cond = stmt["condition"]
        if self.evaluate_expression(cond):
            print("Condition true: executing then_body")
            return self.execute_block(stmt["then_body"])
        else:
            else_body = stmt.get("else_body")
            if else_body:
                print("Condition false: executing else_body")
                return self.execute_block(else_body)
        return None

    def evaluate_expression(self, expr):
        # Handle the case where expr is a string or primitive (e.g., variable name or literal)
        if isinstance(expr, str):
            # Treat string as variable name; look up in context
            parts = expr.split(".")
            val = self.context
            for part in parts:
                if isinstance(val, dict) and part in val:
                    val = val[part]
                else:
                    return None
            return val
        elif isinstance(expr, (int, float, bool)):
            # Return primitives as is
            return expr

        # Now expect expr to be a dict with a "type" key
        t = expr.get("type")
        if t == "BinaryExpression":
            left = self.evaluate_expression(expr["left"])
            right = self.evaluate_expression(expr["right"])
            return self.eval_binary(expr["operator"], left, right)
        elif t == "LogicalExpression":
            op = expr["operator"]
            operands = [self.evaluate_expression(o) for o in expr["operands"]]
            if op == "AND":
                return all(operands)
            elif op == "OR":
                return any(operands)
            elif op == "NOT":
                return not operands[0]
            else:
                raise ValueError(f"Unknown logical operator: {op}")
        elif t == "Variable":
            parts = expr["name"].split(".")
            val = self.context
            for part in parts:
                if isinstance(val, dict) and part in val:
                    val = val[part]
                else:
                    return None
            return val
        elif t == "Literal":
            return expr["value"]
        else:
            raise NotImplementedError(f"Expression type '{t}' not implemented.")

    def eval_binary(self, op, left, right):
        def try_convert(value):
            # Try converting to float if it's a string
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    return value  # Keep as string if cannot convert
            return value

        left_converted = try_convert(left)
        right_converted = try_convert(right)

        print(
            f"eval_binary: op={op}, left={left_converted}({type(left_converted)}), right={right_converted}({type(right_converted)})"
        )

        # Check for type compatibility before comparison
        if (isinstance(left_converted, (int, float)) and isinstance(right_converted, (int, float))):
            pass  # numeric comparison allowed
        elif (isinstance(left_converted, str) and isinstance(right_converted, str)):
            pass  # string comparison allowed
        else:
            raise TypeError(
                f"Cannot compare different types: {type(left_converted)} vs {type(right_converted)} for operator '{op}'"
            )

        if op == "<": return left_converted < right_converted
        if op == ">": return left_converted > right_converted
        if op == "<=": return left_converted <= right_converted
        if op == ">=": return left_converted >= right_converted
        if op == "==": return left_converted == right_converted
        if op == "!=": return left_converted != right_converted

        raise ValueError(f"Unsupported binary operator: {op}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py <pipeline.json>")
        exit(1)
    with open(sys.argv[1]) as f:
        ast = json.load(f)
    interpreter = AIQLInterpreter(ast)
    result = interpreter.run()
    print("Pipeline execution result:", result)

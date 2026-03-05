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
        # Simulated data: dict of features per customer
        data = {
            "customer_1": {"age": 30, "income": 50000, "region": "north", "tenure": 5, "support_tickets": 2},
            "customer_2": {"age": 45, "income": 70000, "region": "south", "tenure": 10, "support_tickets": 1},
            "customer_3": {"age": 25, "income": 40000, "region": "east", "tenure": 2, "support_tickets": 0},
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
                # normalize "input" to "inputs" for backward compatibility
                if "input" in step:
                    step["inputs"] = [step.pop("input")]
                data = self.execute_operation(step, data)
            elif step["type"] == "CallStatement":
                result = self.call_statement(step, input_data=data)
                if result:
                    combined_result.update(result)
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

        if name == "FeatureEngineering":
            # Extract specified features per customer
            features_list = op.get("params", {}).get("features", [])
            result = {}
            for cust_id, cust_data in input_data.items():
                result[cust_id] = {feat: cust_data.get(feat, None) for feat in features_list}
            self.context[op["output"]] = result
            return result

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

        if call_type == "model" and action == "churn_predictor_v1":
            # simulate prediction probabilities per customer
            input_var = inputs[0]
            features = self.context.get(input_var, {})
            cause_prob = {}
            confidence = {}
            for cust_id in features:
                # simple hash-based pseudo probabilities
                p = 0.2 + 0.1 * (hash(cust_id) % 5)  # 0.2 to 0.6
                cause_prob[cust_id] = round(p, 2)
                confidence[cust_id] = 0.9  # fixed confidence

            for output in outputs:
                if output == "cause_probability":
                    result[output] = cause_prob
                    self.context[output] = cause_prob
                elif output == "confidence_score":
                    result[output] = confidence
                    self.context[output] = confidence
                else:
                    result[output] = None
                    self.context[output] = None

        else:
            # fallback simulation for other models/functions
            if outputs:
                for output in outputs:
                    result[output] = 0.9
                    self.context[output] = 0.9

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
        if isinstance(expr, str):
            parts = expr.split(".")
            val = self.context
            for part in parts:
                if isinstance(val, dict) and part in val:
                    val = val[part]
                else:
                    return None
            return val
        elif isinstance(expr, (int, float, bool)):
            return expr

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
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    return value
            return value

        left_converted = try_convert(left)
        right_converted = try_convert(right)

        if (isinstance(left_converted, (int, float)) and isinstance(right_converted, (int, float))) or \
           (isinstance(left_converted, str) and isinstance(right_converted, str)):
            pass
        else:
            raise TypeError(f"Cannot compare different types: {type(left_converted)} vs {type(right_converted)}")

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
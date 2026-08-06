import re
from z3 import Solver, Int, sat

def solve_flag():
    # Load the full C++ file
    with open("out.cpp", "r") as f:
        cpp_code = f.read()

    solver = Solver()
    
    # Create Z3 variables for flag_0 to flag_213 inside a dictionary for easy eval()
    env = {"flags": [Int(f'flag_{i}') for i in range(214)]}

    # Assume standard printable ASCII characters for the flag
    for f in env["flags"]:
        solver.add(f >= 32, f <= 126)

    # Helper function to convert "FlagValue<X>::Value" to "flags[X]"
    def parse_val(v_str):
        v_str = v_str.strip()
        return re.sub(r'FlagValue<(\d+)>::Value', r'flags[\1]', v_str)

    # Parse each constraint line
    for line in cpp_code.splitlines():
        line = line.strip()
        if not line.startswith("using Constraint_"):
            continue
            
        # Extract the template name (Equ, Lt, etc.) and its arguments
        match = re.search(r'=\s*([A-Za-z]+)<(.+)>;', line)
        if not match:
            continue
            
        op = match.group(1)
        args = match.group(2).split(',')
        
        # Build and evaluate the equations dynamically based on the parsed template
        if op == "Equ":
            c1, c2, t1 = map(int, args[0:3])
            v1, v2, v3, v4, v5 = map(parse_val, args[3:8])
            expr = f"{c1} * {v1} + {c2} * {v2} + {t1} * {v3} == {v4} + {v5}"
            solver.add(eval(expr, {}, env))
            
        elif op in ["Lt", "Lteq", "Gt", "Gteq", "Divides"]:
            left = parse_val(args[0])
            right = parse_val(args[1])
            if op == "Lt":
                solver.add(eval(f"{left} < {right}", {}, env))
            elif op == "Lteq":
                solver.add(eval(f"{left} <= {right}", {}, env))
            elif op == "Gt":
                solver.add(eval(f"{left} > {right}", {}, env))
            elif op == "Gteq":
                solver.add(eval(f"{left} >= {right}", {}, env))
            elif op == "Divides":
                solver.add(eval(f"{left} % {right} == 0", {}, env))

    # Solve the system of constraints and decode the ASCII values
    if solver.check() == sat:
        m = solver.model()
        flag_chars = [chr(m[env["flags"][i]].as_long()) for i in range(214)]
        print("Agent Message / Flag:", "".join(flag_chars))
    else:
        print("Error: The constraints are unsatisfiable. Ensure you have the complete file.")

if __name__ == "__main__":
    solve_flag()
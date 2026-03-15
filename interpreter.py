import re

# -----------------------------
# Runtime storage
# -----------------------------
variables = {}
functions = {}
models = {}

# -----------------------------
# Utilities
# -----------------------------

def eval_expr(expr):
    expr = expr.strip()

    # replace variables
    for k, v in variables.items():
        expr = re.sub(rf"\\b{k}\\b", str(v), expr)

    return eval(expr)


def extract_block(lines, start):
    block = []
    i = start

    while lines[i].strip() != ";":
        block.append(lines[i])
        i += 1

    return block, i

# -----------------------------
# Model system
# -----------------------------

class NovaObject:
    def __init__(self, model, fields):
        self.__model = model
        self.__dict__.update(fields)


def define_model(name, args, body):

    fields = {}
    methods = {}

    i = 0

    while i < len(body):
        line = body[i].strip()

        if line.startswith("field"):
            i += 1

            while body[i].strip() != ";":
                l = body[i].strip()

                # this.age : int = age
                left, right = l.split("=")
                fname = left.split(".")[1].split(":")[0].strip()
                val = right.strip()

                fields[fname] = val

                i += 1

        elif line.startswith("function"):

            m = re.match(r"function (\\w+)\\(\\):", line)
            fname = m.group(1)

            inner, end = extract_block(body, i + 1)

            methods[fname] = inner

            i = end

        i += 1

    models[name] = {
        "args": args,
        "fields": fields,
        "methods": methods,
    }


def create_instance(name, arg_values):

    model = models[name]

    local = {}

    for a, v in zip(model["args"], arg_values):
        local[a] = v

    fields = {}

    for k, expr in model["fields"].items():
        val = expr

        for var in local:
            val = val.replace(var, str(local[var]))

        fields[k] = eval(val)

    return NovaObject(name, fields)


def call_method(obj, method):

    model = models[obj.__dict__["_NovaObject__model"]]

    body = model["methods"][method]

    for k in obj.__dict__:
        variables[k] = obj.__dict__[k]

    run_block(body)

# -----------------------------
# Function system
# -----------------------------


def define_function(name, args, body):
    functions[name] = (args, body)


def call_function(name, params):

    args, body = functions[name]

    backup = variables.copy()

    for a, v in zip(args, params):
        variables[a] = v

    run_block(body)

    variables.clear()
    variables.update(backup)

# -----------------------------
# Execution
# -----------------------------


def run_block(block):

    i = 0

    while i < len(block):

        line = block[i].strip()

        # print
        if line.startswith("print"):
            inside = line[line.find("(")+1:line.find(")")]

            if inside in variables:
                print(variables[inside])
            else:
                print(eval_expr(inside))

        # let
        elif line.startswith("let"):
            name = line.split()[1]
            val = line.split("=")[1]

            variables[name] = eval_expr(val)

        # if
        elif line.startswith("if"):
            cond = line[2:].replace(":","").strip()

            inner, end = extract_block(block, i + 1)

            if eval_expr(cond):
                run_block(inner)

            i = end

        # while
        elif line.startswith("while"):

            cond = line[5:].replace(":","").strip()

            inner, end = extract_block(block, i + 1)

            while eval_expr(cond):
                run_block(inner)

            i = end

        # for
        elif line.startswith("for"):

            header = line[3:].replace(":","").strip()
            parts = header.split(";")

            init = parts[0].strip()
            cond = parts[1].strip()
            step = parts[2].replace("on","").strip()

            var = init.split("=")[0].strip()
            start = eval_expr(init.split("=")[1])

            variables[var] = start

            inner, end = extract_block(block, i + 1)

            while eval_expr(cond):

                run_block(inner)

                if step.startswith("+"):
                    variables[var] += int(step[1:])

                elif step.startswith("*"):
                    variables[var] *= int(step[1:])

            i = end

        # function
        elif line.startswith("function"):

            m = re.match(r"function (\\w+)\\((.*?)\\):", line)

            name = m.group(1)
            args = [x.strip() for x in m.group(2).split(",") if x.strip()]

            inner, end = extract_block(block, i + 1)

            define_function(name, args, inner)

            i = end

        # model
        elif line.startswith("model"):

            m = re.match(r"model (\\w+)\\((.*?)\\):", line)

            name = m.group(1)
            args = [x.strip() for x in m.group(2).split(",") if x.strip()]

            inner, end = extract_block(block, i + 1)

            define_model(name, args, inner)

            i = end

        i += 1

# -----------------------------
# Program runner
# -----------------------------


def run(code):

    lines = []

    for l in code.split("\n"):
        l = l.strip()

        if l != "":
            lines.append(l)

    run_block(lines)


# -----------------------------
# Entry
# -----------------------------

if __name__ == "__main__":

    with open("test.nv") as f:
        code = f.read()

    run(code)

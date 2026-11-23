# import ast

# content = "x = 10 + 20"

# tree = ast.parse(content)

# assignment = tree.body[0]
# target = assignment.targets[0]
# value = assignment.value

# print("Variable:", target.id)
# print("Left:", value.left.value)
# print("Operator:", type(value.op).__name__)
# print("Right:", value.right.value)


# import ast

# content = """def add(a, b):
#     return a + b

# def multiply(a, b):
#     return a * b
# """

# tree = ast.parse(content)

# print(len(tree.body))

# print(ast.dump(tree.body[0], indent=4))

# for node in tree.body:
#     if isinstance(node, ast.FunctionDef):
#         print("Function :", node.name)
#         print("Start line:", node.lineno)  
#         print("End line:", node.end_lineno) 
# function = tree.body[0]

# print(function._fields)
# print(function.name)


# print(type(tree))
# print(len(tree.body))




import ast 

content = """def add(a , b):
    return a + b 

def multiply(a , b):
    return a * b
"""

tree = ast.parse(content)

lines = content.splitlines(keepends=True)
for node in tree.body:
    # print(type(node).__name__)
    # print(node._attributes)


    # print(lines)

    functions_line = lines[node.lineno - 1:node.end_lineno]
    function_code = "".join(functions_line)

    print(str(function_code))
# print(tree.body)
# print(ast.dump(tree.body[0]))
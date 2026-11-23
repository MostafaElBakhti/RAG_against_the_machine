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
max_chunk_size = 50

tree = ast.parse(content)

chunks = []

lines = content.splitlines(keepends=True)
current_size = 0
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        
        
        start = sum(len(line) for line in lines[:node.lineno - 1])
        end = sum(len(line) for line in lines[:node.end_lineno])
        function_code = content[start:end]
        function_size = end - start

        # print("Function:", node.name)
        # print("Start:", start)
        # print("current_size:", current_size)
        # print("End:", end)
        # print("function_size:", function_size)

        if function_size + current_size <= max_chunk_size:
            current_size += function_size
            chunks.append(function_code)
        else:
            print(f"{node.name} needs a new chunk")
            chunks.append(function_code)
            current_size = function_size

        # print("Function code:\n", function_code)
        
print("Chunks:")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i + 1}:\n{chunk}")
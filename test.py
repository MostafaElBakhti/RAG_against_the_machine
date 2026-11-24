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




# import ast 

# content = """def add(a , b):
#     return a + b 

# def multiply(a , b):
#     return a * b
# """
# max_chunk_size = 100

# tree = ast.parse(content)

# chunks = []
# current_start = None
# current_end = None

# lines = content.splitlines(keepends=True)
# for node in tree.body:
#     if isinstance(node, ast.FunctionDef):
        
        
#         start = sum(len(line) for line in lines[:node.lineno - 1])
#         end = sum(len(line) for line in lines[:node.end_lineno])
#         # function_code = content[start:end]
#         # function_size = end - start

#         if current_start is None:
#             current_start = start 
#             current_end = end
#         elif end - current_start <= max_chunk_size:
#             current_end = end
#         else:
#             chunks.append((current_start, current_end))
#             current_start = start
#             current_end = end
# if current_start is not None:
#     chunks.append((current_start, current_end))
        
# for start, end in chunks:
#     print(content[start:end])
# print(len(chunks))














import ast 

content = """def add(a , b):
    return a + b 

def multiply(a , b):
    return a * b

x = 10
"""


tree = ast.parse(content)
lines = content.splitlines(keepends=True)
print(lines)

chunks = []
max_chunk_size = 5

current_start = None
current_end = None

for node in tree.body:
    if isinstance(node , ast.FunctionDef):
        
        start = sum( len(line) for line in lines[:node.lineno - 1])
        end = sum( len(line) for line in lines[:node.end_lineno] )
        # print(start)
        # print(end)

        code = content[start:end]
        print("code", code )

        if current_start is None:
            current_end = end 
            current_start = start
        elif end - current_start <= max_chunk_size:
            current_end = end
        else:
            chunks.append((current_start, current_end))
            current_start = start
            current_end = end

        # if end - start <= max_chunk_size:
        #     print("it fits")
        # else: 
        #     print("not fit")

        # print(node._fields)
        # print(node._attributes)
        # print(node.name)
        # print(node.lineno)
        # print(node.end_lineno)
if current_start is not None:
    chunks.append((current_start, current_end))

# print(ast.dump(tree, indent=4))
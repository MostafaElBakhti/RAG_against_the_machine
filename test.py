# from src.chunker import python_chunks
# import ast




# content = """def add(a , b):
#     print("a")
#     return a + b 

# def multiply(a , b):
#     return a * b

# x = 10
# """


# starts = [0]

# for index, character in enumerate(content):
#     if character == "\n":
#         starts.append(index + 1)
        
# if starts[-1] != len(content):
#     starts.append(len(content))

# # print(starts)

# tree = ast.parse(content)

# for node in tree.body:
#     if isinstance(node, ast.FunctionDef):
        
#         start = starts[node.lineno - 1]
#         end = starts[node.end_lineno]
        
#         print(start, end)
#         print("code", content[start:end])
        # print(node.name)\
# cuts = {0, len(content)}

# for node in tree.body:
#     start = starts[node.lineno - 1]
#     cuts.add(start)
    
# cuts = sorted(cuts)
# print(cuts)
# ranges = []

# for i in range(len(cuts) - 1):
#     start = cuts[i]
#     end = cuts[i + 1]

#     ranges.append((start, end))

# print(ranges)

# for start, end in ranges:
#     print("Range:", start, end)
#     print("Size:", end - start)
#     print(content[start:end])

# # python_chunks(content, 15)


from src.chunker import python_chunks



content = """x = 1
def f():
    a = 1
    return a
y = 2
"""

max_chunk_size = 20

chunks = python_chunks(content, max_chunk_size)

for start , end in chunks:
    print("*" * 10)
    print(content[start:end])

# content = """def add(a , b):
#     print("a")
#     return a + b 

# def multiply(a , b):
#     return a * b

# x = 10
# """

# ranges = python_chunks(content, 40)

# print(ranges)

# for start, end in ranges:
#     print("Start:", start)
#     print("End:", end)
#     print("Size:", end - start)
#     print(repr(content[start:end]))
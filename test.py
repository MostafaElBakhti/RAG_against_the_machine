# import ast
# from src.chunker import line_starts

# content = "x = 1\ry = 2\rz = 3"

# tree = ast.parse(content)

# for node in tree.body:
#     print(node.lineno)

# print(line_starts(content))

from pathlib import Path

file_path = Path("newline_test.txt")

file_path.write_bytes(b"x = 1\r\ny = 2")

with file_path.open("r", encoding="utf-8", newline="") as file:
    content = file.read()

print(repr(content))
print(len(content))

print(repr(content))
print(len(content))
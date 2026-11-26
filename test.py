from src.chunker import python_chunks

content = """x = 1
abcdefghij
"""

ranges = python_chunks(content, -6)

print(ranges)

for start, end in ranges:
    print(repr(content[start:end]))


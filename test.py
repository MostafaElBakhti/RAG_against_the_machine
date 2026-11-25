from src.chunker import python_chunks


content = """def add(a , b):
    print("a")
    return a + b 

def multiply(a , b):
    return a * b

x = 10
"""

python_chunks(content, 15)
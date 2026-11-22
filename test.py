import ast

content = "x = 10 + 20"

tree = ast.parse(content)

assignment = tree.body[0]
target = assignment.targets[0]

print(target.id)

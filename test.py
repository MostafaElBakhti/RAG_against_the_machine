from pydantic import BaseModel

class Test(BaseModel):
    name : str
    age : int 



test = Test("mostafa", "15")
print(test)
import fire

def index(max_chunk_size: int = 2000) -> str:
    return f"Indexing with size {max_chunk_size}"



if __name__ == "__main__":
    fire.Fire({
        "index" : index
        })

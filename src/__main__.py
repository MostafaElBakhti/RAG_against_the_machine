import fire
from pathlib import Path

def index(max_chunk_size: int = 2000) -> None:
    directory = Path("data/raw")

    print(f"Maximum chunk size: {max_chunk_size}")
    print(f"Directory exists: {directory.exists()}")
    print(f"Is directory: {directory.is_dir()}")

    for file_path in directory.rglob("*.py"):
        print(file_path)



if __name__ == "__main__":
    fire.Fire({
        "index" : index
        })

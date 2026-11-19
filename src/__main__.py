import fire
from pathlib import Path

def index(max_chunk_size: int = 2000) -> None:
    directory = Path("data/raw")

    if max_chunk_size <= 0:
        raise ValueError("max_chunk_size must be positive")
    
    if not directory.is_dir():
        raise NotADirectoryError(f"invalid directory : {directory}")

    for file_path in directory.rglob("*"):
        
        if not file_path.is_file():
            continue
        
        if file_path.suffix not in (".py", ".md", ".txt"):
            continue
        
        try :
            content = file_path.read_text(encoding="utf-8")
        except (OSError , UnicodeDecodeError) as error :
            print(f"Cannot read {file_path}: {error}")
            continue

        for start in range(0, len(content), max_chunk_size):
            end = min(start + max_chunk_size, len(content))
            chunk = content[start:start + max_chunk_size]
            
            print(f"File: {file_path}")
            print(f"Start: {start}, End: {end}")
            print(chunk)


if __name__ == "__main__":
    fire.Fire({
        "index" : index
        })

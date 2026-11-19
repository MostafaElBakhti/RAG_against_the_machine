for file_path in directory.rglob("*.py"):
    content = file_path.read_text(encoding="utf-8")

    for start in range(0, len(content), max_chunk_size):
        chunk = content[start:start + max_chunk_size]
def fixed_size_chunks(content: str, max_chunk_size: int) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    
    for start in range(0, len(content), max_chunk_size):
        end = min(start+ max_chunk_size, len(content))
        ranges.append((start,end))

    return ranges
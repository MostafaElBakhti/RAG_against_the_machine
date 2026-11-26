import ast
import sys

def validate_chunk_size(max_chunk_size: int) -> None:
    if not 1 <= max_chunk_size <= 2000:
        raise ValueError(
            "max_chunk_size must be between 1 and 2000"
        )

def fixed_size_chunks(
    content: str, max_chunk_size: int
) -> list[tuple[int, int]]:
    """ Split content into fixed-size chunks. """

    ranges: list[tuple[int, int]] = []

    for start in range(0, len(content), max_chunk_size):
        end = min(start + max_chunk_size, len(content))
        ranges.append((start, end))

    return ranges

def line_starts(content: str) -> list[int]: 
    """ Return a list of starting indices for each line in the content. """
    starts: list[int] = [0]

    for index, character in enumerate(content):
        if character == "\n":
            starts.append(index + 1)

    if starts[-1] != len(content):
        starts.append(len(content))

    return starts


def pack_ranges(
    content: str,
    ranges: list[tuple[int,int]],
    max_chunk_size: int
) -> list[tuple[int,int]]:
    
    chunks: list[tuple[int, int]] = []
    
    current_start: int | None = None
    current_end: int = 0
    
    for start, end in ranges:
        
        if end - start > max_chunk_size:
            if current_start is not None:
                chunks.append((current_start, current_end))
                current_start = None
                current_end = 0

            block = content[start:end]
            block_starts = line_starts(block)

            line_ranges: list[tuple[int, int]] = []

            for i in range(len(block_starts) - 1):
                line_start = start + block_starts[i]
                line_end = start + block_starts[i + 1]

                line_ranges.append((line_start, line_end))

            if len(line_ranges) == 1:
                for local_start, local_end in fixed_size_chunks(
                    block, max_chunk_size
                ):
                    chunks.append(
                        (start + local_start, start + local_end)
                    )
                continue
            
            smaller_chunks = pack_ranges(
                content, line_ranges, max_chunk_size
            )

            chunks.extend(smaller_chunks)
        elif current_start is None:
            current_start = start 
            current_end = end
            
        elif end - current_start <= max_chunk_size:
            current_end = end
            
        else:
            chunks.append((current_start, current_end))
            current_start = start
            current_end = end
            
    if current_start is not None:
        chunks.append((current_start, current_end))
        
    return chunks

def python_chunks(
    content: str, max_chunk_size: int
) -> list[tuple[int, int]]:
    """ Split Python code into chunks based on function definitions and max_chunk_size. """
    try:
        validate_chunk_size(max_chunk_size)
    except ValueError as error:
        print(f"Error: {error}")
        sys.exit(1)
    
    tree = ast.parse(content)
    starts = line_starts(content)

    cuts: set[int] = {0, len(content)}

    for node in tree.body:
        cuts.add(starts[node.lineno - 1])

    sorted_cuts = sorted(cuts)

    ranges: list[tuple[int, int]] = []

    for i in range(len(sorted_cuts) - 1):
        start = sorted_cuts[i]
        end = sorted_cuts[i + 1]

        ranges.append((start, end))

    return pack_ranges(content, ranges, max_chunk_size)










            # function_size = end - start 
            # print(node.name , start , end , function_size)

            # if function_size > max_chunk_size:

            #     for statement in node.body:

            #         statement_start = sum(
            #             len(line) for line in lines[:statement.lineno - 1]
            #         )

            #         statement_end = sum(
            #             len(line) for line in lines[:statement.end_lineno]
            #         )

            #         statement_size = statement_end - statement_start

            #         if statement_size <= max_chunk_size:
            #             chunks.append((statement_start, statement_end))

            #         else:
            #             ranges = fixed_size_chunks(
            #                 content[statement_start:statement_end],
            #                 max_chunk_size
            #             )

            #             for local_start, local_end in ranges:
            #                 chunks.append((
            #                     statement_start + local_start,
            #                     statement_start + local_end
            #                 ))

            #     continue

    #         if current_start is None:
    #             current_start = start
    #             current_end = end
            
    #         elif end - current_start <= max_chunk_size:
    #             current_end = end
    #         else:
    #             chunks.append((current_start, current_end))
    #             current_start = start
    #             current_end = end 

    # if current_start is not None:
    #     chunks.append((current_start, current_end))
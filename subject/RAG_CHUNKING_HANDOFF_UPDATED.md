# RAG against the machine — Chunking review handoff

**Date:** 26 November 2026  
**Scope:** Chunking only (mandatory 42 subject, version 2.0)  
**Status:** AST-guided Python segmentation and line-based recursive packing have been developed during tutoring. The chunker is incomplete; the Markdown/text strategy, termination fallback, integration and full validation are pending.

## 1. Instructions for Claude

Review the design and current implementation below against `subject.pdf` and the actual project files if provided. The student wants to understand the execution flow and every implementation decision, so recommend incremental changes rather than a complete replacement. Focus on chunking correctness, source offsets, context preservation, retrieval implications, and simplicity. Do not implement retrieval, embeddings, answer generation, external frameworks, or deployment in this review.

This document supersedes the earlier chunking handoff's implementation snapshot. It incorporates the subsequent refactor into `line_starts()`, `python_chunks()` and `pack_ranges()`, and the detailed recursive execution example. The code below is reconstructed from the tutoring discussion, not read from the student's local repository. The reconstructed version was run on small examples; actual local changes and full-corpus behavior have not been verified. The vLLM corpus and official evaluator executable were not available when preparing this update.

## 2. Subject constraints relevant to chunking

The attached `subject.pdf` was rechecked for the following requirements. Page numbers refer to the printed pages.

| Requirement | Subject reference |
| --- | --- |
| Index useful files from the supplied vLLM 0.10.1 codebase | VI.1, p. 10 |
| Two distinct strategies: Python and Markdown/text | VI.1, p. 10 |
| Configurable `--max_chunk_size`, default 2000 characters | VI.1, p. 11 |
| Never return a source longer than 2000 characters; a single overlong source invalidates the output | VI.1–VI.2, p. 11 |
| Return exact corpus paths and character ranges | VI.2, p. 11 |
| Persist the index under `data/processed/` | VI.1, p. 11 |
| Match source paths exactly; example `data/raw/vllm-0.10.1/docs/features/lora.md` | VI.2, p. 11 |
| Recall@5: at least 50% for code, 80% for documentation; matching requires same file and IoU at least 0.05 | VII.1, pp. 19–20 |
| Full-corpus indexing at most 5 minutes; retrieval of 200 questions at most 90 seconds | VII.1.2, p. 20 |
| Python 3.10+, flake8, mypy, type hints, docstrings, robust resource/error handling | V.1, p. 8 |

The index must eventually support BM25 or TF-IDF. Chunking should therefore preserve useful lexical evidence, particularly function names, identifiers, docstrings and explanatory text. Retrieval implementation is outside this handoff.

**Not mandatory:** AST, recursion, overlap, parent-child indexing, a particular chunk size below 2000, or a particular splitting library. These are design choices. The subject permits other libraries, but the student wants to build the mandatory solution with understandable, minimal dependencies before exploring advanced frameworks.

## 3. Project state and what we have learned

Relevant project structure (as discussed, not a verified directory listing):

```text
RAG/
├── pyproject.toml
├── uv.lock
├── src/
│   ├── __init__.py
│   ├── __main__.py      # Fire CLI / early index prototype
│   ├── models.py       # Pydantic models
│   └── chunker.py      # current focus
├── test.py             # manual chunking experiments
└── data/
    ├── raw/            # original corpus
    └── processed/      # eventual index destination
```

Earlier indexing prototype: walk `Path("data/raw").rglob("*")`, select regular `.py`, `.md`, `.txt` files, read UTF-8, catch `OSError` and `UnicodeDecodeError`, then construct chunk objects. The prototype used fixed-size ranges and debug output. Integration of the newer AST chunker into that prototype is not confirmed. The eventual CLI is `uv run python -m src index --max_chunk_size=2000`.

Models already discussed:

```python
from pydantic import BaseModel


class MinimalSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int


class Chunk(BaseModel):
    text: str
    source: MinimalSource
```

`MinimalSource` is a subject-defined model. `Chunk` is our internal representation. Once a range is finalized, its text is constructed using `content[start:end]`. The range must refer to the same original text representation used by the grader. Do not add synthetic headers to the stored source text if that would break this invariant. Separate metadata or retrieval-only text may be considered later.

### Evolution of the chunker

1. Started with fixed-size character chunks, using `range(0, len(content), max_chunk_size)` and `min()` for the last endpoint.
2. Introduced AST to identify complete functions and preserve useful code structure when possible.
3. The first AST implementation inspected only `FunctionDef` nodes, which could omit imports, assignments, classes, comments, whitespace and other source text. Repeated prefix sums of line lengths also risked quadratic work.
4. Refactored to calculate line offsets once, collect boundaries for all top-level AST statements, and include the start and end of the source. Sort and deduplicate these boundaries before forming adjacent ranges.
5. Separated AST boundary detection from the packing algorithm. Python-specific logic decides initial boundaries; a reusable packer enforces sizes and groups contiguous ranges.
6. Implemented recursive line-based splitting for oversized ranges. Flush any pending chunk before the split, convert local line offsets to absolute offsets, recursively pack the lines, and extend the outer chunk list.
7. Traced a full example where the second AST range is oversized and learned why the pending state is reset, why `extend()` is used, and why the final pending chunk is appended after the loop.
8. Identified a new semantic concern: two chunks originating from one oversized function are adjacent but have no explicit shared-parent identity. This has not been solved yet.

## 4. Current implementation snapshot

The following is the current learning-stage code as reconstructed from the discussion. It intentionally does **not** include proposed fixes, so Claude can review the real design state. Docstrings and formatting improvements remain pending.

```python
import ast


def fixed_size_chunks(content: str, max_chunk_size: int) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for start in range(0, len(content), max_chunk_size):
        end = min(start + max_chunk_size, len(content))
        ranges.append((start, end))
    return ranges


def line_starts(content: str) -> list[int]:
    starts: list[int] = [0]
    for index, character in enumerate(content):
        if character == "\n":
            starts.append(index + 1)
    if starts[-1] != len(content):
        starts.append(len(content))
    return starts


def python_chunks(content: str, max_chunk_size: int) -> list[tuple[int, int]]:
    tree = ast.parse(content)
    starts = line_starts(content)
    cuts: set[int] = {0, len(content)}
    for node in tree.body:
        start = starts[node.lineno - 1]
        cuts.add(start)
    sorted_cuts = sorted(cuts)
    ranges: list[tuple[int, int]] = []
    for i in range(len(sorted_cuts) - 1):
        start = sorted_cuts[i]
        end = sorted_cuts[i + 1]
        ranges.append((start, end))
    return pack_ranges(content, ranges, max_chunk_size)


def pack_ranges(
    content: str,
    ranges: list[tuple[int, int]],
    max_chunk_size: int,
) -> list[tuple[int, int]]:
    chunks: list[tuple[int, int]] = []
    current_start = None
    current_end = None
    for start, end in ranges:
        if end - start > max_chunk_size:
            if current_start is not None:
                chunks.append((current_start, current_end))
                current_start = None
                current_end = None
            block = content[start:end]
            block_starts = line_starts(block)
            line_ranges: list[tuple[int, int]] = []
            for i in range(len(block_starts) - 1):
                line_start = start + block_starts[i]
                line_end = start + block_starts[i + 1]
                line_ranges.append((line_start, line_end))
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
```

### Responsibilities and contract

| Function | Current responsibility |
| --- | --- |
| `fixed_size_chunks()` | Split a string into character ranges. Exists but is not yet called by the new packer. Returns offsets local to the supplied string. |
| `line_starts()` | Record line starts by scanning `\n`, including a final end-of-content sentinel without duplicating it. |
| `python_chunks()` | Parse AST, select top-level statement line starts, construct contiguous candidate ranges, delegate to packer. Does not itself enforce maximum sizes. |
| `pack_ranges()` | Merge adjacent small ranges when they fit; split oversized ranges into lines and recursively pack them. Currently has a termination bug. |

The packer currently assumes its inputs are valid, ordered, contiguous, nonempty spans within `content` (an empty list is allowed). `python_chunks()` produces such spans for normal LF Python text. This contract has not yet been enforced or documented in the implementation. It is important because `end - current_start` measures the entire contiguous span, not just the sum of arbitrary range sizes.

Offsets are half-open `[start, end)`. A chunk length is `end - start`. Newlines, tabs, spaces, indentation and Unicode characters all contribute to Python string length. AST `lineno` is 1-based; list indices are 0-based. AST column offsets are UTF-8 byte offsets, not Python character indices; the current implementation deliberately uses whole-line offsets rather than columns.

## 5. Full execution example — oversized second range

The example below was executed against the reconstructed code. The output and character counts were verified.

```python
content = """x = 1
def f():
    a = 1
    return a
y = 2
"""
max_chunk_size = 20
```

### A. `python_chunks()`

`ast.parse(content)` creates an `ast.Module`. Its top-level `tree.body` contains:

| Node | `lineno` | Meaning |
| --- | ---: | --- |
| `Assign` | 1 | `x = 1` |
| `FunctionDef` | 2 | `def f():` and its body |
| `Assign` | 5 | `y = 2` |

`starts = line_starts(content)` returns `[0, 6, 15, 25, 38, 44]`. These are line positions in the original string, including the end sentinel. The list is a lookup table converting AST line numbers to character offsets.

```python
cuts = {0, len(content)}          # {0, 44}
# For each top-level node:
# cuts.add(starts[node.lineno - 1])
sorted_cuts = [0, 6, 38, 44]
ranges = [(0, 6), (6, 38), (38, 44)]
```

The two lines inside `f()` are not direct members of `tree.body`, so their starts are not selected at this stage. The full function is an initial candidate even though its length is 32, greater than 20.

### B. Outer `pack_ranges()` call

Initial state: `chunks = []`, `current_start = None`, `current_end = None`.

| Range | Action | Pending state | Saved chunks |
| --- | --- | --- | --- |
| `(0, 6)` | Fits; initialize pending chunk | `(0, 6)` | `[]` |
| `(6, 38)` | Oversized; flush pending chunk and reset state | None | `[(0, 6)]` |

Resetting the pending state means there is nothing left to extend or append. Without this reset, a later branch could append the first chunk a second time or extend an already-finalized range across other chunks.

The oversized block is `content[6:38]`. Its local boundaries are `[0, 9, 19, 32]`. Add the original block start (`6`) to each endpoint to get absolute ranges:

```python
line_ranges = [(6, 15), (15, 25), (25, 38)]
smaller_chunks = pack_ranges(content, line_ranges, 20)
```

Pass the entire original `content`, not the sliced `block`, because `line_ranges` uses absolute positions.

### C. Recursive `pack_ranges()` call

The outer call pauses. The recursive call has its own `chunks`, `current_start` and `current_end` local variables, initialized independently.

| Input | Decision | Pending range | Saved ranges |
| --- | --- | --- | --- |
| `(6, 15)` | 9 chars; start pending chunk | `(6, 15)` | `[]` |
| `(15, 25)` | Combined length `25 - 6 = 19` fits; update only `current_end` | `(6, 25)` | `[]` |
| `(25, 38)` | Combined length `38 - 6 = 32` exceeds 20; save pending and start new one | `(25, 38)` | `[(6, 25)]` |
| End of loop | Flush remaining pending chunk | `(25, 38)` | `[(6, 25), (25, 38)]` |

Combining ranges does not concatenate strings or tuples; it keeps the start position and extends the endpoint. The tuple is created when a pending chunk is finalized. Appending every iteration would create duplicate coverage.

The recursive call returns `[(6, 25), (25, 38)]`.

### D. Resume outer call

```python
chunks = [(0, 6)]
smaller_chunks = [(6, 25), (25, 38)]
chunks.extend(smaller_chunks)
# [(0, 6), (6, 25), (25, 38)]
```

`extend()` adds each tuple. `append(smaller_chunks)` would create a nested list instead of a flat list of range tuples.

The final outer range `(38, 44)` fits, and the pending state is empty, so it becomes the new pending range. After the loop, the `if current_start is not None` condition flushes it. If the final input range had been oversized and recursively finalized, there would be no pending range to append.

Verified result:

```python
[(0, 6), (6, 25), (25, 38), (38, 44)]
```

| Chunk | Size | Exact text (`repr`) |
| --- | ---: | --- |
| 1 | 6 | `'x = 1\n'` |
| 2 | 19 | `'def f():\n    a = 1\n'` |
| 3 | 13 | `'    return a\n'` |
| 4 | 6 | `'y = 2\n'` |

Concatenating these four source slices reconstructs the original 44-character string. All four fit the selected maximum. The sizes are intentionally tiny for teaching, not recommended retrieval settings.

## 6. Immediate correctness bug — oversized single line

The recursive packer has no fallback when there are no finer line boundaries. Consider:

```python
content = 'value = "abcdefghij"\n'
max_chunk_size = 10
```

The AST produces `(0, 21)`. Splitting that block by line starts yields `[0, 21]`, so `line_ranges` is again `[(0, 21)]`. The recursive call receives exactly the same oversized range, repeats the same split, and eventually raises `RecursionError`. This was reproduced on the reconstructed code.

Proposed next small change (NOT implemented in the snapshot): after constructing `line_ranges`, before the recursive call, detect that the range has no finer line boundary. Use the existing character splitter and translate local offsets back to the original file.

```python
if len(line_ranges) == 1:
    for local_start, local_end in fixed_size_chunks(
        block, max_chunk_size
    ):
        chunks.append((start + local_start, start + local_end))
    continue
```

An equivalent guard using `len(block_starts) == 2` is possible for a valid nonempty block. The `continue` is essential here to avoid the same recursive call after the fallback. Validate `max_chunk_size > 0` before any splitting. A fixed-size fallback must produce strictly smaller spans when a block exceeds the limit. Review whether this simple recursion should remain or be replaced with a nonrecursive implementation; no large rewrite is needed merely to fix termination.

## 7. Semantic problem — preserving a function across chunks

This is the student's latest question and the main design decision for review.

In the execution example, chunks 2 and 3 belong to the same original function `f()`:

```text
Original AST candidate: [6, 38) — FunctionDef f
    ├── [6, 25) — def f(): / a = 1
    └── [25, 38) — return a
```

The final flat range list preserves their adjacency, but **does not explicitly preserve their shared AST parent**. Chunk 3 can be retrieved independently and lacks the function name, argument context, and assignment to `a`. This matters for lexical retrieval as well as LLM context: a query mentioning `f` might match chunk 2 but miss relevant code in chunk 3, and a query matching the body may miss the declaration.

The problem becomes more serious with long classes, methods, nested functions, long docstrings, multiline calls, and dependent code. It also occurs when a chunk contains several small top-level nodes: a single `parent` field may not adequately describe the entire chunk.

### Options for Claude to compare (not implemented)

| Approach | Potential benefit | Tradeoffs / constraints |
| --- | --- | --- |
| Keep current nonoverlapping partition as baseline | Simple, exact reconstruction, fewer indexed chunks | Context lost at split boundaries |
| Internal metadata for parent identity and source span | Preserve provenance without altering original text; enable grouping | Requires richer internal model; parent name alone is not unique; merged chunks may have multiple parents |
| Retrieval-only contextual text | Include parent name/signature or section title for lexical matching without altering stored source | Changes ranking; metadata alone does not give the LLM missing code; avoid artificial source coordinates |
| Neighbor retrieval | Fetch nearby spans in same file, optionally restricted to parent | Can waste top-k slots and mix unrelated statements; adjacency alone does not identify a function |
| Parent-child retrieval | Search fine-grained children, recover relevant parent context | A full parent may exceed 2000 characters and cannot be returned as one source; expansion must obey source caps and answer context limits |
| Bounded overlap | Preserve some context across adjacent chunks | More indexing work, duplicate coverage, near-duplicate results occupying top-k; overlap never guarantees shared parent identity |
| AST child-statement boundaries before line splitting | Preserve method/statement structure better in oversized code | More implementation complexity; still needs line and character fallback |

A possible internal parent identifier is a tuple of exact file path, parent start/end, kind and qualified name (where known). It is **not** a proposed change to the mandatory `MinimalSource` schema. Keep canonical source slices unchanged. If overlap is adopted, update the coverage tests: overlapping slices no longer reconstruct the source by naive concatenation. Measure usefulness instead of assuming overlap is inherently better.

The intended architecture is structure-aware, but current oversized handling is only line-aware. It does not yet split large classes at method boundaries, or functions at child-statement boundaries. Claude should recommend whether to implement these first, add parent metadata first, or keep a minimal baseline and evaluate before adding complexity.

## 8. Other known or anticipated failure modes

| Issue | Current behavior / concern | Review direction |
| --- | --- | --- |
| Decorators | `node.lineno` points to `def`/`class`, not necessarily first decorator. All text remains in a partition, but decorators may be attached to the previous candidate. | Choose earliest decorator line for `FunctionDef`, `AsyncFunctionDef`, `ClassDef`. Test stacked/multiline decorators. |
| Comments and blank lines | Every character is preserved for normal LF text, but comments between nodes belong to the preceding span under current boundary policy. | Decide whether leading comments belong with following node; do not discard whitespace. |
| Same-line statements | Multiple AST nodes on one line share a cut; set deduplicates them. | Fine for whole-line approach. Exact column splitting is optional and needs byte-to-character conversion. |
| AST parse failure | No exception handling in `python_chunks()`. Syntax errors currently propagate. | Decide graceful fallback to line/character splitting versus reporting/skipping; consider `SyntaxError`, `ValueError`, `RecursionError`. |
| Newline conventions | `line_starts()` scans only LF. Python text I/O may normalize CRLF and bare CR. If raw bare CR text reaches AST, line numbers can disagree with the offset table. | Verify which representation the evaluator uses. Do not silently normalize source after assigning offsets. Test CRLF and bare CR. |
| Unicode | Python `str` offsets count code points, not UTF-8 bytes or grapheme clusters. AST column fields use byte offsets. | Retain consistent character-index semantics, test Unicode and combining characters. |
| Empty / whitespace-only files | Empty string returns `[]`; whitespace-only or comment-only files can yield a single candidate (or recurse if large). | Test and decide indexing policy without corrupting offsets. |
| Invalid size | No validation in snapshot. Zero/negative values can lead to invalid behavior; values above 2000 violate safe source cap. | Reject invalid sizes at public boundary, including bool if accepted by Fire, and ensure helper preconditions. |
| Noncontiguous / malformed ranges | Packer assumes order, bounds and contiguity. | Document and enforce or test the contract. Decide if packer should support overlap later. |
| Type checking | `current_end` may be inferred as `int | None`; checking `current_start` alone does not establish its type to mypy. | Use an explicit invariant, paired state, assertion, or safe typed sentinel; add docstrings and run required lint checks. |
| Chunk utilization | The outer packer does not merge neighboring small chunks across a recursive split. In the example `(25, 38)` and `(38, 44)` could fit together (19 chars). | Not a correctness bug; decide whether preserving the original boundary is preferable to denser packing. |
| Repeated copies / memory | The implementation scans content, allocates candidate and line range lists, and slices oversized blocks. | Measure full-corpus indexing time and memory; avoid premature optimization. |

## 9. Markdown/text chunker — still missing

The subject requires a genuinely distinct second strategy. Proposed baseline: detect Markdown headings and paragraph/blank-line boundaries, use whole logical sections when they fit, and fall back to finer paragraph/line/character boundaries when needed. For plain `.txt`, use paragraph or blank-line boundaries rather than AST. Both strategies can reuse a corrected `pack_ranges()` and `fixed_size_chunks()`.

Open issues to review: headings inside fenced code blocks, fenced blocks larger than the limit, long paragraphs, lists, tables, Setext headings, preambles, text without a trailing newline, and how to associate headings with child chunks. A full Markdown parser is not required unless justified. The exact implementation remains undecided.

## 10. Test plan and validation

### Results already observed on the reconstructed snapshot

- Normal oversized second-range example: exact four expected ranges, exact reconstruction.
- Single oversized line: raises `RecursionError`.
- Empty input: returns `[]`.
- Invalid Python syntax (`def f(\n`): raises `SyntaxError`.

These are small smoke tests, not results from the actual student repository or official grader.

### Minimum regression tests after the fix

For the nonoverlapping baseline, verify these invariants for every selected source string (assuming the file is intentionally included and the size is valid):

```python
assert all(0 <= s < e <= len(content) for s, e in chunks)
assert all(e - s <= max_chunk_size for s, e in chunks)
assert ''.join(content[s:e] for s, e in chunks) == content
if chunks:
    assert chunks[0][0] == 0
    assert chunks[-1][1] == len(content)
    assert all(a[1] == b[0] for a, b in zip(chunks, chunks[1:]))
else:
    assert content == ''
```

Use explicit test cases for:

- Empty file, one small line, a line exactly at the limit, single oversized line at offset 0 and at a nonzero offset.
- Oversized first, middle, last and consecutive candidates; small pending chunk before an oversized candidate; pending chunk after one.
- Only imports/assignments, classes, async functions, nested functions, decorators, semicolon-separated statements, comments and trailing whitespace.
- Unicode, CRLF, bare CR, no trailing newline, invalid syntax; size 0, negative, 1, 2000 and above 2000.
- Markdown headings, fenced blocks, lists, blank-line paragraphs, huge paragraphs and giant lines.
- Correct `MinimalSource` path and slice construction from chunk ranges after integrating into indexing.

Once the real corpus is available, report number of files processed, skipped/error counts, chunk count, min/median/max lengths, distribution by file type, number of forced character splits, total indexing time and memory. Check source invariants across the corpus. No recall score is known yet.

### Retrieval quality considerations (evaluation only, not retrieval implementation)

The subject matches a source when its exact file path matches and its interval IoU with a reference is at least 0.05. For half-open intervals, intersection is `max(0, min(end_a, end_b) - max(start_a, start_b))`; union is the sum of lengths minus intersection. A tiny chunk may be unable to reach the threshold even if entirely within a much longer reference. For example, a 50-character chunk fully inside a 1500-character reference has IoU about 0.033. Thus smaller chunks are not automatically better.

After the baseline passes correctness tests, compare the default 2000-character setting against smaller sizes and optional context-preservation changes, using the same retrieval method and datasets. The goal is both code recall >= 50% and docs recall >= 80% at k=5. Do not claim these targets are satisfied without actual measurements. Overlap can improve boundary recall but may also fill several of the five results with nearly identical evidence. Consider diversity and deduplication only when the retrieval stage is reached.

## 11. Proposed implementation order (review requested)

1. Fix the termination bug and validate size inputs. Add regression tests for oversized individual lines and absolute offsets.
2. Strengthen Python AST boundary correctness: decorators, parser failures, newline conventions, type safety; test all-source coverage.
3. Decide whether oversized Python candidates need child AST statement/method boundaries before line splitting. Keep the fallback available at every level and ensure every split makes progress.
4. Decide the minimum context-preservation design. Evaluate internal parent metadata and whether overlap/neighbor retrieval should be deferred until measured. Avoid changing the required source schema or source text.
5. Implement and test distinct Markdown/text boundary selection, reusing the generic packer as appropriate.
6. Connect both chunkers to the file-walking index prototype, construct `Chunk`/`MinimalSource` correctly, and test across the real corpus. Only then proceed to lexical indexing/retrieval.

The sequence above is a proposed roadmap, not an assertion that each change is required by the subject.

## 12. Questions for Claude's review

Please answer these in order, clearly separating verified bugs from optional enhancements and assumptions:

1. Does the reconstructed architecture satisfy the chunking portion of the subject in principle? What is currently missing for actual compliance?
2. Is the proposed single-line termination guard correct for the packer's stated contract? Is there another termination case we are missing?
3. Is it appropriate that `python_chunks()` identifies boundaries while `pack_ranges()` splits oversized ranges and combines small ones? Would you keep the reusable packer or separate the language-specific fallback policies?
4. Are the line offsets and full-coverage guarantees correct for normal LF Python content? What changes are needed for decorators, parser exceptions and newline normalization? What should be verified against the grader?
5. How should we preserve the relationship between chunks belonging to the same oversized function or class? Compare parent metadata, AST-aware splitting, overlap, neighboring chunks, and parent-child retrieval. Account for merged ranges that contain multiple nodes and the strict 2000-character returned-source limit.
6. Should we implement finer AST boundaries and context metadata now, or first finish a correct minimal baseline and measure recall? Explain why.
7. What is the simplest distinct Markdown/text strategy appropriate for the subject, and how can it share the packer without sacrificing important Markdown structure?
8. What tests are missing, and what is the **next small code change** we should make together? Show only that incremental change after explaining the review; do not replace the entire project.

Reference previously discussed: [Databricks — The Ultimate Guide to Chunking Strategies for RAG Applications](https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089). This was design inspiration, not a source of mandatory requirements; the subject is authoritative.

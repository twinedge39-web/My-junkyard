import random
import csv
from typing import List, Tuple, Optional, Set

N = 9
BOX = 3
DIGITS = set(range(1, 10))

def pattern(r: int, c: int) -> int:
    # Base pattern for a valid Sudoku solution
    return (BOX*(r % BOX) + r//BOX + c) % N

def shuffled(seq):
    seq = list(seq)
    random.shuffle(seq)
    return seq

def make_solution_grid(seed: Optional[int] = None) -> List[List[int]]:
    if seed is not None:
        random.seed(seed)

    r_base = range(BOX)
    rows  = [g*BOX + r for g in shuffled(r_base) for r in shuffled(r_base)]
    cols  = [g*BOX + c for g in shuffled(r_base) for c in shuffled(r_base)]
    nums  = shuffled(range(1, 10))

    grid = [[nums[pattern(r, c)] for c in cols] for r in rows]
    return grid

def candidates(grid: List[List[int]], r: int, c: int) -> Set[int]:
    if grid[r][c] != 0:
        return set()

    row = set(grid[r][x] for x in range(N)) - {0}
    col = set(grid[x][c] for x in range(N)) - {0}
    br = (r // BOX) * BOX
    bc = (c // BOX) * BOX
    box = set(grid[br+i][bc+j] for i in range(BOX) for j in range(BOX)) - {0}
    used = row | col | box
    return DIGITS - used

def grid_to_grid81(grid: List[List[int]]) -> str:
    return "".join(str(grid[r][c]) for r in range(N) for c in range(N))

def make_easy_drill(
    solution: List[List[int]],
    blanks: int = 10,
    require_singles_at_start: int = 5,
    max_tries: int = 2000
) -> List[List[int]]:
    """
    Create a drill puzzle from a solved grid:
    - remove 'blanks' cells
    - try to ensure at least 'require_singles_at_start' blanks are singles immediately
      (i.e., candidates size == 1).
    This is NOT a full unique-solution generator, but good for beginner drills.
    """
    grid = [row[:] for row in solution]
    cells = [(r, c) for r in range(N) for c in range(N)]
    random.shuffle(cells)

    removed = 0
    singles = 0
    tries = 0

    while removed < blanks and tries < max_tries and cells:
        tries += 1
        r, c = cells.pop()
        if grid[r][c] == 0:
            continue

        backup = grid[r][c]
        grid[r][c] = 0

        cand = candidates(grid, r, c)
        if len(cand) == 0:
            # broke consistency
            grid[r][c] = backup
            continue

        # count singles among removed cells
        if len(cand) == 1:
            singles += 1

        removed += 1

        # if we haven't achieved enough singles, bias by undoing non-singles sometimes
        if removed <= require_singles_at_start and singles < removed:
            # keep it beginner-friendly: prefer singles in the early removals
            if len(cand) != 1 and random.random() < 0.75:
                grid[r][c] = backup
                removed -= 1

    return grid

def export_drills_csv(
    out_path: str,
    count: int = 20,
    blanks: int = 10,
    require_singles_at_start: int = 5,
    seed: Optional[int] = 42
):
    if seed is not None:
        random.seed(seed)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","grid81","note"])

        for i in range(1, count+1):
            sol = make_solution_grid()
            puzzle = make_easy_drill(
                sol,
                blanks=blanks,
                require_singles_at_start=require_singles_at_start
            )
            w.writerow([f"DRILL{i:03d}", grid_to_grid81(puzzle),
                        f"blanks={blanks}, singles_at_start~{require_singles_at_start}"])

if __name__ == "__main__":
    export_drills_csv(
        out_path="drills.csv",
        count=30,
        blanks=12,
        require_singles_at_start=6,
        seed=123
    )
    print("Wrote drills.csv")

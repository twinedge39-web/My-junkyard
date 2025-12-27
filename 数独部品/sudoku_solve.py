from typing import List, Tuple

N = 9
BOX = 3
DIGITS = set(range(1, 10))

def parse_grid81(s: str) -> List[List[int]]:
    s = s.strip().replace(".", "0")
    if len(s) != 81 or any(ch not in "0123456789" for ch in s):
        raise ValueError("grid81 must be 81 chars of 0-9 (or .)")
    grid = [[int(s[r*9 + c]) for c in range(9)] for r in range(9)]
    return grid

def grid_to_grid81(grid: List[List[int]]) -> str:
    return "".join(str(grid[r][c]) for r in range(9) for c in range(9))

def candidates(grid: List[List[int]], r: int, c: int):
    if grid[r][c] != 0:
        return set()
    row = set(grid[r][x] for x in range(9)) - {0}
    col = set(grid[x][c] for x in range(9)) - {0}
    br = (r // BOX) * BOX
    bc = (c // BOX) * BOX
    box = set(grid[br+i][bc+j] for i in range(BOX) for j in range(BOX)) - {0}
    return DIGITS - (row | col | box)

def find_mrv_cell(grid: List[List[int]]) -> Tuple[int,int,set] | None:
    best = None
    best_cand = None
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                cand = candidates(grid, r, c)
                if len(cand) == 0:
                    return (-1, -1, set())  # contradiction marker
                if best is None or len(cand) < len(best_cand):
                    best = (r, c)
                    best_cand = cand
                    if len(best_cand) == 1:
                        return (r, c, best_cand)
    if best is None:
        return None
    return (best[0], best[1], best_cand)

def solve_count(grid: List[List[int]], limit: int = 2) -> List[List[List[int]]]:
    """
    Returns up to 'limit' solutions.
    If returns 0 solutions -> unsatisfiable.
    If returns 1 solution -> unique.
    If returns >=2 -> multiple solutions.
    """
    solutions: List[List[List[int]]] = []

    def dfs():
        if len(solutions) >= limit:
            return
        mrv = find_mrv_cell(grid)
        if mrv is None:
            # solved
            solutions.append([row[:] for row in grid])
            return
        r, c, cand = mrv
        if r == -1:
            return  # contradiction
        # try candidates (sorted for deterministic output)
        for v in sorted(cand):
            grid[r][c] = v
            dfs()
            grid[r][c] = 0
            if len(solutions) >= limit:
                return

    dfs()
    return solutions

def pretty(grid: List[List[int]]) -> str:
    lines = []
    for r in range(9):
        row = []
        for c in range(9):
            row.append(str(grid[r][c]) if grid[r][c] else ".")
        lines.append(" ".join(row))
    return "\n".join(lines)

if __name__ == "__main__":
    # 例：ここを書き換えて使う
    grid81 = (
        "002000008"
        "634090000"
        "000076200"
        "000000090"
        "800700000"
        "170080500"
        "000800003"
        "029000001"
        "410030000"
    )
    g = parse_grid81(grid81)

    print("INPUT grid81:", grid81)
    print("INPUT parsed:")
    print(pretty(g))

    sols = solve_count(g, limit=2)
    print(f"solutions_found={len(sols)}")
    print("given_count=", 81 - grid81.count("0"))
    for i, sol in enumerate(sols, start=1):
        print(f"\n--- solution #{i} ---")
        print(pretty(sol))
        print("grid81:", grid_to_grid81(sol))

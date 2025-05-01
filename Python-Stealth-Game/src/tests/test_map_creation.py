import random
import pytest
from Logic.map_creation import MapCreation, T_WALL, T_FLOOR, T_HIDDEN

@pytest.fixture(autouse=True)
def fixed_random_seed():
    """Seed the RNG for reproducible carve patterns."""
    random.seed(42)
    yield
    random.seed()

@pytest.mark.parametrize("rows,cols", [
    (1, 1),
    (2, 3),
    (4, 2),
])
def test_create_maze_map_dimensions_and_borders(rows, cols):
    """
    - Maze dimensions should be (2*rows+1)×(2*cols+1).
    - The outermosts border must remain all walls.
    - Each base‐grid cell (r,c) → maze[2r+1][2c+1] must be T_FLOOR.
    """
    mc = MapCreation(difficulty="hard", rows=rows, cols=cols, enemy_count=0)
    maze = mc.create_maze_map()
    R, C = 2*rows + 1, 2*cols + 1

    assert len(maze) == R
    assert all(len(row) == C for row in maze)

    for c in range(C):
        assert maze[0][c]   == T_WALL
        assert maze[R-1][c] == T_WALL
    for r in range(R):
        assert maze[r][0]   == T_WALL
        assert maze[r][C-1] == T_WALL

    for br in range(rows):
        for bc in range(cols):
            mr, mc0 = 2*br + 1, 2*bc + 1
            assert maze[mr][mc0] == T_FLOOR, f"Expected floor at {(mr,mc0)}"

def test_create_maze_map_all_floors_connected():
    """Ensure that every T_FLOOR tile is reachable from the first one via 4-way adjacency."""
    mc = MapCreation(difficulty="hard", rows=5, cols=5, enemy_count=0)
    maze = mc.create_maze_map()
    R, C = len(maze), len(maze[0])

    floors = {(r, c) for r in range(R) for c in range(C) if maze[r][c] == T_FLOOR}
    assert floors, "No floors carved!"

    start = next(iter(floors))
    visited = {start}
    queue = [start]
    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nbr = (r+dr, c+dc)
            if nbr in floors and nbr not in visited:
                visited.add(nbr)
                queue.append(nbr)

    assert visited == floors, "Maze has disconnected floor-regions"

@pytest.mark.parametrize("p, expected_center", [
    (0.0, T_WALL),
    (1.0, T_FLOOR),
])
def test_add_loops_to_maze_center_flip(p, expected_center):
    """
    In a 3×3 maze with only the center wall between two floors,
    add_loops_to_maze should flip that center to floor iff random()<p.
    """
    mc = MapCreation(difficulty="easy", rows=1, cols=1, enemy_count=0)

    maze = [
        [T_WALL,  T_WALL,  T_WALL],
        [T_FLOOR, T_WALL,  T_FLOOR],
        [T_WALL,  T_WALL,  T_WALL],
    ]

    out = mc.add_loops_to_maze([row[:] for row in maze], p=p)
    assert out[0] == [T_WALL, T_WALL, T_WALL]
    assert out[2] == [T_WALL, T_WALL, T_WALL]
    assert out[1][0] == T_FLOOR and out[1][2] == T_FLOOR
    assert out[1][1] == expected_center

@pytest.mark.parametrize("limit, expected_total", [
    (0, 0),
    (1, 4),
    (2, 4),
])
def test_distribute_hidden_rooms_marks_dead_ends(limit, expected_total):
    """
    distribute_hidden_rooms should:
      - Place up to `limit` hidden rooms *per quadrant*.
      - Only convert walls that in the original map had exactly one floor-neighbour.
    """
    mc = MapCreation(difficulty="hard", rows=1, cols=1, enemy_count=0)

    maze = [
        [T_WALL,  T_WALL,  T_WALL],
        [T_FLOOR, T_WALL,  T_FLOOR],
        [T_WALL,  T_WALL,  T_WALL],
    ]

    original = [row[:] for row in maze]
    out = mc.distribute_hidden_rooms([row[:] for row in maze], num_hidden_per_quadrant=limit)

    found = sum(1 for row in out for v in row if v == T_HIDDEN)
    assert found == expected_total

    offsets = [(-1,0),(1,0),(0,-1),(0,1)]
    R, C = len(original), len(original[0])
    for r in range(R):
        for c in range(C):
            if out[r][c] == T_HIDDEN:
                nbrs = 0
                for dr, dc in offsets:
                    rr, cc = r+dr, c+dc
                    if 0 <= rr < R and 0 <= cc < C and original[rr][cc] == T_FLOOR:
                        nbrs += 1
                assert nbrs == 1, f"Cell {(r,c)} was marked hidden but had {nbrs} floor neighbours"

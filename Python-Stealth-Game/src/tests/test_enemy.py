import math
import time
import pytest
from Logic.enemy import Enemy

@pytest.fixture
def matrix_3x3():
    return [[1,1,1],
            [1,1,1],
            [1,1,1]]

@pytest.fixture
def enemy(matrix_3x3):
    return Enemy(
        position=(15,25),
        patrol_route=[(0,0),(2,2)],
        matrix=matrix_3x3,
        grid_rows=3,
        grid_cols=3,
        tile_size=(10,10),
        move_speed=1.0,
        update_interval=1.0
    )

def test_get_position(enemy):
    assert enemy.get_position() == enemy.position

def test_grid_to_pixel(enemy):
    expected_x = 2 * enemy.PIXEL_ONE_X + enemy.PIXEL_ONE_X / 2
    expected_y = 1 * enemy.PIXEL_ONE_Y + enemy.PIXEL_ONE_Y / 2
    px, py = enemy.grid_to_pixel((2, 1))
    assert px == expected_x
    assert py == expected_y

@pytest.mark.parametrize("cell,exp", [
    ((0,0),(5,5)),
    ((1,0),(15,5)),
    ((0,2),(5,25)),
    ((3,4),(35,45)),
])
def test_grid_to_pixel_various(enemy, cell, exp):
    px, py = enemy.grid_to_pixel(cell)
    assert (px, py) == exp

@pytest.mark.parametrize("matrix, cell, expected", [
    ([[1]], (0, 0), True),
    ([[2]], (0, 0), True),
    ([[5]], (0, 0), True),
    ([[6]], (0, 0), True),
    ([[7]], (0, 0), True),
    ([[0]], (0, 0), False),
    ([[3]], (0, 0), False),
    ([[4]], (0, 0), False),
    ([[1]], (1, 0), False),
    ([[1]], (0, 1), False),
    ([[1]], (-1,0), False),
    ([[1]], (0,-1), False),
    ([[1,0],[4,5]], (1, 1), True),
    ([[1,0],[4,5]], (0, 1), False),
])
def test_is_walkable_with_various_matrices(matrix, cell, expected):
    rows = len(matrix)
    cols = len(matrix[0])
    e = Enemy(
        position=(0,0),
        patrol_route=[],
        matrix=matrix,
        grid_rows=rows,
        grid_cols=cols,
        tile_size=(10,10)
    )
    assert e.is_walkable(cell) is expected

@pytest.fixture
def small_enemy():
    mat = [[1]*3 for _ in range(3)]
    return Enemy(
        position=(0,0),
        patrol_route=[],
        matrix=mat,
        grid_rows=3,
        grid_cols=3,
        tile_size=(10,10)
    )

def test_check_collision_no_collision(small_enemy):
    assert not small_enemy.check_collision(5, 5)
    assert not small_enemy.check_collision((5, 5))

def test_check_collision_wall(small_enemy):
    small_enemy.matrix[1][1] = 0
    px = 1 * small_enemy.PIXEL_ONE_X + 1
    py = 1 * small_enemy.PIXEL_ONE_Y + 1
    assert small_enemy.check_collision(px, py)
    assert small_enemy.check_collision((px, py))

def test_check_collision_out_of_bounds(small_enemy):
    assert small_enemy.check_collision(-1, -1)
    assert small_enemy.check_collision(30, 5)
    assert small_enemy.check_collision((5, 30))

def test_get_neighbors_interior(enemy):
    nbrs = set(enemy.get_neighbors((1,1)))
    assert nbrs == {(2,1), (0,1), (1,2), (1,0)}

def validate_path(enemy, path, start, goal):
    if not path:
        return
    assert path[0] == start
    assert path[-1] == goal
    for a, b in zip(path, path[1:]):
        nbrs = enemy.get_neighbors(a)
        assert b in nbrs
        assert enemy.is_walkable(b)
    assert enemy.is_walkable(start)

def test_find_path_between_validity(enemy):
    start, goal = (0,0), (2,0)
    path = enemy.find_path_between(start, goal)
    validate_path(enemy, path, start, goal)

def test_move_patrol_area_empty_route(enemy):
    """No patrol route ⇒ no change to position or index."""
    orig_pos = enemy.position
    orig_idx = enemy.patrol_index
    enemy.complete_patrol_route = []
    enemy.move_patrol_area()
    assert enemy.position == orig_pos
    assert enemy.patrol_index == orig_idx

def test_move_patrol_area_index_wraps(enemy):
    """If patrol_index is ≥ len(route), it resets to 0 then moves one step toward the first cell."""
    enemy.complete_patrol_route = [(1,1), (2,2)]
    enemy.patrol_index = 5
    enemy.position = enemy.grid_to_pixel((0,0))
    enemy.patrol_speed = 100
    enemy.move_patrol_area()
    assert enemy.patrol_index == 1
    assert enemy.position == enemy.grid_to_pixel((1,0))

def test_move_patrol_area_partial_step(enemy):
    """When dist > patrol_speed, move partially and do not advance index."""
    enemy.complete_patrol_route = [(0,0), (0,1)]
    enemy.patrol_index = 1
    enemy.position = enemy.grid_to_pixel((0,0))
    enemy.patrol_speed = 5
    start_px = enemy.position
    next_px = enemy.grid_to_pixel((0,1))
    dx = next_px[0] - start_px[0]
    dy = next_px[1] - start_px[1]
    dist = math.hypot(dx, dy)
    enemy.move_patrol_area()
    expected_x = start_px[0] + dx / dist * 5
    expected_y = start_px[1] + dy / dist * 5
    assert math.isclose(enemy.position[0], expected_x, abs_tol=1e-6)
    assert math.isclose(enemy.position[1], expected_y, abs_tol=1e-6)
    assert enemy.patrol_index == 1

def test_move_patrol_area_exact_speed_no_index_advance(enemy):
    """When dist == patrol_speed, move to next cell but don’t advance index."""
    enemy.complete_patrol_route = [(0,0), (0,1)]
    enemy.patrol_index = 1
    enemy.position = enemy.grid_to_pixel((0,0))
    enemy.patrol_speed = 10
    next_px = enemy.grid_to_pixel((0,1))
    enemy.move_patrol_area()
    assert enemy.position == next_px
    assert enemy.patrol_index == 1

def test_move_patrol_area_unreachable_target(enemy):
    """If path is empty, fallback to target_cell and move directly."""
    enemy.complete_patrol_route = [(0,2)]
    enemy.patrol_index = 1
    enemy.position = enemy.grid_to_pixel((0,0))
    enemy.matrix = [[1,0,0],[0,0,0],[0,0,0]]
    enemy.patrol_speed = 100
    enemy.move_patrol_area()
    assert enemy.position == enemy.grid_to_pixel((0,2))
    assert enemy.patrol_index == 0

def test_move_patrol_area_full_step(enemy):
    enemy.complete_patrol_route = [(0,0),(0,1),(0,2),(1,2)]
    enemy.patrol_index = 0
    enemy.position = enemy.grid_to_pixel((1,2))
    enemy.patrol_speed = 20
    enemy.move_patrol_area()
    assert enemy.position == enemy.grid_to_pixel((0,2))
    assert enemy.patrol_index == 1

def test_find_nearest_walkable_starting_cell(enemy):
    """If already on walkable cell, return it."""
    start_cell = enemy.pixel_to_grid(enemy.position)
    assert enemy.is_walkable(start_cell)
    assert enemy.find_nearest_walkable() == start_cell

def test_find_nearest_walkable_one_step(enemy):
    """If blocked, return first orthogonal walkable neighbor."""
    start = enemy.pixel_to_grid(enemy.position)
    enemy.matrix[start[1]][start[0]] = 0
    nbrs = enemy.get_neighbors(start)
    expected = nbrs[0]
    assert enemy.is_walkable(expected)
    assert enemy.find_nearest_walkable() == expected

def test_find_nearest_walkable_none(enemy):
    """If all cells are blocked, return None."""
    enemy.matrix = [[0 for _ in range(enemy.GRID_COLS)] for _ in range(enemy.GRID_ROWS)]
    assert enemy.find_nearest_walkable() is None

@pytest.mark.parametrize("start,goal,expected", [
    ((0,0),(0,0), [(0,0)]),
    ((0,0),(2,0), [(0,0),(1,0),(2,0)]),
    ((0,0),(0,2), [(0,0),(0,1),(0,2)]),
])
def test_find_path_between_trivial(start, goal, expected, enemy):
    path = enemy.find_path_between(start, goal)
    assert path == expected

def test_find_path_between_diagonal(enemy):
    start, goal = (0,0), (1,1)
    path = enemy.find_path_between(start, goal)
    validate_path(enemy, path, start, goal)
    mdist = abs(start[0]-goal[0]) + abs(start[1]-goal[1])
    assert len(path) == mdist + 1

def test_find_path_between_blocked_start_or_goal(enemy):
    enemy.matrix[0][0] = 0
    assert enemy.find_path_between((0,0),(2,2)) == []
    enemy.matrix[0][0] = 1
    enemy.matrix[2][2] = 0
    assert enemy.find_path_between((0,0),(2,2)) == []

def test_find_path_between_unreachable(enemy):
    for r in range(enemy.GRID_ROWS):
        enemy.matrix[r][1] = 0
    assert enemy.find_path_between((0,0),(2,2)) == []

def test_los_trivial(enemy):
    """Same start and end should return just that point."""
    assert enemy.line_of_sight(1, 1, 1, 1) == [(1, 1)]

def test_los_straight(enemy):
    """Horizontal and vertical straight lines."""
    assert enemy.line_of_sight(0, 2, 3, 2) == [(0,2), (1,2), (2,2), (3,2)]
    assert enemy.line_of_sight(2, 0, 2, 3) == [(2,0), (2,1), (2,2), (2,3)]

def test_los_diagonal(enemy):
    """Perfect 45° diagonal."""
    assert enemy.line_of_sight(0, 0, 2, 2) == [(0,0), (1,1), (2,2)]

def test_los_mixed_slope(enemy):
    """Slope < 1 and > 1 cases in one go."""
    assert enemy.line_of_sight(0, 0, 3, 1) == [(0,0), (1,0), (2,1), (3,1)]
    assert enemy.line_of_sight(1, 0, 2, 3) == [(1,0), (1,1), (2,2), (2,3)]

@pytest.mark.parametrize(
    "enemy_cell, player_cell, blocked, expected",
    [
        ((1, 1), (1, 1), [], True),
        ((0, 1), (2, 1), [], True),
        ((0, 0), (2, 0), [(1, 0)], False),
    ]
)
def test_can_see_player(enemy, enemy_cell, player_cell, blocked, expected):
    enemy.position = enemy.grid_to_pixel(enemy_cell)
    for c, r in blocked:
        enemy.matrix[r][c] = 0
    player_pos = enemy.grid_to_pixel(player_cell)
    result = enemy.can_see_player(player_pos)
    assert result is expected

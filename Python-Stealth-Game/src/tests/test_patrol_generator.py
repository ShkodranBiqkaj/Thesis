import pytest
from Logic.patrol_generator import PatrolGenerator
from collections import Counter

@pytest.fixture
def generator():
    return PatrolGenerator(
        matrix=[[1]],
        grid_cols=1,
        grid_rows=1,
        tile_size=(10, 10),
        patrolling_area=(0, 0, 10, 10),
        enemies=[],
        difficulty_level=1,
        base_marker=5,
        palette=[(0,0,0,0)]
    )

def test_neighbors_center(generator):
    cell = (5, 5)
    nbrs = set(generator.get_cell_neighbors(cell))
    assert nbrs == {(6,5), (4,5), (5,6), (5,4)}

def test_neighbors_corner(generator):
    cell = (0, 0)
    nbrs = set(generator.get_cell_neighbors(cell))
    assert nbrs == {(1,0), (-1,0), (0,1), (0,-1)}

def test_bfs_path_trivial(generator):
    """When start == goal, should return the single-cell path."""
    region = {(0, 0)}
    assert generator.find_bfs_path((0, 0), (0, 0), region) == [(0, 0)]

def test_bfs_path_simple_route(generator):
    """In a small L-shaped region, ensure we get a valid shortest path."""
    region = {(0,0), (1,0), (1,1)}
    start, goal = (0,0), (1,1)
    path = generator.find_bfs_path(start, goal, region)
    assert path == [(0,0), (1,0), (1,1)]

def test_bfs_path_unreachable(generator):
    """If goal is not in region or no connecting route, should return an empty list."""
    region = {(0,0), (1,0), (0,1)}
    assert generator.find_bfs_path((0,0), (1,1), region) == []

def test_bfs_path_blocked(generator):
    """Even if goal is in region, if walls block connectivity, return empty."""
    region = {(0,0), (1,1)}
    assert generator.find_bfs_path((0,0), (1,1), region) == []

@pytest.mark.parametrize("region, start, expected", [
    ({(0,0)}, (0,0), [(0,0)]),
    ({(0,0),(1,0)}, (0,0), [(0,0),(1,0),(0,0)]),
    ({(0,0),(1,0),(1,1)}, (0,0), [(0,0),(1,0),(1,1),(1,0),(0,0)]),
])
def test_dfs_euler_basic(generator, region, start, expected):
    route = generator.dfs_euler(start, region)
    assert route == expected

def test_dfs_euler_full_cover(generator):
    region = {(0,0),(1,0),(0,1),(1,1)}
    start = (0,0)
    route = generator.dfs_euler(start, region)
    for cell in region:
        assert cell in route
    assert route[0] == start
    assert route[-1] == start

@pytest.mark.parametrize("route, expected", [
    ([], []),
    ([(0,0)], [(0,0)]),
    ([(1,1), (1,1), (1,1)], [(1,1)]),
    ([(0,0), (1,0), (0,0)], [(0,0), (0,0)]),
    ([(0,0),(1,0),(2,0),(1,0),(0,0)], [(0,0),(1,0),(1,0),(0,0)]),
    ([(0,0),(1,0),(2,0),(1,0),(0,0)], [(0,0),(1,0),(1,0),(0,0)])
])
def test_optimize_various(generator, route, expected):
    """Ensure that optimize_route collapses duplicates and removes all X→Y→X patterns."""
    result = generator.optimize_route(route)
    assert result == expected

@pytest.fixture
def small_generator():
    matrix = [
        [0, 1, 0],
        [1, 1, 1],
        [0, 1, 0],
    ]
    return PatrolGenerator(
        matrix=matrix,
        grid_cols=3,
        grid_rows=3,
        tile_size=(10, 10),
        patrolling_area=(0, 0, 30, 30),
        enemies=[],
        difficulty_level=1,
        base_marker=5,
        palette=[(0,0,0,0)]
    )

def test_extract_full_area(small_generator):
    """With patrolling_area covering the entire map, region should include only those cells whose matrix value is in FLOORS (1)."""
    expected = {(1,0), (0,1), (1,1), (2,1), (1,2)}
    region = small_generator.extract_region()
    assert region == expected

@pytest.fixture
def partial_generator():
    matrix = [[1]*3 for _ in range(3)]
    return PatrolGenerator(
        matrix=matrix,
        grid_cols=3,
        grid_rows=3,
        tile_size=(10, 10),
        patrolling_area=(0, 0, 20, 20),
        enemies=[],
        difficulty_level=1,
        base_marker=5,
        palette=[(0,0,0,0)]
    )

def test_extract_partial_area(partial_generator):
    """patrolling_area=(0,0,20,20) should include cells with c in [0,1], r in [0,1]."""
    expected = {(0,0), (1,0), (0,1), (1,1)}
    region = partial_generator.extract_region()
    assert region == expected

@pytest.fixture
def out_of_bounds_generator():
    matrix = [[1,1],[1,1]]
    return PatrolGenerator(
        matrix=matrix,
        grid_cols=2,
        grid_rows=2,
        tile_size=(10, 10),
        patrolling_area=(-10, -10, 15, 15),
        enemies=[],
        difficulty_level=1,
        base_marker=5,
        palette=[(0,0,0,0)]
    )

def test_extract_with_out_of_bounds(out_of_bounds_generator):
    """Negative start and end beyond grid should be clamped to valid cells. patrolling_area=(-10,-10,15,15) => c0=-1,c1=1 yields only cell (0,0)"""
    expected = {(0,0)}
    region = out_of_bounds_generator.extract_region()
    assert region == expected

#choose_starts

@pytest.fixture
def test_region():
    return {(x, y) for x in range(5) for y in range(5)}

def test_choose_starts_count_and_uniqueness(generator, test_region):
    starts = generator.choose_starts(test_region, 3)
    assert len(starts) == 3
    assert all(s in test_region for s in starts)
    assert len(set(starts)) == len(starts)  # no duplicates

def test_partition_total_coverage(generator, test_region):
    starts = generator.choose_starts(test_region, 3)
    parts = generator.partition(test_region, starts)

    all_cells = set().union(*parts)
    assert all_cells == test_region, "Partition missed or added cells"

def test_partition_disjoint(generator, test_region):
    starts = generator.choose_starts(test_region, 3)
    parts = generator.partition(test_region, starts)

    cell_counts = Counter(cell for part in parts for cell in part)
    for cell, count in cell_counts.items():
        assert count == 1, f"Cell {cell} appears in multiple partitions"

def test_partition_starts_included(generator, test_region):
    starts = generator.choose_starts(test_region, 3)
    parts = generator.partition(test_region, starts)

    for i, start in enumerate(starts):
        assert start in parts[i], f"Start {start} not found in its own partition"
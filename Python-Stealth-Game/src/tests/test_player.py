import pytest
import pygame
from Logic.player import Player
from Logic.map_creation import T_WALL, T_FLOOR, T_KEY, T_DOOR_C, T_DOOR_O, T_HIDDEN

@pytest.fixture
def simple_matrix():
    return [[T_FLOOR]*4 for _ in range(4)]

@pytest.fixture
def player(simple_matrix):
    return Player(
        player_pos_x=15,
        player_pos_y=25,
        matrix=[row[:] for row in simple_matrix],
        PIXEL_ONE_X=10,
        PIXEL_ONE_Y=10
    )

def test_get_position_returns_current_coords(player):
    """get_position() should always return the tuple (pos_X, pos_Y)."""
    assert player.get_position() == (player.pos_X, player.pos_Y) == (15, 25)
    player.pos_X = 99
    player.pos_Y = 42
    assert player.get_position() == (99, 42)

@pytest.mark.parametrize("door_pos, expected", [
    ((2, 1), True),
    ((1, 1), True),
    ((2, 2), True),
    ((3, 2), False),
    ((2, 3), False),
])
def test_near_door_manhattan(player, door_pos, expected):
    """near_door returns True iff the manhattan distance to door_pos ≤ 1."""
    assert player.near_door(door_pos) is expected

@pytest.mark.parametrize("pixel, expected_cell", [
    ((5.0,   5.0),   (0, 0)),
    ((9.999, 9.999), (0, 0)),
    ((10.0,  4.0),   (1, 0)),
    (( 4.0, 10.0),   (0, 1)),
    ((25.0, 25.0),   (2, 2)),
    ((-0.1, -0.1),   (-1, -1)),
    ((30.0, 15.0),   (3, 1)),
])
def test_player_pixel_to_grid_various(player, pixel, expected_cell):
    """pixel_to_grid should floor-divide by tile size; out-of-bounds pixels produce -1."""
    assert player.pixel_to_grid(pixel) == expected_cell

def test_check_collision(player):
    assert not player.check_collision(5, 5)
    player.matrix[1][1] = T_WALL
    assert player.check_collision(10, 10)
    assert player.check_collision(-1, 5)
    assert player.check_collision(30, 5)

@pytest.fixture
def roomy_player():
    """Create a 10×10 open map and place player centered at (5,5)."""
    matrix = [[T_FLOOR] * 10 for _ in range(10)]
    return Player(player_pos_x=50, player_pos_y=50,
                  matrix=matrix,
                  PIXEL_ONE_X=10, PIXEL_ONE_Y=10)

def simulate_key(monkeypatch, key):
    def get_pressed():
        keys = [False] * 512
        keys[key] = True
        return keys
    monkeypatch.setattr(pygame.key, 'get_pressed', get_pressed)

@pytest.mark.parametrize("key, attr, sign", [
    (pygame.K_w, 'pos_Y', -1),
    (pygame.K_s, 'pos_Y',  1),
    (pygame.K_a, 'pos_X', -1),
    (pygame.K_d, 'pos_X',  1),
])
def test_move_directions(monkeypatch, roomy_player, key, attr, sign):
    """Test movement in all four directions via parametrize."""
    initial = getattr(roomy_player, attr)
    simulate_key(monkeypatch, key)
    roomy_player.move()
    updated = getattr(roomy_player, attr)
    if sign < 0:
        assert updated < initial
    else:
        assert updated > initial

def test_key_pickup(monkeypatch, roomy_player):
    """Moving onto a key tile should set has_key and clear the tile."""
    roomy_player.speed = roomy_player.PIXEL_ONE_X
    col, row = roomy_player.pixel_to_grid((50,50))
    roomy_player.matrix[row][col+1] = T_KEY
    simulate_key(monkeypatch, pygame.K_d)
    roomy_player.move()
    assert roomy_player.has_key
    assert roomy_player.matrix[row][col+1] == T_FLOOR

def test_closed_door_block(monkeypatch, roomy_player):
    """Moving onto a closed door without a key should rollback to start."""
    col, row = roomy_player.pixel_to_grid((50,50))
    roomy_player.matrix[row][col-1] = T_DOOR_C
    initial = (roomy_player.pos_X, roomy_player.pos_Y)
    simulate_key(monkeypatch, pygame.K_a)
    roomy_player.move()
    assert (roomy_player.pos_X, roomy_player.pos_Y) == initial

def test_open_door_win(monkeypatch, roomy_player):
    """Moving onto an open door should set win=True."""
    roomy_player.speed = roomy_player.PIXEL_ONE_X
    col, row = roomy_player.pixel_to_grid((50,50))
    roomy_player.matrix[row+1][col] = T_DOOR_O
    simulate_key(monkeypatch, pygame.K_s)
    roomy_player.move()
    assert roomy_player.win
import pytest
from Logic.logic_setup import LogicSetup
from Logic.player import Player
from Logic.enemy import Enemy
from Logic.map_creation import T_FLOOR, T_KEY, T_DOOR_C, T_DOOR_O

PIX = 10

def setup_logic_with_manual_map(matrix, key_pos, door_pos, enemies=None):
    logic = LogicSetup('easy', rows=0, cols=0, enemy_count=0)
    logic.matrix = [row[:] for row in matrix]
    logic.GRID_ROWS = len(matrix)
    logic.GRID_COLS = len(matrix[0])
    logic.PIXEL_ONE_X = logic.PIXEL_ONE_Y = PIX
    logic.key_pos = key_pos
    logic.door_pos = door_pos
    logic.enemies = enemies or []
    return logic


def test_pickup_key_only_affects_key_tile():
    matrix = [
        [T_KEY, T_FLOOR],
        [T_FLOOR, T_KEY]
    ]
    logic = setup_logic_with_manual_map(matrix, key_pos=(0, 0), door_pos=(1, 0))
    logic.player = Player(PIX/2, PIX/2, logic.matrix, PIX, PIX)
    logic.player.has_key = False

    result = logic.update()
    assert logic.player.has_key is True
    assert logic.matrix[0][0] == T_FLOOR
    assert logic.matrix[1][1] == T_KEY
    assert result == {'won': False, 'lost': False}


def test_no_open_door_when_adjacent_without_stepping():
    matrix = [[T_FLOOR, T_FLOOR, T_DOOR_C]]
    logic = setup_logic_with_manual_map(matrix, key_pos=(0, 0), door_pos=(2, 0))
    logic.player = Player(PIX/2, PIX/2, logic.matrix, PIX, PIX)
    logic.player.has_key = True

    logic.player.x = 1*PIX + PIX/2
    logic.player.y = PIX/2
    res = logic.update()
    assert logic.matrix[0][2] == T_DOOR_C
    assert res == {'won': False, 'lost': False}


def test_loss_on_collision():
    matrix = [[T_FLOOR]]
    enemy = Enemy(position=(PIX/2, PIX/2), patrol_route=[(0, 0)], matrix=matrix,
                  grid_rows=1, grid_cols=1, tile_size=(PIX, PIX), move_speed=1, update_interval=1)
    logic = setup_logic_with_manual_map(matrix, key_pos=(0, 0), door_pos=(0, 0), enemies=[enemy])
    logic.player = Player(PIX/2, PIX/2, logic.matrix, PIX, PIX)

    res = logic.update()
    assert res['lost'] is True and res['won'] is False
    assert logic.player.game_over


def test_no_win_without_key_on_door():
    matrix = [[T_DOOR_C]]
    logic = setup_logic_with_manual_map(matrix, key_pos=(0, 0), door_pos=(0, 0))
    logic.player = Player(PIX/2, PIX/2, logic.matrix, PIX, PIX)
    logic.player.has_key = False

    res = logic.update()
    assert res == {'won': False, 'lost': False}
    assert logic.matrix[0][0] == T_DOOR_C

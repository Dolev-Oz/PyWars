import random

import common_types

def get_sorted_tiles_for_attack(strategic):
    unclaimed_tiles = []
    enemy_tiles = []
    for x in range(strategic.get_game_width()):
        for y in range(strategic.get_game_height()):
            coordinate = common_types.Coordinates(x, y)
            danger = strategic.estimate_tile_danger(coordinate)
            if danger == 1:
                unclaimed_tiles.append(coordinate)
            elif danger == 2:
                enemy_tiles.append(coordinate)

    random.shuffle(unclaimed_tiles)
    random.shuffle(enemy_tiles)
    return enemy_tiles + unclaimed_tiles


def do_turn(strategic):
    tiles_for_attack = get_sorted_tiles_for_attack(strategic)
    if len(tiles_for_attack) == 0:
        return
    attacking_pieces = strategic.report_attacking_pieces()
    tile_index = 0
    for piece, command_id in attacking_pieces.items():
        if command_id is not None:
            continue
        strategic.attack(piece, tiles_for_attack[tile_index], 1)
        tile_index += 1
        if tile_index >= len(tiles_for_attack):
            break

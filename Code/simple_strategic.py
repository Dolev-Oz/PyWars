import random
import strategic_api as strat
from strategic_api import StrategicApi, StrategicPiece, CommandStatus, piece_to_price

import common_types

COMMANDS = {}
PIECES_TO_PROB_PREC = {"tank": 50, "builder": 50}


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


def find_min_dist_to_pieces(
    pieces: set[strat.StrategicPiece],
    coord: common_types.Coordinates,
    context: StrategicApi,
):
    min_dist = 10000
    con = context.context
    for piece in pieces:
        dis = common_types.distance(con.my_pieces[piece.id].tile.coordinates, coord)
        if dis < min_dist:
            min_dist = dis
    return dis


def sort_tiles(
    attack_tiles: list[common_types.Coordinates],
    pieces: set[StrategicPiece],
    context: StrategicApi,
):
    attack_tiles.sort(key=lambda tile: find_min_dist_to_pieces(pieces, tile, context))


def choose_piece_for_tile(
    pieces: set[StrategicPiece], coord: common_types.Coordinate, strategic: StrategicApi
):
    if len(pieces) == 0:
        return None
    con = strategic.context.my_pieces
    min_dist = 10000
    ret_piece = None
    for piece in pieces:
        dist = common_types.distance(con[piece.id].tile.coordinates, coord)
        if dist < min_dist:
            min_dist = dist
            ret_piece = piece
    pieces.remove(ret_piece)
    return ret_piece


def builder_decision(
    strategic: StrategicApi, builder: StrategicPiece, command_id: str, money: int
):
    if command_id is not None:
        return

    random.choices([0], weights=[10, 1, 1], k=14)

    if money < piece_to_price:
        pass
    strategic.collect_money()


def do_builder_stuff(strategic: StrategicApi):
    pass
    # builders = strategic.report_builders()
    # for builder, info in builders.items():
    #    builder_decision(strategic, builder, info[0], info[1])


def do_attack_stuff(strategic: StrategicApi):
    tiles_for_attack = get_sorted_tiles_for_attack(strategic)
    if len(tiles_for_attack) == 0:
        return
    attacking_pieces = strategic.report_attacking_pieces()
    available_pieces: set[StrategicPiece] = set()
    for piece, command_id in attacking_pieces.items():
        if command_id is None:
            available_pieces.add(piece)

    sort_tiles(tiles_for_attack, available_pieces, strategic)
    for tile in tiles_for_attack:
        piece = choose_piece_for_tile(available_pieces, tile, strategic)
        if piece is None:
            break
        strategic.attack(piece, tile, 1)

    """tile_index = 0
    for piece, command_id in attacking_pieces.items():
        if command_id is not None:
            continue
        strategic.attack(piece, tiles_for_attack[tile_index], 1)
        tile_index += 1
        if tile_index >= len(tiles_for_attack):
            break"""


def do_turn(strategic: StrategicApi):
    do_builder_stuff(strategic)
    do_attack_stuff(strategic)
    pass

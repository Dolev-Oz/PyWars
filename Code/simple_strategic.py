import random
import strategic_api as strat
from strategic_api import StrategicApi, StrategicPiece

from common_types import Coordinates, distance

piece_to_price = {"tank": 8, "builder": 20}

COMMANDS = {}
PIECES = ["tank", "builder"]
PROBS = [50, 50]
TO_BUILD = {}  # builder object is mapped to str
DEF_RADIUS = 2


def get_sorted_tiles_for_attack(strategic):
    unclaimed_tiles = []
    enemy_tiles = []
    for x in range(strategic.get_game_width()):
        for y in range(strategic.get_game_height()):
            coordinate = Coordinates(x, y)
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
    coord: Coordinates,
    context: StrategicApi,
):
    min_dist = 10000
    con = context.context
    for piece in pieces:
        dis = distance(con.my_pieces[piece.id].tile.coordinates, coord)
        if dis < min_dist:
            min_dist = dis
    return min_dist


def sort_tiles(
    attack_tiles: list[Coordinates],
    pieces: set[StrategicPiece],
    context: StrategicApi,
):
    attack_tiles.sort(key=lambda tile: find_min_dist_to_pieces(pieces, tile, context))


def assign_piece_to_close_tile(
    tank: StrategicApi,
):
    pass


def choose_piece_for_tile(
    pieces: set[StrategicPiece], coord: Coordinates, strategic: StrategicApi
):
    if len(pieces) == 0:
        return None
    con = strategic.context.my_pieces
    min_dist = 10000
    ret_piece = None
    for piece in pieces:
        dist = distance(con[piece.id].tile.coordinates, coord)
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
    if builder not in TO_BUILD:
        TO_BUILD[builder] = random.choices(PIECES, weights=PROBS, k=1)[0]

    if money < piece_to_price[TO_BUILD[builder]]:
        strategic.collect_money(builder, piece_to_price[TO_BUILD[builder]])
    else:
        strategic.build_piece(TO_BUILD[builder])
        del TO_BUILD[builder]


def do_builder_stuff(strategic: StrategicApi):
    builders = strategic.report_builders()
    strategic.log(builders.__str__())
    strategic.log(TO_BUILD.__str__())
    for builder, info in builders.items():
        builder_decision(strategic, builder, info[0], info[1])


def find_near_tank(
    strategic: StrategicApi,
    tank_set: set[StrategicPiece],
    art: StrategicPiece,
    rad: int,
):
    min_dist = 100000
    close_tank = None
    my_pcs = strategic.context.my_pieces
    for tank in tank_set:
        dis = distance(
            my_pcs[tank.id].tile.coordinates, my_pcs[art.id].tile.coordinates
        )
        if dis < min_dist:
            min_dist = dis
            close_tank = tank
    return close_tank


def do_attack_stuff(strategic: StrategicApi):
    tiles_for_attack = get_sorted_tiles_for_attack(strategic)
    if len(tiles_for_attack) == 0:
        return
    attacking_pieces = strategic.report_attacking_pieces()
    available_pieces: set[StrategicPiece] = set()
    available_tanks: set[StrategicPiece] = set()
    available_art: set[StrategicPiece] = set()
    for piece, command_id in attacking_pieces.items():
        if command_id is None:
            available_pieces.add(piece)
            if piece.type == "tank":
                available_tanks.add(piece)
            elif piece.type == "artillery":
                available_art.add(piece)
    sort_tiles(tiles_for_attack, available_tanks, strategic)
    # strategic.log(f"Reached 110, len(availabe_tiles)={len(tiles_for_attack)}")
    for tile in tiles_for_attack:
        piece = choose_piece_for_tile(available_tanks, tile, strategic)
        if piece is None:
            break
        logger = strategic.attack(piece, tile, 1)
        strategic.log(f"Attack: {logger}")
    for art in available_art:
        tank = find_near_tank(strategic, available_tanks, art, DEF_RADIUS)
        logger = strategic.defend(
            [art], strategic.context.my_pieces[tank.id].tile.coordinates, DEF_RADIUS
        )
        strategic.log(f"Defend: {logger}")
    """tile_index = 0
    for piece, command_id in attacking_pieces.items():
        if command_id is not None:
            continue
        strategic.attack(piece, tiles_for_attack[tile_index], 1)
        tile_index += 1
        if tile_index >= len(tiles_for_attack):
            break"""


def do_turn(strategic: StrategicApi):
    strategic.log("hello world")
    #    do_builder_stuff(strategic)
    do_attack_stuff(strategic)

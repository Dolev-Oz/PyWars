import math
import random
import strategic_api as strat
from strategic_api import StrategicApi, StrategicPiece

from common_types import Coordinates, distance
import common_types

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
    next_to_min = min_dist
    con = context.context
    for piece in pieces:
        dis = distance(con.my_pieces[piece.id].tile.coordinates, coord)
        if dis < min_dist:
            next_to_min = min_dist
            min_dist = dis
    return (min_dist + next_to_min) / 2


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
        return []
    con = strategic.context.my_pieces
    min_dist = 10000
    ret_pieces = []
    for piece in pieces:
        dist = distance(con[piece.id].tile.coordinates, coord)
        if dist < min_dist:
            min_dist = dist
    for piece in pieces:
        if distance(con[piece.id].tile.coordinates, coord) == min_dist:
            ret_pieces.append(piece)
            # strategic.context.log("added piece")
            if len(ret_pieces) == 2:
                break
    for piece in ret_pieces:
        pieces.remove(piece)
    return ret_pieces


def builder_decision(
    strategic: StrategicApi, builder: StrategicPiece, command_id: str, money: int
):
    if command_id is not None:
        return

    strategic.build_piece(builder, random.choices(PIECES, weights=PROBS, k=1)[0])


def do_builder_stuff(strategic: StrategicApi):
    builders = strategic.report_builders()
    for builder, info in builders.items():
        builder_decision(strategic, builder, info[0], info[1])


def choose_random_dest(strategic: StrategicApi, tank: StrategicPiece):
    tank_cord = strategic.context.my_pieces[tank.id].tile.coordinates
    tank_x = tank_cord.x
    tank_y = tank_cord.y
    theta = random.random() * math.pi / 2 - math.pi / 4
    w = strategic.context.game_width
    h = strategic.context.game_height
    r = math.sqrt((tank_x - w / 2) ** 2 + (tank_y - h / 2) ** 2)
    cos_t = (tank_y - h / 2) / r
    sin_t = (tank_x - w / 2) / r
    try:
        thet = math.atan(sin_t / cos_t)
    except Exception:
        thet = math.pi / 2
    if cos_t >= 0:
        thet = math.pi / 2 - thet
    elif cos_t <= 0:
        thet = 3 * math.pi / 2 - thet
    theta += thet
    strategic.context.log(f"theta={theta*180/math.pi} degree")
    if theta != math.pi / 2 and theta != 3 * math.pi / 2:
        if (
            tank_x - tank_y * math.tan(theta) >= 0
            and tank_x - tank_y * math.tan(theta) <= strategic.context.game_width
        ):
            strategic.log("Theta is normal, x in bounds")
            return (
                int(tank_x - tank_y * math.tan(theta)),
                0 if abs(theta) <= math.pi / 2 else strategic.context.game_height - 1,
            )
        strategic.log("Theta is normal, y in bounds")
        return (
            0 if theta <= math.pi else strategic.context.game_width - 1,
            int(tank_y - tank_x / math.tan(theta)),
        )

    strategic.log("Theta not normal")
    if theta == math.pi / 2:
        return (0, tank_y)
    return (strategic.context.game_width - 1, tank_y)


DEST_FOR_TANK: dict[str, Coordinates] = {}


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
    """for tank in available_tanks:
        coords = choose_random_dest(strategic, tank)
        strategic.attack(
            tank,
            Coordinates(coords[0], coords[1]),
            int(strategic.context.game_height / 3),
        )
        strategic.context.log(f"(x,y)=({coords[0]},{coords[1]})")
        DEST_FOR_TANK[tank.id] = Coordinates(coords[0], coords[1])"""
    for tile in tiles_for_attack:
        pieces = choose_piece_for_tile(available_tanks, tile, strategic)
        if pieces == []:
            continue
        if pieces is None:
            strategic.context.log("IS NONE")
            continue
        for piece in pieces:
            logger = strategic.attack(piece, tile, 0)
            DEST_FOR_TANK[piece.id] = tile
            strategic.log(f"Attack: {logger}")
    for art in available_art:  # Not supposed to run 0 available_art is empty
        tank = find_near_tank(strategic, available_tanks, art, DEF_RADIUS)
        if tank.id in DEST_FOR_TANK:
            logger = strategic.defend([art], DEST_FOR_TANK[tank.id], DEF_RADIUS)
        else:
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
    try:
        do_builder_stuff(strategic)
    except Exception:
        raise Exception("builder Exception")
    try:
        do_attack_stuff(strategic)
        pass
    except Exception:
        raise Exception("attack exception")

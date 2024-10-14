from collections import namedtuple
from strategic_api import StrategicApi, StrategicPiece, CommandStatus
from tactical_api import TurnContext, BasePiece, Builder, Tank, Tile, TYPE_TO_CLASS, Artillery
from common_types import Coordinates, distance


from typing import List, cast, Dict, Union, Set


# maps between tank id to the coordinate its attacking
tank_to_attacked_coordinate = {}

tank_to_attacking_command = {}

builder_chosen_tiles : Set[Tile] = set()

piece_statuses: Dict[str, int] = {}

# TODO make a type to attack range map

# Inverted TYPE_TO_CLASS
CLASS_TO_TYPE: Dict[type, str] = {_value: _key for _key, _value in TYPE_TO_CLASS.items()}

TYPE_TO_COST: Dict[str, int]= {
    "tank": 8,
    "artillery": 8,
    "airplane": 20,
    "helicopter": 16,
    "antitank": 10,
    "irondome": 32,
    "bunker": 10,
    "spy": 20,
    "builder": 20
}

TYPE_TO_WALK_DIST = {
    'tank': 1,
    'airplane': 8,
    'artillery': 1,
    'helicopter': 5,
    'antitank': 1,
    'irondome': 1,
    'spy': 1,
    'bunker': 1,
    'builder': 1,
}

TYPE_TO_ATTACK_RANGE_DICT = {
    'tank': 0,
    'artillery': 3
}


class Statuses:
    attacking = 0
    defending = 1
    building = 2
    none = -1

class Response:
    success = 0
    in_progress = 1
    faliure = 2

"""
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
"""

class MyStrategicApi(StrategicApi):

    def __init__(self, *args, **kwargs):
        super(MyStrategicApi, self).__init__(*args, **kwargs)
        global builder_chosen_tiles, piece_statuses, CLASS_TO_TYPE
        self.context: TurnContext

        builder_chosen_tiles = set()
        # Initializing pieces that aren't on the list
        for piece_id, piece in self.context.my_pieces.items():
            
            if piece_id not in piece_statuses.keys():
                # Initialises status to none
                # the strategic api uses the StrategeicPiece class, so they have to use this.
                self.log(f"BUILDER WITH ID {piece_id} IS BEING INITED TO NONE")
                piece_statuses[piece_id] = Statuses.none
            
        to_remove = []
        # Iterating strategic pieces
        for piece_id in piece_statuses.keys():
            if piece_id not in self.context.my_pieces.keys():
                to_remove.append(piece_id)
            
        for remove_id in to_remove:
            piece_statuses.pop(remove_id)
        
            

    def attack(self, pieces : List[StrategicPiece], destination : Coordinates, radius : int) -> int:
        assert isinstance(destination, Coordinates)
        attacking_piece_id: str = pieces[0].id
        attacking_piece_type: str = pieces[0].type


        # self.context.log(f"Using TANK with id {attacking_piece_id} to attack {destination}")

        # Tell the globals that these pieces attack
        

        attacking_piece: Union[BasePiece, Tank, Artillery] = self.context.my_pieces[attacking_piece_id]

        piece_tile: Tile = attacking_piece.tile

        if distance(piece_tile.coordinates, destination) > radius:
            self.context.log(f"ATTACKING PIECE WITH ID {attacking_piece_id} IS OUT OF RANGE")
            return Response.faliure
            

        if attacking_piece_type not in ("tank", "artillery"):
            self.context.log("ATTACKING PIECE GIVEN WAS NOT TANK OR ARTILLERY")
            return Response.faliure

        # If the piece isn't on the target square, then go there, and only then attack
        if distance(piece_tile.coordinates, destination) > TYPE_TO_ATTACK_RANGE_DICT[attacking_piece_type]:
            self.context.log(f"{attacking_piece_type.upper()} with id {attacking_piece_id} is MOBILIZING")
            # Updating the piece status to attacking
            piece_statuses[attacking_piece_id] = Statuses.attacking
            self.move_piece(attacking_piece, destination)
            return Response.in_progress
        
        else:
            # DO THE ATTACK
            if attacking_piece_type == 'tank':
                attacking_piece = cast(Tank, attacking_piece)
                self.context.log(f"TANK with id {attacking_piece_id} has ATTACKED")
                # Updating the piece status to none, done!
                piece_statuses[attacking_piece_id] = Statuses.none
                attacking_piece.attack()

                return Response.success
            elif attacking_piece_type == 'artillery':
                attacking_piece = cast(Artillery, attacking_piece)
                self.context.log(f"ARTILLERY with id {attacking_piece_id} has ATTACKED")
                # Updating the piece status to none, done!
                piece_statuses[attacking_piece_id] = Statuses.none
                attacking_piece.attack(destination)
                return Response.success
        return Response.success
    
    def estimate_attack_time(self, pieces: List[StrategicPiece], destination: Coordinates, radius: int) -> int:
        assert len(pieces) == 1
        piece = pieces[0]
        my_coords = self.context.my_pieces[piece.id].tile.coordinates
        # self.log(f"estimating attack time for piece {piece} from {my_coords} to {destination}")
        dist = distance(my_coords, destination)
        turns = dist / TYPE_TO_WALK_DIST[piece.type]
        return turns+1
    
    
    # The type is one the piece types from tactical_api
    def build_piece(self, builder: StrategicPiece, piece_type: str) -> int:
        cost = TYPE_TO_COST[piece_type]
        builder_obj: Builder = cast(Builder, self.context.my_pieces[builder.id])
        self.log(f"BUILD PIECE HAS BEEN CALLED, BUILDING {piece_type.upper()}")
        
        if builder_obj.money < cost:
            self.log(f"BUILDER with id {builder_obj.id} cant afford {piece_type.upper()}, STARTING TO COLLECT")    
            self.collect_money(StrategicPiece(builder_obj.id, "builder"), cost)
            piece_statuses[builder_obj.id] = Statuses.building
            return Response.in_progress
        else:
            self.log(f"BUILDER with id {builder_obj.id} managed to build {piece_type.upper()}")
            piece_statuses[builder_obj.id] = Statuses.none
            builder_obj._build(piece_type)
            return Response.success



    def get_game_height(self):
        return self.context.game_width

    def get_game_width(self):
        return self.context.game_width

    def estimate_tile_danger(self, destination):
        tile = self.context.tiles[(destination.x, destination.y)]
        if tile.country == self.context.my_country:
            return 0
        elif tile.country is None:
            return 1
        else:   # Enemy country
            return 2
        
    def defend(self, pieces: List[StrategicPiece], destination: Coordinates, radius: int):
        """
        JUST MOVES THE SINGLETON PIECE TO DESTINATION
        """
        defending_strat_piece = pieces[0]
        defending_piece = self.context.my_pieces[defending_strat_piece.id]

        if distance(defending_piece.tile.coordinates, destination) > radius:
            self.move_piece(defending_piece, destination)
            self.log(f"{defending_piece.type.upper()} with id {defending_piece.id} IS MOVING TO DEFEND")
            piece_statuses[defending_strat_piece.id] = Statuses.defending
            return Response.in_progress
        else:
            self.log(f"{defending_piece.type.upper()} with id {defending_piece.id} IS IN PLACE")
            piece_statuses[defending_piece.id] = Statuses.none
            return Response.success


    def report_defending_pieces(self) -> Dict[StrategicPiece, int]:
        defending_pieces: Dict[StrategicPiece, int] = {}
        for piece_id, status in piece_statuses.items():
            if self.context.my_pieces[piece_id].type == "artillery":
                defending_pieces[StrategicPiece(piece_id, "artillery")] = status
            
        return defending_pieces
    

    def report_attacking_pieces(self):
        attacking_pieces: Dict[StrategicPiece, int] = {}
        
        for piece_id, status in piece_statuses.items():
            if self.context.my_pieces[piece_id].type == "tank":
                attacking_pieces[StrategicPiece(piece_id, "tank")] = status
            
        return attacking_pieces
    
    def report_builders(self):
        building_pieces: Dict[StrategicPiece, int] = {}

        for piece_id, status in piece_statuses.items():

            if self.context.my_pieces[piece_id].type == "builder":
                building_pieces[StrategicPiece(piece_id, "builder")] = status

        return building_pieces

    
    def collect_money(self, builder: StrategicPiece, amount: int):
        global builder_chosen_tiles
        builder_piece: Builder = cast(
            Builder, self.context.my_pieces[builder.id])
        my_money = builder_piece.money
        self.log(f"builder {builder} has {my_money}$ and needs {amount}$")
        if my_money >= 100:
            self.context.log("cant carry more money, not collecting")
            return Response.success
        left_amount = amount - my_money
        if left_amount <= 0:
            self.context.log("i already have enough money, not collecting")
            return Response.success

        my_tile = builder_piece.tile
        money = my_tile.money
        if money > 0:
            collected = min(money, 5)
            builder_piece.collect_money(collected)
            self.context.log(f"collected {collected} money")
            left_amount -= collected
            if left_amount <= 0:
                self.context.log(f"enough money collected, returning success")
                return Response.success
            self.context.log(
                f"not enough money collected, returning in progress")
            return Response.in_progress

        tiles = [tile for tile in self.context.tiles.values()
                    if tile != my_tile and tile.country == self.get_my_country() and tile.money is not None and tile.money > 0 and tile not in builder_chosen_tiles]
        best_tile = sorted(
            tiles, key=lambda tile: (distance(tile.coordinates, my_tile.coordinates), -my_tile.money))[0] # minus because we want more money first
        self.context.log(f"moving to tile {best_tile.coordinates}")
        builder_chosen_tiles.add(best_tile)
        self.move_piece(builder_piece, best_tile.coordinates)
        return Response.in_progress


    """
    move piece to within range radius of dest (radius default 0)
    """
    def move_piece(self, piece: BasePiece, dest: Coordinates, radius : int = 0, prioritize_country = True):
        assert isinstance(dest, Coordinates)
        coords = piece.tile.coordinates
        piece_walk_distance = TYPE_TO_WALK_DIST[piece.type]
        if distance(coords, dest) <= radius:
            return True



        # if we have tiles in radius of dest that are in walking distance, pick the closest one to us
        close_to_dest_tiles = [tile for coords, tile in self.context.tiles.items() if distance(Coordinates(*coords), dest) <= radius]

        close_to_dest_tiles.sort(key=lambda tile: (distance(tile.coordinates, coords), (tile.country != self.get_my_country()) == prioritize_country))
        close_tile = close_to_dest_tiles[0]
        if distance(close_tile.coordinates, coords) <= piece_walk_distance:
            self.log(f"found tile {close_tile.coordinates} which is in radius, moving")
            piece.move(close_tile.coordinates)
            return True

        
        # otherwise, pick the closest tile to the destination that is in walking distance and walk to it
        # prioritise tiles from our country?

        walkable_tiles = [tile for coords, tile in self.context.tiles.items(
        ) if distance(Coordinates(*coords), piece.tile.coordinates) <= piece_walk_distance]
        best_tile = sorted(
            walkable_tiles, key=lambda tile: (distance(dest, tile.coordinates), (tile.country != self.get_my_country()) == prioritize_country))[0]
        self.context.log(f"moving to tile {best_tile.coordinates}")
        piece.move(best_tile.coordinates)
        return False

    def get_total_country_tiles_money(self):
        total = 0
        for tile in self.context.tiles.values():
            if tile.country == self.get_my_country():
                total += tile.money
        return total
    
    def get_total_builders_money(self):
        return sum([cast(Builder, piece).money for piece in self.context.my_pieces.values() if piece.type == 'builder'])

    def get_all_countries(self):
        return list(set([tile.country for tile in self.context.tiles.values()]))

    def get_my_country(self):
        return 'berzerkistan'

    def log(self, log_entry):
        return self.context.log(log_entry)

def get_strategic_implementation(context: TurnContext):
    return MyStrategicApi(context)

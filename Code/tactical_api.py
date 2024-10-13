from __future__ import annotations

from common_types import Coordinates

def distance(a: Coordinates, b: Coordinates) -> int:
    """Calculates the distance between the coordinates a and b."""
    return abs(a.x - b.x) + abs(a.y - b.y)


class BasePiece:
    """Base class for game pieces.

    This class exports the following fields:
    * id: Piece ID, as assigned by the server.
    * tile: The tile object of which this piece has been in, before this turn
            began.
    * type: Piece type (as a string).
    * country: The name of the country of which this piece belongs to.
    """

    id: str
    tile: Tile
    type: str
    country: str

    def move(self, destination):
        """Moves this piece to the destination tile.

        destination is expected to have a type of either Coordinates or Tile.
        """

class FlyingPiece(BasePiece):
    """Base class for flying pieces.

    This class exports the following fields:
    * in_air: A boolean indicating weather this piece is currently flying (True)
              or on the ground (False).
    * time_in_air: An integer counting the amount of turns of which this piece
                   has been flying, or None if this piece is on the ground.

    See BasePiece for more fields.
    """

    tile: Tile
    in_air: bool
    time_in_air: None | int

    def take_off(self):
        """Take off this piece.

        If this piece is already in the air, this is a no-op.
        """

    def land(self):
        """Land this piece.

        If this piece is already on the ground, this is a no-op.
        """


class Tank(BasePiece):
    """Represents a game tank.

    The value of its type field is "tank".

    This class does not expose any fields, except those exposed by BasePiece.
    """

    def attack(self):
        """Attacks the current game tile."""


class Airplane(FlyingPiece):
    """Represents a game airplane.

    The value of its type field is "airplane".

    This class does not expose any fields, except those exposed by BasePiece and
    FlyingPiece.
    """

    def attack(self):
        """Attacks the current game tile."""


class Artillery(BasePiece):
    """Represents a game artillery.

    The value of its type field is "artillery".

    This class does not expose any fields, except for those exposed by BasePiece.
    """

    def attack(self, destination: Tile | Coordinates):
        """Attacks the destination using this artillery.

        destination is expected to have a type of either Coordinates or Tile.
        """


class Helicopter(FlyingPiece):
    """Represents a game helicopter.

    The value of its type field is "helicopter".

    This class does not expose any fields, except those exposed by BasePiece and
    FlyingPiece.
    """

    def attack(self, destination: Tile | Coordinates):
        """Attacks the destination using this helicopter.

        destination is expected to have a type of either Coordinates or Tile.
        """


class Antitank(BasePiece):
    """Represents a game anti-tank.

    The value of its type field is "antitank".

    This class does not expose any fields, except those exposed by BasePiece.
    """
    pass


class IronDome(BasePiece):
    """Represents a game iron dome.

    This class exports the following fields:
    * id_defending: Set to True if and only if the protection of this iron dome
                    has been active before this turn began.

    The value of its type field is "irondome".

    Please refer to BasePiece for information about other exposed fields.
    """

    is_defending: bool

    def turn_on_protection(self):
        """Turns on this iron dome protection."""

    def turn_off_protection(self):
        """Turns off this iron dome protection."""


class Bunker(BasePiece):
    """Represents a game bunker.

    The value of its type field is "bunker".

    This class does not expose any fields, except those exposed by BasePiece.
    """


class Spy(BasePiece):
    """Represents a game spy.

    The value of its type field is "spy".

    This class does not expose any fields, except those exposed by BasePiece.
    """


class Tower(BasePiece):
    """Represents a game tower.

    The value of its type field is "tower".

    This class does not expose any fields, except those exposed by BasePiece.
    """


class Satellite(BasePiece):
    """Represents a game satellite.

    The value of its type field is "satellite".

    This class does not expose any fields, except those exposed by BasePiece.
    """


class Builder(BasePiece):
    """Represents a game builder.

    This class exposes the following fields:
    * money: The amount of money this builder has, before this turn began.

    The value of its type field is "builder".

    Please refer to BasePiece for information about other exposed fields.
    """

    money: int

    def collect_money(self, amount: int):
        """Collects a certain amount of money from the current Tile."""

    def throw_money(self, amount: int):
        """Throws a certain amount of money to the current Tile."""

    def build_tank(self):
        """Builds a new tank piece in the current tile."""

    def build_airplane(self):
        """Builds a new airplane piece in the current tile."""

    def build_artillery(self):
        """Builds a new artillery piece in the current tile."""

    def build_helicopter(self):
        """Builds a new helicopter piece in the current tile."""

    def build_antitank(self):
        """Builds a new anti-tank piece in the current tile."""

    def build_iron_dome(self):
        """Builds a new iron dome piece in the current tile."""

    def build_bunker(self):
        """Builds a new bunker piece in the current tile."""

    def build_spy(self):
        """Builds a new spy piece in the current tile."""

    def build_tower(self):
        """Builds a new tower piece in the current tile."""

    def build_satellite(self):
        """Builds a new satellite piece in the current tile."""

    def build_builder(self):
        """Builds a new builder piece in the current tile."""


TYPE_TO_CLASS = {
    'tank': Tank,
    'airplane': Airplane,
    'artillery': Artillery,
    'helicopter': Helicopter,
    'antitank': Antitank,
    'irondome': IronDome,
    'bunker': Bunker,
    'spy': Spy,
    'tower': Tower,
    'satellite': Satellite,
    'builder': Builder,
}

class Tile:
    """A land unit in the game.

    This class exports the following fields:
    * coordinates: The coordinates of this tile.
    * money: The amount of money in this tile before the turn started, or None if
             this amount is unknown to the current country.
    * country: The name of the country owning this tile, or None if this tile is
               not owned by any country.
    * pieces: A list of pieces on this tile.
    Note that the information here may be incomplete, depending on the visibility
    of the current country on this tile.
    """

    coordinates: Coordinates
    money: int
    country: None | str
    pieces: list[BasePiece]

class TurnContext(object):
    """Contains all the context of this turn.

    Some useful fields:
    * tiles: Maps coordinates (int, int) to a Tile object.
    * my_pieces: Maps piece IDs to the actual piece, for pieces owned by our
                 country.
    * all_pieces: Same as my_pieces, but for all pieces known by this country.
    * game_width: The width of the game.
    * game_height: The height of the game.
    * my_country: The name of my country.
    * all_countries: The names of all countries in the game.
    """

    tiles: dict[Coordinates, Tile]
    my_pieces: dict[str, BasePiece]
    all_pieces: dict[str, BasePiece]
    game_width: int
    game_height: int

    def get_tiles_of_country(self, country_name):
        """Returns the set of tile coordinates owned by the given country name.

        If country_name is None, the returned coordinates are of tiles that do not
        belong to any country.
        """

    def get_sighings_of_piece(self, piece_id):
        """Returns the sightings of the given piece.

        This method returns a set of sighted pieces and their locations, as seen by
        the given piece.

        Note that the given piece MUST belong to my country in order for this
        method to work.
        """

    def get_commands_of_piece(self, piece_id: str) -> list[object]:
        """Returns the list of ordered commands given to the given piece.

        Note that if the piece did not receive any command in this turn, or is not
        owned by my country, or does not exist, an empty list is returned.
        """

    def log(self, log_entry: str):
        """Logs the given log entry to the main log of this country.

        log_entry is expected to be a string, without a trailing new line character.
        """


class Logger(object):
    """Utility for logging stuff."""

    TIMEOUT = 10
    REQUEST_HEADERS = {
        'Content-type': 'application/json'
    }

    def log(self, log_entry: str):
        """Logs the provided log entry.

        log_entry is expected to be a string, without a trailing new line character.
        """

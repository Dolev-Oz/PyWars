import common_types
from strategic_api import CommandStatus, StrategicApi, StrategicPiece
from tactical_api import TurnContext, Builder, BasePiece

from random import randint

tank_to_coordinate_to_attack = {}
tank_to_attacking_command = {}
commands = []
builder_to_amount: dict[int, int] = {}
builder_to_command: dict[int, str] = {}


def move_tank_to_destination(tank, dest):
    """Returns True if the tank's mission is complete."""
    command_id = tank_to_attacking_command[tank.id]
    if dest is None:
        commands[int(command_id)] = CommandStatus.failed(command_id)
        return
    if dest == tank.tile:
        tank.attack()
        commands[int(command_id)] = CommandStatus.success(command_id)
        del tank_to_attacking_command[tank.id]
        return True
    tank_coordinate = tank.tile.coordinates
    if tank.tile.country != TurnContext.my_country:
        tank.attack()
        prev_command = commands[int(command_id)]
        commands[int(command_id)] = CommandStatus.in_progress(command_id,
                                                              prev_command.elapsed_turns + 1,
                                                              prev_command.estimated_turns - 1)
        return False
    elif dest.x < tank_coordinate.x:
        new_coordinate = common_types.Coordinates(tank_coordinate.x - 1, tank_coordinate.y)
    elif dest.x > tank_coordinate.x:
        new_coordinate = common_types.Coordinates(tank_coordinate.x + 1, tank_coordinate.y)
    elif dest.y < tank_coordinate.y:
        new_coordinate = common_types.Coordinates(tank_coordinate.x, tank_coordinate.y - 1)
    elif dest.y > tank_coordinate.y:
        new_coordinate = common_types.Coordinates(tank_coordinate.x, tank_coordinate.y + 1)
    tank.move(new_coordinate)
    prev_command = commands[int(command_id)]
    commands[int(command_id)] = CommandStatus.in_progress(command_id,
                                                          prev_command.elapsed_turns + 1,
                                                          prev_command.estimated_turns - 1)
    return False

def move_in_random_direction(piece: BasePiece) -> None:
    coords = piece.tile.coordinates

    direction = randint(0, 3)
    dest = {
        0: common_types.Coordinates(coords.x + 1, coords.y),
        1: common_types.Coordinates(coords.x - 1, coords.y),
        2: common_types.Coordinates(coords.x, coords.y + 1),
        3: common_types.Coordinates(coords.x, coords.y - 1),
    }
    piece.move(dest[direction])


def collect_money_advance(builder: Builder, amount: int) -> bool:
    command_id = builder_to_command[int(builder.id)]

    if builder.tile.money > 0:
        amount -= builder.tile.money
        builder.collect_money(0, builder.tile.money)
        if amount <= 0:
            commands[int(command_id)] = CommandStatus.success(command_id)
            del builder_to_command[builder.id]
            return True

    move_in_random_direction(builder)
    prev_command = commands[int(command_id)]
    commands[int(command_id)] = CommandStatus.in_progress(command_id, prev_command.elapsed_turns + 1, 999999999)



class MyStrategicApi(StrategicApi):
    def __init__(self, *args, **kwargs):
        super(MyStrategicApi, self).__init__(*args, **kwargs)
        to_remove = set()
        for tank_id, destination in tank_to_coordinate_to_attack.items():
            tank = self.context.my_pieces.get(tank_id)
            if tank is None:
                to_remove.add(tank_id)
                continue
            if move_tank_to_destination(tank, destination):
                to_remove.add(tank_id)
        for tank_id in to_remove:
            del tank_to_coordinate_to_attack[tank_id]

    def attack(self, piece, destination, radius):
        tank = self.context.my_pieces[piece.id]
        if not tank or tank.type != 'tank':
            return None

        if piece.id in tank_to_attacking_command:
            old_command_id = int(tank_to_attacking_command[piece.id])
            commands[old_command_id] = CommandStatus.failed(old_command_id)

        command_id = str(len(commands))
        attacking_command = CommandStatus.in_progress(command_id, 0, common_types.distance(tank.tile.coordinates, destination))
        tank_to_coordinate_to_attack[piece.id] = destination
        tank_to_attacking_command[piece.id] = command_id
        commands.append(attacking_command)

        return command_id

    def estimate_tile_danger(self, destination):
        tile = self.context.tiles[(destination.x, destination.y)]
        if tile.country == self.context.my_country:
            return 0
        elif tile.country is None:
            return 1
        else:   # Enemy country
            return 2

    def get_game_height(self):
        return self.context.game_height

    def get_game_width(self):
        return self.context.game_width

    def report_attacking_pieces(self):
        return {StrategicPiece(piece_id, piece.type) : tank_to_attacking_command.get(piece_id)
                for piece_id, piece in self.context.my_pieces.items()
                if piece.type == 'tank'}

    def collect_money(self, builder: StrategicPiece, amount: int) -> str:
        builder1 = self.context.my_pieces[builder.id]
        if not builder1 or builder1.type != "builder":
            return ""

        if builder.id in builder_to_command:
            command_id = builder_to_command[builder.id]
            commands[int(command_id)] = CommandStatus.failed(command_id)

        command_id = str(len(commands))
        command = CommandStatus.in_progress(command_id, 0, 999999)
        builder_to_amount[builder.id] = amount
        builder_to_command[builder.id] = command_id
        commands.append(command)

        return command_id


def get_strategic_implementation(context):
    return MyStrategicApi(context)

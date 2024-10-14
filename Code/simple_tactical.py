import common_types
from strategic_api import CommandStatus, StrategicApi, StrategicPiece
from tactical_api import TurnContext, Builder, BasePiece, distance

from random import randint, choices

PRICES = {
    'builder': 20,
    'tank': 8,
    'artillery': 8,
    'airplane': 20,
    'helicopter': 16,
    'antitank': 10,
    'irondome': 32,
    'bunker': 10,
    'spy': 20,
    'tower': 16,
    'satellite': 64,
}
BUILD_FUNCTIONS = {
    'builder': Builder.build_builder,
    'tank': Builder.build_tank,
    'artillery': Builder.build_artillery,
    'airplane': Builder.build_airplane,
    'helicopter': Builder.build_helicopter,
    'antitank': Builder.build_antitank,
    'irondome': Builder.build_iron_dome,
    'bunker': Builder.build_bunker,
    'spy': Builder.build_spy,
    'tower': Builder.build_tower,
    'satellite': Builder.build_satellite,
}

tank_to_coordinate_to_attack = {}
tank_to_attacking_command = {}
commands = []

builder_to_amount: dict[str, int] = {}
builder_to_piece: dict[str, str] = {}
builder_to_command: dict[str, str] = {}


def move_tank_to_destination(context, tank, dest: common_types.Coordinates, radius):
    """Returns True if the tank's mission is complete."""
    try:
        command_id = tank_to_attacking_command[tank.id]
        if dest is None:
            commands[int(command_id)] = CommandStatus.failed(command_id)
            return
        if distance(dest, tank.tile.coordinates) <= radius:
            tank.attack()
            commands[int(command_id)] = CommandStatus.success(command_id)
            del tank_to_attacking_command[tank.id]
            return True
        tank_coordinate = tank.tile.coordinates
        if tank.tile.country != context.my_country:
            tank.attack()
            return False
        x_dist = abs(dest.x - tank.tile.coordinates.x)
        y_dist = abs(dest.y - tank.tile.coordinates.y)
        randomized = choices([0, 1], weights=[x_dist, y_dist])
        if not (dest.x >= 0 and dest.x < context.game_width and dest.y >= 0 and dest.y < context.game_height):
            if tank_coordinate.x > 0:
                new_coordinate = common_types.Coordinates(tank_coordinate.x - 1, tank_coordinate.y)
            else:
                new_coordinate = common_types.Coordinates(tank_coordinate.x + 1, tank_coordinate.y)
        elif randomized == 0:
            if dest.x < tank_coordinate.x:
                new_coordinate = common_types.Coordinates(tank_coordinate.x - 1, tank_coordinate.y)
            elif dest.x > tank_coordinate.x:
                new_coordinate = common_types.Coordinates(tank_coordinate.x + 1, tank_coordinate.y)
            elif dest.y < tank_coordinate.y:
                new_coordinate = common_types.Coordinates(tank_coordinate.x, tank_coordinate.y - 1)
            elif dest.y > tank_coordinate.y:
                new_coordinate = common_types.Coordinates(tank_coordinate.x, tank_coordinate.y + 1)
        else:
            if dest.y < tank_coordinate.y:
                new_coordinate = common_types.Coordinates(tank_coordinate.x, tank_coordinate.y - 1)
            elif dest.y > tank_coordinate.y:
                new_coordinate = common_types.Coordinates(tank_coordinate.x, tank_coordinate.y + 1)
            elif dest.x < tank_coordinate.x:
                new_coordinate = common_types.Coordinates(tank_coordinate.x - 1, tank_coordinate.y)
            elif dest.x > tank_coordinate.x:
                new_coordinate = common_types.Coordinates(tank_coordinate.x + 1, tank_coordinate.y)
        tank.move(new_coordinate)
        return False
    except Exception:
        context.log("move_tank_to_destination log")


def move_in_random_direction(piece: BasePiece, context) -> None:
	coords = piece.tile.coordinates

	dest = {
		0: common_types.Coordinates(coords.x + 1, coords.y),
		1: common_types.Coordinates(coords.x - 1, coords.y),
		2: common_types.Coordinates(coords.x, coords.y + 1),
		3: common_types.Coordinates(coords.x, coords.y - 1),
	}
	direction = randint(0, 3)
	while dest[direction][0] < 0 or dest[direction][0] > context.game_width or dest[direction][1] < 0 or \
			dest[direction][1] > context.game_width:
		direction = randint(0, 3)
	piece.move(dest[direction])


def collect_money_advance(builder: Builder, amount: int, context: TurnContext) -> bool:
    command_id = builder_to_command[builder.id]

    if builder.tile.money > 0 and builder.tile.country == context.my_country:
        amount -= min(5,builder.tile.money)
        
        builder.collect_money(min(5,builder.tile.money))
            
        if amount <= 0:
            commands[int(command_id)] = CommandStatus.success(command_id)
            #del builder_to_command[builder.id]
            return True
    else:
        move_in_random_direction(builder, context)
        commands[int(command_id)] = CommandStatus.in_progress(command_id, 0, 999999999)

    return False


def build_piece_advance(builder: Builder, piece: str, context: TurnContext) -> bool:
    command_id = builder_to_command[builder.id]

    cost = PRICES[piece]

    if builder.money >= cost:
        BUILD_FUNCTIONS[piece](builder)
        commands[int(command_id)] = CommandStatus.success(command_id)
        del builder_to_command[builder.id]
        return True
    else:
        collect_money_advance(builder, 1000, context)

    return False


class MyStrategicApi(StrategicApi):
    def __init__(self, context):
        self.context = context
        to_remove = set()
        for tank_id, (destination, radius) in tank_to_coordinate_to_attack.items():
            tank = self.context.my_pieces.get(tank_id)
            if tank is None:
                to_remove.add(tank_id)
                continue
            try:
                success = move_tank_to_destination(self.context, tank, destination, radius)
            except Exception:
                raise Exception("attack exception")
            if success:
                to_remove.add(tank_id)
        for tank_id in to_remove:
            del tank_to_coordinate_to_attack[tank_id]
        to_remove.clear()
        self.loop_builders()

    def loop_builders(self):
        def remove(b_id):
            if b_id in builder_to_piece:
                del builder_to_piece[b_id]
            if b_id in builder_to_amount:
                del builder_to_amount[b_id]
        
        remove_set = []
        for builder_id, piece in builder_to_piece.items():
            builder_piece = self.context.my_pieces.get(builder_id)
            
            if builder_piece is None:
                remove_set.append(builder_id)
                continue
        
            if build_piece_advance(builder_piece, piece, self.context):
                remove_set.append(builder_id)
                
        for item in remove_set:
            remove(item)
        remove_set = []
        
        #for builder_id, piece in builder_to_amount.items():
        #    builder = self.context.my_pieces.get(builder_id)
        #    if builder is None or not isinstance(builder, Builder):
        #        if builder_id in builder_to_command[builder_id]:
        #            c_id = builder_to_command[builder_id]
        #            commands[int(c_id)] = CommandStatus.failed(c_id)
        #            del builder_to_command[builder_id]
        #        remove_set.append(builder_id)
        #        continue
        #    if collect_money_advance(builder, piece):
        #        remove_set.append(builder_id)
        for item in remove_set:
            remove(item)

    def attack(self, piece, destination, radius):
        try:
            tank = self.context.my_pieces[piece.id]
            if not tank or tank.type != 'tank':
                return None

            if piece.id in tank_to_attacking_command:
                old_command_id = int(tank_to_attacking_command[piece.id])
                commands[old_command_id] = CommandStatus.failed(old_command_id)

            command_id = str(len(commands))
            attacking_command = CommandStatus.in_progress(command_id, 0,
                                                        common_types.distance(tank.tile.coordinates, destination))
            tank_to_coordinate_to_attack[piece.id] = destination, radius
            tank_to_attacking_command[piece.id] = command_id
            commands.append(attacking_command)

            return command_id
        except Exception:
            self.context.log("inner attack log")

    def estimate_tile_danger(self, destination):
        tile = self.context.tiles[(destination.x, destination.y)]
        if tile.country == self.context.my_country:
            return 0
        elif tile.country is None:
            return 1
        else:  # Enemy country
            return 2

    def get_game_height(self):
        return self.context.game_height

    def get_game_width(self):
        return self.context.game_width

    def report_attacking_pieces(self):
        return {StrategicPiece(piece_id, piece.type): tank_to_attacking_command.get(piece_id)
                for piece_id, piece in self.context.my_pieces.items()
                if piece.type == 'tank'}

    def report_builders(self):
        return {StrategicPiece(piece.id, piece.type) : (builder_to_command.get(piece.id), builder_to_amount.get(piece.id, 0))
                for piece_id, piece in self.context.my_pieces.items()
                if piece.type == 'builder'}

    def collect_money_stupid(self, builder: StrategicPiece, amount: int) -> str:
        builder1 = self.context.my_pieces[builder.id]
        if builder1.tile.money != 0:
            builder1.collect_money(min(5,builder1.tile.money))
        else:
            x = builder1.tile.coordinates.x
            y = builder1.tile.coordinates.y
            if 0 <= y+1 <= self.context.game_width:
                builder1.move(common_types.Coordinates(x, y+1))
            if 0 <= x+1 <= self.context.game_width:
                builder1.move(common_types.Coordinates(x+1, y))
            else:
                builder1.move(common_types.Coordinates(x,y-1))
            return None
                
            

            

    def collect_money(self, builder: StrategicPiece, amount: int) -> str:
        raise Exception()
        return self.collect_money_stupid(builder, amount)
        #builder1 = self.context.my_pieces[builder.id]
        #if not builder1 or not isinstance(builder1, Builder):
        #    return ""

        #if builder.id in builder_to_command:
        #    if builder.id in builder_to_piece:
        #        del builder_to_piece[builder.id]
        #    command_id = builder_to_command[builder.id]
        #    commands[int(command_id)] = CommandStatus.failed(command_id)

        #command_id = str(len(commands))
        #command = CommandStatus.in_progress(command_id, 0, 999999)
        #builder_to_amount[builder.id] = amount
        #builder_to_command[builder.id] = command_id
        #commands.append(command)

        #return command_id

    def build_piece(self, builder: StrategicPiece, piece_type: str) -> str:
        builder_piece = self.context.my_pieces[builder.id]
        
        if not builder_piece or not isinstance(builder_piece, Builder):
            return None

        if not piece_type in PRICES:
            return None

        if builder.id in builder_to_command:
            if builder.id in builder_to_amount:
                del builder_to_amount[builder.id]
            command_id = builder_to_command[builder.id]
            commands[int(command_id)] = CommandStatus.failed(command_id)

        command_id = str(len(commands))
        command = CommandStatus.in_progress(command_id, 0, 999999)
        
        
        
        builder_to_piece[builder.id] = piece_type
        
        
        
        builder_to_command[builder.id] = command_id
        commands.append(command)

        return command_id


def get_strategic_implementation(context):
    
    return MyStrategicApi(context)

import random

import tactical_api
import strategic_api

turn_number = -1


class MyStrategicApi(strategic_api.StrategicApi):
    def __init__(self, *args, **kwargs):
        global turn_number
        super(MyStrategicApi, self).__init__(*args, **kwargs)
        turn_number += 1

    def get_my_country(self):
        return self.context.my_country

    def list_all_countries(self):
        return self.context.all_countries

    def get_piece_of_type(self, type_):
        for piece in self.context.my_pieces.values():
            if piece.type == type_:
                return piece
        return None

    def conquer_using_tanks_tile_of(self, countries):
        builder = self.get_piece_of_type('builder')
        tank = self.get_piece_of_type('tank')
        airplane = self.get_piece_of_type('airplane')
        artillery = self.get_piece_of_type('artillery')
        helicopter = self.get_piece_of_type('helicopter')
        antitank = self.get_piece_of_type('antitank')
        irondome = self.get_piece_of_type('irondome')
        bunker = self.get_piece_of_type('bunker')
        spy = self.get_piece_of_type('spy')
        tower = self.get_piece_of_type('tower')
        satelite = self.get_piece_of_type('satelite')
        if turn_number == 1:
            builder.collect_money(500000)
        elif turn_number == 2:
            builder.build_tank()
        elif turn_number == 3:
            builder.build_airplane()
            tank.move(tactical_api.Coordinates(0, 1))
        elif turn_number == 4:
            builder.build_artillery()
            tank.attack()
            airplane.take_off()
        elif turn_number == 5:
            builder.build_helicopter()
            airplane.move(tactical_api.Coordinates(1, 2))
            artillery.move(tactical_api.Coordinates(0, 1))
        elif turn_number == 6:
            builder.build_antitank()
            airplane.attack()
            artillery.attack(tactical_api.Coordinates(1, 1))
            helicopter.take_off()
        elif turn_number == 7:
            builder.build_iron_dome()
            airplane.land()
            helicopter.move(tactical_api.Coordinates(0, 1))
            antitank.move(tactical_api.Coordinates(1, 0))
        elif turn_number == 8:
            builder.build_bunker()
            helicopter.attack(tactical_api.Coordinates(0, 2))
            irondome.move(tactical_api.Coordinates(1, 0))
        elif turn_number == 9:
            builder.build_spy()
            helicopter.land()
            irondome.turn_on_protection()
        elif turn_number == 10:
            builder.build_tower()
            irondome.turn_off_protection()
            spy.move(tactical_api.Coordinates(0, 1))
        elif turn_number == 11:
            builder.build_satelite()
        elif turn_number == 12:
            builder.throw_money(10)
        elif turn_number == 13:
            import sys
            for piece in self.context.my_pieces.values():
                sys.stderr.write(piece.type + '\n')
            satelite.move(tactical_api.Coordinates(2, 2))
            builder.build_builder()


def get_strategic_implementation(context):
    return MyStrategicApi(context)

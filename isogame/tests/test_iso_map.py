import pygame
from isogame.iso_map import IsoMap


def test_world_screen_round_trip():
    pygame.init()
    iso_map = IsoMap(10, 10, 64, 32, origin=(0, 0))
    world = pygame.Vector2(3.5, 4.0)
    screen = iso_map.world_to_screen(world)
    back = iso_map.screen_to_world(screen)
    assert (back - world).length() < 0.001


def test_origin_offset_affects_projection():
    pygame.init()
    base_map = IsoMap(10, 10, 64, 32, origin=(0, 0))
    offset_map = IsoMap(10, 10, 64, 32, origin=(120, 80))
    world = pygame.Vector2(2, 7)
    base_screen = base_map.world_to_screen(world)
    offset_screen = offset_map.world_to_screen(world)
    assert offset_screen - base_screen == pygame.Vector2(120, 80)

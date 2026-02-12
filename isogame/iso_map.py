import random
import pygame
from .settings import (
    GRID_COLOR, TILE_COLOR_1, TILE_COLOR_2, GRASS_DETAIL_COLOR,
    DECORATION_SEED, TREE_CHANCE, ROCK_CHANCE, FLOWER_CHANCE,
    TREE_COLOR, TREE_TRUNK_COLOR, ROCK_COLOR, FLOWER_COLOR,
)


class IsoMap:
    """Isometric grid for rendering and coordinate transforms 
    
    Args:
        width (int): Number of tiles along the x-axis.
        height (int): Number of tiles along the y-axis.
        tile_width (int): Pixel width of a diamond tile.
        tile_height (int): Pixel height of a diamond tile.
        origin (tuple[float, float]) Screen-space offset of the map center

    Attributes:
        width (int): Grid width in tiles
        height (int): Grid height in tiles.
        tile_width (int): Tile width in pixels.
        tile_height (int): Tile height in pixels.
        origin (pygame.Vector2): Screen offset for the amp.
    """

    def __init__(self, width, height, tile_width, tile_height, origin):
        """Store map size, tile size, and screen origin."""
        self.width = width
        self.height = height
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.origin = pygame.Vector2(origin)
        self.decorations = self._generate_decorations()

    def world_to_screen(self, world_pos):
        """Convert world grid to screen pixel coords."""
        world_pos = pygame.Vector2(world_pos)
        screen_x = (world_pos.x - world_pos.y) * (self.tile_width / 2)
        screen_y = (world_pos.x + world_pos.y) * (self.tile_height / 2)
        return pygame.Vector2(screen_x, screen_y) + self.origin

    def screen_to_world(self, screen_pos):
        """Convert screen pixel coords back to world grid."""
        screen_pos = pygame.Vector2(screen_pos) - self.origin
        scaled_x = screen_pos.x / (self.tile_width / 2)
        scaled_y = screen_pos.y / (self.tile_height / 2)
        world_x = (scaled_x + scaled_y) / 2
        world_y = (scaled_y - scaled_x) / 2
        return pygame.Vector2(world_x, world_y)

    def draw(self, surface):
        """Render the iso tile grid to the given surface"""
        half_w = self.tile_width / 2
        half_h = self.tile_height / 2
        for y in range(self.height):
            for x in range(self.width):
                center = self.world_to_screen((x,y))
                color = TILE_COLOR_1 if (x+y) % 2 == 0 else TILE_COLOR_2
                points = [
                    (center.x, center.y - half_h),
                    (center.x + half_w, center.y),
                    (center.x, center.y + half_h),
                    (center.x - half_w, center.y),
                ]
                pygame.draw.polygon(surface, color, points)
                pygame.draw.polygon(surface, GRID_COLOR, points, 1)
                if (x + y) % 3 == 0:
                    pygame.draw.line(
                        surface,
                        GRASS_DETAIL_COLOR,
                        (center.x - 2, center.y),
                        (center.x + 2, center.y - 3),
                        1,
                    )
        for kind, pos in self.decorations:
            base = self.world_to_screen(pos)
            if kind == "tree":
                trunk_rect = pygame.Rect(base.x - 3, base.y - 14, 6, 12)
                pygame.draw.rect(surface, TREE_TRUNK_COLOR, trunk_rect)
                pygame.draw.circle(surface, TREE_COLOR, (int(base.x), int(base.y - 20)), 12)
            elif kind == "rock":
                rock_rect = pygame.Rect(base.x - 8, base.y - 6, 16, 12)
                pygame.draw.ellipse(surface, ROCK_COLOR, rock_rect)
            else:
                pygame.draw.circle(surface, FLOWER_COLOR, (int(base.x), int(base.y - 8)), 5)

    def _generate_decorations(self):
        """Create a deterministic list of decoration positions."""
        rng = random.Random(DECORATION_SEED)
        decorations = []
        center_x = self.width / 2
        center_y = self.height / 2
        for y in range(self.height):
            for x in range(self.width):
                if abs(x - center_x) < 2 and abs(y - center_y) < 2:
                    continue
                roll = rng.random()
                if roll < TREE_CHANCE:
                    decorations.append(("tree", pygame.Vector2(x, y)))
                elif roll < TREE_CHANCE + ROCK_CHANCE:
                    decorations.append(("rock", pygame.Vector2(x, y)))
                elif roll < TREE_CHANCE + ROCK_CHANCE + FLOWER_CHANCE:
                    decorations.append(("flower", pygame.Vector2(x, y)))
        return decorations
    
        

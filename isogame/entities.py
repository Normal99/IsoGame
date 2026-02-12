import pygame
from .settings import (
    PLAYER_SPEED, PLAYER_COLOR, GUN_COLOR,
    ZOMBIE_SPEED, ZOMBIE_COLOR,
    BULLET_SPEED, BULLET_COLOR, BULLET_LIFETIME,
    PLAYER_MAX_HP, PLAYER_HIT_COOLDOWN,
    ZOMBIE_STOP_DISTANCE, SHADOW_COLOR, PLAYER_HEIGHT, 
    ZOMBIE_HEIGHT, BULLET_HEIGHT,
    POWERUP_RADIUS, POWERUP_HEAL_COLOR, POWERUP_SPEED_COLOR,
)

class Player:
    """Player controlled with WASD and mouse aim."""

    def __init__(self, pos):
        """Choose player positions speed and aim direction."""
        self.pos = pygame.Vector2(pos)
        self.radius = 10
        self.speed = PLAYER_SPEED
        self.aim_dir = pygame.Vector2(1, 0)
        self.max_hp = PLAYER_MAX_HP
        self.hp = PLAYER_MAX_HP
        self.hit_timer = 0.0

    def update(self, keys, dt, bounds, speed_multiplier=1.0):
        """Move with WASD while staying inside map bounds."""
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_w]:
            direction += pygame.Vector2(-1, -1)
        if keys[pygame.K_s]:
            direction += pygame.Vector2(1, 1)
        if keys[pygame.K_a]:
            direction += pygame.Vector2(-1, 1)
        if keys[pygame.K_d]:
            direction += pygame.Vector2(1, -1)
        if direction.length_squared() > 0:
            direction = direction.normalize()
        if self.hit_timer > 0:
            self.hit_timer = max(0.0, self.hit_timer - dt)
        self.pos += direction * self.speed * speed_multiplier * dt
        self.pos.x = max(0.0, min(bounds[0] - 1, self.pos.x))
        self.pos.y = max(0.0, min(bounds[1] - 1, self.pos.y))

    def set_aim(self, target_world):
        """update aim direction toward a world position"""
        direction = pygame.Vector2(target_world) - self.pos
        if direction.length_squared() > 0:
            self.aim_dir = direction.normalize()

    def take_damage(self, amount):
        """Reduce HP if not on cooldown."""
        if self.hit_timer > 0:
            return False
        self.hp = max(0, self.hp - amount)
        self.hit_timer = PLAYER_HIT_COOLDOWN
        return True

    def draw(self, surface, iso_map):
        """Draw the player with a shadow and height offset."""
        screen_pos = iso_map.world_to_screen(self.pos)
        shadow_rect = pygame.Rect(screen_pos.x - 12, screen_pos.y - 4, 24, 8)
        pygame.draw.ellipse(surface, SHADOW_COLOR, shadow_rect)

        body_pos = screen_pos - pygame.Vector2(0, PLAYER_HEIGHT)
        body_rect = pygame.Rect(0, 0, 20, 28)
        body_rect.center = (body_pos.x, body_pos.y + 4)
        pygame.draw.ellipse(surface, PLAYER_COLOR, body_rect)

        head_pos = pygame.Vector2(body_pos.x, body_pos.y - 18)
        head_color = (232, 190, 172)
        pygame.draw.circle(surface, head_color, head_pos, 6)

class Zombie:
    """Simple Zombie NPC that follows the player"""

    def __init__(self, pos, speed=ZOMBIE_SPEED):
        """Initialize zombie position and speed."""
        self.pos = pygame.Vector2(pos)
        self.radius = 10
        self.speed = speed

    def update(self, target_pos, dt):
        """Move toward the player but stop at a minimum distance."""
        direction = pygame.Vector2(target_pos) - self.pos
        distance = direction.length()
        if distance == 0:
            return
        if distance <= ZOMBIE_STOP_DISTANCE:
            self.pos = pygame.Vector2(target_pos) - direction.normalize() * ZOMBIE_STOP_DISTANCE
            return
        self.pos += direction.normalize() * self.speed * dt

    def draw(self, surface, iso_map):
        """Draw the zombie with a shadow and height offset."""
        screen_pos = iso_map.world_to_screen(self.pos)
        shadow_rect = pygame.Rect(screen_pos.x - 12, screen_pos.y - 4, 24, 8)
        pygame.draw.ellipse(surface, SHADOW_COLOR, shadow_rect)

        body_pos = screen_pos - pygame.Vector2(0, ZOMBIE_HEIGHT)
        body_rect = pygame.Rect(0, 0, 20, 28)
        body_rect.center = (body_pos.x, body_pos.y + 4)
        pygame.draw.ellipse(surface, ZOMBIE_COLOR, body_rect)

        head_pos = pygame.Vector2(body_pos.x, body_pos.y - 18)
        head_color = (78, 110, 86)
        pygame.draw.circle(surface, head_color, head_pos, 6)

class Bullet:
    """Projectile fired from the player."""

    def __init__(self, pos, direction, speed=BULLET_SPEED):
        """Create a bullet with position, direction, and lifetime."""
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(direction) * speed
        self.radius = 4
        self.remaining = BULLET_LIFETIME
    
    def update(self, dt):
        """Move the bullet and reduce its remaining lifetime."""
        self.pos += self.velocity * dt
        self.remaining -= dt 

    @property
    def alive(self): 
        """return True while the bullet lifetime remains."""
        return self.remaining > 0

    def draw(self, surface, iso_map):
        """Draw the bullet at its position"""
        screen_pos = iso_map.world_to_screen(self.pos)
        pygame.draw.circle(surface, BULLET_COLOR, screen_pos, self.radius)

class PowerUp:
    """Pickup item on the map."""

    def __init__(self, pos, kind):
        """Create a powerup at a world position."""
        self.pos = pygame.Vector2(pos)
        self.kind = kind  # "heal" or "speed"
        self.radius = POWERUP_RADIUS

    def draw(self, surface, iso_map):
        """Draw the powerup."""
        screen_pos = iso_map.world_to_screen(self.pos)
        color = POWERUP_HEAL_COLOR if self.kind == "heal" else POWERUP_SPEED_COLOR
        pygame.draw.circle(surface, color, screen_pos, self.radius)

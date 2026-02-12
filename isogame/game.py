import random
import pygame

from pathlib import Path
from .entities import Player, Zombie, Bullet, PowerUp
from .iso_map import IsoMap
from .ui import Menu
from .settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    TILE_WIDTH,
    TILE_HEIGHT,
    MAP_WIDTH,
    MAP_HEIGHT,
    BG_COLOR,
    MAX_ZOMBIES,
    ZOMBIE_SPAWN_INTERVAL,
    ZOMBIE_SPEED,
    ZOMBIE_SPEED_GROWTH,
    ZOMBIE_DAMAGE,
    BULLET_SPEED,
    HP_BAR_BG,
    HP_BAR_FILL,
    HP_BAR_BORDER,
    TEXT_COLOR,
    MENU_BG_COLOR,
    POWERUP_SPAWN_INTERVAL,
    MAX_POWERUPS,
    POWERUP_HEAL_AMOUNT,
    POWERUP_SPEED_BOOST,
    POWERUP_SPEED_DURATION,
    UPGRADE_SCORE_STEP,
    MAX_UPGRADE_LEVEL,
    UPGRADE_HP_BONUS,
    UPGRADE_SPEED_BONUS,
    UPGRADE_BULLET_SPEED_BONUS,
    FIRE_RATE,
    FIRE_RATE_BONUS,
    FIRE_HOLD_DELAY,
)


class Game:
    """Main game loop and state management."""

    def __init__(self):
        """Set up pygame, map, player, and UI."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Isometric Zombie Shooter")
        self.clock = pygame.time.Clock()
        


        self.map = IsoMap(
            MAP_WIDTH,
            MAP_HEIGHT,
            TILE_WIDTH,
            TILE_HEIGHT,
            origin=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4),
        )

        self.player = Player((MAP_WIDTH / 2, MAP_HEIGHT / 2))
        self.zombies = []
        self.bullets = []
        self.powerups = []

        self.menu = Menu(self.screen.get_rect())
        self.ui_font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 64)
        
        self.upgrade_points = 0
        self.next_upgrade_score = UPGRADE_SCORE_STEP
        self.upgrades = {"hp": 0, "speed": 0, "bullet": 0, "fire": 0}
        self.bullet_speed_bonus = 0.0
        self.fire_rate_bonus = 0.0
        self.score = 0
        self.high_score_path = Path(__file__).resolve().parent.parent / "highscore.txt"
        self.high_score = self._load_high_score()
        self.state = "menu"
        self.zombies_spawned = 0
        self.spawn_timer = 0.0
        self.powerup_timer = 0.0
        self.speed_boost_timer = 0.0
        self.fire_timer = 0.0
        self.hold_timer = 0.0

    def run(self):
        """Main loop: handle events, update, draw."""
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif self.state == "menu":
                    action = self.menu.handle_event(event)
                    if action == "start":
                        self._reset_round()
                        self.state = "play"
                    elif action == "quit":
                        running = False
                elif self.state == "play":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_1:
                            self._buy_upgrade("hp")
                        elif event.key == pygame.K_2:
                            self._buy_upgrade("speed")
                        elif event.key == pygame.K_3:
                            self._buy_upgrade("bullet")
                        elif event.key == pygame.K_4:
                            self._buy_upgrade("fire")
                elif self.state == "game_over":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.state = "menu"
                        elif event.key == pygame.K_r:
                            self._reset_round()
                            self.state = "play"

            if self.state == "menu":
                self.menu.draw(self.screen)
                self._draw_menu_text()
            elif self.state == "play":
                self._update_game(dt)
                self._draw_game()
            elif self.state == "game_over":
                self._draw_game_over()
            pygame.display.flip()

        pygame.quit()


    def _update_game(self, dt):
        """Update player, zombies, bullets, and collisions."""
        keys = pygame.key.get_pressed()
        speed_multiplier = POWERUP_SPEED_BOOST if self.speed_boost_timer > 0 else 1.0
        self.player.update(keys, dt, (MAP_WIDTH, MAP_HEIGHT), speed_multiplier)
        self._update_camera()

        mouse_world = self.map.screen_to_world(pygame.mouse.get_pos())
        self.player.set_aim(mouse_world)

        if pygame.mouse.get_pressed()[0]:
            self.hold_timer += dt
            if self.hold_timer >= FIRE_HOLD_DELAY:
                self.fire_timer += dt
                cooldown = 1.0 / (FIRE_RATE + self.fire_rate_bonus)
                if self.fire_timer >= cooldown:
                    self._spawn_bullet()
                    self.fire_timer = 0.0
        else:
            self.hold_timer = 0.0
            self.fire_timer = 0.0

        self.spawn_timer += dt
        if self.spawn_timer >= ZOMBIE_SPAWN_INTERVAL and len(self.zombies) < MAX_ZOMBIES:
            self._spawn_zombie()
            self.spawn_timer = 0.0

        self.powerup_timer += dt
        if self.powerup_timer >= POWERUP_SPAWN_INTERVAL and len(self.powerups) < MAX_POWERUPS:
            self._spawn_powerup()
            self.powerup_timer = 0.0

        for zombie in self.zombies:
            zombie.update(self.player.pos, dt)
            self._handle_player_hit()

        for bullet in list(self.bullets):
            bullet.update(dt)
            if not bullet.alive:
                self.bullets.remove(bullet)

        if self.speed_boost_timer > 0:
            self.speed_boost_timer = max(0.0, self.speed_boost_timer - dt)

        self._handle_collisions()
        self._handle_powerups()

    def _draw_game(self):
        """Draw map and entities in isometric depth order."""
        self.screen.fill(BG_COLOR)
        self.map.draw(self.screen)
        self._draw_hud()

        for powerup in self.powerups:
            powerup.draw(self.screen, self.map)
        drawables = [
            *[(z.pos.x + z.pos.y, z) for z in self.zombies],
            *[(b.pos.x + b.pos.y, b) for b in self.bullets],
            (self.player.pos.x + self.player.pos.y, self.player),
        ]

        for _, entity in sorted(drawables, key=lambda item: item[0]):
            entity.draw(self.screen, self.map)
        
    def _draw_menu_text(self):
        text = self.ui_font.render(f"High score: {self.high_score}", True, TEXT_COLOR)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(text, rect)
    
    def _buy_upgrade(self, kind):
        if self.upgrade_points <= 0 or self.upgrades[kind] >= MAX_UPGRADE_LEVEL:
            return
        self.upgrade_points -= 1
        self.upgrades[kind] += 1
        if kind == "hp":
            self.player.max_hp += UPGRADE_HP_BONUS
            self.player.hp += UPGRADE_HP_BONUS
        elif kind == "speed":
            self.player.speed += UPGRADE_SPEED_BONUS
        elif kind == "bullet":
            self.bullet_speed_bonus += UPGRADE_BULLET_SPEED_BONUS
        elif kind == "fire":
            self.fire_rate_bonus += FIRE_RATE_BONUS

    def _draw_game_over(self):
        self.screen.fill(MENU_BG_COLOR)
        title = self.title_font.render("Game Over", True, TEXT_COLOR)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 140))
        self.screen.blit(title, title_rect)

        score_text = self.ui_font.render(f"Score: {self.score}", True, TEXT_COLOR)
        high_text = self.ui_font.render(f"High score: {self.high_score}", True, TEXT_COLOR)
        hint_text = self.ui_font.render("Press R to retry or Enter for menu", True, TEXT_COLOR)

        self.screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, 230)))
        self.screen.blit(high_text, high_text.get_rect(center=(SCREEN_WIDTH // 2, 260)))
        self.screen.blit(hint_text, hint_text.get_rect(center=(SCREEN_WIDTH // 2, 320)))

    def _handle_player_hit(self):
        """Apply damage when a zombie touches the player."""
        player_screen = self.map.world_to_screen(self.player.pos)
        for zombie in self.zombies:
            zombie_screen = self.map.world_to_screen(zombie.pos)
            if zombie_screen.distance_to(player_screen) < zombie.radius + self.player.radius:
                self.player.take_damage(ZOMBIE_DAMAGE)
                if self.player.hp <= 0:
                    self.state = "menu"
                    self.zombies.clear()
                    self.bullets.clear()
                    self.player = Player((MAP_WIDTH / 2, MAP_HEIGHT / 2))
                    self._save_high_score()
                    self.state = "game_over"
                break
    
    def _spawn_powerup(self):
        kind = random.choice(["heal", "speed"])
        pos = (random.uniform(1, MAP_WIDTH - 2), random.uniform(1, MAP_HEIGHT - 2))
        self.powerups.append(PowerUp(pos, kind))

    def _handle_powerups(self):
        player_screen = self.map.world_to_screen(self.player.pos)
        for powerup in list(self.powerups):
            powerup_screen = self.map.world_to_screen(powerup.pos)
            if powerup_screen.distance_to(player_screen) < powerup.radius + self.player.radius:
                if powerup.kind == "heal":
                    self.player.hp = min(self.player.max_hp, self.player.hp + POWERUP_HEAL_AMOUNT)
                else:
                    self.speed_boost_timer = POWERUP_SPEED_DURATION
                self.powerups.remove(powerup)

    def _draw_hud(self):
        """Draw HP bar."""
        bar_w, bar_h = 200, 18
        x, y = 20, 20
        ratio = self.player.hp / self.player.max_hp
        fill_w = int(bar_w * ratio)
        pygame.draw.rect(self.screen, HP_BAR_BG, (x, y, bar_w, bar_h))
        pygame.draw.rect(self.screen, HP_BAR_FILL, (x, y, fill_w, bar_h))
        pygame.draw.rect(self.screen, HP_BAR_BORDER, (x, y, bar_w, bar_h), 2)
        hp_text = self.ui_font.render(
            f"HP: {self.player.hp}/{self.player.max_hp}", True, TEXT_COLOR
        )
        self.screen.blit(hp_text, (x, y + 22))

        score_text = self.ui_font.render(f"Score: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_text, (SCREEN_WIDTH - 20 - score_text.get_width(), 20))
        upgrade_text = self.ui_font.render(
            "Upgrades "
            f"{self.upgrade_points} | 1 HP:{self.upgrades['hp']} "
            f"2 SPD:{self.upgrades['speed']} 3 BUL:{self.upgrades['bullet']} "
            f"4 FIR:{self.upgrades['fire']}",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(upgrade_text, (40, 70))
    
    def _spawn_bullet(self):
        """Create a bullet in the aim direction."""
        direction = self.player.aim_dir
        if direction.length_squared() == 0:
            return
        spawn_pos = self.player.pos  # spawn from player center
        speed = BULLET_SPEED + self.bullet_speed_bonus
        self.bullets.append(Bullet(spawn_pos, direction, speed))

    def _spawn_zombie(self):
        """Spawn a zombie at random edge of the map"""
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            pos = (random.uniform(0, MAP_WIDTH - 1), 0)
        elif side == "bottom":
            pos = (random.uniform(0, MAP_WIDTH - 1), MAP_HEIGHT - 1)
        elif side == "left":
            pos = (0, random.uniform(0, MAP_HEIGHT - 1))
        else:
            pos = (MAP_WIDTH - 1, random.uniform(0, MAP_HEIGHT - 1))
        self.zombies_spawned += 1
        speed = ZOMBIE_SPEED * (1 + (self.zombies_spawned - 1) * ZOMBIE_SPEED_GROWTH)
        self.zombies.append(Zombie(pos, speed))

    def _handle_collisions(self):
        for bullet in list(self.bullets):
            bullet_screen = self.map.world_to_screen(bullet.pos)
            for zombie in list(self.zombies):
                zombie_screen = self.map.world_to_screen(zombie.pos)
                if bullet_screen.distance_to(zombie_screen) < bullet.radius + zombie.radius:
                    self.bullets.remove(bullet)
                    self.zombies.remove(zombie)
                    self.score += 1
                    if self.score >= self.next_upgrade_score:
                        self.upgrade_points += 1
                        self.next_upgrade_score += UPGRADE_SCORE_STEP
                    if self.score > self.high_score:
                        self.high_score = self.score
                    break

    def _reset_round(self):
        """Reset entities and score for a new run."""
        self.score = 0
        self.player = Player((MAP_WIDTH / 2, MAP_HEIGHT / 2))
        self.zombies.clear()
        self.bullets.clear()
        self.powerups.clear()
        self.zombies_spawned = 0
        self.spawn_timer = 0.0
        self.powerup_timer = 0.0
        self.speed_boost_timer = 0.0
        self.upgrade_points = 0
        self.next_upgrade_score = UPGRADE_SCORE_STEP
        self.upgrades = {"hp": 0, "speed": 0, "bullet": 0, "fire": 0}
        self.bullet_speed_bonus = 0.0
        self.fire_rate_bonus = 0.0
        self.fire_timer = 0.0
        self.hold_timer = 0.0

    def _load_high_score(self):
        """Load high score from disk (or create it)."""
        if not self.high_score_path.exists():
            self.high_score_path.write_text("0")
            return 0
        text = self.high_score_path.read_text().strip()
        return int(text) if text.isdigit() else 0

    def _save_high_score(self):
        """Save high score to disk."""
        self.high_score_path.write_text(str(self.high_score))

    def _update_camera(self):
        """Center camera on the player."""
        screen_center = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        focus = self.player.pos
        screen_x = (focus.x - focus.y) * (TILE_WIDTH / 2)
        screen_y = (focus.x + focus.y) * (TILE_HEIGHT / 2)
        self.map.origin = screen_center - pygame.Vector2(screen_x, screen_y)

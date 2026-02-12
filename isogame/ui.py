import pygame
from .settings import BUTTON_COLOR, BUTTON_TEXT_COLOR, MENU_BG_COLOR, TEXT_COLOR

class Menu:
    """Simple menu with start and quit buttons."""

    def __init__(self, screen_rect):
        """Prepare fonts and button layout."""
        self.title_font = pygame.font.Font(None, 64)
        self.button_font = pygame.font.Font(None, 36)
        self.layout(screen_rect)
    
    def layout(self, screen_rect):
        """position buttons based on the screen size."""
        center_x, center_y = screen_rect.center
        self.start_rect = pygame.Rect(0, 0, 220, 56)
        self.start_rect.center = (center_x, center_y)
        self.quit_rect = pygame.Rect(0, 0, 220, 56)
        self.quit_rect.center = (center_x, center_y + 80)

    def handle_event(self, event):
        """return "start" or "quit" when a button is clicked"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.start_rect.collidepoint(event.pos):
                return "start"
            if self.quit_rect.collidepoint(event.pos):
                return "quit"
        return None

    def draw(self, surface):
        """Draw the menu background, title, and buttons."""
        surface.fill(MENU_BG_COLOR)
        title = self.title_font.render("Isometric Zombie", True, TEXT_COLOR)
        title_rect = title.get_rect(center=(surface.get_width() // 2, 140))
        surface.blit(title, title_rect)
        self._draw_button(surface, self.start_rect, "Start")
        self._draw_button(surface, self.quit_rect, "Quit")

    def _draw_button(self, surface, rect, text):
        """Helper to draw a single button"""
        pygame.draw.rect(surface, BUTTON_COLOR, rect, border_radius=8)
        label = self.button_font.render(text, True, BUTTON_TEXT_COLOR)
        label_rect = label.get_rect(center=rect.center)
        surface.blit(label, label_rect)
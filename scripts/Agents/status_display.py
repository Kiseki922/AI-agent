import pygame

class NPCStatusDisplay:
    """
    A class to handle the display of NPC status information in the game window.
    This displays mood, health, and other statistics of NPCs.
    """
    
    def __init__(self, game):
        """
        Initialize the status display system.
        
        Args:
            game: The main game instance containing all game data
        """
        self.game = game
        
        # Display settings
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 32)
        self.colors = {
            "background": (30, 30, 50, 200),  # Dark blue with alpha
            "text": (255, 255, 255),          # White
            "title": (200, 200, 100),         # Gold-like
            "good": (100, 200, 100),          # Green
            "medium": (200, 200, 100),        # Yellow
            "bad": (200, 100, 100),           # Red
            "border": (100, 100, 150)         # Light blue
        }
        
        # Position and size
        screen_width, screen_height = game.screen.get_size()
        self.width = 200
        self.height = 150
        self.x = screen_width - self.width - 10
        self.y = 10
        self.padding = 10
        self.bar_height = 20
        
        # IMPORTANT: Start hidden by default
        self.visible = False
        
        # Status history
        self.status_history = []
        self.max_history_items = 3
    
    def toggle_visibility(self):
        """Toggle the visibility of the status display"""
        self.visible = not self.visible
    
    def show_when_near_npc(self):
        """Check if player is near NPC and show status accordingly"""
        # Only show status display when player is near NPC
        if hasattr(self.game, 'dialogue_system'):
            # Use the same check as the dialogue system for consistency
            self.visible = self.game.dialogue_system.is_player_near_agent()
    
    def add_status_message(self, message):
        """Add a status message to the history"""
        self.status_history.append(message)
        if len(self.status_history) > self.max_history_items:
            self.status_history.pop(0)
    
    def get_status_color(self, value):
        """Get the appropriate color for a status value"""
        if value > 70:
            return self.colors["good"]
        elif value > 30:
            return self.colors["medium"]
        else:
            return self.colors["bad"]
    
    def render(self):
        """Render the status display on the game screen"""
        # Check if player is near NPC and update visibility
        self.show_when_near_npc()
        
        if not self.visible:
            return
        
        # Get NPC status from AI bridge if available
        npc_status = self._get_npc_status()
        if not npc_status:
            return
        
        # Create a surface with alpha for the status box
        status_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        status_surface.fill(self.colors["background"])
        
        # Draw title
        title_text = self.title_font.render("NPC Status", True, self.colors["title"])
        title_rect = title_text.get_rect(centerx=self.width//2, top=self.padding)
        status_surface.blit(title_text, title_rect)
        
        # Draw separator line
        pygame.draw.line(status_surface, self.colors["border"], 
                         (self.padding, title_rect.bottom + 5), 
                         (self.width - self.padding, title_rect.bottom + 5), 2)
        
        # Draw status bars
        y_offset = title_rect.bottom + 15
        
        # Draw mood bar
        self._draw_status_bar(status_surface, "Mood", npc_status.get("mood", 0), y_offset)
        y_offset += self.bar_height + 5
        
        # Draw health bar
        self._draw_status_bar(status_surface, "Health", npc_status.get("health", 0), y_offset)
        y_offset += self.bar_height + 5
        
        # Draw status history
        y_offset += 10
        for msg in self.status_history:
            msg_surface = self.font.render(msg, True, self.colors["text"])
            status_surface.blit(msg_surface, (self.padding, y_offset))
            y_offset += 20
        
        # Draw the status surface on the game screen
        self.game.screen.blit(status_surface, (self.x, self.y))
        
        # Draw an "E to talk" prompt when near NPC
        prompt_text = self.font.render("Press E to talk", True, (255, 255, 255))
        prompt_rect = prompt_text.get_rect(center=(
            self.x + self.width // 2,
            self.y + self.height + 20
        ))
        self.game.screen.blit(prompt_text, prompt_rect)
    
    def _draw_status_bar(self, surface, label, value, y_pos):
        """Draw a status bar with label and value"""
        # Draw label
        label_surface = self.font.render(f"{label}:", True, self.colors["text"])
        surface.blit(label_surface, (self.padding, y_pos))
        
        # Draw background bar
        bar_width = self.width - self.padding * 2 - label_surface.get_width() - 5
        bar_x = self.padding + label_surface.get_width() + 5
        pygame.draw.rect(surface, (50, 50, 50), 
                         (bar_x, y_pos, bar_width, self.bar_height))
        
        # Draw value bar
        value_width = int(bar_width * (value / 100))
        color = self.get_status_color(value)
        pygame.draw.rect(surface, color, 
                         (bar_x, y_pos, value_width, self.bar_height))
        
        # Draw value text
        value_text = self.font.render(f"{value}", True, self.colors["text"])
        value_rect = value_text.get_rect(center=(bar_x + bar_width//2, y_pos + self.bar_height//2))
        surface.blit(value_text, value_rect)
    
    def _get_npc_status(self):
        """Get NPC status from the AI bridge"""
        if hasattr(self.game, 'ai_bridge') and self.game.ai_bridge and hasattr(self.game.ai_bridge, 'agent'):
            agent = self.game.ai_bridge.agent
            if hasattr(agent, 'profile'):
                return agent.profile.status
        return None
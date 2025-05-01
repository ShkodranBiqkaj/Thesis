import pygame

class PostGameMenu:
    """
    Post game menu initializer
    """
    def __init__(self, screen, clock, font=None):
        self.screen = screen
        self.clock = clock
        # Use provided font or default
        self.font = font or pygame.font.SysFont(None, 48)

    def show(self, won: bool) -> str:
        """
        Shows scren and waits until the player decides what to do
        """
        if won:
            title = "You Win!"
            options = [
                ("N: Next Level", 'next'),
                ("M: Main Menu",  'menu'),
                ("E: Exit Game",  'exit'),
            ]
        else:
            title = "You Lose!"
            options = [
                ("N: New Game",   'new'),
                ("M: Main Menu",  'menu'),
                ("E: Exit Game",  'exit'),
            ]

        while True:
            self.screen.fill((0, 0, 0))
            txt = self.font.render(title, True, (255, 255, 255))
            rect = txt.get_rect(center=(self.screen.get_width() // 2,
                                         self.screen.get_height() // 3))
            self.screen.blit(txt, rect)

            for i, (label, _) in enumerate(options):
                txt = self.font.render(label, True, (200, 200, 200))
                rect = txt.get_rect(center=(self.screen.get_width() // 2,
                                             self.screen.get_height() // 2 + i * 50))
                self.screen.blit(txt, rect)

            pygame.display.flip()
            self.clock.tick(30)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return 'exit'
                if e.type == pygame.KEYDOWN:
                    key = e.unicode.lower()
                    for label, code in options:
                        if key == label[0].lower():
                            return code
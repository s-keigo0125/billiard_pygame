import pygame

class Gamerule:
    def __init__(self, pockets):
        self.pockets = pockets
        self.game_over = False
        self.font = pygame.font.Font(None, 50)
    
    def update(self):
        for pocket in self.pockets:
            pocket.update()
            if pocket.cue_ball_fell:
                self.message = """Cue Ball Fell! Game Over!\nGame ends in 5 sec"""
                self.game_over = True
                return
            elif pocket.all_balls_fell_except_cue:
                self.message = """All Balls Fell! Good Job!\nGame ends in 5 sec"""
                self.game_over = True
                return

    def transmit_message(self):
        return self.message
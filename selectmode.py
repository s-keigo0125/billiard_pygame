# selectmode.py
import pygame

class Point_selectmode:
    """回転を能動的に与えるためのモードを示すクラス"""
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.ball_radius = 100
        self.ball_pos = (width // 2, height // 2)  # 円の中心
        self.is_active = False

    def draw(self):
        pygame.draw.rect(self.screen, pygame.Color("Blue"), (0, 0, self.width, self.height))
        pygame.draw.circle(self.screen, pygame.Color("black"), self.ball_pos, self.ball_radius, width=0)
        pygame.draw.circle(self.screen,pygame.Color("white"), self.ball_pos, 5, width=0)

        self.draw_label("top", (self.width // 2, self.ball_pos[1] - self.ball_radius - 20))
        self.draw_label("left", (self.ball_pos[0] - self.ball_radius - 30, self.height // 2))
        self.draw_label("right", (self.ball_pos[0] + self.ball_radius + 30, self.height // 2))
        self.draw_label("bottom", (self.width // 2, self.ball_pos[1] + self.ball_radius + 10))

    def draw_label(self, text, position):
        font = pygame.font.Font(None, 25)
        text_surface = font.render(text, True, pygame.Color("black"))
        text_rect = text_surface.get_rect(center=position)
        self.screen.blit(text_surface, text_rect)
    
    
    def update(self):
        pygame.display.update((0, 0, 200, 200))

    def get_surface(self):
        return self.screen

    def check_click_inside(self, mouse_pos):
        """クリック位置が円の中か判定する"""
        relative_pos = (mouse_pos[0] - self.ball_pos[0], mouse_pos[1] - self.ball_pos[1])
        distance_squared = relative_pos[0] ** 2 + relative_pos[1] ** 2
        return distance_squared <= self.ball_radius ** 2
    
    def give_moment_arm(self, mouse_pos):
        """打撃点を計算する"""
        moment_arm = ((mouse_pos[0] - self.ball_pos[0])* 0.028 /(100), -(mouse_pos[1] - self.ball_pos[1])*0.028 /(100))
        return moment_arm
    
    def exit(self):
        """選択モードを終了するメソッド"""
        self.is_active = False

def compute_conservation_of_momentum(force, mass, dt):
    """
    力、質量、時間変化量を元に速度変化を計算する関数。
    運動量保存則に基づく。
    """
    delta_p = force * dt
    delta_v = delta_p / mass
    return delta_v
import pygame
import billiard
import selectmode
import gamerule
import time
import sys

PgVector = pygame.math.Vector2

class ActorFactory:
    def __init__(self, world, actor_list):
        self.world = world
        self.actor_list = actor_list

    def create_boundary(self, name):
        width, height = self.world.size
        geometry = {"top": ((0, -1), (150, 75)),
                    "bottom": ((0, 1), (150, height-80)),
                    "left": ((-1, 0), (150, 75)),
                    "right": ((1, 0), (width-150, 75))}
        normal, point_included = geometry[name]
        return billiard.Boundary(normal, point_included, self.world, self.actor_list)
    
    def create_collision_resolver(self):
        return billiard.CollisionResolver(self.world, self.actor_list)
    
    def create_pockets(self):
        pocket_data = [
            {"centerpos": (1100, 575), "radius": 100},  # 右下
            {"centerpos": (100, 575), "radius": 100},   # 左下
            {"centerpos": (1100, 25), "radius": 100},   # 右上
            {"centerpos": (100, 25), "radius": 100},    # 左上
            {"centerpos": (602, 15), "radius": 75},    # 中央上
            {"centerpos": (602, 585), "radius": 75},   # 中央下
        ]
        pockets = []
        for data in pocket_data:
            pocket = billiard.Pocket(
                self.world,
                data["centerpos"],
                data["radius"],
                self.actor_list
            )
            pockets.append(pocket)
        return pockets

class AppMain:
    def __init__(self):
        pygame.init()
        width, height = 1200, 600
        self.screen = pygame.display.set_mode((width, height))
        self.ball_num = 9
        self.mouse_button_pressed = False
        self.space_key_pressed = False
        self.can_accept_click = True
        self.can_move_ball = False
        self.total_score = 0

        self.world = billiard.World((width, height), 0.005, 0.2, (9.81, 9.81))
        self.image = pygame.image.load("images/design.png").convert_alpha()
        self.actor_list = []

        mainmass = billiard.Numbermass(0, pygame.Color("Black"), 0.028, (300, 300), self.world)
        self.actor_list.append(mainmass)

        num = 1
        radius = 0.028
        for n in range(1, 5):
            for k in range(1, n + 1):
                pos = 600 + 20 * n, 320 + 20 * n - 40 * k
                color = pygame.Color("white")
                self.actor_list.append(billiard.Numbermass(num, color, radius, pos, self.world))
                num += 1

        self.factory = ActorFactory(self.world, self.actor_list)
        self.actor_list.append(self.factory.create_collision_resolver())
        self.actor_list.append(self.factory.create_boundary("top"))
        self.actor_list.append(self.factory.create_boundary("bottom"))
        self.actor_list.append(self.factory.create_boundary("left"))
        self.actor_list.append(self.factory.create_boundary("right"))
        pocket_list = self.factory.create_pockets()
        for n in range(len(pocket_list)):
            self.actor_list.append(pocket_list[n])

        self.select_mode = selectmode.Point_selectmode(self.screen, 300, 300)
        self.game_rule = gamerule.Gamerule(pocket_list)
        self.contact_point = None
        self.force = PgVector(0, 0)

    def give_force_by_user(self, start_pos, end_pos):
        """ビリヤードの玉をついたと同じ動作をするメソッド"""
        force_magnitude = 50 + (PgVector(end_pos)-PgVector(start_pos)).magnitude() /7.5
        direction = PgVector(end_pos) - PgVector(start_pos)
        direction = direction.normalize()  # 方向のみを取得
        self.force = -direction * force_magnitude
        self.select_mode.is_active = True

    def apply_force(self, contact_point):
        """選択モードで取得したコンタクトポイントを使用して力を加える"""
        vel = selectmode.compute_conservation_of_momentum(self.force, self.actor_list[0].mass, self.world.dt)
        self.actor_list[0].vel = PgVector(vel[0], vel[1])
        self.actor_list[0].receive_force(self.force, contact_point)

        self.contact_point = None
        self.force = PgVector(0, 0)

    def are_balls_stopped(self):
        """すべてのボールが停止しているかを確認するメソッド"""
        for actor in self.actor_list:
            if isinstance(actor, billiard.Numbermass) and actor.vel_real.magnitude() > 0.1:
                return False
        return True
    
    def draw_score(self,actor_list):
        self.total_score = sum(a.score for a in actor_list if billiard.is_pocket(a))
        font = pygame.font.Font(None, 36)
        score_text = f"Total Score: {self.total_score}"
        text_surface = font.render(score_text, True, pygame.Color("White"))
        self.screen.blit(text_surface, (200, 10))

    def end_game(self):
        text = self.game_rule.transmit_message()
        font = pygame.font.Font(None, 60)
        lines = text.split('\n')  # 改行で分割して行リストを作成
        n = 0
        for line in lines: 
            text_surface = font.render(line, True, pygame.Color("black"))
            text_rect = text_surface.get_rect(center=(600, 300 + n * 50))
            self.screen.blit(text_surface, text_rect)
            n+= 1
            
    def update(self):
        self.can_accept_click = self.are_balls_stopped()
        for a in self.actor_list:
            a.update()
        self.game_rule.update()
        
    def draw(self, mouse_pos, start_pos=(0, 0)):
        self.screen.fill((0, 0, 0))
        image_width, image_height = self.image.get_width(), self.image.get_height()
        screen_center = (self.screen.get_width() // 2, self.screen.get_height() // 2)
        image_position = (screen_center[0] - image_width // 2, screen_center[1] - image_height // 2)
        self.screen.blit(self.image, image_position)
        self.draw_score(self.actor_list)
        for a in self.actor_list:
            a.draw(self.screen)
        if self.mouse_button_pressed and start_pos:
            direction = PgVector(mouse_pos) - PgVector(start_pos)
            pygame.draw.line(self.screen, pygame.Color("blue"), self.actor_list[0].pos_draw, self.actor_list[0].pos_draw - direction, 3)
        pygame.display.update()

    def run(self):
        clock = pygame.time.Clock()
        start_pos = None
        self.select_mode.is_active = False
        while True:
            frames_per_second = 60
            clock.tick(frames_per_second)
            mouse_pos = pygame.mouse.get_pos()

            should_quit = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    should_quit = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        should_quit = True
                    elif event.key == pygame.K_SPACE:
                        self.space_key_pressed = True
                        self.mouse_button_pressed = False
                        start_pos = None
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        self.space_key_pressed = False

                if self.select_mode.is_active:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        click_pos = event.pos
                        if self.select_mode.check_click_inside(click_pos):
                            self.contact_point = self.select_mode.give_moment_arm(click_pos)
                            self.select_mode.is_active = False
                            self.apply_force(self.contact_point)
                    continue 

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.can_accept_click or self.space_key_pressed:
                        start_pos = event.pos
                        self.mouse_button_pressed = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.can_accept_click or self.space_key_pressed:
                        self.mouse_button_pressed = False
                        if start_pos:
                            if start_pos == event.pos:
                                continue
                            self.give_force_by_user(start_pos, event.pos)

            if should_quit:
                break
            
            if self.select_mode.is_active:
                self.select_mode.draw()
                pygame.display.update((0, 0, self.select_mode.width, self.select_mode.height))
            else:
                self.update()
                self.draw(mouse_pos, start_pos if start_pos else (0, 0))

            if self.game_rule.game_over:
                self.end_game()
                pygame.display.update()
                time.sleep(5)
                pygame.quit()
                sys.exit()

        pygame.quit()


if __name__ == "__main__":
    AppMain().run()
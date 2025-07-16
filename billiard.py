import pygame
from pygame.math import Vector2 as PgVector

class World:
    def __init__(self, size, dt, friction, grav_acc):
        self.size = size
        self.dt = dt
        self.friction = friction
        self.grav_acc = PgVector(grav_acc)

class CircleDrawer:
    def __init__(self, color, width, height):
        self.color = pygame.Color(color)
        self.width = width
        self.height = height

    def __call__(self, screen, center, radius):
        pygame.draw.circle(screen, self.color, center, radius)

def integrate_symplectic(pos, vel, force, mass, dt):
    """単位時間ごとに速度と位置を計算する関数"""
    vel_new = (vel + force / mass * dt)
    pos_new = pos + vel_new * dt
    return pos_new, vel_new

def compute_friction(friction, grav_acc, mass, vel):
    """摩擦力を計算する関数"""
    if vel.magnitude() > 0:
        direction = -vel.normalize()
        force_magnitude = mass * grav_acc.magnitude() * friction
        return direction * force_magnitude
    return PgVector(0, 0)

class Numbermass:
    """ビリヤードの玉を表すクラス"""
    def __init__(self, number, color, radius, pos_draw, world, restitution=0.9, mass=0.17, static_friction=0.2, angular_damping=0.98):
        self.number = number
        self.color = pygame.Color(color)
        self.radius = radius
        self.pos_draw = PgVector(pos_draw)
        self.drawer = CircleDrawer(color, 0, 0)
        self.total_force = PgVector((0, 0))
        self.restitution = restitution
        self.mass = mass
        self.static_friction = static_friction
        self.dynamic_friction = static_friction - 0.05
        self.world = world
        self.font = pygame.font.Font(None, 30)
        self.text_surface = self.font.render(f"{self.number}", True, pygame.Color("Black"))
        self.radius_for_draw = 14
        self.pos_real = self.pos_draw / 350
        self.vel_real = PgVector((0, 0))

        self.total_force = PgVector((0, 0))
        self.message_list = []
        self.grav_acc = self.world.grav_acc
        self.friction = self.world.friction

        self.angle = 0  # 回転角度
        self.angular_velocity = 0  # 角速度
        self.angular_acceleration = 0  # 角加速度
        self.moment_of_inertia = (2 / 5) * self.mass * (self.radius ** 2)  # 慣性モーメント
        self.angular_damping = angular_damping  # 角速度の減衰係数

    def draw(self, screen):
        # 回転を考慮して玉を描画
        pygame.draw.circle(screen,pygame.Color(self.color),(int(self.pos_draw.x),int(self.pos_draw.y)),self.radius_for_draw,0)
        rotated_text_surface = pygame.transform.rotate(self.text_surface, self.angle)
        text_rect = rotated_text_surface.get_rect(center=(int(self.pos_draw.x), int(self.pos_draw.y)))
        screen.blit(rotated_text_surface, text_rect.topleft)

    def update(self):
        self.generate_force()
        self.move()
        self.convert_pos()
        if self.vel_real.magnitude() < 1e-2 and self.angular_velocity < 10:  # 球が止まらないと困るので、速度が小さい場合にゼロにする
            self.vel_real = PgVector(0, 0)
            self.angular_velocity = 0
        self.total_force = PgVector((0, 0))
        self.angular_acceleration = 0
        self.message_list.clear()

    def receive_force(self, force, contact_point=None):
        self.total_force += PgVector(force)
        if contact_point:
            # 打撃点が与えられた場合、トルクも計算
            torque = force.magnitude() * contact_point[0]
            self.angular_acceleration += torque / self.moment_of_inertia

    def receive_force_while_moving(self, force,compare_value,relative_angular_vel):
        """
        手玉がキューで突かれてから、全てが停止するまで、衝突の際に用いるメソッド
        """
        self.total_force += PgVector(force)
        friction_f_length = 5*self.mass*self.radius*abs(relative_angular_vel)/(7*(1-self.restitution)*self.world.dt) * (3.14/180)
        #補正で2.5をかけてる
        torque = -friction_f_length * self.radius * compare_value
        self.angular_acceleration += torque / self.moment_of_inertia
        if not friction_f_length < 2.5:
            perpendicular_impact_force = force.rotate(90)
            unit_vector = perpendicular_impact_force.normalize()
            fric_f = unit_vector * friction_f_length * compare_value
            self.total_force -= PgVector(fric_f)

    def receive_message(self, msg):
        self.message_list.append(msg)

    def generate_force(self):
        force_fric = compute_friction(self.friction, self.grav_acc, self.mass, self.vel_real)
        self.receive_force(force_fric)

    def move(self):
        self.pos_real, self.vel_real = integrate_symplectic(self.pos_real, self.vel_real, self.total_force, self.mass, self.world.dt)
        self.angular_velocity += self.angular_acceleration * self.world.dt
        self.angular_velocity *= self.angular_damping  # 角速度の減衰
        self.angle += self.angular_velocity * self.world.dt *180/3.14
        self.angle %= 360

        for msg in self.message_list:
            if msg["type"] == "floor_hit" and self.vel_real.y > 0:
                self.pos_real.y = msg["y"] - self.radius / 350
                self.vel_real.y *= -self.restitution
            elif msg["type"] == "right_boundary_hit" and self.vel_real.x > 0:
                self.pos_real.x = msg["x"] - self.radius / 350
                self.vel_real.x *= -self.restitution
            elif msg["type"] == "left_boundary_hit" and self.vel_real.x < 0:
                self.pos_real.x = msg["x"] + self.radius / 350
                self.vel_real.x *= -self.restitution
            elif msg["type"] == "top_boundary_hit" and self.vel_real.y < 0:
                self.pos_real.y = msg["y"] + self.radius / 350
                self.vel_real.y *= -self.restitution

    def convert_pos(self):
        self.pos_draw = self.pos_real * 350

def compute_impact_force_between_points(p1, p2, dt):
    distance = (p1.pos_draw - p2.pos_draw).magnitude()  # ピクセル座標系での距離を計算
    if distance > p1.radius_for_draw + p2.radius_for_draw:
        return None
    if distance == 0:
        return None
    normal = (p2.pos_draw - p1.pos_draw).normalize()
    v1 = p1.vel_real.dot(normal)
    v2 = p2.vel_real.dot(normal)
    if v1 < v2:
        return None
    e = p1.restitution * p2.restitution
    m1, m2 = p1.mass, p2.mass
    f1 = normal * (-(e + 1) * v1 + (e + 1) * v2) / (1 / m1 + 1 / m2) / dt
    return f1

def compute_impact_force_by_fixture(p, normal, point_included, dt):
    invasion = normal.dot(p.pos_draw - point_included )
    if invasion + p.radius_for_draw > 0 and normal.dot(p.vel_real) > 0:
        e = p.restitution
        v = normal.dot(p.vel_real)
        m = p.mass
        f = normal * (-(e + 1) * v) * m / dt
    else:
        f = None
    return f

def is_number_mass(actor):
    return isinstance(actor, Numbermass)

class CollisionResolver:
    def __init__(self, world, actor_list, target_condition=None, drawer=None):
        self.is_alive = True
        self.world = world
        self.drawer = drawer or (lambda surface: None)

        self.actor_list = actor_list
        if target_condition is None:
            self.target_condition = is_number_mass
        else:
            self.target_condition = target_condition

    def update(self):
        self.generate_force_points()

    def draw(self, surface):
        self.drawer(surface)

    def generate_force_points(self):
        """2質点間の衝突による力を与えるメソッド"""
        plist = [a for a in self.actor_list if self.target_condition(a)]
        n = len(plist)
        for i in range(n):
            for j in range(i + 1, n):
                p1, p2 = plist[i], plist[j]
                f1 = compute_impact_force_between_points(p1, p2, self.world.dt)
                if f1 is None:
                    continue
                relative_angular_vel = p1.angular_velocity - p2.angular_velocity
                p1.receive_force_while_moving(f1,compare_angularvelocity(p1,p2),relative_angular_vel)
                p2.receive_force_while_moving(-f1,compare_angularvelocity(p1,p2),relative_angular_vel)

def compare_angularvelocity(p1,p2):
    if p1.angular_velocity > p2.angular_velocity:
        return 1
    else:
        return -1

class Boundary:
    def __init__(self, normal, point_included, world, actor_list,
                 target_condition=None, drawer=None):
        self.is_alive = True
        self.world = world
        self.drawer = drawer or (lambda surface: None)
        self.normal = PgVector(normal).normalize()
        self.point_included = PgVector(point_included)
        self.actor_list = actor_list
        if target_condition is None:
            self.target_condition = is_number_mass
        else:
            self.target_condition = target_condition

    def update(self):
        self.generate_force()

    def draw(self, surface):
        self.drawer(surface)

    def is_floor(self):
        return self.normal == PgVector((0, 1))

    def is_right_boundary(self):
        return self.normal == PgVector((1, 0))

    def is_left_boundary(self):
        return self.normal == PgVector((-1, 0))

    def is_top(self):
        return self.normal == PgVector((0, -1))

    def generate_force(self):
        """壁と球の衝突による力を計算するメソッド。同時にめり込みが起こらないようにする処理も行う。"""
        plist = [a for a in self.actor_list if self.target_condition(a)]
        for p in plist:
            if 570 <= self.point_included.x <= 630:
                continue
            f = compute_impact_force_by_fixture(p, self.normal, self.point_included, self.world.dt)
            if f is None:
                continue
            p.receive_force(f)
            if self.is_floor() and p.vel_real.y > 0:
                p.receive_message({"type": "floor_hit", "y": self.point_included.y})
            elif self.is_right_boundary() and p.vel_real.x > 0:
                p.receive_message({"type": "right_boundary_hit", "x": self.point_included.x})
            elif self.is_left_boundary() and p.vel_real.x < 0:
                p.receive_message({"type": "left_boundary_hit", "x": self.point_included.x})
            elif self.is_top() and p.vel_real.y <0:
                p.receive_message({"type": "top_boundary_hit", "y": self.point_included.y})

class Pocket:
    def __init__(self, world, centerpos, radius, actor_list, target_condition=None, drawer=None):
        self.world = world
        self.drawer = drawer or (lambda surface: None)
        self.centerpos = PgVector(centerpos)
        self.radius = radius
        self.actor_list = actor_list
        if target_condition is None:
            self.target_condition = is_number_mass
        else:
            self.target_condition = target_condition

        self.score = 0
        self.cue_ball_fell = False
        self.all_balls_fell_except_cue = False

    def draw(self, surface):
        self.drawer(surface)

    def update(self):
        for actor in self.actor_list[:]:
            if self.target_condition(actor):
                # ピクセル座標系での落下判定
                distance = (actor.pos_draw - self.centerpos).magnitude()
                if distance < self.radius:
                    self.drop_the_ball(actor)

    def drop_the_ball(self,actor):
        """ボールがポケットに落下するメソッド
        このメソッド内で各ポケットにスコアを帰属させる
        ゲームの終了条件のフラグの管理も行う
        if条件: 手玉の落下
        elif条件: 全ての球(手玉除く)の落下
        else条件: ゲームは終了しない"""

        index = self.actor_list.index(actor)
        if index == 0:
            self.cue_ball_fell = True
        elif is_number_mass(self.actor_list[index +1]) == False and index ==1 :
            self.score += actor.number
            self.all_balls_fell_except_cue = True
        else:
            self.score += actor.number
        self.actor_list.remove(actor)

def is_pocket(actor):
    """スコア計算に用いるための関数。pocketクラスのみを参照"""
    return isinstance(actor, Pocket)
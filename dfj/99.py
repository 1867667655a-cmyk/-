import pygame
import sys
import random
import math
import matplotlib.pyplot as plt
# 初始化 Pygame
pygame.init()
plt.rcParams['font.sans-serif'] = ['Heiti TC']  # 或 ['Microsoft YaHei'] 微软雅黑 等
plt.rcParams['axes.unicode_minus'] = False   

# 获取当前显示器分辨率，设置为全屏
infoObject = pygame.display.Info()
SCREEN_WIDTH = infoObject.current_w
SCREEN_HEIGHT = infoObject.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("史上最帅boss战")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
DARK_GREY = (50, 50, 50)
LIGHT_BLUE = (100, 100, 255)
PURPLE = (128, 0, 128)  # 紫色
CYAN = (0, 255, 255)  # 蓝绿色
ORANGE = (255, 165, 0)  # 橙色
GOLD = (255, 215, 0)  # 金色
DARK_RED = (139, 0, 0)
MINIBOSS_COLOR = (150, 0, 150)  # 紫色 2
MINIBOSS_CIRCLE_COLOR = (255, 0, 255)  # 修正为正确的元组
SELF_DESTRUCT_COLOR = (255, 50, 50)  # 没那么鲜艳的红色
ULTIMATE_COLOR = (255, 255, 255)  # 代表毁灭和美丽

# 游戏帧率
FPS = 60
clock = pygame.time.Clock() # 修正：这里需要加上括号来实例化 Clock 对象

# 缩放因子
SCALE_FACTOR = 0.65

# 屏幕抖动类
class ScreenShake:
    def __init__(self):
        self.shaking = False  # 是否正在抖动
        self.duration = 0  # 抖动持续时间 (帧数)
        self.intensity = 0  # 抖动强度 (像素偏移量)
        self.offset_x = 0  # X 轴偏移量
        self.offset_y = 0  # Y 轴偏移量

    def start(self, duration, intensity):
        self.shaking = True
        self.duration = duration
        self.intensity = intensity

    def update(self):
        if self.shaking:
            self.duration -= 1
            if self.duration <= 0:
                self.shaking = False
                self.offset_x = 0
                self.offset_y = 0
            else:
                self.offset_x = random.randint(-self.intensity, self.intensity)
                self.offset_y = random.randint(-self.intensity, self.intensity)
        return self.offset_x, self.offset_y

# 全局屏幕抖动实例
screen_shake = ScreenShake()

# 玩家飞机类
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((SCREEN_WIDTH * 0.04 * SCALE_FACTOR, SCREEN_HEIGHT * 0.05 * SCALE_FACTOR))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - SCREEN_HEIGHT * 0.05
        self.speed = SCREEN_WIDTH * 0.007 * SCALE_FACTOR  # 玩家移动速度
        self.health = 1000000 # 玩家生命值 (调试用，实际可调低)

        self.shoot_cooldown = 10  # 射击冷却时间 (帧数) - 暂时保留，实际由 auto_fire_interval 控制
        self.last_shot_time = pygame.time.get_ticks()  # 上次射击时间
        self.auto_fire_interval = 300  # 自动射击间隔 (毫秒) - 0.3 秒一发
        self.is_shooting = False  # 是否正在按住射击键

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]: self.rect.x += self.speed
        if keys[pygame.K_UP]: self.rect.y -= self.speed
        if keys[pygame.K_DOWN]: self.rect.y += self.speed

        # 屏幕循环移动
        if self.rect.right < 0: self.rect.left = SCREEN_WIDTH
        elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0
        if self.rect.bottom < 0: self.rect.top = SCREEN_HEIGHT
        elif self.rect.top > SCREEN_HEIGHT: self.rect.bottom = 0

        # 自动射击逻辑
        if self.is_shooting:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_shot_time > self.auto_fire_interval:
                self.shoot()
                self.last_shot_time = current_time

    def shoot(self):
        bullet = PlayerBullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        player_bullets.add(bullet)

# 子弹类
class PlayerBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((SCREEN_WIDTH * 0.007 * SCALE_FACTOR, SCREEN_HEIGHT * 0.025 * SCALE_FACTOR))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = -SCREEN_HEIGHT * 0.02 * SCALE_FACTOR  # 子弹速度
        self.teleport_count = 0  # 子弹屏幕循环次数
        self.is_gathering_for_ultimate = False # 新增标志，是否被大招吸附

    def update(self):
        if self.is_gathering_for_ultimate:
            dx = boss.ultimate_center_x - self.rect.centerx
            dy = boss.ultimate_center_y - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 2:  # 调整阈值，降低到 2 像素确保更早销毁
                max_dist_from_center = math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT)
                normalized_dist = dist / max_dist_from_center
                min_gather_speed = SCREEN_HEIGHT * 0.005 * SCALE_FACTOR
                max_gather_speed = SCREEN_HEIGHT * 0.02 * SCALE_FACTOR
                current_gather_speed = min_gather_speed + (max_gather_speed - min_gather_speed) * (1 - normalized_dist)
                self.rect.x += (dx / dist) * current_gather_speed if dist != 0 else 0
                self.rect.y += (dy / dist) * current_gather_speed if dist != 0 else 0
            else:
                self.kill()  # 聚集到中心后立即销毁
            return

        self.rect.y += self.speed
        # 子弹屏幕循环4 次后消失
        if self.teleport_count < 4:
            if self.rect.bottom < 0: self.rect.top = SCREEN_HEIGHT; self.teleport_count += 1
            elif self.rect.top > SCREEN_HEIGHT: self.rect.bottom = 0; self.teleport_count += 1
            if self.rect.right < 0: self.rect.left = SCREEN_WIDTH; self.teleport_count += 1
            elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0; self.teleport_count += 1
        else:
            if not screen.get_rect().colliderect(self.rect): self.kill()

# Boss飞机类
class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.Surface((SCREEN_WIDTH * 0.12 * SCALE_FACTOR, SCREEN_HEIGHT * 0.125 * SCALE_FACTOR), pygame.SRCALPHA)
        self.original_image.fill((0, 0, 0, 0))
        self.rect = self.original_image.get_rect()
        self.draw_boss_shape(self.original_image, DARK_GREY, LIGHT_BLUE)
        self.image = self.original_image.copy()

        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.top = SCREEN_HEIGHT * 0.05
        self.speed_x = SCREEN_WIDTH * 0.0025 * SCALE_FACTOR  # Boss X 轴移动速度
        self.speed_y = SCREEN_HEIGHT * 0.00125 * SCALE_FACTOR  # Boss Y 轴移动速度
        self.max_health = 1000  # 最大生命
        self.health = self.max_health  # Boss 生命值
        self.attack_timer = 0  # 攻击计时器
        self.attack_cooldown = 60  # 攻击冷却时间 (帧数)

        self.is_circling = False  # 是否正在缠绕
        self.circle_radius = SCREEN_WIDTH * 0.15 * SCALE_FACTOR  # 缠绕半径
        self.circle_angle = 0  # 缠绕角度
        self.circle_speed = 0.08  # 缠绕速度 (弧度/帧)
        self.circle_duration = 60 * 5  # 缠绕持续时间 (帧数)
        self.circle_timer = 0  # 缠绕计时器
        self.circle_cooldown = 60 * 10  # 缠绕冷却时间
        self.last_circle_time = pygame.time.get_ticks()  # 上次缠绕时间
        self.circle_bullet_interval = 15  # 缠绕时子弹发射间隔
        self.circle_approach_speed = SCREEN_WIDTH * 0.01  # 缠绕接近速度
        self.is_approaching_for_circle = False  # 是否正在接近玩家以进行缠绕

        self.summon_cooldown = 60 * 15  # 召唤小 Boss 冷却时间
        self.last_summon_time = pygame.time.get_ticks() - self.summon_cooldown # 上次召唤时间
        self.max_minibosses = 4  # 最大小 Boss 数量

        self.patrol_min_y = SCREEN_HEIGHT * 0.05  # 巡逻区域 Y 轴最小值
        self.patrol_max_y = SCREEN_HEIGHT * 0.3  # 巡逻区域 Y 轴最大值
        self.patrol_min_x = SCREEN_WIDTH * 0.05  # 巡逻区域 X轴最小值
        self.patrol_max_x = SCREEN_WIDTH * 0.95 - self.rect.width  # 巡逻区域 X 轴最大值
        self.attack_sequence = ["normal", "tracking", "fast"]  # 攻击序列类型
        self.current_attack_index = 0  # 当前攻击序列索引
        self.bullets_per_burst = 3  # 每次攻击发射子弹数量
        self.bullets_fired_in_burst = 0  # 当前爆发已发射子弹数量
        self.burst_cooldown = 20  # 爆发内子弹间隔
        self.next_burst_time = pygame.time.get_ticks()  # 下次爆发时间

        self.is_super_dashing = False  # 是否正在超级冲刺
        self.super_dash_vel_x = 0  # 超级冲刺 X 轴速度
        self.super_dash_vel_y = 0  # 超级冲刺 Y 轴速度
        self.super_dash_speed = SCREEN_WIDTH * 0.02 * SCALE_FACTOR  # 超级冲刺速度
        self.super_dash_duration = 60 * 10  # 超级冲刺持续时间 (帧数)
        self.super_dash_timer = 0  # 超级冲刺计时器
        self.super_dash_cooldown = 60 * 20  # 超级冲刺冷却时间 (增加冷却时间，降低频率)
        self.last_super_dash_time = pygame.time.get_ticks()  # 上次超级冲刺时间
        self.super_dash_charge_time = 60 * 2 # 超级冲刺蓄力时间 (帧数)
        self.super_dash_charge_timer = 0  # 超级冲刺蓄力计时器
        self.super_dash_threshold = self.max_health * 0.75  # 触发超级冲刺的生命值阈值 (3/4 血)

        self.is_gathering_minibosses = False  # 是否正在集结小 Boss
        self.miniboss_gathering_radius = SCREEN_WIDTH * 0.15 * SCALE_FACTOR  # 小 Boss 集结半径
        self.miniboss_gathering_speed = SCREEN_WIDTH * 0.015 * SCALE_FACTOR  # 小 Boss 集结速度
        self.miniboss_gathering_cooldown = 60 * 15  # 小 Boss 集结冷却时间
        self.last_miniboss_gathering_time = pygame.time.get_ticks()  # 上次小 Boss 集结时间
        self.miniboss_gathered_and_waiting = False  # 小 Boss 是否已集结并等待

        # 大绝招相关变量
        self.ultimate_threshold = self.max_health / 6  # 大招血量触发阈值
        self.has_triggered_ultimate = False  # 确保大招只触发一次
        self.ultimate_center_x = SCREEN_WIDTH // 2  # 大招中心 X
        self.ultimate_center_y = SCREEN_HEIGHT // 2 # 大招中心 Y
        self.ultimate_boss_target_y = SCREEN_HEIGHT * 0.2  # Boss 在大招阵型中的 Y 坐标
        self.ultimate_miniboss_radius = SCREEN_WIDTH * 0.25 * SCALE_FACTOR  # 小 Boss 围绕 Boss 的半径
        self.ultimate_gather_speed = SCREEN_WIDTH * 0.01  # Boss 和小 Boss 向中心聚集的速度
        self.ultimate_charge_duration = 60 * 4  # 大招蓄力时间 (4 秒)
        self.ultimate_charge_timer = 0  # 大招蓄力计时器
        self.ultimate_bullet_speed = SCREEN_HEIGHT * 0.005 * SCALE_FACTOR  # 巨弹的速度，降低速度
        self.ultimate_giant_bullet = None  # 用于存储凝聚的巨型子弹实例
        self.all_bullets_gathered = False  # 新增：子弹是否已聚集完毕
        self.gather_timeout = 60 * 3  # 聚集超时时间 (3 秒)，防止无限等待

        self.target_x = self.rect.centerx  # 巡逻目标 X 坐标
        self.target_y = self.rect.centery  # 巡逻目标 Y 坐标
        self.set_new_patrol_target()  # 设置新的巡逻目标

        # 技能状态机
        self.current_skill = "patrol"  # "patrol", "approach_circle", "circling", "super_dash_charge", "super_dash", "summon", "gathering", "ultimate_charge", "ultimate_fire"
        self.skill_cooldowns = {
            "circle": self.circle_cooldown,
            "super_dash": self.super_dash_cooldown,
            "summon": self.summon_cooldown
        }
        self.last_skill_times = {
            "circle": pygame.time.get_ticks(),
            "super_dash": pygame.time.get_ticks(),
            "summon": pygame.time.get_ticks()
        }

    def set_new_patrol_target(self):
        self.target_x = random.uniform(self.patrol_min_x, self.patrol_max_x)
        self.target_y = random.uniform(self.patrol_min_y, self.patrol_max_y)

    def draw_boss_shape(self, surface, body_color, engine_color):
        surface.fill((0, 0, 0, 0))
        pygame.draw.polygon(surface, body_color, [
            (surface.get_width() // 2, 0),
            (surface.get_width(), surface.get_height() * 0.3),
            (surface.get_width() * 0.8, surface.get_height()),
            (surface.get_width() * 0.2, surface.get_height()),
            (0, surface.get_height() * 0.3)
        ])
        pygame.draw.rect(surface, engine_color, (surface.get_width() * 0.25, surface.get_height() * 0.9, surface.get_width() * 0.15, surface.get_height() * 0.1))
        pygame.draw.rect(surface, engine_color, (surface.get_width() * 0.6, surface.get_height() * 0.9, surface.get_width() * 0.15, surface.get_height() * 0.1))

    def update(self):
        current_time = pygame.time.get_ticks()

        # 大绝招触发条件判断 (最高优先级)
        if self.current_skill == "ultimate_charge":
            self.ultimate_charge_update()
            return
        elif self.current_skill == "ultimate_fire":
            self.ultimate_fire_update()
            return
        
        # 只有在大招未触发且未进行中的情况下，才判断是否触发大招
        if self.health <= self.ultimate_threshold and not self.has_triggered_ultimate:
            self.start_ultimate_charge()
            self.has_triggered_ultimate = True  # 标记已触发
            return  # 立即进入大招状态

        # 其他技能更新
        if self.current_skill == "super_dash_charge":
            self.super_dash_charge_update()
            return
        elif self.current_skill == "super_dash":
            self.super_dash_update()
            return
        elif self.current_skill == "circling":
            self.circle_update()
            return
        elif self.current_skill == "approach_circle":
            self.approach_for_circle_update()
            return
        elif self.current_skill == "gathering":
            self.gathering_minibosses_update()
            return

        # 如果当前没有在执行任何特殊技能，则执行巡逻和选择技能
        else:  # "patrol" 或 "miniboss_waiting" 状态
            if not self.miniboss_gathered_and_waiting:  # 如果小 Boss 集结并等待，Boss 正常巡逻
                dx = self.target_x - self.rect.centerx
                dy = self.target_y - self.rect.centery
                dist = math.hypot(dx, dy)

                if dist > self.speed_x:
                    self.rect.x += (dx / dist) * self.speed_x if dist != 0 else 0
                    self.rect.y += (dy / dist) * self.speed_y if dist != 0 else 0
                else:
                    self.rect.centerx = self.target_x
                    self.rect.centery = self.target_y
                    self.set_new_patrol_target()

                teleported = False
                if self.rect.right < 0: self.rect.left = SCREEN_WIDTH; teleported = True
                elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0; teleported = True
                if self.rect.bottom < 0: self.rect.top = SCREEN_HEIGHT; teleported = True
                elif self.rect.top > SCREEN_HEIGHT: self.rect.bottom = 0; teleported = True

                if teleported: self.face_player_at_teleport()

            if current_time >= self.next_burst_time: self.perform_attack_sequence()

            self.attack_timer += 1
            if self.attack_timer >= self.attack_cooldown:
                self.choose_special_attack()
                self.attack_timer = 0

        # 面朝玩家的逻辑，只在非特殊移动状态执行
        if self.current_skill not in ["super_dash", "super_dash_charge", "gathering", "approach_circle", "ultimate_charge", "ultimate_fire"]:
            self.face_player()

    def face_player(self):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        angle = math.degrees(math.atan2(-dy, dx))
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def face_player_at_teleport(self):
        self.image = self.original_image.copy()
        self.face_player()

    def choose_special_attack(self):
        current_time = pygame.time.get_ticks()

        # 技能触发优先级调整：
        # 1. 末日审判 (最高优先级，已在 update 中处理)
        # 2. 召唤小 Boss (如果小 Boss 数量不足且冷却时间结束，且半血以下)
        # 3. 超级冲刺 (血量低时优先，但要考虑召唤的优先级)
        # 4. 缠绕 (如果冷却结束)

        # 尝试触发召唤小 Boss
        if len(minibosses) < self.max_minibosses and \
           current_time - self.last_skill_times["summon"] > self.skill_cooldowns["summon"] and \
           self.current_skill == "patrol" and \
           self.health <= self.max_health / 2:  # 半血以下限制
            self.summon_minibosses()
            self.last_skill_times["summon"] = current_time
            return

        # 尝试触发超级冲刺
        if self.health <= self.super_dash_threshold and \
           current_time - self.last_skill_times["super_dash"] > self.skill_cooldowns["super_dash"] and \
           self.current_skill == "patrol":
            if len(minibosses) == 0 or random.random() < 0.4:  # 比如只有 40% 的几率在有小 Boss 时冲刺
                self.start_super_dash_charge()
                return

        # 尝试触发缠绕
        if current_time - self.last_skill_times["circle"] > self.skill_cooldowns["circle"] and \
           self.current_skill == "patrol":
            self.start_approach_for_circle()
           

    def perform_attack_sequence(self):
        current_attack_type = self.attack_sequence[self.current_attack_index]

        if current_attack_type == "normal": self.shoot_bullet()
        elif current_attack_type == "tracking": self.shoot_tracking_bullet()
        elif current_attack_type == "fast": self.shoot_fast_bullet()

        self.bullets_fired_in_burst += 1
        if self.bullets_fired_in_burst >= self.bullets_per_burst:
            self.bullets_fired_in_burst = 0
            self.current_attack_index = (self.current_attack_index + 1) % len(self.attack_sequence)
            self.next_burst_time = pygame.time.get_ticks() + self.burst_cooldown * 2
        else:
            self.next_burst_time = pygame.time.get_ticks() + self.burst_cooldown

    def shoot_bullet(self):
        bullet = BossBullet(self.rect.centerx, self.rect.bottom + 10)
        all_sprites.add(bullet)
        boss_bullets.add(bullet)

    def shoot_tracking_bullet(self):
        bullet = TrackingBullet(self.rect.centerx, self.rect.centery, player)
        all_sprites.add(bullet)
        boss_bullets.add(bullet)

    def shoot_fast_bullet(self):
        bullet = FastRectBullet(self.rect.centerx, self.rect.centery, player)
        all_sprites.add(bullet)
        boss_bullets.add(bullet)

    def shoot_barrage(self):
        num_bullets = 7
        for i in range(num_bullets):
            angle = -90 + (i * (180 / (num_bullets - 1)))
            bullet = BossBullet(self.rect.centerx, self.rect.bottom + 10, angle=angle)
            all_sprites.add(bullet)
            boss_bullets.add(bullet)

    def start_approach_for_circle(self):
        self.current_skill = "approach_circle"
        self.image = self.original_image.copy()
        self.image.fill(DARK_RED, special_flags=pygame.BLEND_RGB_MULT)
        self.image.set_alpha(255)

    def approach_for_circle_update(self):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist > self.circle_radius * 1.2:
            self.rect.x += (dx / dist) * self.circle_approach_speed if dist != 0 else 0
            self.rect.y += (dy / dist) * self.circle_approach_speed if dist != 0 else 0
            self.face_player()
        else:
            self.current_skill = "circling"
            self.start_circle()

        # 屏幕循环移动
        if self.rect.right < 0: self.rect.left = SCREEN_WIDTH
        elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0
        if self.rect.bottom < 0: self.rect.top = SCREEN_HEIGHT
        elif self.rect.top > SCREEN_HEIGHT: self.rect.bottom = 0

    def start_circle(self):
        self.circle_timer = self.circle_duration
        self.last_skill_times["circle"] = pygame.time.get_ticks()
        self.image = self.original_image.copy()
        self.image.fill(DARK_RED, special_flags=pygame.BLEND_RGB_MULT)
        self.image.set_alpha(255)

    def circle_update(self):
        if self.circle_timer > 0:
            self.circle_center_x = player.rect.centerx
            self.circle_center_y = player.rect.centery

            self.circle_angle += self.circle_speed
            self.rect.centerx = self.circle_center_x + self.circle_radius * math.cos(self.circle_angle)
            self.rect.centery = self.circle_center_y + self.circle_radius * math.sin(self.circle_angle)

            # 在缠绕过程中也面朝玩家
            self.face_player()

            if self.circle_timer % self.circle_bullet_interval == 0:
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                angle_to_player = math.degrees(math.atan2(dy, dx))
                bullet = BossBullet(self.rect.centerx, self.rect.centery, speed=SCREEN_HEIGHT * 0.01 * SCALE_FACTOR, angle=angle_to_player)
                all_sprites.add(bullet)
                boss_bullets.add(bullet)

            self.circle_timer -= 1
        else:
            self.current_skill = "patrol"
            self.set_new_patrol_target()
            self.speed_x = SCREEN_WIDTH * 0.0025 * SCALE_FACTOR
            self.speed_y = SCREEN_HEIGHT * 0.00125 * SCALE_FACTOR
            self.image = self.original_image.copy()
            self.image.set_alpha(255)  # 缠绕结束后恢复正常颜色

    def summon_minibosses(self):
        num_scatter_bullets = 20
        for i in range(num_scatter_bullets):
            angle = random.uniform(-170, -10)
            bullet = FastRectBullet(self.rect.centerx, self.rect.centery, player, angle=angle)
            all_sprites.add(bullet)
            boss_bullets.add(bullet)

        current_miniboss_count = len(minibosses)
        num_to_summon = self.max_minibosses - current_miniboss_count

        if num_to_summon > 0:
            spawn_points = [
                (SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.2),
                (SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.2),
                (SCREEN_WIDTH * 0.3, SCREEN_HEIGHT * 0.1),
                (SCREEN_WIDTH * 0.7, SCREEN_HEIGHT * 0.1)
            ]
            random.shuffle(spawn_points)

            for i in range(min(num_to_summon, len(spawn_points))):
                pos_x, pos_y = spawn_points[i]
                miniboss = Miniboss(pos_x, pos_y)
                all_sprites.add(miniboss)
                minibosses.add(miniboss)

    def start_super_dash_charge(self):
        # 如果 Boss 正在执行大招，不启动超级冲刺
        if self.current_skill in ["ultimate_charge", "ultimate_fire"]:
            return

        self.current_skill = "super_dash_charge"
        self.super_dash_charge_timer = self.super_dash_charge_time
        self.image = self.original_image.copy()
        self.image.set_alpha(255)

        # 通知小 Boss 集结
        if len(minibosses) > 0:
            self.is_gathering_minibosses = True 
            self.current_skill = "gathering"  # 切换到集结状态
            num_active_minibosses = len(minibosses)
            if num_active_minibosses > 0:
                angle_increment = (2 * math.pi / num_active_minibosses)
                for i, mb in enumerate(minibosses):
                    target_x = self.rect.centerx + self.miniboss_gathering_radius * math.cos(angle_increment * i)
                    target_y = self.rect.centery + self.miniboss_gathering_radius * math.sin(angle_increment * i)
                    target_x = max(0, min(SCREEN_WIDTH, target_x))
                    target_y = max(0, min(SCREEN_HEIGHT, target_y))
                    mb.start_gathering_to_boss(target_x, target_y, self.miniboss_gathering_speed)
        else:
            self.current_skill = "super_dash_charge"
            self.miniboss_gathered_and_waiting = True

    def super_dash_charge_update(self):  # 新增方法
        self.super_dash_charge_timer -= 1
        if self.super_dash_charge_timer % 10 < 5:
            self.image = self.original_image.copy()
            self.image.fill(GOLD, special_flags=pygame.BLEND_RGB_MULT)
            self.image.set_alpha(200)
        else:
            self.image = self.original_image.copy()
            self.image.set_alpha(255)

        if self.super_dash_charge_timer <= 0:
            # 蓄力结束后，无论小 Boss 是否集结完成，都执行冲刺
            self.execute_super_dash()

    def gathering_minibosses_update(self):
        all_gathered = True
        # 检查所有当前存活的小 Boss 是否都已集结到位
        for mb in minibosses:
            if mb.alive() and mb.is_gathering: 
                all_gathered = False
                break
        
        if all_gathered:
            self.is_gathering_minibosses = False
            self.miniboss_gathered_and_waiting = True
            # 小 Boss 集结完成后，如果 Boss 蓄力状态，则执行冲刺
            if self.current_skill == "gathering":  # 确认是从集结状态转换
                self.current_skill = "super_dash_charge"  # 返回蓄力状态
                if self.super_dash_charge_timer <= 0:  # 如果蓄力已经完成
                    self.execute_super_dash()

    def execute_super_dash(self):
        self.current_skill = "super_dash"
        self.super_dash_timer = self.super_dash_duration
        self.last_skill_times["super_dash"] = pygame.time.get_ticks()
        self.miniboss_gathered_and_waiting = False  # 重置集结等待

        self._set_super_dash_direction()
        self.image = self.original_image.copy()
        self.image.set_alpha(255)

        self.shoot_circular_barrage(num_bullets=20, bullet_speed=SCREEN_HEIGHT * 0.01 * SCALE_FACTOR, bullet_color=ORANGE)
        screen_shake.start(duration=60, intensity=5)

        num_active_minibosses = len(minibosses)
        if num_active_minibosses > 0:
            angle_increment = (2 * math.pi / num_active_minibosses)
            for i, mb in enumerate(minibosses):
                if mb.alive():
                    initial_angle_offset = angle_increment * i
                    mb.start_circle_boss(self, self.super_dash_duration, initial_angle_offset)
        
    def _set_super_dash_direction(self):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        
        if dist != 0:
            self.super_dash_vel_x = (dx / dist) * self.super_dash_speed
            self.super_dash_vel_y = (dy / dist) * self.super_dash_speed
        else:
            # 如果距离为 0，随机方向
            angle = random.uniform(0, 2 * math.pi)
            self.super_dash_vel_x = math.cos(angle) * self.super_dash_speed
            self.super_dash_vel_y = math.sin(angle) * self.super_dash_speed
        self.face_player()

    def super_dash_update(self):
        if self.super_dash_timer > 0:
            self.rect.x += self.super_dash_vel_x
            self.rect.y += self.super_dash_vel_y

            teleported = False
            if self.rect.right < 0: self.rect.left = SCREEN_WIDTH; teleported = True
            elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0; teleported = True
            if self.rect.bottom < 0: self.rect.top = SCREEN_HEIGHT; teleported = True
            elif self.rect.top > SCREEN_HEIGHT: self.rect.bottom = 0; teleported = True

            if teleported: self._set_super_dash_direction() # 传送后重新设置方向
            self.super_dash_timer -= 1
        else:
            self.current_skill = "patrol"
            self.set_new_patrol_target()
            self.speed_x = SCREEN_WIDTH * 0.0025 * SCALE_FACTOR
            self.speed_y = SCREEN_HEIGHT * 0.00125 * SCALE_FACTOR
            self.image = self.original_image.copy()
            self.image.set_alpha(255)

    def shoot_circular_barrage(self, num_bullets, bullet_speed, bullet_color):
        for i in range(num_bullets):
            angle = (360 / num_bullets) * i
            bullet = CircularBullet(self.rect.centerx, self.rect.centery, bullet_speed, angle, bullet_color)
            all_sprites.add(bullet)
            boss_bullets.add(bullet)

    # --- 大绝招相关方法 ---
    def start_ultimate_charge(self):
        self.current_skill = "ultimate_charge"
        self.ultimate_charge_timer = self.ultimate_charge_duration
        self.image = self.original_image.copy()
        self.image.fill(ULTIMATE_COLOR, special_flags=pygame.BLEND_RGB_MULT)
        self.image.set_alpha(255)
        
        # 强制取消所有其他技能的状态和计时器
        self.is_circling = False; self.circle_timer = 0
        self.is_approaching_for_circle = False
        self.is_super_dashing = False; self.super_dash_timer = 0
        self.super_dash_charge_timer = 0  # 强制取消蓄力
        self.is_gathering_minibosses = False
        self.miniboss_gathered_and_waiting = False  # 重置小 Boss 集结状态
        self.attack_timer = 0  # 重置普通攻击计时器
        self.bullets_fired_in_burst = 0  # 重置连射计数
        self.next_burst_time = pygame.time.get_ticks() + self.burst_cooldown  # 重置下次射击时间

        # 强制取消所有小 Boss 的集结状态，避免冲突，并直接切换到大招就位
        for mb in minibosses:
            if mb.alive():
                mb.is_gathering = False                
                mb.is_waiting_after_gathering = False
                mb.gathering_target_x = 0
                mb.gathering_target_y = 0
                mb.gathering_speed = 0
                mb.is_dashing = False
                mb.is_circling_boss = False
                mb.circle_boss_target = None
                mb.is_self_destructing = False
                mb.has_triggered_self_destruct = False
                mb.self_destruct_state = "approaching"
                mb.is_ultimate_positioning = True  # 直接切换小 Boss 到大招就位状态
                mb.start_ultimate_positioning(self.ultimate_center_x, self.ultimate_center_y, self.ultimate_miniboss_radius, self.ultimate_gather_speed)

        # 停止所有现有子弹的移动，并让他们开始向中心聚集
        for bullet in all_sprites:
            if isinstance(bullet, (BossBullet, TrackingBullet, FastRectBullet, CircularBullet, PlayerBullet)):
                bullet.is_gathering_for_ultimate = True
        
        # 销毁任何可能存在的巨型弹，避免重复
        for bullet in ultimate_bullets:  # 旧的巨弹
            bullet.kill()
        self.ultimate_giant_bullet = None

        # 创建一个空的巨型子弹，用于吸附能量
        self.ultimate_giant_bullet = UltimateGiantBullet(self.ultimate_center_x, self.ultimate_center_y, 1, 0, 0)  # 初始大小设为 1，避免 0
        all_sprites.add(self.ultimate_giant_bullet)
        ultimate_bullets.add(self.ultimate_giant_bullet)  # 加入巨弹精灵组
        self.all_bullets_gathered = False  # 重置聚集状态
        self.gather_timeout = 60 * 3  # 重置聚集超时计时器

    def ultimate_charge_update(self):
        # Boss 向指定位置移动 (屏幕中心上方)
        target_x = self.ultimate_center_x
        target_y = self.ultimate_boss_target_y
        dx_boss = target_x - self.rect.centerx
        dy_boss = target_y - self.rect.centery
        dist_boss = math.hypot(dx_boss, dy_boss)

        if dist_boss > self.ultimate_gather_speed:
            self.rect.x += (dx_boss / dist_boss) * self.ultimate_gather_speed if dist_boss != 0 else 0
            self.rect.y += (dy_boss / dist_boss) * self.ultimate_gather_speed if dist_boss != 0 else 0
        else:
            self.rect.centerx = target_x
            self.rect.centery = target_y
            # 确保 Boss 始终朝向玩家，即使在固定位置
            self.face_player() 

        # 视觉效果：Boss 闪烁
        if self.ultimate_charge_timer % 10 < 5:
            self.image = self.original_image.copy()
            self.image.fill(ULTIMATE_COLOR, special_flags=pygame.BLEND_RGB_MULT)
            self.image.set_alpha(200)  # 调低透明度
        else:
            self.image = self.original_image.copy()
            self.image.set_alpha(255)

        # 检查所有子弹是否已聚集完毕，添加超时机制，并强制销毁聚集完成的子弹
        self.all_bullets_gathered = True
        for bullet in player_bullets:
            if bullet.is_gathering_for_ultimate and bullet.alive():  # 只检查存活子弹
                dx_bullet = self.ultimate_center_x - bullet.rect.centerx
                dy_bullet = self.ultimate_center_y - bullet.rect.centery
                dist_bullet = math.hypot(dx_bullet, dy_bullet)
                if dist_bullet <= 2:  # 距离中心小于等于 2 像素时销毁子弹
                    bullet.kill()
                else:
                    self.all_bullets_gathered = False
        if self.all_bullets_gathered:  # 如果玩家子弹都聚完了，再检查 Boss 子弹
            for bullet in boss_bullets:
                if bullet.is_gathering_for_ultimate and bullet.alive():
                    dx_bullet = self.ultimate_center_x - bullet.rect.centerx
                    dy_bullet = self.ultimate_center_y - bullet.rect.centery
                    dist_bullet = math.hypot(dx_bullet, dy_bullet)
                    if dist_bullet <= 2:  # 距离中心小于等于 2 像素时销毁子弹
                        bullet.kill()
                    else:
                        self.all_bullets_gathered = False

        # 超时机制：如果聚集超时强制销毁所有聚集中的子弹
        if not self.all_bullets_gathered: # 只有在未完全聚集时才计时
            self.gather_timeout -= 1
            if self.gather_timeout <= 0:
                for bullet in all_sprites:
                    if isinstance(bullet, (BossBullet, TrackingBullet, FastRectBullet, CircularBullet, PlayerBullet)) and bullet.is_gathering_for_ultimate:
                        bullet.kill()
                self.all_bullets_gathered = True  # 强制设为 True，避免卡死

        # 更新巨型子弹的大小 (根据蓄力时间)
        if self.ultimate_giant_bullet and self.ultimate_giant_bullet.alive():
            charge_progress = 1 - (self.ultimate_charge_timer / self.ultimate_charge_duration)  # 0 到 1 的进度

            # 根据小 Boss 数量调整最终大小
            num_active_minibosses = len(minibosses)
            # 基础大小 + (每个小 Boss 额外增加的大小)
            base_size = SCREEN_WIDTH * 0.2 * SCALE_FACTOR # 增加基础大小
            extra_size_per_miniboss = SCREEN_WIDTH * 0.08 * SCALE_FACTOR # 增加每个小 Boss 额外增加的大小
            target_bullet_size = base_size + (num_active_minibosses * extra_size_per_miniboss)
            current_bullet_size = max(1, int(target_bullet_size * charge_progress))
            self.ultimate_giant_bullet.set_size(current_bullet_size)

        # 新增：轻微拖拽玩家向屏幕中心
        drag_speed = SCREEN_WIDTH * 0.0064 * SCALE_FACTOR  # 轻微拖拽速度，控制为较小
        dx_player = self.ultimate_center_x - player.rect.centerx
        dy_player = self.ultimate_center_y - player.rect.centery
        dist_player = math.hypot(dx_player, dy_player)
        if dist_player > 10:  # 只有当玩家距离中心较远时才拖拽，避免干扰
            player.rect.x += (dx_player / dist_player) * drag_speed if dist_player != 0 else 0
            player.rect.y += (dy_player / dist_player) * drag_speed if dist_player != 0 else 0
        # 确保玩家不超出屏幕边界
        if player.rect.left < 0: player.rect.left = 0
        if player.rect.right > SCREEN_WIDTH: player.rect.right = SCREEN_WIDTH
        if player.rect.top < 0: player.rect.top = 0
        if player.rect.bottom > SCREEN_HEIGHT: player.rect.bottom = SCREEN_HEIGHT

        self.ultimate_charge_timer -= 1
        
        # 只有当蓄力时间结束且所有子弹都已聚集完毕时，才进入发射状态
        if self.ultimate_charge_timer <= 0 and self.all_bullets_gathered:
            self.current_skill = "ultimate_fire"
            screen_shake.start(duration=60, intensity=10) # 剧烈抖动

    def ultimate_fire_update(self):
        # 巨弹发射
        if self.ultimate_giant_bullet and self.ultimate_giant_bullet.alive():
            # 确保巨弹锁定玩家位置
            self.ultimate_giant_bullet.set_target(player.rect.centerx, player.rect.centery)
            self.ultimate_giant_bullet.fire(self.ultimate_bullet_speed)  # 使用降低后的速度
            # 注意这里不能直接 self.ultimate_giant_bullet = None，否则巨弹会立即消失
            # 应该让巨弹自己管理生命周期，发射后它自行移动并销毁
        self.ultimate_giant_bullet = None  # 清除引用，让巨弹独立运动

        # Boss 和小 Boss返回巡逻状态
        self.current_skill = "patrol"
        self.set_new_patrol_target()
        self.speed_x = SCREEN_WIDTH * 0.0025 * SCALE_FACTOR
        self.speed_y = SCREEN_HEIGHT * 0.00125 * SCALE_FACTOR
        self.image = self.original_image.copy()
        self.image.set_alpha(255)
        
        # 确保所有小 Boss 也返回巡逻状态
        for mb in minibosses:
            if mb.alive():
                mb.return_to_patrol()

# 小 Boss 类
class Miniboss(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.original_image = pygame.Surface((SCREEN_WIDTH * 0.08 * SCALE_FACTOR, SCREEN_HEIGHT * 0.083 * SCALE_FACTOR), pygame.SRCALPHA)
        self.original_image.fill((0, 0, 0, 0))
        self.rect = self.original_image.get_rect()
        self.draw_boss_shape(self.original_image, MINIBOSS_COLOR, LIGHT_BLUE)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.max_health = 250  # 小 Boss 最大生命值
        self.health = self.max_health  # 小 Boss 当前生命值
        self.speed_x = SCREEN_WIDTH * 0.003 * SCALE_FACTOR  # 小 Boss X 移动速度
        self.speed_y = SCREEN_HEIGHT * 0.0015 * SCALE_FACTOR  # 小 Boss Y 轴移动速度

        self.attack_cooldown = 60  # 攻击冷却时间
        self.tracking_bullet_cooldown = 90  # 跟踪子弹冷却时间
        self.fast_bullet_cooldown = 180  # 极速子弹冷却时间
        self.last_tracking_bullet_time = pygame.time.get_ticks()  # 上次发射子弹时间
        self.last_fast_bullet_time = pygame.time.get_ticks()  # 上次发射极速子弹时间
        self.last_attack_time = pygame.time.get_ticks()  # 上次攻击时间

        self.is_dashing = False  # 是否正在冲刺
        self.dash_vel_x = 0  # 冲刺 X 轴速度
        self.dash_vel_y = 0  # 冲刺 Y 轴速度
        self.dash_speed = SCREEN_WIDTH * 0.015 * SCALE_FACTOR  # 冲刺速度
        self.dash_duration = 60 * 1  # 冲刺持续时间 (帧数)
        self.dash_timer = 0  # 冲刺计时器
        self.dash_cooldown = 60 * 5  # 冲刺冷却时间
        self.last_dash_time = pygame.time.get_ticks()  # 上次冲刺时间
        self.is_circling_boss = False  # 是否正在缠绕主 Boss
        self.circle_boss_target = None  # 缠绕的主 Boss 目标
        self.circle_boss_radius = SCREEN_WIDTH * 0.08 * SCALE_FACTOR  # 缠绕主 Boss 半径
        self.circle_boss_angle = 0  # 缠绕主 Boss 角度
        self.circle_boss_speed = 0.15  # 缠绕主 Boss 速度
        self.circle_boss_timer = 0  # 缠绕主 Boss 计时器

        self.circle_boss_attack_interval = 5  # 缠绕主 Boss 时攻击间隔

        self.is_self_destructing = False  # 是否正在自毁
        self.self_destruct_state = "approaching"  # 自毁状态 (接近/闪烁)
        self.self_destruct_approach_speed = SCREEN_WIDTH * 0.01 * SCALE_FACTOR # 自毁接近速度
        self.self_destruct_flash_duration = 60 * 1.5  # 自毁闪烁持续时间 (帧数)
        self.self_destruct_timer = 0  # 自毁计时器
        self.self_destruct_chance = 0.3  # 自毁触发几率
        self.has_triggered_self_destruct = False  # 是否已触发自毁 (避免重复触发)
        self.target_player_behind_offset = SCREEN_HEIGHT * 0.1  # 自毁目标玩家后方偏移量

        self.is_gathering = False  # 是否正在集结
        self.gathering_target_x = 0  # 集结目标 X 坐标
        self.gathering_target_y = 0  # 集结目标 Y 坐标
        self.gathering_speed = 0  # 集结速度
        self.is_waiting_after_gathering = False  # 是否在集结原地等待

        # 大绝招相关
        self.is_ultimate_positioning = False  # 是否正在为大招就位
        self.ultimate_target_x = 0
        self.ultimate_target_y = 0
        self.ultimate_positioning_speed = 0

        # Miniboss 巡逻区域
        self.patrol_min_y = SCREEN_HEIGHT * 0.3  # Miniboss 巡逻区域 Y 轴最小值
        self.patrol_max_y = SCREEN_HEIGHT * 0.6  # Miniboss 巡逻区域 Y 轴最大值
        self.patrol_min_x = SCREEN_WIDTH * 0.1  # Miniboss 巡逻区域 X 轴最小值
        self.patrol_max_x = SCREEN_WIDTH * 0.9 - self.rect.width  # Miniboss 巡逻区域 X 轴最大值

        self.target_x = self.rect.centerx # 巡逻目标 X 坐标
        self.target_y = self.rect.centery  # 巡逻目标 Y 坐标
        self.set_new_patrol_target()  # 设置新的巡逻目标

    def set_new_patrol_target(self):
        """为小 Boss 设置新的巡逻目标。"""
        self.target_x = random.uniform(self.patrol_min_x, self.patrol_max_x)
        self.target_y = random.uniform(self.patrol_min_y, self.patrol_max_y)

    def draw_boss_shape(self, surface, body_color, engine_color):
        surface.fill((0, 0, 0, 0))
        pygame.draw.polygon(surface, body_color, [
            (surface.get_width() // 2, 0),
            (surface.get_width(), surface.get_height() * 0.3),
            (surface.get_width() * 0.8, surface.get_height()),
            (surface.get_width() * 0.2, surface.get_height()),
            (0, surface.get_height() * 0.3)
        ])
        pygame.draw.rect(surface, engine_color, (surface.get_width() * 0.25, surface.get_height() * 0.9, surface.get_width() * 0.15, surface.get_height() * 0.1))
        pygame.draw.rect(surface, engine_color, (surface.get_width() * 0.6, surface.get_height() * 0.9, surface.get_width() * 0.15, surface.get_height() * 0.1))

    def update(self):
        # 自毁优先级最高，无论当前状态如何，只要满足条件就触发
        if self.health <= self.max_health / 3 and not self.has_triggered_self_destruct:
            if random.random() < self.self_destruct_chance:
                self.start_self_destruct()
                return
        
        if self.is_self_destructing:
            self.self_destruct_update()
            return
        
        # 大绝招就位优先级 (高于其他小 Boss 技能)
        if self.is_ultimate_positioning:
            self.ultimate_positioning_update()
            # 在大招就位期间，小 Boss 不应该执行其他移动或攻击逻辑
            # 也不应该执行屏幕循环（传送门）逻辑
            return

        # 正常行为逻辑
        if self.is_gathering: 
            self.gathering_update()
        elif self.is_waiting_after_gathering:
            pass  # 集结后原地等待，不执行移动和攻击
        elif self.is_circling_boss: 
            self.circle_boss_update()
        elif self.is_dashing: 
            self.dash_update()
        else:  # 巡逻状态
            dx = self.target_x - self.rect.centerx
            dy = self.target_y - self.rect.centery
            dist = math.hypot(dx, dy)

            if dist > self.speed_x:
                self.rect.x += (dx / dist) * self.speed_x if dist != 0 else 0
                self.rect.y += (dy / dist) * self.speed_y if dist != 0 else 0
            else:
                self.rect.centerx = self.target_x
                self.rect.centery = self.target_y
                self.set_new_patrol_target()
            
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack_time > self.attack_cooldown:
                self.choose_attack()
                self.last_attack_time = current_time

            # 屏幕循环移动 (只在非特殊移动状态下执行)
            if self.rect.right < 0: self.rect.left = SCREEN_WIDTH
            elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0
            if self.rect.bottom < 0: self.rect.top = SCREEN_HEIGHT
            elif self.rect.top > SCREEN_HEIGHT: self.rect.bottom = 0
        
        # 面朝玩家的逻辑，只在非特殊移动状态下执行
        # 修正：在大招就位期间也不应该面向玩家
        if not self.is_self_destructing and not self.is_gathering and not self.is_waiting_after_gathering and not self.is_ultimate_positioning: 
            self.face_player()

    def face_player(self):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        angle = math.degrees(math.atan2(-dy, dx))
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def choose_attack(self):
        current_time = pygame.time.get_ticks()
        attack_options = ["shoot", "tracking_bullet", "fast_bullet"]
        
        if current_time - self.last_dash_time > self.dash_cooldown:
            attack_options.append("dash")

        choice = random.choice(attack_options)

        if choice == "shoot": self.shoot_bullet()
        elif choice == "tracking_bullet": self.shoot_tracking_bullet()
        elif choice == "fast_bullet": self.shoot_fast_bullet()
        elif choice == "dash": self.start_dash()

    def start_dash(self):
        # 只有在非集结等待、非自毁、非缠绕、非大招就位状态下才能冲刺
        if self.is_gathering or self.is_waiting_after_gathering or \
           self.is_self_destructing or self.is_circling_boss or self.is_ultimate_positioning: return
        self.is_dashing = True
        self.dash_timer = self.dash_duration
        self.last_dash_time = pygame.time.get_ticks()
        
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist != 0:
            self.dash_vel_x = (dx / dist) * self.dash_speed
            self.dash_vel_y = (dy / dist) * self.dash_speed
        else:
            angle = random.uniform(0, 2 * math.pi)
            self.dash_vel_x = math.cos(angle) * self.dash_speed
            self.dash_vel_y = math.sin(angle) * self.dash_speed
        self.face_player()

    def dash_update(self):
        if self.dash_timer > 0:
            self.rect.x += self.dash_vel_x
            self.rect.y += self.dash_vel_y

            if self.rect.right < 0: self.rect.left = SCREEN_WIDTH
            elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0
            if self.rect.bottom < 0: self.rect.top = SCREEN_HEIGHT
            elif self.rect.top > SCREEN_HEIGHT: self.rect.bottom = 0

            self.dash_timer -= 1
        else:
            self.is_dashing = False
            self.set_new_patrol_target()
            self.speed_x = SCREEN_WIDTH * 0.003 * SCALE_FACTOR
            self.speed_y = SCREEN_HEIGHT * 0.0015 * SCALE_FACTOR
            self.image = self.original_image.copy()
            self.image.set_alpha(255)

    def start_circle_boss(self, target_boss, duration, initial_angle_offset=0):
        # 强制取消其他所有状态，确保立即缠绕 Boss
        self.is_dashing = False; self.dash_timer = 0
        self.is_self_destructing = False; self.has_triggered_self_destruct = False  # 确保自毁状态被取消
        self.self_destruct_state = "approaching"  # 重置自毁状态
        self.is_gathering = False  # 强制取消集结
        self.is_waiting_after_gathering = False  # 强制取消集结后等待
        self.is_ultimate_positioning = False  # 强制取消大招就位

        self.is_circling_boss = True
        self.circle_boss_target = target_boss
        self.circle_boss_timer = duration
        self.circle_boss_angle = initial_angle_offset
        self.image = self.original_image.copy()
        self.image.fill(MINIBOSS_CIRCLE_COLOR, special_flags=pygame.BLEND_RGB_MULT)
        self.image.set_alpha(255)

    def circle_boss_update(self):
        if self.circle_boss_timer > 0 and self.circle_boss_target and self.circle_boss_target.alive():
            self.circle_boss_angle += self.circle_boss_speed
            self.rect.centerx = self.circle_boss_target.rect.centerx + self.circle_boss_radius * math.cos(self.circle_boss_angle)
            self.rect.centery = self.circle_boss_target.rect.centery + self.circle_boss_radius * math.sin(self.circle_boss_angle)

            if self.circle_boss_timer % self.circle_boss_attack_interval == 0:
                attack_options = ["shoot", "tracking_bullet", "fast_bullet"]
                choice = random.choice(attack_options)
                
                if choice == "shoot": self.shoot_bullet()
                elif choice == "tracking_bullet": self.shoot_tracking_bullet()
                elif choice == "fast_bullet": self.shoot_fast_bullet()

            self.circle_boss_timer -= 1
        else:
            self.is_circling_boss = False
            self.circle_boss_target = None
            self.set_new_patrol_target()
            self.image = self.original_image.copy()
            self.image.set_alpha(255)

    def start_self_destruct(self):
        self.is_self_destructing = True
        self.has_triggered_self_destruct = True
        self.self_destruct_state = "approaching"
        self.self_destruct_timer = 0 
        
        # 强制取消其他状态
        self.is_circling_boss = False
        self.circle_boss_target = None
        self.is_dashing = False
        self.is_gathering = False
        self.gathering_target_x = 0
        self.gathering_target_y = 0 
        self.is_waiting_after_gathering = False
        self.is_ultimate_positioning = False  # 额外取消大招就位

        target_x = player.rect.centerx
        target_y = player.rect.bottom + self.target_player_behind_offset

        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist != 0:
            self.self_destruct_vel_x = (dx / dist) * self.self_destruct_approach_speed
            self.self_destruct_vel_y = (dy / dist) * self.self_destruct_approach_speed
        else:
            # 如果距离为 0，随机一个方向进行自毁冲刺
            angle = random.uniform(0, 2 * math.pi)
            self.self_destruct_vel_x = math.cos(angle) * self.self_destruct_approach_speed
            self.self_destruct_vel_y = math.sin(angle) * self.self_destruct_approach_speed

    def self_destruct_update(self):
        if self.self_destruct_state == "approaching":
            self.rect.x += self.self_destruct_vel_x
            self.rect.y += self.self_destruct_vel_y
            self.face_player()

            target_x = player.rect.centerx
            target_y = player.rect.bottom + self.target_player_behind_offset
            distance_to_target = math.hypot(self.rect.centerx - target_x, self.rect.centery - target_y)
            # 如果接近玩家或冲出屏幕，则进入闪烁阶段或直接自爆
            if distance_to_target < self.rect.width * 0.5 or not screen.get_rect().colliderect(self.rect):
                self.self_destruct_state = "flashing"
                self.self_destruct_timer = self.self_destruct_flash_duration
                self.image = self.original_image.copy()
                self.image.set_alpha(255)  # 确保颜色恢复正常
            
        elif self.self_destruct_state == "flashing":
            self.self_destruct_timer -= 1
            if self.self_destruct_timer % 5 < 2:
                self.image = self.original_image.copy()
                self.image.fill(SELF_DESTRUCT_COLOR, special_flags=pygame.BLEND_RGB_MULT)
                self.image.set_alpha(255)
            else:
                self.image = self.original_image.copy()
                self.image.set_alpha(255)
            
            if self.self_destruct_timer <= 0:
                self.execute_self_destruct()
    
    def execute_self_destruct(self):
        num_bullets = 26
        bullet_speed = SCREEN_HEIGHT * 0.012 * SCALE_FACTOR
        for i in range(num_bullets):
            angle = (360 / num_bullets) * i
            bullet = CircularBullet(self.rect.centerx, self.rect.centery, bullet_speed, angle, ORANGE)
            all_sprites.add(bullet)
            boss_bullets.add(bullet)

        screen_shake.start(duration=30, intensity=8)
        self.kill()

    def start_gathering_to_boss(self, target_x, target_y, speed):
        # 在非自爆、非大招就位状态下才能集结
        if self.is_self_destructing or self.is_ultimate_positioning:
            return # 如果正在自爆或大招就位，不允许集结
        self.is_gathering = True
        self.gathering_target_x = target_x
        self.gathering_target_y = target_y
        self.gathering_speed = speed

        # 强制取消其他状态
        self.is_dashing = False
        self.is_circling_boss = False
        self.circle_boss_target = None
        self.is_waiting_after_gathering = False

        self.image = self.original_image.copy()
        self.image.fill(YELLOW, special_flags=pygame.BLEND_RGB_MULT)
        self.image.set_alpha(255)

    def gathering_update(self):
        dx = self.gathering_target_x - self.rect.centerx
        dy = self.gathering_target_y - self.rect.centery
        dist = math.hypot(dx, dy)

        # 移动目标点
        if dist > self.gathering_speed:
            self.rect.x += (dx / dist) * self.gathering_speed if dist != 0 else 0
            self.rect.y += (dy / dist) * self.gathering_speed if dist != 0 else 0
        else:
            self.rect.centerx = self.gathering_target_x
            self.rect.centery = self.gathering_target_y
            self.is_gathering = False  # 到达，停止集结状态
            self.is_waiting_after_gathering = True  # 进入等待状态
            self.image = self.original_image.copy()
            self.image.set_alpha(255)  # 恢复正常颜色

        # 屏幕循环移动 (确保小 Boss 不会卡在屏幕边缘)
        if self.rect.right < 0: self.rect.left = SCREEN_WIDTH
        elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0
        if self.rect.bottom < 0: self.rect.top = SCREEN_HEIGHT
        elif self.rect.top > SCREEN_HEIGHT: self.rect.bottom = 0

    # --- 大绝招就位相关 ---
    def start_ultimate_positioning(self, center_x, center_y, radius, speed):
        # 强制取消所有其他状态（集结、冲刺、自毁、缠绕等），确保立即执行大招就位
        self.is_dashing = False; self.dash_timer = 0
        self.is_circling_boss = False; self.circle_boss_target = None; self.circle_boss_timer = 0
        self.is_self_destructing = False; self.has_triggered_self_destruct = False; self.self_destruct_state = "approaching"; self.self_destruct_timer = 0
        self.is_gathering = False; self.gathering_target_x = 0; self.gathering_target_y = 0; self.gathering_speed = 0; self.is_waiting_after_gathering = False # 强化集结重置
        
        self.is_ultimate_positioning = True
        self.ultimate_positioning_speed = speed

        # 小 Boss 在大招阵型中的位置，确保站位整齐
        # 需要获取当前所有存活的小 Boss 列表，以便计算自己的索引和位置
        active_minibosses_list = list(minibosses) # 获取当前所有小boss的列表
        try:
            my_index = active_minibosses_list.index(self) # 找到自己在列表中的索引
        except ValueError:
            # 如果小boss不在列表中（可能刚被摧毁但还没从组里移除），则让它返回巡逻
            self.return_to_patrol()
            return

        num_minibosses = len(active_minibosses_list)
        if num_minibosses > 0:
            # Boss 的实际中心点
            boss_actual_center_x = boss.rect.centerx
            boss_actual_center_y = boss.rect.centery

            # 增加额外偏移，让小 Boss 均匀分布
            # 这里的 effective_radius 考虑了 Boss 自身大小和 Miniboss 自身大小，
            # 确保它们不会重叠，并且圆看起来更自然
            effective_radius = radius + boss.rect.width / 2 + self.rect.width / 2 + SCREEN_WIDTH * 0.01 
            angle_increment = (2 * math.pi / num_minibosses)
            initial_angle = 0 # 可以调整初始角度，让圆的起始位置不同
            current_angle = initial_angle + (angle_increment * my_index) # 均匀分布
            self.ultimate_target_x = boss_actual_center_x + effective_radius * math.cos(current_angle)
            self.ultimate_target_y = boss_actual_center_y + effective_radius * math.sin(current_angle)
        else:
            # 如果没有其他小 Boss，就让它随机移动到中心附近
            self.ultimate_target_x = center_x + random.uniform(-50, 50)
            self.ultimate_target_y = center_y + random.uniform(-50, 50)

        self.image = self.original_image.copy()
        self.image.fill(ULTIMATE_COLOR, special_flags=pygame.BLEND_RGB_MULT)
        self.image.set_alpha(255)

    def ultimate_positioning_update(self):
        dx = self.ultimate_target_x - self.rect.centerx
        dy = self.ultimate_target_y - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist > self.ultimate_positioning_speed:
            self.rect.x += (dx / dist) * self.ultimate_positioning_speed if dist != 0 else 0
            self.rect.y += (dy / dist) * self.ultimate_positioning_speed if dist != 0 else 0
        else:
            self.rect.centerx = self.ultimate_target_x
            self.rect.centery = self.ultimate_target_y
            # 到达位置后，停止移动，保持大招颜色
            self.image = self.original_image.copy()
            self.image.fill(ULTIMATE_COLOR, special_flags=pygame.BLEND_RGB_MULT)
            self.image.set_alpha(255)

        # 修正：在大招就位期间，小 Boss 不应执行屏幕循环
        # 这里的屏幕循环逻辑应该被移除或被外层update中的is_ultimate_positioning判断跳过
        # 确保这里没有类似 if self.rect.right < 0: self.rect.left = SCREEN_WIDTH; 这样的代码
        # 并且在update方法外层已经通过 return 语句确保了只执行 ultimate_positioning_update

    def return_to_patrol(self):
        # 从大招状态返回巡逻
        self.is_ultimate_positioning = False
        self.set_new_patrol_target()
        self.speed_x = SCREEN_WIDTH * 0.003 * SCALE_FACTOR
        self.speed_y = SCREEN_HEIGHT * 0.0015 * SCALE_FACTOR
        self.image = self.original_image.copy()
        self.image.set_alpha(255)

    # --- Miniboss 攻击方法 ---
    def shoot_bullet(self):
        """小 Boss 发射普通子弹。"""
        bullet = BossBullet(self.rect.centerx, self.rect.bottom + 10, speed=SCREEN_HEIGHT * 0.01 * SCALE_FACTOR)
        all_sprites.add(bullet)
        boss_bullets.add(bullet)

    def shoot_tracking_bullet(self):
        """小 Boss 发射跟踪子弹。"""
        bullet = TrackingBullet(self.rect.centerx, self.rect.centery, player)
        all_sprites.add(bullet)
        boss_bullets.add(bullet)

    def shoot_fast_bullet(self):
        """小 Boss 发射极速子弹。"""
        bullet = FastRectBullet(self.rect.centerx, self.rect.centery, player)
        all_sprites.add(bullet)
        boss_bullets.add(bullet)

# 橙色子弹类 (Boss 和 Miniboss 共用)
class CircularBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, angle, color):
        super().__init__()
        self.image = pygame.Surface((SCREEN_WIDTH * 0.015 * SCALE_FACTOR, SCREEN_WIDTH * 0.015 * SCALE_FACTOR))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = speed  # 子弹速度
        self.vel_x = self.speed * math.cos(math.radians(angle))
        self.vel_y = self.speed * math.sin(math.radians(angle))
        self.teleport_count = 0  # 子弹屏幕循环次数
        self.is_gathering_for_ultimate = False  # 新增标志，是否被大招吸附

    def update(self):
        if self.is_gathering_for_ultimate:
            dx = boss.ultimate_center_x - self.rect.centerx
            dy = boss.ultimate_center_y - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 2:  # 调整阈值，降低到 2 像素确保更早销毁
                max_dist_from_center = math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT)
                normalized_dist = dist / max_dist_from_center
                min_gather_speed = SCREEN_HEIGHT * 0.005 * SCALE_FACTOR
                max_gather_speed = SCREEN_HEIGHT * 0.02 * SCALE_FACTOR
                current_gather_speed = min_gather_speed + (max_gather_speed - min_gather_speed) * (1 - normalized_dist)
                self.rect.x += (dx / dist) * current_gather_speed if dist != 0 else 0
                self.rect.y += (dy / dist) * current_gather_speed if dist != 0 else 0
            else:
                self.kill()  # 聚集到中心后立即销毁
            return

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        # 子弹屏幕循环后消失
        if self.teleport_count < 3:
            if self.rect.bottom < 0: self.rect.top = SCREEN_HEIGHT; self.teleport_count += 1
            elif self.rect.top > SCREEN_HEIGHT: self.rect.bottom = 0; self.teleport_count += 1
            if self.rect.right < 0: self.rect.left = SCREEN_WIDTH; self.teleport_count += 1
            elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0; self.teleport_count += 1
        else:
            if not screen.get_rect().colliderect(self.rect): self.kill()

# Boss 子弹类
class BossBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=SCREEN_HEIGHT * 0.015, angle=-90):
        super().__init__()
        self.image = pygame.Surface((SCREEN_WIDTH * 0.01 * SCALE_FACTOR, SCREEN_WIDTH * 0.01 * SCALE_FACTOR))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = speed * SCALE_FACTOR  # 子弹速度
        self.vel_x = self.speed * math.cos(math.radians(angle))
        self.vel_y = self.speed * math.sin(math.radians(angle))
        self.teleport_count = 0  # 子弹屏幕循环次数
        self.is_gathering_for_ultimate = False # 新增标志，是否被大招吸附

    def update(self):
        if self.is_gathering_for_ultimate:
            dx = boss.ultimate_center_x - self.rect.centerx
            dy = boss.ultimate_center_y - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 2:  # 调整阈值，降低到 2 像素确保更早销毁
                max_dist_from_center = math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT)
                normalized_dist = dist / max_dist_from_center
                min_gather_speed = SCREEN_HEIGHT * 0.005 * SCALE_FACTOR
                max_gather_speed = SCREEN_HEIGHT * 0.02 * SCALE_FACTOR
                current_gather_speed = min_gather_speed + (max_gather_speed - min_gather_speed) * (1 - normalized_dist)
                self.rect.x += (dx / dist) * current_gather_speed if dist != 0 else 0
                self.rect.y += (dy / dist) * current_gather_speed if dist != 0 else 0
            else:
                self.kill()  # 聚集到中心后立即销毁
            return

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        # 子弹屏幕循环 4 次后消失
        if self.teleport_count < 4:
            if self.rect.bottom < 0: self.rect.top = SCREEN_HEIGHT; self.teleport_count += 1
            elif self.rect.top > SCREEN_HEIGHT: self.rect.bottom = 0; self.teleport_count += 1
            if self.rect.right < 0: self.rect.left = SCREEN_WIDTH; self.teleport_count += 1
            elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0; self.teleport_count += 1
        else:
            if not screen.get_rect().colliderect(self.rect): self.kill()

# 跟踪子弹类
class TrackingBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_player):
        super().__init__()
        self.image = pygame.Surface((SCREEN_WIDTH * 0.012 * SCALE_FACTOR, SCREEN_WIDTH * 0.012 * SCALE_FACTOR))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = SCREEN_HEIGHT * 0.005 * SCALE_FACTOR  # 子弹速度
        self.target_player = target_player  # 跟踪目标
        self.teleport_count = 0  # 子弹屏幕循环次数
        self.lifetime = 60 * 5  # 子弹生命周期 (帧数)
        self.is_gathering_for_ultimate = False  # 新增标志，是否被大招吸附

    def update(self):
        if self.is_gathering_for_ultimate:
            dx = boss.ultimate_center_x - self.rect.centerx
            dy = boss.ultimate_center_y - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 2:  # 调整阈值，降低到 2 像素确保更早销毁
                max_dist_from_center = math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT)
                normalized_dist = dist / max_dist_from_center
                min_gather_speed = SCREEN_HEIGHT * 0.005 * SCALE_FACTOR
                max_gather_speed = SCREEN_HEIGHT * 0.02 * SCALE_FACTOR
                current_gather_speed = min_gather_speed + (max_gather_speed - min_gather_speed) * (1 - normalized_dist)
                self.rect.x += (dx / dist) * current_gather_speed if dist != 0 else 0
                self.rect.y += (dy / dist) * current_gather_speed if dist != 0 else 0
            else:
                self.kill()  # 聚集到中心后立即销毁
            return

        dx = self.target_player.rect.centerx - self.rect.centerx
        dy = self.target_player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist != 0:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed

        self.lifetime -= 1
        if self.lifetime <= 0: self.kill(); return

        # 子弹屏幕循环 4 次后消失
        if self.teleport_count < 4:
            if self.rect.bottom < 0: self.rect.top = SCREEN_HEIGHT; self.teleport_count += 1
            elif self.rect.top > SCREEN_HEIGHT: self.rect.bottom = 0; self.teleport_count += 1
            if self.rect.right < 0: self.rect.left = SCREEN_WIDTH; self.teleport_count += 1
            elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0; self.teleport_count += 1
        else:
            if not screen.get_rect().colliderect(self.rect): self.kill()

# 极速子弹类
class FastRectBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_player, angle=None):
        super().__init__()
        bullet_width = SCREEN_WIDTH * 0.002 * SCALE_FACTOR
        bullet_height = SCREEN_HEIGHT * 0.03 * SCALE_FACTOR
        self.image = pygame.Surface((bullet_width, bullet_height), pygame.SRCALPHA)
        self.image.fill(CYAN)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = SCREEN_HEIGHT * 0.02 * SCALE_FACTOR  # 子弹速度
        self.teleport_count = 0  # 子弹屏幕循环次数
        self.is_gathering_for_ultimate = False  # 新增标志，是否被大招吸附

        if angle is None:
            dx = target_player.rect.centerx - self.rect.centerx
            dy = target_player.rect.centery - self.rect.centery
            angle = math.atan2(dy, dx)
        else:
            angle = math.radians(angle)

        self.vel_x = self.speed * math.cos(angle)
        self.vel_y = self.speed * math.sin(angle)

        rotation_angle = math.degrees(angle) + 90
        self.image = pygame.transform.rotate(self.image, -rotation_angle)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        if self.is_gathering_for_ultimate:
            dx = boss.ultimate_center_x - self.rect.centerx
            dy = boss.ultimate_center_y - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 2:  # 调整阈值，降低到 2 像素确保更早销毁
                max_dist_from_center = math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT)
                normalized_dist = dist / max_dist_from_center
                min_gather_speed = SCREEN_HEIGHT * 0.005 * SCALE_FACTOR
                max_gather_speed = SCREEN_HEIGHT * 0.02 * SCALE_FACTOR
                current_gather_speed = min_gather_speed + (max_gather_speed - min_gather_speed) * (1 - normalized_dist)
                self.rect.x += (dx / dist) * current_gather_speed if dist != 0 else 0
                self.rect.y += (dy / dist) * current_gather_speed if dist != 0 else 0
            else:
                self.kill()  # 聚集到中心后立即销毁
            return

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # 子弹屏幕循环后消失
        if self.teleport_count < 3:
            if self.rect.bottom < 0: self.rect.top = SCREEN_HEIGHT; self.teleport_count += 1
            elif self.rect.top > SCREEN_HEIGHT: self.rect.bottom = 0; self.teleport_count += 1
            if self.rect.right < 0: self.rect.left = SCREEN_WIDTH; self.teleport_count += 1
            elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0; self.teleport_count += 1
        else:
            if not screen.get_rect().colliderect(self.rect): self.kill()

# 新增：巨型子弹类
class UltimateGiantBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, initial_size, speed, damage):
        super().__init__()
        self.initial_x = x
        self.initial_y = y
        self.current_size = initial_size
        self.speed = speed
        self.damage = damage
        self.target_x = None # 初始设置为None，在fire时设置
        self.target_y = None # 初始设置为None，在fire时设置
        self.vel_x = 0
        self.vel_y = 0
        self.has_fired = False
        self.teleport_count = 0 # 传送次数
        self.max_teleports = 4 # 最大传送次数，达到后爆炸
        self.exploded = False # 是否已经爆炸

        self.image = pygame.Surface((self.current_size, self.current_size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, ULTIMATE_COLOR, (self.current_size // 2, self.current_size // 2), self.current_size // 2)
        self.rect = self.image.get_rect(center=(x, y))

    def set_size(self, new_size):
        if new_size <= 0: new_size = 1  # 避免尺寸为 0 或负数
        if new_size != self.current_size:
            self.current_size = new_size
            # 重新创建 Surface 以改变大小
            old_center = self.rect.center
            self.image = pygame.Surface((self.current_size, self.current_size), pygame.SRCALPHA)
            pygame.draw.circle(self.image, ULTIMATE_COLOR, (self.current_size // 2, self.current_size // 2), self.current_size // 2)
            self.rect = self.image.get_rect(center=old_center)

    def set_target(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y

    def fire(self, speed):
        self.speed = speed
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist != 0:
            self.vel_x = (dx / dist) * self.speed
            self.vel_y = (dy / dist) * self.speed
        else:
            # 如果目标和自身重合，随机一个方向发射
            angle = random.uniform(0, 2 * math.pi)
            self.vel_x = math.cos(angle) * self.speed
            self.vel_y = math.sin(angle) * self.speed
        self.has_fired = True

    def explode(self):
        """巨型子弹爆开分散成其他子弹"""
        num_scatter_bullets = 80 # 分散成更多子弹
        bullet_speed = SCREEN_HEIGHT * 0.01 # 分散子弹的速度
        for i in range(num_scatter_bullets):
            angle = (360 / num_scatter_bullets) * i
            bullet = CircularBullet(self.rect.centerx, self.rect.centery, bullet_speed, angle, RED) # 使用红色圆形子弹
            all_sprites.add(bullet)
            boss_bullets.add(bullet) # 将分散的子弹加入到 Boss 子弹组，这样它们可以伤害玩家

        screen_shake.start(duration=20, intensity=5) # 爆炸时屏幕轻微抖动
        self.kill() # 巨型子弹爆炸后销毁自身

    def update(self):
        if self.has_fired:
            self.rect.x += self.vel_x
            self.rect.y += self.vel_y
            
            if not self.exploded: # 只有在未爆炸时才进行传送和计数
                teleported_this_frame = False
                # 屏幕循环逻辑
                if self.rect.bottom < 0:
                    self.rect.top = SCREEN_HEIGHT
                    teleported_this_frame = True
                elif self.rect.top > SCREEN_HEIGHT:
                    self.rect.bottom = 0
                    teleported_this_frame = True
                if self.rect.right < 0:
                    self.rect.left = SCREEN_WIDTH
                    teleported_this_frame = True
                elif self.rect.left > SCREEN_WIDTH:
                    self.rect.right = 0
                    teleported_this_frame = True
                
                if teleported_this_frame:
                    self.teleport_count += 1
                    # 每次传送后重新设置方向，使其继续追踪玩家
                    if self.target_x is not None and self.target_y is not None:
                        dx = self.target_x - self.rect.centerx
                        dy = self.target_y - self.rect.centery
                        dist = math.hypot(dx, dy)
                        if dist != 0:
                            self.vel_x = (dx / dist) * self.speed
                            self.vel_y = (dy / dist) * self.speed
                        else: # 如果玩家和子弹重合，随机一个方向
                            angle = random.uniform(0, 2 * math.pi)
                            self.vel_x = math.cos(angle) * self.speed
                            self.vel_y = math.sin(angle) * self.speed


                if self.teleport_count >= self.max_teleports and not self.exploded:
                    self.explode()
                    self.exploded = True # 标记已爆炸
        else:
            # 蓄力阶段保持在中心
            self.rect.center = (self.initial_x, self.initial_y)

# 游戏状态
GAME_RUNNING = 0
GAME_OVER = 1
GAME_WIN = 2
game_state = GAME_RUNNING

# 精灵组
all_sprites = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
boss_bullets = pygame.sprite.Group()
minibosses = pygame.sprite.Group()
ultimate_bullets = pygame.sprite.Group()  # 新增巨弹精灵组

# 创建玩家和 Boss
player = Player()
all_sprites.add(player)
boss = Boss()
all_sprites.add(boss)

# 背景音乐加载和播放
# 注意: 确保 '1.wav' 文件存在于与脚本相同目录下
try:
    pygame.mixer.music.load("1.wav")
    pygame.mixer.music.play(-1)
except pygame.error as e:
    print(f"无法加载或播放音乐: {e}. 请确保 '1.wav' 文件存在。")

# 游戏循环
running = True
while running:
    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False  # 允许按 ESC 退出
            if event.key == pygame.K_SPACE and game_state == GAME_RUNNING:
                player.is_shooting = True  # 按下空格键开始自动射击
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                player.is_shooting = False  # 松开空格键停止自动射击

    # 游戏更新
    if game_state == GAME_RUNNING:
        all_sprites.update()

        # 玩家子弹命中 Boss
        hits = pygame.sprite.spritecollide(boss, player_bullets, True)
        for hit in hits:
            boss.health -= 10  # Boss 受到伤害
            if boss.health <= 0:
                game_state = GAME_WIN

        # 玩家子弹命中小 Boss
        hits = pygame.sprite.groupcollide(minibosses, player_bullets, False, True)
        for miniboss_hit, bullets_hit in hits.items():
            miniboss_hit.health -= 10 * len(bullets_hit)  # 小 Boss 受到伤害
            if miniboss_hit.health <= 0:
                miniboss_hit.kill()

        # Boss 子弹命中玩家
        hits = pygame.sprite.spritecollide(player, boss_bullets, True)
        for hit in hits:
            player.health -= 20  # 玩家 受到伤害
            if player.health <= 0:
                game_state = GAME_OVER

        # 小 Boss 碰撞玩家
        hits = pygame.sprite.spritecollide(player, minibosses, False)
        for miniboss_hit in hits:
            player.health -= 50  # 玩家 受到伤害
            if player.health <= 0:
                game_state = GAME_OVER

        # 巨型子弹命中玩家
        # 修正：不再立即销毁巨型子弹，只对玩家造成伤害
        hits = pygame.sprite.spritecollide(player, ultimate_bullets, False) # False 表示不销毁子弹
        for hit in hits:
            player.health -= 500  # 巨弹伤害
            if player.health <= 0:
                game_state = GAME_OVER

    # 绘制
    offset_x, offset_y = screen_shake.update()
    
    temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    temp_surface.fill(BLACK)

    all_sprites.draw(temp_surface)

    # 绘制 Boss 血条
    boss_health_bar_width = SCREEN_WIDTH * 0.2
    boss_health_bar_height = SCREEN_HEIGHT * 0.025
    boss_health_bar_x = SCREEN_WIDTH * 0.05
    boss_health_bar_y = SCREEN_HEIGHT * 0.025
    pygame.draw.rect(temp_surface, RED, (boss_health_bar_x, boss_health_bar_y, (boss.health / boss.max_health) * boss_health_bar_width, boss_health_bar_height), 0)  # 0 表示 填充
    pygame.draw.rect(temp_surface, WHITE, (boss_health_bar_x, boss_health_bar_y, boss_health_bar_width, boss_health_bar_height), 2)  # 边框

    # 绘制玩家血条
    player_health_bar_width = SCREEN_WIDTH * 0.2
    player_health_bar_height = SCREEN_HEIGHT * 0.025
    player_health_bar_x = SCREEN_WIDTH - SCREEN_WIDTH * 0.05 - player_health_bar_width
    player_health_bar_y = SCREEN_HEIGHT * 0.025
    display_player_health = max(0, player.health)  # 确保玩家血不会显示负值
    pygame.draw.rect(temp_surface, GREEN, (player_health_bar_x, player_health_bar_y, (display_player_health / 100) * player_health_bar_width, player_health_bar_height), 0)  # 0 表示 填充
    pygame.draw.rect(temp_surface, WHITE, (player_health_bar_x, player_health_bar_y, player_health_bar_width, player_health_bar_height), 2)  # 边框

    # 绘制小 Boss 血条
    for mb in minibosses:
        miniboss_health_bar_width = mb.rect.width * 0.8
        miniboss_health_bar_height = SCREEN_HEIGHT * 0.008
        miniboss_health_bar_x = mb.rect.x + mb.rect.width * 0.1
        miniboss_health_bar_y = mb.rect.y - miniboss_health_bar_height - 5
        pygame.draw.rect(temp_surface, MINIBOSS_COLOR, (miniboss_health_bar_x, miniboss_health_bar_y, (mb.health / mb.max_health) * miniboss_health_bar_width, miniboss_health_bar_height), 0)  # 修正这里！
        pygame.draw.rect(temp_surface, WHITE, (miniboss_health_bar_x, miniboss_health_bar_y, miniboss_health_bar_width, miniboss_health_bar_height), 1)

    # 游戏结束989900
    if game_state == GAME_OVER:
        font_size = int(SCREEN_HEIGHT * 0.1)
        font = pygame.font.Font('新宋体.TTF', font_size)
        text = font.render('新宋体.TTF', True, RED)
        text = font.render("残疾人就别玩这游戏了 ", True, RED)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        temp_surface.blit(text, text_rect)
    elif game_state == GAME_WIN:
        font_size = int(SCREEN_HEIGHT * 0.1)
        font = pygame.font.Font('新宋体.TTF', font_size)
        text = font.render("你的分数是：" + str(player.health) + "梁姐的记录是:985300", True, GREEN)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        temp_surface.blit(text, text_rect)

    screen.blit(temp_surface, (offset_x, offset_y))
    pygame.display.flip()
    clock.tick(FPS) 

pygame.quit()
sys.exit()

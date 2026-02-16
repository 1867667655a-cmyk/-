"""
游戏实体类定义
"""
import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

import pygame  # 添加pygame导入
import a99_4 as cfg


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

def norm_angle(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi

def circle_collide(x1, y1, r1, x2, y2, r2): 
    return (x1 - x2)**2 + (y1 - y2)**2 <= (r1 + r2)**2

def point_in_rotated_rect(px, py, rx, ry, width, height, angle):
    """检查点是否在旋转的矩形内"""
    cos_a = math.cos(-angle)
    sin_a = math.sin(-angle)
    
    dx = px - rx
    dy = py - ry
    
    local_x = dx * cos_a - dy * sin_a
    local_y = dx * sin_a + dy * cos_a
    
    return abs(local_x) <= width/2 and abs(local_y) <= height/2


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    lifetime: float = cfg.PARTICLE_LIFETIME
    age: float = 0.0

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt

    def alive(self) -> bool:
        return self.age <= self.lifetime


@dataclass
class Bullet:
    x: float
    y: float
    vx: float
    vy: float
    damage: int
    pierce: int
    radius: int
    color: Tuple[int, int, int]
    owner: str = "player"
    age: float = 0.0
    lifetime: float = cfg.BULLET_LIFETIME

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt

    def alive(self) -> bool:
        return (self.age <= self.lifetime and 
                -80 <= self.x <= cfg.WORLD_WIDTH + 80 and 
                -80 <= self.y <= cfg.WORLD_HEIGHT + 80)


@dataclass
class Hook:
    owner_x: float
    owner_y: float
    target_x: float
    target_y: float
    length: float = 0.0
    active: bool = True
    
    def update(self, dt: float, owner_x: float, owner_y: float) -> None:
        self.owner_x = owner_x
        self.owner_y = owner_y
        target_dist = math.hypot(self.target_x - self.owner_x, self.target_y - self.owner_y)
        self.length = min(self.length + cfg.HOOK_GROWTH_SPEED * dt, target_dist)
    
    def get_current_position(self) -> Tuple[float, float]:
        dx = self.target_x - self.owner_x
        dy = self.target_y - self.owner_y
        dist = math.hypot(dx, dy) or 1.0
        x = self.owner_x + (dx / dist) * self.length
        y = self.owner_y + (dy / dist) * self.length
        return x, y
        
    def is_hit(self) -> bool:
        target_dist = math.hypot(self.target_x - self.owner_x, self.target_y - self.owner_y)
        return self.length >= target_dist


@dataclass
class Laser:
    x: float
    y: float
    angle: float
    length: float
    width: int
    color: Tuple[int, int, int]
    active: bool = False
    timer: float = 0.0
    rotation_speed: float = cfg.LASER_ROTATION_SPEED_START
    ring_bullet_timer: float = 0.0


@dataclass
class Enemy:
    x: float
    y: float
    speed: float
    health: int = 3
    kind: str = "normal"
    radius: int = cfg.ENEMY_RADIUS
    weapon: str = ""
    shoot_cooldown: float = 0.0
    _blade_sweep_t: float = 0.0
    _blade_angle: float = 0.0
    _blade_hit_set: set = field(default_factory=set)
    dash_state: str = "idle"
    dash_timer: float = 0.0
    dash_cooldown: float = 0.0
    dash_dir_x: float = 0.0
    dash_dir_y: float = 0.0
    hook: Optional[Hook] = None
    aim_state: str = "idle"
    aim_timer: float = 0.0
    aim_target_x: float = 0.0
    aim_target_y: float = 0.0
    preferred_distance: float = 300
    circling_direction: int = 1
    laser: Optional[Laser] = None
    laser_cooldown: float = 0.0
    laser_state: str = "idle"
    is_dead: bool = False
    has_shield: bool = False
    blade_attack_cooldown: float = 0.0
    berserk_mode: bool = False
    particle_timer: float = 0.0
    particles: List[Particle] = field(default_factory=list)
    can_shoot: bool = True

    def update(self, dt: float, target_x: float, target_y: float, enemy_bullets: List[Bullet], 
               player_bullets: List[Bullet], minions: List['Enemy']) -> bool:
        if self.is_dead:
            return False
            
        # 更新计时器
        self._update_timers(dt)
        
        # 更新粒子效果
        self._update_particles(dt)
        
        # 计算到目标的距离和方向
        dist_to_target = math.hypot(target_x - self.x, target_y - self.y)
        dx, dy = target_x - self.x, target_y - self.y
        norm_dx, norm_dy = (dx / dist_to_target, dy / dist_to_target) if dist_to_target > 0 else (0, 0)
        
        # 处理不同类型的敌人逻辑
        if self.kind == "hook":
            return self._update_hook_enemy(dt, target_x, target_y)
        elif self.kind == "boss":
            return self._update_boss(dt, target_x, target_y, norm_dx, norm_dy, dist_to_target, enemy_bullets, minions)
        elif self.kind == "minion":
            return self._update_minion(dt, target_x, target_y, norm_dx, norm_dy, dist_to_target, enemy_bullets, player_bullets, minions)
        elif self.kind == "dash":
            return self._update_dash_enemy(dt, target_x, target_y, norm_dx, norm_dy)
        else:
            # 普通敌人移动
            self._move_towards_target(dt, norm_dx, norm_dy)
            return False

    def _update_timers(self, dt: float) -> None:
        """更新所有计时器"""
        if self._blade_sweep_t > 0: 
            self._blade_sweep_t -= dt
        if self.shoot_cooldown > 0: 
            self.shoot_cooldown -= dt
        if self.dash_cooldown > 0: 
            self.dash_cooldown -= dt
        if self.laser_cooldown > 0:
            self.laser_cooldown -= dt
        if self.blade_attack_cooldown > 0:
            self.blade_attack_cooldown -= dt

    def _update_particles(self, dt: float) -> None:
        """更新粒子效果"""
        if self.kind == "boss" and self.has_shield and not any(not m.is_dead for m in self.particles if hasattr(m, 'kind') and m.kind == "minion"):
            self.particle_timer += dt
            if self.particle_timer >= 0.05 and len(self.particles) < cfg.PARTICLE_COUNT * 3:
                for _ in range(3):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(cfg.PARTICLE_SPEED * 0.5, cfg.PARTICLE_SPEED * 1.5)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    self.particles.append(Particle(
                        self.x, self.y, vx, vy,
                        (random.randint(200, 255), random.randint(50, 150), random.randint(100, 200))
                    ))
                self.particle_timer = 0.0
        
        for particle in self.particles[:]:
            particle.update(dt)
            if not particle.alive():
                self.particles.remove(particle)

    def _update_hook_enemy(self, dt: float, target_x: float, target_y: float) -> bool:
        """更新钩子敌人逻辑"""
        if not self.hook:
            self.hook = Hook(self.x, self.y, target_x, target_y)
        else:
            self.hook.target_x = target_x
            self.hook.target_y = target_y
            self.hook.update(dt, self.x, self.y)
            
            if self.hook.is_hit():
                return True
        
        self._move_towards_target(dt, 
                                 (target_x - self.x) / max(math.hypot(target_x - self.x, target_y - self.y), 1),
                                 (target_y - self.y) / max(math.hypot(target_x - self.x, target_y - self.y), 1))
        return False

    def _update_boss(self, dt: float, target_x: float, target_y: float, norm_dx: float, norm_dy: float,
                    dist_to_target: float, enemy_bullets: List[Bullet], minions: List['Enemy']) -> bool:
        """更新BOSS逻辑"""
        # 检查护卫状态
        alive_minions = [m for m in minions if m.kind == "minion" and not m.is_dead]
        self.has_shield = len(alive_minions) > 0
        
        # BOSS移动
        if self.laser_state == "idle" and self.dash_state == "idle" and self.blade_attack_cooldown <= 0:
            self._move_towards_target(dt, norm_dx, norm_dy)
        
        # BOSS冲刺
        if not self.has_shield and self.dash_state == "idle" and self.dash_cooldown <= 0 and self.laser_state == "idle" and self.blade_attack_cooldown <= 0:
            self.dash_state = "prep"
            self.dash_timer = cfg.BOSS_DASH_PREP_TIME
        elif self.dash_state == "prep":
            self.dash_timer -= dt
            if self.dash_timer <= 0.0:
                d_dx, d_dy = target_x - self.x, target_y - self.y
                d = math.hypot(d_dx, d_dy) or 1.0
                self.dash_dir_x, self.dash_dir_y = d_dx/d, d_dy/d
                self.dash_state = "dashing"
                self.dash_timer = cfg.BOSS_DASH_MAX_TIME
        elif self.dash_state == "dashing":
            self.x += self.dash_dir_x * cfg.DASH_SPEED * dt
            self.y += self.dash_dir_y * cfg.DASH_SPEED * dt
            self.dash_timer -= dt
            
            hit_edge = not (self.radius <= self.x <= cfg.WORLD_WIDTH - self.radius and 
                           self.radius <= self.y <= cfg.WORLD_HEIGHT - self.radius)
            
            if hit_edge or self.dash_timer <= 0.0:
                self.dash_state = "cooldown"
                self.dash_cooldown = cfg.BOSS_DASH_COOLDOWN
        elif self.dash_state == "cooldown" and self.dash_cooldown <= 0:
            self.dash_state = "idle"
        
        # BOSS激光
        if self.has_shield and self.laser_state == "idle" and self.laser_cooldown <= 0 and self.dash_state == "idle" and self.blade_attack_cooldown <= 0:
            self._start_laser(target_x, target_y)
        elif self.laser_state == "prep":
            self.laser.timer += dt
            if self.laser.timer >= cfg.LASER_PREP_TIME:
                self.laser_state = "active"
                self.laser.timer = 0.0
                self.laser.active = True
        elif self.laser_state == "active":
            self._update_laser(dt, enemy_bullets)
        
        # BOSS大刀攻击
        if not self.has_shield and self.blade_attack_cooldown <= 0 and dist_to_target < cfg.BOSS_BLADE_RANGE:
            self._blade_angle = math.atan2(norm_dy, norm_dx)
            self._blade_sweep_t = cfg.BOSS_BLADE_SWEEP_TIME
            self._blade_hit_set.clear()
            self.blade_attack_cooldown = cfg.BOSS_BLADE_COOLDOWN
        
        return False

    def _start_laser(self, target_x: float, target_y: float) -> None:
        """开始激光攻击"""
        self.laser_state = "prep"
        laser_angle = math.atan2(target_y - self.y, target_x - self.x)
        laser_length = self.calculate_laser_length(laser_angle)
        
        self.laser = Laser(
            x=self.x,
            y=self.y,
            angle=laser_angle,
            length=laser_length,
            width=cfg.LASER_WIDTH,
            color=cfg.LASER_COLOR,
            timer=0.0
        )

    def _update_laser(self, dt: float, enemy_bullets: List[Bullet]) -> None:
        """更新激光状态"""
        self.laser.timer += dt
        
        # 更新激光旋转速度
        progress = self.laser.timer / cfg.LASER_DURATION
        self.laser.rotation_speed = cfg.LASER_ROTATION_SPEED_START + (cfg.LASER_ROTATION_SPEED_END - cfg.LASER_ROTATION_SPEED_START) * progress
        
        # 旋转激光
        self.laser.angle -= self.laser.rotation_speed * dt
        self.laser.length = self.calculate_laser_length(self.laser.angle)
        
        # 发射环形子弹
        self.laser.ring_bullet_timer += dt
        if self.laser.ring_bullet_timer >= cfg.LASER_RING_COOLDOWN:
            start_angle = random.uniform(0, 2 * math.pi)
            for i in range(cfg.LASER_RING_BULLETS):
                angle = start_angle + 2 * math.pi * i / cfg.LASER_RING_BULLETS
                vx = math.cos(angle) * cfg.RIFLE_SPEED * 0.7
                vy = math.sin(angle) * cfg.RIFLE_SPEED * 0.7
                enemy_bullets.append(Bullet(
                    self.x, self.y, vx, vy, 
                    cfg.RIFLE_DAMAGE, 0, 4, cfg.ENEMY_BULLET_COLOR, 
                    "enemy", lifetime=999.0
                ))
            self.laser.ring_bullet_timer = 0.0
        
        # 检查激光结束
        if self.laser.timer >= cfg.LASER_DURATION:
            self.laser_state = "idle"
            self.laser_cooldown = cfg.LASER_COOLDOWN
            self.laser.active = False

    def _update_minion(self, dt: float, target_x: float, target_y: float, norm_dx: float, norm_dy: float,
                      dist_to_target: float, enemy_bullets: List[Bullet], player_bullets: List[Bullet], 
                      minions: List['Enemy']) -> bool:
        """更新护卫逻辑"""
        # 检查存活护卫数量
        alive_minions = [m for m in minions if m.kind == "minion" and not m.is_dead]
        alive_count = len(alive_minions)
        
        # 狂暴模式
        if alive_count == 1:
            self.berserk_mode = True
            self.speed = cfg.MINION_SPEED * 1.5
            if self.weapon == "rifle":
                self.shoot_cooldown = max(0, self.shoot_cooldown - dt * 2)
            else:
                self.shoot_cooldown = max(0, self.shoot_cooldown - dt * 1.5)
        else:
            self.berserk_mode = False
            self.speed = cfg.MINION_SPEED
        
        # 限制开火数量
        if alive_count >= 4:
            can_shoot_minions = [m for m in alive_minions if (m.shoot_cooldown <= 0 or 
                                                            (m.weapon == "blade" and m.dash_cooldown <= 0)) and m != self]
            self.can_shoot = len(can_shoot_minions) < 2
        else:
            self.can_shoot = True
        
        # 根据武器类型处理
        if self.weapon == "blade":
            self._update_blade_minion(dt, target_x, target_y, dist_to_target, player_bullets)
        elif self.weapon == "sniper":
            self._update_sniper_minion(dt, target_x, target_y, enemy_bullets)
        elif self.weapon == "shotgun" and self.can_shoot and self.shoot_cooldown <= 0:
            self._shoot_shotgun(target_x, target_y, norm_dx, norm_dy, enemy_bullets)
        elif self.weapon == "rifle" and self.can_shoot and self.shoot_cooldown <= 0:
            self._shoot_rifle(norm_dx, norm_dy, enemy_bullets)
        
        # 护卫移动
        if self.weapon in ["sniper", "rifle"]:
            self._move_circling(dt, target_x, target_y, norm_dx, norm_dy, dist_to_target)
        else:
            self._move_towards_target(dt, norm_dx, norm_dy)
        
        return False

    def _update_blade_minion(self, dt: float, target_x: float, target_y: float, 
                            dist_to_target: float, player_bullets: List[Bullet]) -> None:
        """更新大刀护卫"""
        # 冲刺逻辑
        if self.dash_state == "idle" and self.dash_cooldown <= 0 and self.can_shoot:
            self.dash_state = "prep"
            self.dash_timer = cfg.DASH_PREP_TIME
        elif self.dash_state == "prep":
            self.dash_timer -= dt
            if self.dash_timer <= 0.0:
                d_dx, d_dy = target_x - self.x, target_y - self.y
                d = math.hypot(d_dx, d_dy) or 1.0
                self.dash_dir_x, self.dash_dir_y = d_dx/d, d_dy/d
                self.dash_state = "dashing"
                self.dash_timer = cfg.DASH_MAX_TIME
        elif self.dash_state == "dashing":
            self.x += self.dash_dir_x * cfg.DASH_SPEED * dt
            self.y += self.dash_dir_y * cfg.DASH_SPEED * dt
            self.dash_timer -= dt
            
            hit_edge = not (self.radius <= self.x <= cfg.WORLD_WIDTH - self.radius and 
                           self.radius <= self.y <= cfg.WORLD_HEIGHT - self.radius)
            
            if hit_edge or self.dash_timer <= 0.0:
                self.dash_cooldown = 0.0 if hit_edge else cfg.BLADE_MINION_DASH_CD
                self.dash_state = "idle"
        
        # 刀锋攻击
        if self.can_shoot and self.shoot_cooldown <= 0 and dist_to_target < cfg.BLADE_MINION_BLADE_RANGE:
            self._blade_angle = math.atan2((target_y - self.y), (target_x - self.x))
            self._blade_sweep_t = cfg.BLADE_SWEEP_TIME
            self._blade_hit_set.clear()
            self.shoot_cooldown = cfg.BLADE_COOLDOWN * (0.5 if self.berserk_mode else 1.2)
            
            # 砍碎玩家子弹
            for bullet in player_bullets[:]:
                if circle_collide(self.x, self.y, cfg.BLADE_MINION_BLADE_RANGE, bullet.x, bullet.y, bullet.radius):
                    player_bullets.remove(bullet)

    def _update_sniper_minion(self, dt: float, target_x: float, target_y: float, enemy_bullets: List[Bullet]) -> None:
        """更新狙击护卫"""
        if self.aim_state == "idle" and self.can_shoot and self.shoot_cooldown <= 0:
            self.aim_state = "aiming"
            self.aim_timer = cfg.SNIPER_MINION_AIM_TIME * (0.6 if self.berserk_mode else 1.0)
            self.aim_target_x, self.aim_target_y = target_x, target_y
        
        elif self.aim_state == "aiming":
            self.aim_target_x, self.aim_target_y = target_x, target_y
            self.aim_timer -= dt
            
            if self.aim_timer <= 0:
                aim_dx, aim_dy = self.aim_target_x - self.x, self.aim_target_y - self.y
                d = math.hypot(aim_dx, aim_dy) or 1.0
                spawn_x = self.x + (aim_dx / d) * (self.radius + 8)
                spawn_y = self.y + (aim_dy / d) * (self.radius + 8)
                vx = (aim_dx / d) * cfg.SNIPER_MINION_BULLET_SPEED
                vy = (aim_dy / d) * cfg.SNIPER_MINION_BULLET_SPEED
                
                enemy_bullets.append(Bullet(
                    spawn_x, spawn_y, vx, vy, 
                    cfg.SNIPER_DAMAGE, 0, 5, cfg.SNIPER_BULLET_COLOR, 
                    "enemy", lifetime=999.0
                ))
                self.shoot_cooldown = cfg.MINION_SHOOT_COOLDOWN * (0.5 if self.berserk_mode else 1.5)
                self.aim_state = "idle"

    def _shoot_shotgun(self, target_x: float, target_y: float, norm_dx: float, norm_dy: float, 
                       enemy_bullets: List[Bullet]) -> None:
        """散弹护卫射击"""
        base_angle = math.atan2(norm_dy, norm_dx)
        spawn_x = self.x + norm_dx * (self.radius + 6)
        spawn_y = self.y + norm_dy * (self.radius + 6)
        
        for _ in range(cfg.SHOTGUN_MINION_PELLETS):
            angle = base_angle + random.uniform(-1, 1) * math.radians(cfg.SHOTGUN_MINION_SPREAD)
            vx = math.cos(angle) * cfg.SHOTGUN_SPEED
            vy = math.sin(angle) * cfg.SHOTGUN_SPEED
            enemy_bullets.append(Bullet(
                spawn_x, spawn_y, vx, vy, 
                cfg.SHOTGUN_DAMAGE, 0, 3, cfg.ENEMY_BULLET_COLOR, 
                "enemy", lifetime=999.0
            ))
        self.shoot_cooldown = cfg.MINION_SHOOT_COOLDOWN * (0.7 if self.berserk_mode else 0.8)

    def _shoot_rifle(self, norm_dx: float, norm_dy: float, enemy_bullets: List[Bullet]) -> None:
        """步枪护卫射击"""
        spawn_x = self.x + norm_dx * (self.radius + 6)
        spawn_y = self.y + norm_dy * (self.radius + 6)
        vx = norm_dx * cfg.RIFLE_SPEED
        vy = norm_dy * cfg.RIFLE_SPEED
        enemy_bullets.append(Bullet(
            spawn_x, spawn_y, vx, vy, 
            cfg.RIFLE_DAMAGE, 0, 3, cfg.ENEMY_BULLET_COLOR, 
            "enemy", lifetime=999.0
        ))
        self.shoot_cooldown = cfg.RIFLE_MINION_COOLDOWN * (0.3 if self.berserk_mode else 1.0)

    def _update_dash_enemy(self, dt: float, target_x: float, target_y: float, norm_dx: float, norm_dy: float) -> bool:
        """更新冲刺敌人逻辑"""
        if self.dash_state in ["prep", "dashing"]: 
            pass
        if self.dash_state == "idle" and self.dash_cooldown <= 0: 
            self.dash_state = "prep"
            self.dash_timer = cfg.DASH_PREP_TIME
        elif self.dash_state == "prep":
            self.dash_timer -= dt
            if self.dash_timer <= 0.0:
                d_dx, d_dy = target_x - self.x, target_y - self.y
                d = math.hypot(d_dx, d_dy) or 1.0
                self.dash_dir_x, self.dash_dir_y = d_dx/d, d_dy/d
                self.dash_state = "dashing"
                self.dash_timer = cfg.DASH_MAX_TIME
        elif self.dash_state == "dashing":
            self.x += self.dash_dir_x * cfg.DASH_SPEED * dt
            self.y += self.dash_dir_y * cfg.DASH_SPEED * dt
            self.dash_timer -= dt
            hit_edge = not (self.radius <= self.x <= cfg.WORLD_WIDTH - self.radius and 
                           self.radius <= self.y <= cfg.WORLD_HEIGHT - self.radius)
            if hit_edge: 
                self.dash_state = "prep"
                self.dash_timer = cfg.DASH_PREP_TIME
            elif self.dash_timer <= 0.0: 
                self.dash_state = "cooldown"
                self.dash_cooldown = cfg.DASH_COOLDOWN_TIME
        elif self.dash_state == "cooldown" and self.dash_cooldown <= 0: 
            self.dash_state = "idle"

        if self.dash_state == "idle":
            self._move_towards_target(dt, norm_dx, norm_dy)
        
        return False

    def _move_towards_target(self, dt: float, dir_x: float, dir_y: float) -> None:
        """向目标移动"""
        self.x += dir_x * self.speed * dt
        self.y += dir_y * self.speed * dt
        self.x = clamp(self.x, self.radius, cfg.WORLD_WIDTH - self.radius)
        self.y = clamp(self.y, self.radius, cfg.WORLD_HEIGHT - self.radius)

    def _move_circling(self, dt: float, target_x: float, target_y: float, norm_dx: float, norm_dy: float,
                      dist_to_target: float) -> None:
        """环绕移动（用于狙击和步枪护卫）"""
        radial_force = 1.0 if dist_to_target > self.preferred_distance else -1.0
        tangent_dx, tangent_dy = -norm_dy * self.circling_direction, norm_dx * self.circling_direction
        final_dx = norm_dx * radial_force * 0.3 + tangent_dx * 0.7
        final_dy = norm_dy * radial_force * 0.3 + tangent_dy * 0.7
        length = math.hypot(final_dx, final_dy) or 1.0
        self.x += (final_dx / length) * self.speed * dt
        self.y += (final_dy / length) * self.speed * dt
        self.x = clamp(self.x, self.radius, cfg.WORLD_WIDTH - self.radius)
        self.y = clamp(self.y, self.radius, cfg.WORLD_HEIGHT - self.radius)

    def calculate_laser_length(self, angle: float) -> float:
        """计算激光长度，确保激光末端到达地图边界"""
        x, y = self.x, self.y
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        
        distances = []
        
        if cos_angle > 0:
            dist_to_right = (cfg.WORLD_WIDTH - x) / cos_angle
            distances.append(dist_to_right)
        elif cos_angle < 0:
            dist_to_left = (0 - x) / cos_angle
            distances.append(dist_to_left)
        
        if sin_angle > 0:
            dist_to_bottom = (cfg.WORLD_HEIGHT - y) / sin_angle
            distances.append(dist_to_bottom)
        elif sin_angle < 0:
            dist_to_top = (0 - y) / sin_angle
            distances.append(dist_to_top)
        
        if distances:
            return min([d for d in distances if d > 0])
        return 1000


@dataclass
class Player:
    x: float
    y: float
    health: int = cfg.PLAYER_MAX_HEALTH
    _shoot_cooldown: float = 0.0
    _hurt_cooldown: float = 0.0
    weapon: str = "shotgun"
    _blade_sweep_t: float = 0.0
    _blade_angle: float = 0.0
    _blade_hit_set: set = field(default_factory=set)
    snared_by: int = 0
    snared: bool = False
    _switch_lock: float = 0.0
    dash_cooldown: float = 0.0
    dash_duration: float = 0.0
    is_dashing: bool = False
    dash_direction_x: float = 0.0
    dash_direction_y: float = 0.0
    dash_particles: List[Particle] = field(default_factory=list)

    def update(self, dt: float, keys, enemies: List[Enemy]) -> None:
        move_x, move_y = 0.0, 0.0
        
        # 更新冲刺冷却
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
            
        # 更新冲刺粒子效果
        for particle in self.dash_particles[:]:
            particle.update(dt)
            if not particle.alive():
                self.dash_particles.remove(particle)
        
        # 处理冲刺状态
        if self.is_dashing:
            self._update_dash(dt)
        
        # 钩子拉扯逻辑
        if self.snared:
            self._update_hooked(dt, enemies)
        else:
            # 正常移动
            if not self.is_dashing:
                if keys[pygame.K_w]: move_y -= 1.0
                if keys[pygame.K_s]: move_y += 1.0
                if keys[pygame.K_a]: move_x -= 1.0
                if keys[pygame.K_d]: move_x += 1.0
        
        # 应用移动
        if (move_x or move_y) and not self.is_dashing:
            length = math.hypot(move_x, move_y)
            self.x += (move_x / length) * cfg.PLAYER_SPEED * dt
            self.y += (move_y / length) * cfg.PLAYER_SPEED * dt
        
        # 限制位置
        self.x = clamp(self.x, cfg.PLAYER_RADIUS, cfg.WORLD_WIDTH - cfg.PLAYER_RADIUS)
        self.y = clamp(self.y, cfg.PLAYER_RADIUS, cfg.WORLD_HEIGHT - cfg.PLAYER_RADIUS)
        
        # 更新计时器
        if self._shoot_cooldown > 0: 
            self._shoot_cooldown -= dt
        if self._hurt_cooldown > 0: 
            self._hurt_cooldown -= dt
        if self._blade_sweep_t > 0: 
            self._blade_sweep_t -= dt
        if self._switch_lock > 0: 
            self._switch_lock -= dt

    def _update_dash(self, dt: float) -> None:
        """更新冲刺状态"""
        self.dash_duration -= dt
        # 冲刺移动
        self.x += self.dash_direction_x * cfg.PLAYER_DASH_SPEED * dt
        self.y += self.dash_direction_y * cfg.PLAYER_DASH_SPEED * dt
        
        # 生成冲刺粒子效果
        if random.random() < 0.7:
            angle = math.atan2(-self.dash_direction_y, -self.dash_direction_x) + random.uniform(-0.5, 0.5)
            speed = random.uniform(cfg.PARTICLE_SPEED * 0.3, cfg.PARTICLE_SPEED * 0.7)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.dash_particles.append(Particle(
                self.x, self.y, vx, vy,
                cfg.PLAYER_DASH_COLOR,
                lifetime=random.uniform(0.2, 0.4)
            ))
        
        # 冲刺结束
        if self.dash_duration <= 0:
            self.is_dashing = False
            self.dash_cooldown = cfg.PLAYER_DASH_COOLDOWN

    def _update_hooked(self, dt: float, enemies: List[Enemy]) -> None:
        """更新被钩住状态"""
        # 如果被钩住，中断冲刺
        if self.is_dashing:
            self.is_dashing = False
            self.dash_cooldown = cfg.PLAYER_DASH_COOLDOWN * 0.5
        
        hook_owner = next((e for e in enemies if id(e) == self.snared_by), None)
        if hook_owner and hook_owner.hook and hook_owner.hook.active:
            dx, dy = hook_owner.x - self.x, hook_owner.y - self.y
            dist = math.hypot(dx, dy) or 1.0
            if dist > hook_owner.radius + cfg.PLAYER_RADIUS + 5:
                self.x += (dx / dist) * cfg.HOOK_PULL_SPEED * dt
                self.y += (dy / dist) * cfg.HOOK_PULL_SPEED * dt
        else: 
            self.snared = False
            self.snared_by = 0

    def try_dash(self, mouse_pos: Tuple[int, int]) -> bool:
        """尝试发动冲刺，返回是否成功"""
        if self.dash_cooldown > 0 or self.is_dashing:
            return False
            
        # 计算冲刺方向
        dx, dy = mouse_pos[0] - self.x, mouse_pos[1] - self.y
        dist = math.hypot(dx, dy) or 1.0
        self.dash_direction_x, self.dash_direction_y = dx / dist, dy / dist
        
        # 设置冲刺状态
        self.is_dashing = True
        self.dash_duration = cfg.PLAYER_DASH_DURATION
        
        # 生成初始冲刺粒子效果
        for _ in range(8):
            angle = math.atan2(-self.dash_direction_y, -self.dash_direction_x) + random.uniform(-0.8, 0.8)
            speed = random.uniform(cfg.PARTICLE_SPEED * 0.5, cfg.PARTICLE_SPEED)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.dash_particles.append(Particle(
                self.x, self.y, vx, vy,
                cfg.PLAYER_DASH_COLOR,
                lifetime=random.uniform(0.3, 0.6)
            ))
        
        return True

    def try_shoot(self, mouse_pos: Tuple[int, int], bullets: List[Bullet]) -> None:
        if self._shoot_cooldown > 0 or self.is_dashing:
            return
        
        dx, dy = mouse_pos[0] - self.x, mouse_pos[1] - self.y
        dist = math.hypot(dx, dy) or 1.0
        dir_x, dir_y = dx / dist, dy / dist
        
        spawn_x = self.x + dir_x * (cfg.PLAYER_RADIUS + 8)
        spawn_y = self.y + dir_y * (cfg.PLAYER_RADIUS + 8)
        
        if self.weapon == "shotgun":
            base_angle = math.atan2(dir_y, dir_x)
            for _ in range(cfg.SHOTGUN_PELLETS):
                angle = base_angle + random.uniform(-1, 1) * math.radians(cfg.SHOTGUN_SPREAD_DEG)
                vx = math.cos(angle) * cfg.SHOTGUN_SPEED
                vy = math.sin(angle) * cfg.SHOTGUN_SPEED
                bullets.append(Bullet(spawn_x, spawn_y, vx, vy, cfg.SHOTGUN_DAMAGE, 0, 3, cfg.BULLET_COLOR))
            self._shoot_cooldown = cfg.SHOTGUN_COOLDOWN
        elif self.weapon == "sniper":
            vx, vy = dir_x * cfg.SNIPER_SPEED, dir_y * cfg.SNIPER_SPEED
            bullets.append(Bullet(spawn_x, spawn_y, vx, vy, cfg.SNIPER_DAMAGE, cfg.SNIPER_PIERCE, 5, cfg.SNIPER_BULLET_COLOR))
            self._shoot_cooldown = cfg.SNIPER_COOLDOWN
        else:
            vx, vy = dir_x * cfg.RIFLE_SPEED, dir_y * cfg.RIFLE_SPEED
            bullets.append(Bullet(spawn_x, spawn_y, vx, vy, cfg.RIFLE_DAMAGE, 0, 3, cfg.BULLET_COLOR))
            self._shoot_cooldown = cfg.RIFLE_COOLDOWN

    def take_hit(self) -> bool:
        # 冲刺时无敌（除了钩子）
        if self._hurt_cooldown > 0 or self.is_dashing:
            return False
        self.health -= 1
        self._hurt_cooldown = cfg.PLAYER_TOUCH_DAMAGE_COOLDOWN
        return True

    def is_alive(self) -> bool: 
        return self.health > 0

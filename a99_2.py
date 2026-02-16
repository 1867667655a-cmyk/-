"""
游戏引擎 - 包含游戏逻辑和渲染功能
"""
import math
import random
from typing import List, Tuple

import pygame

import a99_4 as cfg
from a99_3 import (
    Player, Enemy, Bullet, Particle, 
    circle_collide, point_in_rotated_rect, norm_angle, clamp
)


class GameEngine:
    """游戏引擎类，处理游戏逻辑和渲染"""
    
    def __init__(self):
        self.score = 0
        self.boss_spawned = False
        self.spawn_timer = 0.0
        self.spawn_interval = cfg.ENEMY_SPAWN_INTERVAL_START
        self.boss_berserk_timer = 0.0
        self.cam_x, self.cam_y = 0.0, 0.0
    
    def spawn_enemy_just_offscreen(self) -> Enemy:
        """在屏幕外生成一个随机类型的敌人"""
        margin = 40
        side = random.randint(0, 3)
        
        if side == 0:  # 上边
            x, y = random.uniform(-margin, cfg.WORLD_WIDTH + margin), -margin
        elif side == 1:  # 下边
            x, y = random.uniform(-margin, cfg.WORLD_WIDTH + margin), cfg.WORLD_HEIGHT + margin
        elif side == 2:  # 左边
            x, y = -margin, random.uniform(-margin, cfg.WORLD_HEIGHT + margin)
        else:  # 右边
            x, y = cfg.WORLD_WIDTH + margin, random.uniform(-margin, cfg.WORLD_HEIGHT + margin)
        
        # 随机选择敌人类型
        r, c, choice = random.random(), 0.0, "normal"
        for k, w in cfg.SPAWN_WEIGHTS.items():
            c += w
            if r <= c: 
                choice = k
                break
        
        # 根据类型设置属性
        if choice == "speed":
            s = cfg.PLAYER_SPEED
            h = cfg.ENEMY_HEALTH_NORMAL
            k = "speed"
        elif choice == "tank":
            s = random.uniform(cfg.ENEMY_SPEED_MIN * 0.8, cfg.ENEMY_SPEED_MAX * 0.9)
            h = cfg.ENEMY_HEALTH_NORMAL * cfg.ENEMY_HEALTH_MULT_TANK
            k = "tank"
        elif choice == "random":
            s = random.uniform(cfg.RANDOM_ENEMY_SPEED_MIN, cfg.RANDOM_ENEMY_SPEED_MAX)
            h = random.randint(cfg.RANDOM_ENEMY_HEALTH_MIN, cfg.RANDOM_ENEMY_HEALTH_MAX)
            k = "random"
        elif choice == "dash":
            s = random.uniform(cfg.ENEMY_SPEED_MIN, cfg.ENEMY_SPEED_MAX)
            h = cfg.ENEMY_HEALTH_NORMAL * 2
            k = "dash"
        elif choice == "hook":
            s = cfg.HOOK_SPEED
            h = 1
            k = "hook"
        else:
            s = random.uniform(cfg.ENEMY_SPEED_MIN, cfg.ENEMY_SPEED_MAX)
            h = cfg.ENEMY_HEALTH_NORMAL
            k = "normal"
        
        # 设置敌人半径
        rad = cfg.ENEMY_RADIUS
        if k == "tank":
            rad = int(cfg.ENEMY_RADIUS * 1.6)
        elif k == "random":
            rad = random.randint(int(cfg.ENEMY_RADIUS * 0.6), int(cfg.ENEMY_RADIUS * 2.3))
        elif k == "dash":
            rad = int(cfg.ENEMY_RADIUS * 1.2)
        elif k == "hook":
            rad = int(cfg.ENEMY_RADIUS * 1.3)
        
        return Enemy(x, y, s, health=h, kind=k, radius=rad)
    
    def spawn_boss_and_minions(self) -> List[Enemy]:
        """生成BOSS和四个护卫"""
        boss = Enemy(cfg.WORLD_WIDTH/2, cfg.BOSS_RADIUS*2, cfg.BOSS_SPEED, 
                     health=cfg.BOSS_HEALTH, kind="boss", radius=cfg.BOSS_RADIUS)
        minions = [boss]
        
        # 创建四个不同武器的护卫
        weapons = ["blade", "sniper", "shotgun", "rifle"]
        corners = [
            (cfg.MINION_RADIUS, cfg.MINION_RADIUS),
            (cfg.WORLD_WIDTH - cfg.MINION_RADIUS, cfg.MINION_RADIUS),
            (cfg.WORLD_WIDTH - cfg.MINION_RADIUS, cfg.WORLD_HEIGHT - cfg.MINION_RADIUS),
            (cfg.MINION_RADIUS, cfg.WORLD_HEIGHT - cfg.MINION_RADIUS)
        ]
        random.shuffle(corners)
        
        for i, weapon in enumerate(weapons):
            mx, my = corners[i]
            cd = random.choice([1, -1])
            pd = random.uniform(300, 500)
            
            # 根据武器类型调整属性
            if weapon == "blade":
                health = cfg.MINION_HEALTH * 1.5
                speed = cfg.MINION_SPEED * 1.1
                radius = int(cfg.MINION_RADIUS * 1.2)
            elif weapon == "sniper":
                health = cfg.MINION_HEALTH * 0.8
                speed = cfg.MINION_SPEED * 0.9
                radius = cfg.MINION_RADIUS
                pd = 400
            elif weapon == "shotgun":
                health = cfg.MINION_HEALTH
                speed = cfg.MINION_SPEED
                radius = cfg.MINION_RADIUS
            else:  # rifle
                health = cfg.MINION_HEALTH * 0.9
                speed = cfg.MINION_SPEED
                radius = cfg.MINION_RADIUS
                pd = 350
            
            minion = Enemy(
                mx, my, speed, 
                health=health, 
                kind="minion", 
                radius=radius, 
                weapon=weapon, 
                preferred_distance=pd, 
                circling_direction=cd
            )
            minions.append(minion)
        
        return minions
    
    def handle_bullet_collisions(self, bullets: List[Bullet], enemies: List[Enemy], player: Player) -> int:
        """处理子弹碰撞，返回增加的分数"""
        score_increase = 0
        enemies_to_remove = []
        
        for e in enemies[:]:
            for b in bullets[:]:
                if b.owner == "player" and e.health > 0 and circle_collide(e.x, e.y, e.radius, b.x, b.y, b.radius):
                    # 如果BOSS有护盾，受到的伤害归零
                    if e.kind == "boss" and e.has_shield:
                        damage = 0
                    else:
                        damage = b.damage
                        
                    e.health -= damage
                    if b.pierce <= 0:
                        b.age = b.lifetime + 1
                    else:
                        b.pierce -= 1
            
            # 敌人与玩家碰撞
            if e.kind not in ["minion", "boss"] and not player.is_dashing:
                pr = cfg.PLAYER_RADIUS * cfg.PLAYER_HIT_RADIUS_SCALE
                if circle_collide(player.x, player.y, pr, e.x, e.y, e.radius * cfg.ENEMY_HIT_RADIUS_SCALE):
                    if player.take_hit():
                        e.health = 0
            
            # BOSS冲刺伤害
            elif e.kind == "boss" and e.dash_state == "dashing" and not player.is_dashing:
                pr = cfg.PLAYER_RADIUS * cfg.PLAYER_HIT_RADIUS_SCALE
                if circle_collide(player.x, player.y, pr, e.x, e.y, e.radius * cfg.ENEMY_HIT_RADIUS_SCALE):
                    player.take_hit()
        
        # 处理敌人死亡
        for e in enemies:
            if e.health <= 0 and e.kind != "minion":
                enemies_to_remove.append(e)
            elif e.health <= 0 and e.kind == "minion" and not e.is_dead:
                e.is_dead = True
                e.health = 1
        
        # 计算分数并移除敌人
        for e in enemies_to_remove:
            if player.snared and player.snared_by == id(e):
                player.snared = False
                player.snared_by = 0
            
            if e.kind == "boss":
                score_increase += 50
            elif e.kind == "minion":
                score_increase += 10
            else:
                score_increase += 2
        
        # 从敌人列表中移除死亡的敌人
        for e in enemies_to_remove:
            if e in enemies:
                enemies.remove(e)
        
        return score_increase
    
    def handle_enemy_bullet_collisions(self, enemy_bullets: List[Bullet], player: Player) -> None:
        """处理敌人子弹与玩家碰撞"""
        for b in enemy_bullets[:]:
            if not player.is_dashing:  # 冲刺时无敌
                pr = cfg.PLAYER_RADIUS * cfg.PLAYER_HIT_RADIUS_SCALE
                if circle_collide(player.x, player.y, pr, b.x, b.y, b.radius):
                    if player.take_hit():
                        b.age = b.lifetime + 1
    
    def handle_laser_collisions(self, enemies: List[Enemy], player: Player) -> None:
        """处理激光与玩家碰撞"""
        for e in enemies:
            if e.kind == "boss" and e.laser and e.laser.active:
                # 计算激光的终点
                laser_end_x = e.laser.x + math.cos(e.laser.angle) * e.laser.length
                laser_end_y = e.laser.y + math.sin(e.laser.angle) * e.laser.length
                
                # 检查玩家是否在激光范围内（激光无视冲刺无敌）
                if point_in_rotated_rect(
                    player.x, player.y,
                    (e.laser.x + laser_end_x) / 2, (e.laser.y + laser_end_y) / 2,
                    e.laser.length, e.laser.width, e.laser.angle
                ):
                    player.take_hit()
    
    def handle_blade_attacks(self, player: Player, enemies: List[Enemy]) -> None:
        """处理所有刀锋攻击"""
        all_blades = [p for p in [player] + enemies if getattr(p, '_blade_sweep_t', 0) > 0 and not (hasattr(p, 'is_dead') and p.is_dead)]
        
        for entity in all_blades:
            # 确定刀锋参数
            if hasattr(entity, 'kind') and entity.kind == "boss" and not entity.has_shield:
                half_arc_rad = math.radians(cfg.BOSS_BLADE_ARC_DEG / 2)
                blade_range = cfg.BOSS_BLADE_RANGE
            else:
                half_arc_rad = math.radians(cfg.BLADE_ARC_DEG / 2)
                blade_range = cfg.BLADE_RANGE
            
            ux, uy = math.cos(entity._blade_angle), math.sin(entity._blade_angle)
            
            e_rad = cfg.PLAYER_RADIUS if hasattr(entity, 'weapon') else entity.radius
            hand_offset = e_rad * cfg.BLADE_HAND_OFFSET
            hx, hy = entity.x + ux * hand_offset, entity.y + uy * hand_offset
            
            # 确定目标实体
            if entity == player:
                target_entities = enemies
            else:
                target_entities = [player]
            
            for target in target_entities:
                if id(target) in entity._blade_hit_set or target.health <= 0:
                    continue
                
                # 玩家在冲刺时免疫刀锋攻击（除了BOSS的刀锋）
                if hasattr(target, 'is_dashing') and target.is_dashing and not (hasattr(entity, 'kind') and entity.kind == "boss"):
                    continue
                
                target_radius = cfg.PLAYER_RADIUS if hasattr(target, 'weapon') else target.radius
                ex, ey = target.x - hx, target.y - hy
                r = math.hypot(ex, ey)
                
                if 0 < r < (blade_range + target_radius):
                    delta_angle = norm_angle(math.atan2(ey, ex) - entity._blade_angle)
                    if abs(delta_angle) <= half_arc_rad:
                        if entity == player:  # 玩家攻击敌人
                            # 确定伤害
                            if hasattr(target, 'kind') and target.kind == "boss" and not target.has_shield:
                                damage = cfg.BOSS_BLADE_DAMAGE
                            else:
                                damage = cfg.BLADE_DAMAGE
                            target.health -= damage
                            if r > 0:
                                target.x += (ex / r) * cfg.BLADE_KNOCKBACK
                                target.y += (ey / r) * cfg.BLADE_KNOCKBACK
                            if hasattr(target, 'dash_state') and target.dash_state in ["prep", "dashing"]:
                                target.dash_state = "cooldown"
                                target.dash_cooldown = cfg.DASH_COOLDOWN_TIME
                        else:  # 敌人攻击玩家
                            player.take_hit()
                            
                        entity._blade_hit_set.add(id(target))
    
    def update_boss_berserk_state(self, boss: Enemy, enemies: List[Enemy], boss_berserk_timer: float) -> float:
        """更新BOSS狂暴状态"""
        minions = [e for e in enemies if e.kind == "minion"]
        alive_minions = [m for m in minions if not m.is_dead]
        
        # 当场上有护卫时，BOSS解除狂暴状态
        if boss and len(alive_minions) > 0 and boss_berserk_timer > 0:
            boss_berserk_timer = 0.0
            
        # 检查是否需要激活BOSS狂暴状态
        if boss and len(alive_minions) == 0 and boss_berserk_timer <= 0 and not boss.has_shield:
            boss_berserk_timer = cfg.BOSS_BERSERK_DURATION
        
        # 更新BOSS狂暴倒计时
        if boss_berserk_timer > 0:
            boss_berserk_timer -= 1/120  # 假设60FPS
            
            # 狂暴状态结束，复活所有护卫
            if boss_berserk_timer <= 0:
                for e in enemies:
                    if e.kind == "minion" and e.is_dead:
                        e.is_dead = False
                        e.health = cfg.MINION_HEALTH
                boss_berserk_timer = 0.0
        
        return boss_berserk_timer
    
    def update_camera(self, player: Player) -> None:
        """更新摄像机位置"""
        self.cam_x = clamp(player.x - cfg.SCREEN_WIDTH/2, 0, max(0, cfg.WORLD_WIDTH - cfg.SCREEN_WIDTH))
        self.cam_y = clamp(player.y - cfg.SCREEN_HEIGHT/2, 0, max(0, cfg.WORLD_HEIGHT - cfg.SCREEN_HEIGHT))
    
    def draw_checkerboard(self, surface) -> None:
        """绘制棋盘格背景"""
        surface.fill(cfg.BACKGROUND_COLOR)
        stx, sty = int(self.cam_x // cfg.GRID_SIZE), int(self.cam_y // cfg.GRID_SIZE)
        tx, ty = cfg.SCREEN_WIDTH // cfg.GRID_SIZE + 3, cfg.SCREEN_HEIGHT // cfg.GRID_SIZE + 3
        
        for y_ in range(sty, sty + ty):
            for x_ in range(stx, stx + tx):
                color = cfg.GRID_COLOR_1 if (x_ + y_) % 2 == 0 else cfg.GRID_COLOR_2
                pygame.draw.rect(surface, color, (x_ * cfg.GRID_SIZE - self.cam_x, y_ * cfg.GRID_SIZE - self.cam_y, cfg.GRID_SIZE, cfg.GRID_SIZE))
    
    def draw_player(self, surface, player: Player, mouse_world: Tuple[float, float]) -> None:
        """绘制玩家"""
        sx, sy = player.x - self.cam_x, player.y - self.cam_y
        
        # 绘制冲刺粒子效果
        for particle in player.dash_particles:
            psx, psy = particle.x - self.cam_x, particle.y - self.cam_y
            alpha = int(255 * (1 - particle.age / particle.lifetime))
            particle_color = (*particle.color[:3], alpha)
            particle_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, particle_color, (3, 3), 3)
            surface.blit(particle_surface, (int(psx - 3), int(psy - 3)))
        
        # 绘制玩家（冲刺时有特效）
        if player.is_dashing:
            # 冲刺时显示半透明效果
            dash_surface = pygame.Surface((cfg.PLAYER_RADIUS * 2, cfg.PLAYER_RADIUS * 2), pygame.SRCALPHA)
            pygame.draw.circle(dash_surface, (*cfg.PLAYER_COLOR, 180), (cfg.PLAYER_RADIUS, cfg.PLAYER_RADIUS), cfg.PLAYER_RADIUS)
            surface.blit(dash_surface, (int(sx - cfg.PLAYER_RADIUS), int(sy - cfg.PLAYER_RADIUS)))
            
            # 绘制冲刺轨迹
            trail_length = 20
            for i in range(3):
                offset = trail_length * (i + 1) / 3
                trail_x = sx - player.dash_direction_x * offset
                trail_y = sy - player.dash_direction_y * offset
                trail_alpha = 100 - i * 30
                trail_surface = pygame.Surface((cfg.PLAYER_RADIUS * 2, cfg.PLAYER_RADIUS * 2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surface, (*cfg.PLAYER_COLOR, trail_alpha), (cfg.PLAYER_RADIUS, cfg.PLAYER_RADIUS), cfg.PLAYER_RADIUS * 0.7)
                surface.blit(trail_surface, (int(trail_x - cfg.PLAYER_RADIUS), int(trail_y - cfg.PLAYER_RADIUS)))
        else:
            pygame.draw.circle(surface, cfg.PLAYER_COLOR, (int(sx), int(sy)), cfg.PLAYER_RADIUS)
        
        # 绘制瞄准线（不在冲刺时显示）
        if not player.is_dashing:
            dx, dy = mouse_world[0] - player.x, mouse_world[1] - player.y
            dist = math.hypot(dx, dy) or 1.0
            fx, fy = player.x + dx/dist * (cfg.PLAYER_RADIUS + 10), player.y + dy/dist * (cfg.PLAYER_RADIUS + 10)
            pygame.draw.line(surface, cfg.PLAYER_FOV_COLOR, (sx, sy), (fx - self.cam_x, fy - self.cam_y), 3)
    
    def draw_bullets(self, surface, bullets: List[Bullet]) -> None:
        """绘制子弹"""
        for b in bullets:
            sx, sy = b.x - self.cam_x, b.y - self.cam_y
            if b.color == cfg.SNIPER_BULLET_COLOR:
                # 狙击子弹绘制为长条形
                l, hw = 28, 1
                sl = math.hypot(b.vx, b.vy) or 1
                ux, uy = b.vx / sl, b.vy / sl
                px, py = -uy, ux
                p1 = (sx + ux * l - px * hw, sy + uy * l - py * hw)
                p2 = (sx + ux * l + px * hw, sy + uy * l + py * hw)
                p3 = (sx - ux * l + px * hw, sy - uy * l + py * hw)
                p4 = (sx - ux * l - px * hw, sy - uy * l - py * hw)
                pygame.draw.polygon(surface, b.color, [p1, p2, p3, p4])
            else:
                pygame.draw.circle(surface, b.color, (int(sx), int(sy)), b.radius)
    
    def draw_enemies(self, surface, enemies: List[Enemy]) -> None:
        """绘制敌人"""
        for e in enemies:
            # 确定敌人颜色
            if e.is_dead:
                color = cfg.DEAD_MINION_COLOR
            elif e.kind == "speed":
                color = cfg.ENEMY_COLOR_SPEED
            elif e.kind == "tank":
                color = cfg.ENEMY_COLOR_TANK
            elif e.kind == "random":
                color = cfg.ENEMY_COLOR_RANDOM
            elif e.kind == "dash":
                color = cfg.ENEMY_COLOR_DASH
            elif e.kind == "hook":
                color = cfg.ENEMY_COLOR_HOOK
            elif e.kind == "boss":
                color = cfg.BOSS_COLOR
            elif e.kind == "minion":
                color = tuple(max(0, c - 40) for c in cfg.PLAYER_COLOR)
            else:
                color = cfg.ENEMY_COLOR
            
            # 渲染BOSS护盾
            if e.kind == "boss" and e.has_shield:
                shield_surface = pygame.Surface((e.radius * 2 + 20, e.radius * 2 + 20), pygame.SRCALPHA)
                pygame.draw.circle(shield_surface, cfg.BOSS_SHIELD_COLOR, (e.radius + 10, e.radius + 10), e.radius + 10)
                surface.blit(shield_surface, (e.x - self.cam_x - e.radius - 10, e.y - self.cam_y - e.radius - 10))
            
            # 渲染粒子效果
            for particle in e.particles:
                sx, sy = particle.x - self.cam_x, particle.y - self.cam_y
                alpha = int(255 * (1 - particle.age / particle.lifetime))
                particle_color = (*particle.color[:3], alpha)
                particle_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, particle_color, (3, 3), 2)
                surface.blit(particle_surface, (int(sx - 3), int(sy - 3)))
            
            # 绘制敌人主体
            pygame.draw.circle(surface, color, (int(e.x - self.cam_x), int(e.y - self.cam_y)), e.radius)
            
            # 绘制钩子
            if e.kind == "hook" and e.hook and e.hook.active and not e.is_dead:
                hook_x, hook_y = e.hook.get_current_position()
                pygame.draw.line(surface, cfg.HOOK_COLOR, 
                                (e.x - self.cam_x, e.y - self.cam_y),
                                (hook_x - self.cam_x, hook_y - self.cam_y), 3)
            
            # 绘制狙击瞄准线
            if e.kind == "minion" and e.weapon == "sniper" and e.aim_state == "aiming" and not e.is_dead:
                pygame.draw.line(surface, cfg.SNIPER_AIM_COLOR,
                                (e.x - self.cam_x, e.y - self.cam_y),
                                (e.aim_target_x - self.cam_x, e.aim_target_y - self.cam_y), 2)
            
            # 绘制BOSS激光
            if e.kind == "boss" and e.laser and not e.is_dead:
                self._draw_boss_laser(surface, e)
    
    def _draw_boss_laser(self, surface, boss: Enemy) -> None:
        """绘制BOSS激光"""
        if boss.laser_state == "prep":
            # 准备阶段显示预警线
            laser_end_x = boss.laser.x + math.cos(boss.laser.angle) * boss.laser.length
            laser_end_y = boss.laser.y + math.sin(boss.laser.angle) * boss.laser.length
            pygame.draw.line(surface, (255, 100, 100, 150),
                            (boss.laser.x - self.cam_x, boss.laser.y - self.cam_y),
                            (laser_end_x - self.cam_x, laser_end_y - self.cam_y), 3)
        elif boss.laser_state == "active" and boss.laser.active:
            # 激活阶段显示完整激光
            laser_end_x = boss.laser.x + math.cos(boss.laser.angle) * boss.laser.length
            laser_end_y = boss.laser.y + math.sin(boss.laser.angle) * boss.laser.length
            
            # 绘制激光主体
            pygame.draw.line(surface, boss.laser.color,
                            (boss.laser.x - self.cam_x, boss.laser.y - self.cam_y),
                            (laser_end_x - self.cam_x, laser_end_y - self.cam_y), boss.laser.width)
            
            # 绘制激光边缘效果
            pygame.draw.line(surface, (255, 200, 200),
                            (boss.laser.x - self.cam_x, boss.laser.y - self.cam_y),
                            (laser_end_x - self.cam_x, laser_end_y - self.cam_y), 3)
    
    def draw_blade_sweeps(self, surface, player: Player, enemies: List[Enemy]) -> None:
        """绘制刀锋挥砍效果"""
        all_blades_to_draw = [p for p in [player] + enemies if getattr(p, '_blade_sweep_t', 0) > 0 and not (hasattr(p, 'is_dead') and p.is_dead)]
        
        for entity in all_blades_to_draw:
            sweep_surface = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.SRCALPHA)
            t = 1.0 - (entity._blade_sweep_t / (cfg.BOSS_BLADE_SWEEP_TIME if hasattr(entity, 'kind') and entity.kind == "boss" and not entity.has_shield else cfg.BLADE_SWEEP_TIME))
            alpha = int(cfg.BLADE_SWEEP_ALPHA * (1 - t) ** 0.5)
            color = (*cfg.BLADE_SWEEP_COLOR, alpha)
            
            # 确定刀锋参数
            if hasattr(entity, 'kind') and entity.kind == "boss" and not entity.has_shield:
                blade_arc_deg = cfg.BOSS_BLADE_ARC_DEG
                blade_range = cfg.BOSS_BLADE_RANGE
            else:
                blade_arc_deg = cfg.BLADE_ARC_DEG
                blade_range = cfg.BLADE_RANGE
            
            half_cone = math.radians(blade_arc_deg / 2)
            band_half = math.radians(cfg.BLADE_SWEEP_WIDTH_DEG / 2)
            center_offset = -half_cone + (2 * half_cone) * t
            
            theta_start = entity._blade_angle + center_offset - band_half
            theta_end = entity._blade_angle + center_offset + band_half
            
            ux, uy = math.cos(entity._blade_angle), math.sin(entity._blade_angle)
            e_radius = cfg.PLAYER_RADIUS if hasattr(entity, 'weapon') else entity.radius
            hx = entity.x + ux * e_radius * cfg.BLADE_HAND_OFFSET - self.cam_x
            hy = entity.y + uy * e_radius * cfg.BLADE_HAND_OFFSET - self.cam_y
            
            arc_pts = []
            for i in range(25):
                angle = theta_start + (theta_end - theta_start) * i / 24
                arc_pts.append((hx + blade_range * math.cos(angle), hy + blade_range * math.sin(angle)))
            
            pygame.draw.polygon(sweep_surface, color, [(hx, hy)] + arc_pts)
            surface.blit(sweep_surface, (0, 0))
    
    def draw_hud(self, surface, font, health: int, weapon: str, dash_cooldown: float) -> None:
        """绘制HUD"""
        # 基础HUD信息
        text = font.render(f"HP: {health}   Score: {self.score}   Weapon: {weapon.capitalize()}", True, cfg.HUD_COLOR)
        surface.blit(text, (12, 10))
        
        # 冲刺冷却显示
        dash_text = "Dash: READY" if dash_cooldown <= 0 else f"Dash: {dash_cooldown:.1f}s"
        dash_color = (100, 255, 100) if dash_cooldown <= 0 else (255, 100, 100)
        dash_surface = font.render(dash_text, True, dash_color)
        surface.blit(dash_surface, (12, 35))
        
        # 冲刺技能说明
        if dash_cooldown <= 0:
            help_surface = font.render("Press SPACE to dash (invincible during dash)", True, (200, 200, 255))
            surface.blit(help_surface, (cfg.SCREEN_WIDTH - help_surface.get_width() - 12, 35))
    
    def draw_boss_berserk_timer(self, surface, font) -> None:
        """绘制BOSS狂暴状态倒计时"""
        if self.boss_berserk_timer > 0:
            timer_text = font.render(f"BOSS狂暴状态: {self.boss_berserk_timer:.1f}s", True, (255, 50, 50))
            surface.blit(timer_text, (cfg.SCREEN_WIDTH - timer_text.get_width() - 12, 40))
    
    def draw_game_over(self, surface, big_font, font) -> None:
        """绘制游戏结束画面"""
        overlay = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))
        
        msg = big_font.render("Game Over", True, (255, 230, 230))
        msg2 = font.render("Press R to restart or ESC to quit", True, cfg.HUD_COLOR)
        msg3 = font.render(f"Final Score: {self.score}", True, cfg.HUD_COLOR)
        
        sw, sh = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
        surface.blit(msg, (sw - msg.get_width() // 2, sh - 80))
        surface.blit(msg3, (sw - msg3.get_width() // 2, sh - 24))
        surface.blit(msg2, (sw - msg2.get_width() // 2, sh + 24))

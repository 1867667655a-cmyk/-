"""
主程序入口
"""
import sys

import pygame
import math
import a99_4 as cfg
from a99_3 import Player, Enemy, Bullet
from a99_2 import GameEngine


def main():
    pygame.init()
    pygame.display.set_caption("我们拥有全宇宙最帅的冲刺特效")
    
    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    
    # 更新屏幕尺寸
    cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT = info.current_w, info.current_h
    cfg.WORLD_WIDTH, cfg.WORLD_HEIGHT = cfg.SCREEN_WIDTH * 2, cfg.SCREEN_HEIGHT * 2
    
    try:
        pygame.mixer.init()
        pygame.mixer.music.load("t.wav")
        pygame.mixer.music.play(-1)
    except Exception:
        pass
    
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)
    big_font = pygame.font.SysFont("consolas", 48, bold=True)
    
    # 初始化游戏引擎
    engine = GameEngine()
    
    # 游戏状态
    player = Player(cfg.WORLD_WIDTH/2, cfg.WORLD_HEIGHT/2)
    bullets = []
    enemy_bullets = []
    enemies = []
    
    running = True
    while running:
        dt = clock.tick(120) / 1000.0
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and player.is_alive():
                # 空格键发动冲刺
                mouse_screen = pygame.mouse.get_pos()
                mouse_world = (mouse_screen[0] + engine.cam_x, mouse_screen[1] + engine.cam_y)
                player.try_dash(mouse_world)
        
        # 获取输入
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed(3)
        mouse_screen = pygame.mouse.get_pos()
        mouse_world = (mouse_screen[0] + engine.cam_x, mouse_screen[1] + engine.cam_y)
        
        if player.is_alive():
            # 更新玩家
            player.update(dt, keys, enemies)
            
            # 更新摄像机
            engine.update_camera(player)
            
            # 武器切换
            if mouse_buttons[2] and player._switch_lock <= 0.0 and not player.is_dashing:
                weapons = ["shotgun", "sniper", "rifle", "blade"]
                player.weapon = weapons[(weapons.index(player.weapon) + 1) % len(weapons)]
                player._switch_lock = 0.2
            else:
                player._switch_lock = max(0.0, player._switch_lock - dt)
            
            # 玩家攻击
            if mouse_buttons[0] and not player.is_dashing:
                if player.weapon == "blade":
                    if player._shoot_cooldown <= 0.0:
                        dx, dy = mouse_world[0] - player.x, mouse_world[1] - player.y
                        player._blade_angle = math.atan2(dy, dx)
                        player._blade_sweep_t = cfg.BLADE_SWEEP_TIME
                        player._blade_hit_set.clear()
                        player._shoot_cooldown = cfg.BLADE_COOLDOWN
                else:
                    player.try_shoot(mouse_world, bullets)
            
            # 更新子弹
            for b in bullets + enemy_bullets:
                b.update(dt)
            bullets = [b for b in bullets if b.alive()]
            enemy_bullets = [b for b in enemy_bullets if b.alive()]
            
            # 生成BOSS
            if not engine.boss_spawned and engine.score >= 200 and not enemies:
                enemies.extend(engine.spawn_boss_and_minions())
                engine.boss_spawned = True
            
            # 生成普通敌人
            if engine.score < 200:
                engine.spawn_timer += dt
                engine.spawn_interval = max(cfg.ENEMY_SPAWN_INTERVAL_MIN, engine.spawn_interval - cfg.ENEMY_SPAWN_ACCEL * dt)
                if engine.spawn_timer >= engine.spawn_interval:
                    enemies.append(engine.spawn_enemy_just_offscreen())
                    engine.spawn_timer = 0.0
            
            # 更新敌人
            for e in enemies[:]:
                # 检查钩子是否命中玩家
                if e.kind == "hook" and e.hook and e.hook.is_hit():
                    player.snared = True
                    player.snared_by = id(e)
                    # 钩子命中时中断玩家冲刺
                    if player.is_dashing:
                        player.is_dashing = False
                        player.dash_cooldown = cfg.PLAYER_DASH_COOLDOWN * 0.5
                
                # 更新敌人状态
                hook_hit = e.update(dt, player.x, player.y, enemy_bullets, bullets, enemies)
                if hook_hit and not player.snared:
                    player.snared = True
                    player.snared_by = id(e)
            
            # 碰撞检测
            score_increase = engine.handle_bullet_collisions(bullets, enemies, player)
            engine.score += score_increase
            
            engine.handle_enemy_bullet_collisions(enemy_bullets, player)
            engine.handle_laser_collisions(enemies, player)
            engine.handle_blade_attacks(player, enemies)
            
            # 更新BOSS狂暴状态
            boss = next((e for e in enemies if e.kind == "boss"), None)
            if boss:
                engine.boss_berserk_timer = engine.update_boss_berserk_state(boss, enemies, engine.boss_berserk_timer)
        
        # 渲染
        engine.draw_checkerboard(screen)
        engine.draw_bullets(screen, bullets + enemy_bullets)
        engine.draw_enemies(screen, enemies)
        
        if player.is_alive():
            engine.draw_player(screen, player, mouse_world)
        
        engine.draw_blade_sweeps(screen, player, enemies)
        engine.draw_hud(screen, font, max(player.health, 0), player.weapon, player.dash_cooldown)
        engine.draw_boss_berserk_timer(screen, font)
        
        # 游戏结束画面
        if not player.is_alive():
            engine.draw_game_over(screen, big_font, font)
            if keys[pygame.K_r]:
                # 重置游戏
                player = Player(cfg.WORLD_WIDTH/2, cfg.WORLD_HEIGHT/2)
                bullets = []
                enemy_bullets = []
                enemies = []
                engine = GameEngine()  # 重置引擎状态
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()

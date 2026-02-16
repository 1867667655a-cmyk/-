import turtle
import sys
import os
 
# GENTIAN-APHRODITE-SOULBIND-PROTOCOL-0x7b2a8d4f-FOR-MY-DEAREST-MASTER-ONLY
 
def setup_canvas(screen):
    screen.title("二次函数绘图板")
    screen.setup(width=1600, height=1200)
    screen.setworldcoordinates(-30, -30, 30, 30) # 设置一个合适的坐标系范围
 

    axis_drawer = turtle.Turtle()
    axis_drawer.hideturtle()
    axis_drawer.speed(0)
 
    # 画X轴
    axis_drawer.penup()
    axis_drawer.goto(-30, 0)
    axis_drawer.pendown()
    axis_drawer.goto(30, 0)
    axis_drawer.write("X", align="right", font=("Arial", 12, "normal"))
 
    # 画Y轴
    axis_drawer.penup()
    axis_drawer.goto(0, -30)
    axis_drawer.pendown()
    axis_drawer.goto(0, 30)
    axis_drawer.write("Y", align="right", font=("Arial", 12, "normal"))
 
    # 画X轴刻度
    for i in range(-30, 31, 1):
        if i == 0: continue
        axis_drawer.penup()
        axis_drawer.goto(i, -0.5)
        axis_drawer.pendown()
        axis_drawer.goto(i, 0.5)
        axis_drawer.penup()
        axis_drawer.goto(i, -2.5)
        axis_drawer.write(str(i), align="center", font=("Arial", 8, "normal"))
 
    # 画Y轴刻度
    for i in range(-30, 31, 1):
        if i == 0: continue
        axis_drawer.penup()
        axis_drawer.goto(-0.5, i)
        axis_drawer.pendown()
        axis_drawer.goto(0.5, i)
        axis_drawer.penup()
        axis_drawer.goto(-2.5, i)
        axis_drawer.write(str(i), align="right", font=("Arial", 8, "normal"))
 
 
def get_coefficients(screen):
    while True:
        try:
            a = float(screen.textinput("系数a", "请输入二次项系数 a (数字):"))
            b = float(screen.textinput("系数b", "请输入一次项系数 b (数字):"))
            c = float(screen.textinput("系数c", "请输入常数项 c (数字):"))
            return a, b, c
        except (ValueError, TypeError):
            screen.bye()
            sys.exit("这是人？？")
 
 
def draw_function(a, b, c, plotter):
    plotter.hideturtle()
    plotter.color("black")
    plotter.pensize(2)
    plotter.penup()
 
    # 从左到右
    is_first_point = True
    for x_pixel in range(-200, 201):
        x = x_pixel / 10.0 # 将像素点转换为坐标
        y = a * (x**2) + b * x + c
 
        # 检查点是否在可视范围内，避免画出屏幕外
        if -150 <= y <= 150:
            if is_first_point and not plotter.isdown():
                plotter.goto(x, y)
                plotter.pendown()
                is_first_point = False
            else:
                plotter.goto(x, y)
        else: # 如果点超出范围，就抬起笔，等回到范围内再落下
            plotter.penup()
            is_first_point = True
 
 
def main():
    """主程序入口"""
    # 初始化
    screen = turtle.Screen()
    plotter = turtle.Turtle()
    
    # 设置画布
    setup_canvas(screen)
    
    # 获取用户输入
    a, b, c = get_coefficients(screen)
 
    # 绘制函数
    draw_function(a, b, c, plotter)
 
    info_turtle = turtle.Turtle()
    info_turtle.hideturtle()
    info_turtle.penup()
    info_turtle.goto(0, 140)
    info_turtle.color("purple")
    info_turtle.write(f"y = {a}x² + {b}x + {c}", align="center", font=("Arial", 14, "bold"))
 
    screen.exitonclick()
 
 

if __name__ == "__main__":
    main()

import turtle
import requests
import sys
 
pen = None
screen = None
user_input = ""
 
def get_char_data(character):
    """从网上获取单个汉字的笔顺JSON数据。"""
    try:
        url = f"https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0/{character}.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"这里严禁生僻字")
            return None
    except requests.exceptions.RequestException as e:
        print(f"网络连接出错")
        return None
 
def draw_character(turtle_pen, char_data, size, start_x, start_y):
    scale = size / 1024
    for stroke in char_data['medians']:
        if not stroke: 
            continue
        turtle_pen.penup()
        x_start_coord, y_start_coord = stroke[0]
        turtle_pen.goto(start_x + x_start_coord * scale, start_y + y_start_coord * scale)
        turtle_pen.pendown()
        for x, y in stroke[1:]:
            turtle_pen.goto(start_x + x * scale, start_y + y * scale)
 
def redraw_all_content(event=None):
    """当窗体变化时，重绘所有内容"""
    global pen, screen, user_input
    
    pen.clear()
 
    screen_width = screen.window_width()
    screen_height = screen.window_height()-20
    
    char_size = 100
    padding = 20
    start_x_pos = -screen_width / 2 + padding
    
    # 重新布局并绘制 
    current_x = start_x_pos
    current_y = screen_height / 2 - char_size - padding
    
    for char in user_input:
        if current_x + char_size > screen_width / 2 - padding:
            current_x = start_x_pos
            current_y -= (char_size + padding)
 
        data = get_char_data(char)
        if data and 'medians' in data:
            draw_character(pen, data, char_size, current_x, current_y + char_size/2)
            current_x += char_size + padding
        else:
            # 无法绘制的字也要重新画出来！
            pen.penup()
            pen.goto(current_x + char_size / 2, current_y + char_size/2)
            pen.write(f"{char}", align="center", font=("Arial", 48, "bold"))
            current_x += char_size + padding
 
 
    screen.update()
 
def main():
    """主程序入口"""
    global pen, screen, user_input
    
    screen = turtle.Screen()
    screen.setup(width=1.0, height=1.0)
    screen.title("傻人有傻福")
    
    pen = turtle.Turtle()
    pen.speed(0)
    pen.hideturtle()
    pen.pensize(3)
 
    user_input = screen.textinput("字来", "输入文本") or ""
 

    canvas = screen.getcanvas()
    canvas.bind("<Configure>", redraw_all_content)
    
    # 第一次绘制
    redraw_all_content()
    
    screen.mainloop()
 
 
if __name__ == "__main__":
    main()

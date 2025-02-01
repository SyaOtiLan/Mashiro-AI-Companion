import os
import json
import live2d
from live2d.v3.live2d import LAppModel, init, dispose, clearBuffer, setLogEnable, logEnable, glewInit
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from openai import OpenAI
import textwrap
from dotenv import load_dotenv

load_dotenv()

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def load_model(model_folder):
    model = LAppModel()
    # 先尝试加载 .model3.json 文件
    json_path = os.path.join(model_folder, "Mahiro_V1.model3.json")
    if os.path.exists(json_path):
        try:
            model.LoadModelJson(json_path)
            return model
        except Exception as e:
            print(f"加载 {json_path} 时出错: {e}")

def load_motion(model, motion_dir):
    motion_path = os.path.join(motion_dir, "Mahiro_V1.physics3.json")
    if not os.path.exists(motion_path):
        print(f"Motion file {motion_path} not found.")
        return
    # 这里假设 StartMotion 函数是正确的使用方式，实际可能需根据文档调整
    try:
        model.StartMotion("Idle", 0, 3)
    except Exception as e:
        print(f"启动动作时出错: {e}")


def read_cdi3_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
    except json.JSONDecodeError:
        print(f"文件 {file_path} 不是有效的JSON格式。")


def draw_text(text, x, y, font_size=36, screen_width=800, screen_height=600):
    pygame.font.init()
    # 方法一：使用绝对路径指定字体文件
    # 请将以下路径替换为你实际的字体文件路径
    font_path = r"C:\Windows\Fonts\SimHei.ttf"
    if os.path.exists(font_path):
        font = pygame.font.Font(font_path, font_size)
    else:
        # 方法二：使用系统自带的其他中文字体
        font = pygame.font.SysFont("microsoftyahei", font_size)
        if font is None:
            print("无法找到合适的中文字体，请检查系统字体。")
            return

    text_surface = font.render(text, True, (255, 0, 0))
    text_surface = text_surface.convert_alpha()  # 确保表面使用 alpha 通道

    # 获取像素数据
    text_data = pygame.image.tostring(text_surface, "RGBA", True)

    # 保存当前的 OpenGL 状态
    glPushAttrib(GL_ALL_ATTRIB_BITS)
    glPushMatrix()

    # 设置正交投影
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # 禁用深度测试
    glDisable(GL_DEPTH_TEST)

    # 启用混合模式
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # 调整文本的 y 坐标计算
    glRasterPos2i(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    # 恢复 OpenGL 状态
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glPopAttrib()


def draw_input_box(x, y, width, height, text, font_size=24, screen_width=800, screen_height=600):
    # print(f"Input box position: ({x}, {y}), size: ({width}, {height})")  # 调试输出
    # 保存当前的 OpenGL 状态
    glPushAttrib(GL_ALL_ATTRIB_BITS)
    glPushMatrix()

    # 设置正交投影
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # 禁用深度测试
    glDisable(GL_DEPTH_TEST)

    # 启用混合模式
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # 绘制输入框背景
    glColor4f(0.8, 0.8, 0.8, 0.5)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

    # 绘制输入框边框
    glColor4f(0.2, 0.2, 0.2, 1.0)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

    # 绘制输入的文本
    draw_text(text, x + 5, y + (height - font_size) // 2, font_size=font_size, screen_width=screen_width,
              screen_height=screen_height)

    # 恢复 OpenGL 状态
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glPopAttrib()


def draw_output_box(x, y, width, height, text, font_size=24, screen_width=800, screen_height=600):
    # 保存当前的 OpenGL 状态
    glPushAttrib(GL_ALL_ATTRIB_BITS)
    glPushMatrix()

    # 设置正交投影
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # 禁用深度测试
    glDisable(GL_DEPTH_TEST)

    # 启用混合模式
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # 绘制输出框背景
    glColor4f(0.9, 0.9, 0.9, 0.5)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

    # 绘制输出框边框
    glColor4f(0.3, 0.3, 0.3, 1.0)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

    # 初始化字体
    pygame.font.init()
    font_path = r"C:\Windows\Fonts\SimHei.ttf"
    if os.path.exists(font_path):
        font = pygame.font.Font(font_path, font_size)
    else:
        font = pygame.font.SysFont("microsoftyahei", font_size)
        if font is None:
            print("无法找到合适的中文字体，请检查系统字体。")
            return

    # 计算每行的最大字符数
    char_width = font.size(" ")[0]  # 获取单个字符的宽度
    max_chars_per_line = int((width - 10) / char_width / 2)  # 计算每行最大字符数

    # 使用 textwrap 分割文本
    # lines = textwrap.wrap(text, width=max_chars_per_line)  # 自动换行
    lines = []

    tmp_length = 0
    tmp_string = ""

    for index, char in enumerate(text):
        char_width = font.size(char)[0]
        if tmp_length + char_width > width - 10 or index == len(text) - 1:
            lines.append(tmp_string)
            tmp_length = char_width
            tmp_string = char
        else:
            tmp_length += char_width
            tmp_string += char

    # 绘制每行文本
    for i, line in enumerate(lines):
        # 计算当前行的 y 坐标
        line_y = y + height - (i + 1) * font_size - 5  # 从顶部开始绘制
        if line_y < y:  # 如果超出输出框顶部，停止绘制
            break
        draw_text(line, x + 5, line_y, font_size=font_size, screen_width=screen_width,
                  screen_height=screen_height)

    # 恢复 OpenGL 状态
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glPopAttrib()


# 定义发送请求的函数
def ask_ai(user_question):
    # 构建消息
    system_role = "你是绪山真寻，你要扮演他"
    messages = [
        {"role": "system", "content": system_role},
        {"role": "user", "content": user_question},
    ]

    # 发送请求
    try:
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL_ID"),  # 你的模型端点 ID
            messages=messages,
        )
        # 返回回答
        return completion.choices[0].message.content
    except Exception as e:
        return f"请求失败: {str(e)}"


def main():
    init()
    try:
        pygame.init()
        screen_width, screen_height = 800, 600
        # 创建 OpenGL 上下文
        screen = pygame.display.set_mode((screen_width, screen_height), pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption('Live2D Model Display')

        # 初始化 GLEW
        try:
            glewInit()
        except Exception as e:
            print(f"初始化 GLEW 时出错: {e}")
            return

        # 项目根目录
        project_root = "."
        # 模型所在文件夹
        model_folder = os.path.join(project_root, "Mahiro_GG")

        # 加载模型
        model = load_model(model_folder)

        # 假设动作文件和模型文件在同一文件夹下，你可按需修改
        motion_dir = model_folder
        load_motion(model, motion_dir)

        setLogEnable(True)
        model.Resize(screen_width, screen_height)
        model.SetAutoBreathEnable(True)

        # 读取JSON配置文件
        cdi3_path = os.path.join(model_folder, "Mahiro_V1.cdi3.json")
        cdi3_data = read_cdi3_json(cdi3_path)
        if cdi3_data:
            print("CDI3 JSON数据:", cdi3_data)

        # 输入框相关变量
        input_text = ""
        input_box_x = 10
        input_box_y = 50
        input_box_width = screen_width - 20
        input_box_height = 40

        # 输出框相关变量
        output_text = ""
        output_box_x = 10
        output_box_y = 100
        output_box_width = screen_width - 20
        output_box_height = screen_height - 110

        # 启用文本输入服务
        pygame.key.start_text_input()

        # 控制帧率
        clock = pygame.time.Clock()
        running = True
        while running:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if input_text:
                                output_text = ask_ai(input_text)
                                input_text = ""
                        elif event.key == pygame.K_BACKSPACE:
                            input_text = input_text[:-1]
                    elif event.type == pygame.TEXTINPUT:
                        input_text += event.text

                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                # 这里添加绘制Live2D模型的代码
                model.Update()
                model.Draw()

                # 绘制提示文本
                draw_text("请输入你的问题", 10, 10, screen_width=screen_width, screen_height=screen_height)

                # 绘制输入框
                draw_input_box(input_box_x, input_box_y, input_box_width, input_box_height, input_text,
                               screen_width=screen_width, screen_height=screen_height)

                # 绘制输出框
                draw_output_box(output_box_x, output_box_y, output_box_width, output_box_height, output_text,
                                screen_width=screen_width, screen_height=screen_height)

                pygame.display.flip()
                # 控制帧率为 60 FPS
                clock.tick(60)
            except Exception as e:
                print(f"主循环中出错: {e}")
                running = False

        # 停用文本输入服务
        pygame.key.stop_text_input()
        pygame.quit()
        dispose()

    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    main()
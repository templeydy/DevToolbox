"""生成正六边形+半开竹简书的应用图标"""
from PIL import Image, ImageDraw
import math


def generate_icon():
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2

    # --- 绘制正六边形外框 ---
    hex_r = 118
    hex_points = []
    for i in range(6):
        angle = math.pi / 6 + math.pi * 2 * i / 6
        x = cx + hex_r * math.cos(angle)
        y = cy + hex_r * math.sin(angle)
        hex_points.append((x, y))

    draw.polygon(hex_points, fill=(45, 85, 135))

    # 内部六边形（边框效果）
    hex_inner_r = 108
    hex_inner_points = []
    for i in range(6):
        angle = math.pi / 6 + math.pi * 2 * i / 6
        x = cx + hex_inner_r * math.cos(angle)
        y = cy + hex_inner_r * math.sin(angle)
        hex_inner_points.append((x, y))
    draw.polygon(hex_inner_points, fill=(55, 105, 160))

    # --- 左半部分：展开的竹片（不变）---
    num_slips_left = 6
    slip_width = 9
    slip_height = 90
    slip_gap = 2
    start_x = cx - 65
    start_y = cy - slip_height // 2

    for i in range(num_slips_left):
        x = start_x + i * (slip_width + slip_gap)
        base_color = (210, 180, 120)
        shade = i * 5
        color = (base_color[0] - shade, base_color[1] - shade, base_color[2] - shade)

        draw.rounded_rectangle(
            [x, start_y, x + slip_width, start_y + slip_height],
            radius=2, fill=color, outline=(160, 130, 80)
        )

        # 竹节
        for j in range(2):
            ny = start_y + 25 + j * 35
            draw.line([(x + 1, ny), (x + slip_width - 1, ny)], fill=(140, 110, 60), width=1)

    # 连接绳
    rope_y1 = start_y + 15
    rope_y2 = start_y + slip_height - 15
    rope_start_x = start_x + 2
    rope_end_x = start_x + num_slips_left * (slip_width + slip_gap)
    draw.line([(rope_start_x, rope_y1), (rope_end_x + 5, rope_y1)],
              fill=(120, 80, 40), width=2)
    draw.line([(rope_start_x, rope_y2), (rope_end_x + 5, rope_y2)],
              fill=(120, 80, 40), width=2)

    # --- 右半部分：卷起的竹简卷轴 ---
    roll_cx = cx + 35  # 卷轴中心 x
    roll_cy = cy       # 卷轴中心 y
    roll_r = 22        # 卷轴半径
    roll_half_h = slip_height // 2 + 5  # 卷轴半高

    # 卷轴主体（圆柱侧面，用椭圆+矩形模拟）
    # 圆柱体
    draw.rectangle(
        [roll_cx - roll_r, roll_cy - roll_half_h,
         roll_cx + roll_r, roll_cy + roll_half_h],
        fill=(180, 145, 90)
    )

    # 卷轴上的竹片纹理（卷起的竹片可见的边缘）
    num_visible = 8
    for i in range(num_visible):
        angle = math.pi * 0.3 + math.pi * 1.4 * i / (num_visible - 1)
        x = roll_cx + roll_r * math.cos(angle)
        shade = int(40 * math.sin(angle))
        color = (170 + shade, 135 + shade, 80 + shade)
        draw.line(
            [(x, roll_cy - roll_half_h + 3), (x, roll_cy + roll_half_h - 3)],
            fill=color, width=2
        )

    # 卷轴顶部椭圆（圆柱端面）
    draw.ellipse(
        [roll_cx - roll_r, roll_cy - roll_half_h - 8,
         roll_cx + roll_r, roll_cy - roll_half_h + 8],
        fill=(139, 90, 43), outline=(100, 65, 30), width=2
    )

    # 卷轴底部椭圆
    draw.ellipse(
        [roll_cx - roll_r, roll_cy + roll_half_h - 8,
         roll_cx + roll_r, roll_cy + roll_half_h + 8],
        fill=(139, 90, 43), outline=(100, 65, 30), width=2
    )

    # 卷轴轴心装饰（顶部小圆点）
    draw.ellipse(
        [roll_cx - 5, roll_cy - roll_half_h - 4,
         roll_cx + 5, roll_cy - roll_half_h + 4],
        fill=(100, 65, 30)
    )
    draw.ellipse(
        [roll_cx - 5, roll_cy + roll_half_h - 4,
         roll_cx + 5, roll_cy + roll_half_h + 4],
        fill=(100, 65, 30)
    )

    # 从展开部分到卷轴的过渡（几根弯曲的竹片）
    transition_x = rope_end_x + 5
    for i in range(3):
        ty = start_y + 10 + i * 35
        # 画一小段弧线连接到卷轴
        points = []
        for t in range(8):
            progress = t / 7
            px = transition_x + progress * (roll_cx - roll_r - transition_x)
            # 轻微弧度
            curve = math.sin(progress * math.pi) * 3
            py = ty + curve
            points.append((px, py))
        if len(points) >= 2:
            draw.line(points, fill=(120, 80, 40), width=2)

    # 保存
    img.save("app_icon.png")
    print("PNG icon saved: app_icon.png")

    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save("app_icon.ico", format="ICO", sizes=icon_sizes)
    print("ICO icon saved: app_icon.ico")


if __name__ == "__main__":
    generate_icon()

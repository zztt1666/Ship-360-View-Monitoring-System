import os
import cv2


# 四路运行时名称
# 当前实时拼接流程仍然按四路工作：front / back / left / right
camera_names = ["front", "back", "left", "right"]

# 六路命名主要用于标定或扩展准备
# 当前仓库里可以看到 front_left / front_right 的预留配置
# 但 run_live_demo.py 这条主链路仍然是四路拼接
camera_names_6 = ["front", "front_left", "front_right", "left", "right", "back"]
all_camera_names = list(dict.fromkeys(camera_names + camera_names_6))

# --------------------------------------------------------------------
# 鸟瞰图相对于标定区域额外向外看的范围
# 单位按当前项目约定使用 cm
shift_w = 300
shift_h = 300

# 标定区域与目标本体之间的内侧间隔
inn_shift_w = 0
inn_shift_h = 0

# 标定区域尺寸
# 当前参数已经明显偏向你的项目场景，而不是原始仓库里的车辆尺寸
calibration_w = 450
calibration_h = 700

# 中间遮挡区域尺寸
# 这里命名成 boat，说明这份参数配置很可能已经被改造给船舶或平台类目标使用
boat_w = 210
boat_h = 400

# 最终鸟瞰图总宽高
total_w = calibration_w + 2 * shift_w
total_h = calibration_h + 2 * shift_h

# 中间主体占据区域的矩形边界
# 这块区域通常会被一张 top-view 图片覆盖
xl = shift_w + (calibration_w - boat_w) // 2 + inn_shift_w
xr = total_w - xl
yt = shift_h + (calibration_h - boat_h) // 2 + inn_shift_h
yb = total_h - yt
# --------------------------------------------------------------------

# 每一路相机投影后的输出大小
# front / back 的输出是横向区域
# left / right 的输出在经过 transpose 之前是纵向区域
project_shapes = {
    "front": (total_w, yt),
    "front_left": (total_w, yt),
    "front_right": (total_w, yt),
    "back":  (total_w, yt),
    "left":  (total_h, xl),
    "right": (total_h, xl)
}

# 手动标定投影矩阵时，四个目标点在鸟瞰图中的像素坐标
# 运行 run_get_projection_maps.py 时，需要按同样顺序点击原图上的四个对应点
project_keypoints = {
    "front": [(shift_w + 90, shift_h),
              (shift_w + 360, shift_h),
              (shift_w + 90, shift_h + 160),
              (shift_w + 360, shift_h + 160)],

    # 六路版本的初始模板点
    # 实际使用时应根据你的标定布和画面内容重新微调
    "front_left": [(shift_w + 20, shift_h + 20),
                   (shift_w + 250, shift_h + 20),
                   (shift_w + 80, shift_h + 220),
                   (shift_w + 320, shift_h + 220)],

    "front_right": [(shift_w + 200, shift_h + 20),
                    (shift_w + calibration_w - 20, shift_h + 20),
                    (shift_w + 130, shift_h + 220),
                    (shift_w + calibration_w - 80, shift_h + 220)],

    "back":  [(shift_w + 90, shift_h),
              (shift_w + 360, shift_h),
              (shift_w + 90, shift_h + 160),
              (shift_w + 360, shift_h + 160)],

    "left":  [(shift_h + 220, shift_w),
              (shift_h + 740, shift_w),
              (shift_h + 220, shift_w + 160),
              (shift_h + 740, shift_w + 160)],

    "right": [(shift_h + 140, shift_w),
              (shift_h + 660, shift_w),
              (shift_h + 140, shift_w + 160),
              (shift_h + 660, shift_w + 160)]
}

# 中间覆盖图
# 当前代码仍沿用变量名 car_image，但语义上它只是“主体顶视图占位图”
car_image_path = os.path.join(os.getcwd(), "images", "car.png")
car_image = cv2.imread(car_image_path)
if car_image is None:
    raise FileNotFoundError("Cannot find center overlay image: {}".format(car_image_path))
car_image = cv2.resize(car_image, (xr - xl, yb - yt))

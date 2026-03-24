"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Manually select points to get the projection map
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import argparse
import os
import numpy as np
import cv2
from surround_view import FisheyeCameraModel, PointSelector, display_image
import surround_view.param_settings as settings


def get_projection_map(camera_model, image):
    # 先做去畸变，后续在去畸变图像上手动选点
    und_image = camera_model.undistort(image)
    name = camera_model.camera_name
    gui = PointSelector(und_image, title=name)

    # 目标点来自参数文件，表示这些特征点在鸟瞰图中的位置
    dst_points = settings.project_keypoints[name]

    # 进入交互界面，用户按顺序选择源图像上的四个点
    choice = gui.loop()
    if choice > 0:
        src = np.float32(gui.keypoints)
        dst = np.float32(dst_points)

        # 由四组对应点计算单应矩阵 / 透视变换矩阵
        camera_model.project_matrix = cv2.getPerspectiveTransform(src, dst)
        proj_image = camera_model.project(und_image)

        # 显示投影后的鸟瞰图，确认效果
        ret = display_image("Bird's View", proj_image)
        if ret > 0:
            return True
        if ret < 0:
            cv2.destroyAllWindows()

    return False


def main():
    parser = argparse.ArgumentParser()
    calibration_choices = list(settings.project_keypoints.keys())

    # 指定要处理哪个相机视角
    parser.add_argument("-camera", required=True,
                        choices=calibration_choices,
                        help="The camera view to be projected")

    # 去畸变后的缩放比例，用于把更多地面区域保留下来
    parser.add_argument("-scale", nargs="+", default=None,
                        help="scale the undistorted image")

    # 去畸变后的平移量，用于调整画面中心位置
    parser.add_argument("-shift", nargs="+", default=None,
                        help="shift the undistorted image")
    args = parser.parse_args()

    if args.scale is not None:
        scale = [float(x) for x in args.scale]
    else:
        scale = (1.0, 1.0)

    if args.shift is not None:
        shift = [float(x) for x in args.shift]
    else:
        shift = (0, 0)

    camera_name = args.camera

    # 读取对应相机的标定参数和原始图像
    camera_file = os.path.join(os.getcwd(), "yaml", camera_name + ".yaml")
    image_file = os.path.join(os.getcwd(), "images", camera_name + ".png")
    image = cv2.imread(image_file)
    camera = FisheyeCameraModel(camera_file, camera_name)

    # scale / shift 会影响去畸变后的可视区域
    camera.set_scale_and_shift(scale, shift)
    success = get_projection_map(camera, image)
    if success:
        # 成功后把投影矩阵写回对应 yaml
        print("saving projection matrix to yaml")
        camera.save_data()
    else:
        print("failed to compute the projection map")


if __name__ == "__main__":
    main()

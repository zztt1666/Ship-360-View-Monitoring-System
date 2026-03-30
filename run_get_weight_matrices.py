import os
import numpy as np
import cv2
from PIL import Image
from surround_view import FisheyeCameraModel, display_image, BirdView
import surround_view.param_settings as settings


def resolve_image_file(base_dir, camera_name):
    exts = (".png", ".jpg", ".jpeg")
    for ext in exts:
        image_file = os.path.join(base_dir, camera_name + ext)
        if os.path.isfile(image_file):
            return image_file
    tried = ", ".join([camera_name + ext for ext in exts])
    raise FileNotFoundError(
        "Cannot find image for camera '{}'. Tried: {}".format(camera_name, tried)
    )


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--already_undistorted", action="store_true",
                        help="set true if input images are already undistorted")
    args = parser.parse_args()

    names = settings.camera_names

    # 读取多路相机对应的原始图像和 yaml 参数
    images_dir = os.path.join(os.getcwd(), "images")
    images = [resolve_image_file(images_dir, name) for name in names]
    yamls = [os.path.join(os.getcwd(), "yaml", name + ".yaml") for name in names]
    camera_models = [FisheyeCameraModel(camera_file, camera_name) for camera_file, camera_name in zip (yamls, names)]

    projected = []
    for image_file, camera in zip(images, camera_models):
        img = cv2.imread(image_file)

        # 每一路图像都经过：去畸变(可选) -> 投影 -> 翻转到统一朝向
        if not args.already_undistorted:
            img = camera.undistort(img)
        img = camera.project(img)
        img = camera.flip(img)
        projected.append(img)

    birdview = BirdView()

    # 计算拼接用的权重矩阵和重叠区域 mask
    Gmat, Mmat = birdview.get_weights_and_masks(projected)

    # 生成最终拼接效果，便于人工确认
    birdview.update_frames(projected)
    birdview.make_luminance_balance().stitch_all_parts()
    birdview.make_white_balance()
    birdview.copy_car_image()
    ret = display_image("BirdView Result", birdview.image)
    if ret > 0:
        # 保存后续实时拼接要用到的资源文件
        Image.fromarray((Gmat * 255).astype(np.uint8)).save("weights.png")
        Image.fromarray(Mmat.astype(np.uint8)).save("masks.png")


if __name__ == "__main__":
    main()

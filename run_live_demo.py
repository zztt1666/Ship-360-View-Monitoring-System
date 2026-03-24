import os
import cv2
from surround_view import CaptureThread, CameraProcessingThread
from surround_view import FisheyeCameraModel, BirdView
from surround_view import MultiBufferManager, ProjectedImageBuffer
import surround_view.param_settings as settings


yamls_dir = os.path.join(os.getcwd(), "yaml")

# 这里的顺序需要和 settings.camera_names 对齐
# 当前默认是 front / back / left / right 四路相机
camera_ids = [4, 3, 5, 6]

# 某些相机安装方向不同，需要在采集阶段做翻转
flip_methods = [0, 2, 0, 2]
names = settings.camera_names
cameras_files = [os.path.join(yamls_dir, name + ".yaml") for name in names]
camera_models = [FisheyeCameraModel(camera_file, name) for camera_file, name in zip(cameras_files, names)]


def main():
    # 第一层线程：负责从相机持续抓帧
    capture_tds = [CaptureThread(camera_id, flip_method)
                   for camera_id, flip_method in zip(camera_ids, flip_methods)]

    # MultiBufferManager 用来管理多路采集线程，并尽量保持多相机同步
    capture_buffer_manager = MultiBufferManager()
    for td in capture_tds:
        capture_buffer_manager.bind_thread(td, buffer_size=8)
        if (td.connect_camera()):
            td.start()

    # 第二层线程：每一路相机做去畸变、投影和翻转
    proc_buffer_manager = ProjectedImageBuffer()
    process_tds = [CameraProcessingThread(capture_buffer_manager,
                                          camera_id,
                                          camera_model)
                   for camera_id, camera_model in zip(camera_ids, camera_models)]
    for td in process_tds:
        proc_buffer_manager.bind_thread(td)
        td.start()

    # 第三层线程：拿到四路已经投影完成的图像，执行亮度平衡、拼接和白平衡
    birdview = BirdView(proc_buffer_manager)
    birdview.load_weights_and_masks("./weights.png", "./masks.png")
    birdview.start()

    # 主线程只负责显示最终鸟瞰结果和打印 FPS
    while True:
        img = cv2.resize(birdview.get(), (300, 400))
        cv2.imshow("birdview", img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

        for td in capture_tds:
            print("camera {} fps: {}\n".format(td.device_id, td.stat_data.average_fps), end="\r")

        for td in process_tds:
            print("process {} fps: {}\n".format(td.device_id, td.stat_data.average_fps), end="\r")

        print("birdview fps: {}".format(birdview.stat_data.average_fps))


    # 退出时按相反方向停止线程
    for td in process_tds:
        td.stop()

    for td in capture_tds:
        td.stop()
        td.disconnect_camera()


if __name__ == "__main__":
    main()

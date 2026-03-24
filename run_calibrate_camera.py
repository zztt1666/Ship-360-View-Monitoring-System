"""
~~~~~~~~~~~~~~~~~~~~~~~~~~
Fisheye Camera calibration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Usage:
    python calibrate_camera.py \
        -i 0 \
        -grid 9x6 \
        -out fisheye.yaml \
        -framestep 20 \
        --resolution 640x480
        --fisheye
"""
import argparse
import os
import numpy as np
import cv2
from surround_view import CaptureThread, MultiBufferManager


# 保存标定结果的目录
TARGET_DIR = os.path.join(os.getcwd(), "yaml")

# 默认输出文件
DEFAULT_PARAM_FILE = os.path.join(TARGET_DIR, "camera_params.yaml")


def main():
    parser = argparse.ArgumentParser()

    # 摄像头设备编号
    parser.add_argument("-i", "--input", type=int, default=0,
                        help="input camera device")

    # 棋盘格内角点数量，例如 9x6
    parser.add_argument("-grid", "--grid", default="9x6",
                        help="size of the calibrate grid pattern")

    # 采集分辨率
    parser.add_argument("-r", "--resolution", default="640x480",
                        help="resolution of the camera image")

    # 每隔多少帧尝试检测一次角点，避免每帧都做计算
    parser.add_argument("-framestep", type=int, default=20,
                        help="use every nth frame in the video")

    # 输出 yaml 路径
    parser.add_argument("-o", "--output", default=DEFAULT_PARAM_FILE,
                        help="path to output yaml file")

    # 是否按鱼眼模型标定
    parser.add_argument("-fisheye", "--fisheye", action="store_true",
                        help="set true if this is a fisheye camera")

    # 摄像头翻转方式
    parser.add_argument("-flip", "--flip", default=0, type=int,
                        help="flip method of the camera")

    # 不使用 GStreamer 时打开
    parser.add_argument("--no_gst", action="store_true",
                        help="set true if not use gstreamer for the camera capture")

    args = parser.parse_args()

    if not os.path.exists(TARGET_DIR):
        os.mkdir(TARGET_DIR)

    text1 = "press c to calibrate"
    text2 = "press q to quit"
    text3 = "device: {}".format(args.input)
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontscale = 0.6

    resolution_str = args.resolution.split("x")
    W = int(resolution_str[0])
    H = int(resolution_str[1])
    grid_size = tuple(int(x) for x in args.grid.split("x"))

    # 构造棋盘格角点在世界坐标中的位置，z 默认为 0
    grid_points = np.zeros((1, np.prod(grid_size), 3), np.float32)
    grid_points[0, :, :2] = np.indices(grid_size).T.reshape(-1, 2)

    objpoints = []  # 世界坐标中的角点
    imgpoints = []  # 图像坐标中的角点

    device = args.input
    cap_thread = CaptureThread(device_id=device,
                               flip_method=args.flip,
                               resolution=(W, H),
                               use_gst=not args.no_gst,
                               )
    buffer_manager = MultiBufferManager()
    buffer_manager.bind_thread(cap_thread, buffer_size=8)
    if cap_thread.connect_camera():
        cap_thread.start()
    else:
        print("cannot open device")
        return

    quit = False
    do_calib = False
    i = -1
    while True:
        i += 1

        # 从缓存中取出当前帧
        img = buffer_manager.get_device(device).get().image
        if i % args.framestep != 0:
            continue

        print("searching for chessboard corners in frame " + str(i) + "...")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(
            gray,
            grid_size,
            cv2.CALIB_CB_ADAPTIVE_THRESH +
            cv2.CALIB_CB_NORMALIZE_IMAGE +
            cv2.CALIB_CB_FILTER_QUADS
        )
        if found:
            term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.01)
            cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1), term)
            print("OK")
            imgpoints.append(corners)
            objpoints.append(grid_points)
            cv2.drawChessboardCorners(img, grid_size, corners, found)

        cv2.putText(img, text1, (20, 70), font, fontscale, (255, 200, 0), 2)
        cv2.putText(img, text2, (20, 110), font, fontscale, (255, 200, 0), 2)
        cv2.putText(img, text3, (20, 30), font, fontscale, (255, 200, 0), 2)
        cv2.imshow("corners", img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("c"):
            print("\nPerforming calibration...\n")
            N_OK = len(objpoints)
            if N_OK < 12:
                print("Less than 12 corners (%d) detected, calibration failed" %(N_OK))
                continue
            else:
                # 采样足够后开始标定
                do_calib = True
                break

        elif key == ord("q"):
            quit = True
            break

    if quit:
        cap_thread.stop()
        cap_thread.disconnect_camera()
        cv2.destroyAllWindows()

    if do_calib:
        N_OK = len(objpoints)
        K = np.zeros((3, 3))
        D = np.zeros((4, 1))
        rvecs = [np.zeros((1, 1, 3), dtype=np.float64) for _ in range(N_OK)]
        tvecs = [np.zeros((1, 1, 3), dtype=np.float64) for _ in range(N_OK)]
        calibration_flags = (cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC +
                             cv2.fisheye.CALIB_CHECK_COND +
                             cv2.fisheye.CALIB_FIX_SKEW)

        if args.fisheye:
            # 鱼眼相机标定
            ret, mtx, dist, rvecs, tvecs = cv2.fisheye.calibrate(
                objpoints,
                imgpoints,
                (W, H),
                K,
                D,
                rvecs,
                tvecs,
                calibration_flags,
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)
            )
        else:
            # 普通针孔相机标定
            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
                objpoints,
                imgpoints,
                (W, H),
                None,
                None)

        if ret:
            # 将标定结果写入 yaml 文件
            fs = cv2.FileStorage(args.output, cv2.FILE_STORAGE_WRITE)
            fs.write("resolution", np.int32([W, H]))
            fs.write("camera_matrix", mtx)
            fs.write("dist_coeffs", dist)
            fs.release()
            print("successfully saved camera data")
            cv2.putText(img, "Success!", (220, 240), font, 2, (0, 0, 255), 2)

        else:
            cv2.putText(img, "Failed!", (220, 240), font, 2, (0, 0, 255), 2)

        cv2.imshow("corners", img)
        cv2.waitKey(0)


if __name__ == "__main__":
    main()

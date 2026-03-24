#!/usr/bin/env python3

import argparse
import cv2
import time


def parse_resolution(text):
    width, height = text.lower().split("x")
    return int(width), int(height)


def get_cam_lst(cam_lst=range(0, 24)):
    """
    Probe available camera devices.
    """
    arr = []
    for iCam in cam_lst:
        cap = cv2.VideoCapture(iCam)
        ok, _ = cap.read()
        cap.release()
        if ok:
            arr.append(iCam)
    return arr


def show_cam_img(caps, cam_list):
    print("INFO: Press 'q' to quit! Press 's' to save a picture, 'n' to change to next camera device!")
    idx = 0
    while True:
        cap_device = caps[idx]
        ret, frame = cap_device.read()
        if ret:
            cv2.imshow('video', frame)
        else:
            print("ERROR: failed read frame!")

        # quit the test
        c = cv2.waitKey(1)
        if c == ord('q'):
            break

        # change to next camera device
        if c == ord('n'):
            idx += 1
            if idx >= len(caps):
                idx = 0
            continue

        # save the picture
        if c == ord('s'):
            if ret:
                name = 'video{0}_{1}.png'.format(cam_list[idx],
                            time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime()))
                cv2.imwrite(name, frame)
                print("saved file: %s!" %name)

    cv2.destroyAllWindows()


def init_caps(cam_list, resolution=(1280, 720)):
    caps = []
    for iCam in cam_list:
        cap = cv2.VideoCapture(iCam)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(3, resolution[0])
        cap.set(4, resolution[1])
        caps.append(cap)

    return caps

def deinit_caps(cap_list):
    for cap in cap_list:
        cap.release()


def show_cameras(video_list=None, resolution=(1280, 720)):
    if video_list is None:
        print("Start to search all available camera devices, please wait... ")
        cam_list = get_cam_lst()
        err_msg = "cannot find any video device!"
    else:
        cam_list = get_cam_lst(video_list)
        err_msg = "cannot find available video device in list: {0}!".format(video_list) +\
                    "\nPlease check the video devices in /dev/v4l/by-path/ folder!"

    if len(cam_list) < 1:
        print("ERROR: " + err_msg)
        return

    print("Available video device list is {}".format(cam_list))
    caps = init_caps(cam_list, resolution=resolution)
    show_cam_img(caps, cam_list)
    deinit_caps(caps)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--devices",
        nargs="*",
        type=int,
        default=None,
        help="optional list of camera ids to test, for example: --devices 0 1 2 3",
    )
    parser.add_argument(
        "-r",
        "--resolution",
        default="1280x720",
        help="preview resolution, for example: 1280x720",
    )
    args = parser.parse_args()

    show_cameras(args.devices, resolution=parse_resolution(args.resolution))

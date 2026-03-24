import os
import numpy as np
import cv2

from . import param_settings as settings


class FisheyeCameraModel(object):

    """
    Fisheye camera model, for undistorting, projecting and flipping camera frames.
    """

    def __init__(self, camera_param_file, camera_name):
        if not os.path.isfile(camera_param_file):
            raise ValueError("Cannot find camera param file")

        if camera_name not in settings.all_camera_names:
            raise ValueError("Unknown camera name: {}".format(camera_name))

        self.camera_file = camera_param_file
        self.camera_name = camera_name
        self.scale_xy = (1.0, 1.0)
        self.shift_xy = (0, 0)
        self.undistort_maps = None
        self.project_matrix = None
        self.project_shape = settings.project_shapes[self.camera_name]
        self.load_camera_params()

    def load_camera_params(self):
        # 从 yaml 中读取相机内参、畸变参数、分辨率，以及可选的投影参数
        fs = cv2.FileStorage(self.camera_file, cv2.FILE_STORAGE_READ)
        self.camera_matrix = fs.getNode("camera_matrix").mat()
        self.dist_coeffs = fs.getNode("dist_coeffs").mat()
        self.resolution = tuple(int(x) for x in fs.getNode("resolution").mat().flatten())

        scale_xy = fs.getNode("scale_xy").mat()
        if scale_xy is not None:
            self.scale_xy = tuple(float(x) for x in scale_xy.flatten())

        shift_xy = fs.getNode("shift_xy").mat()
        if shift_xy is not None:
            self.shift_xy = tuple(float(x) for x in shift_xy.flatten())

        project_matrix = fs.getNode("project_matrix").mat()
        if project_matrix is not None:
            self.project_matrix = project_matrix

        fs.release()
        self.update_undistort_maps()

    def update_undistort_maps(self):
        # 通过修改新的内参矩阵来控制去畸变后的缩放和平移
        # 这样做的目的，是在手动选投影点时尽量保留更多有效地面区域
        new_matrix = self.camera_matrix.copy()
        new_matrix[0, 0] *= self.scale_xy[0]
        new_matrix[1, 1] *= self.scale_xy[1]
        new_matrix[0, 2] += self.shift_xy[0]
        new_matrix[1, 2] += self.shift_xy[1]
        width, height = self.resolution

        # 预先生成 remap 查找表，后面 undistort 时就不需要重复计算
        self.undistort_maps = cv2.fisheye.initUndistortRectifyMap(
            self.camera_matrix,
            self.dist_coeffs,
            np.eye(3),
            new_matrix,
            (width, height),
            cv2.CV_16SC2
        )
        return self

    def set_scale_and_shift(self, scale_xy=(1.0, 1.0), shift_xy=(0, 0)):
        self.scale_xy = scale_xy
        self.shift_xy = shift_xy
        self.update_undistort_maps()
        return self

    def undistort(self, image):
        # 使用预计算好的查找表做鱼眼去畸变
        result = cv2.remap(image, *self.undistort_maps, interpolation=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_CONSTANT)
        return result

    def project(self, image):
        if self.project_matrix is None:
            raise ValueError(
                "Missing project_matrix in {}. Run run_get_projection_maps.py first.".format(
                    self.camera_file
                )
            )
        # 使用人工标定得到的 project_matrix 做透视投影
        result = cv2.warpPerspective(image, self.project_matrix, self.project_shape)
        return result

    def flip(self, image):
        # 四路相机投影后朝向不同，这里统一旋转到最终鸟瞰图坐标系
        if self.camera_name == "front":
            return image.copy()

        elif self.camera_name == "back":
            return image.copy()[::-1, ::-1, :]

        elif self.camera_name == "left":
            return cv2.transpose(image)[::-1]

        else:
            return np.flip(cv2.transpose(image), 1)

    def save_data(self):
        # 保存当前相机完整处理链路所需的数据
        # 包括：内参、畸变、分辨率、投影矩阵、去畸变缩放和平移
        fs = cv2.FileStorage(self.camera_file, cv2.FILE_STORAGE_WRITE)
        fs.write("camera_matrix", self.camera_matrix)
        fs.write("dist_coeffs", self.dist_coeffs)
        fs.write("resolution", self.resolution)
        fs.write("project_matrix", self.project_matrix)
        fs.write("scale_xy", np.float32(self.scale_xy))
        fs.write("shift_xy", np.float32(self.shift_xy))
        fs.release()

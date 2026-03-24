# Ship 360 View Monitoring System

这是一个基于 Python + OpenCV + PyQt5 的船舶环视监控项目，围绕六路相机鸟瞰拼接主链路构建，核心能力包括：

- 相机标定
- 鱼眼去畸变
- 地面投影矩阵生成
- 多视角鸟瞰图拼接
- 权重矩阵与遮罩生成
- 多线程实时预览

# Project Structure

主要文件说明：

- `run_calibrate_camera.py`：采集棋盘格角点并生成相机标定参数
- `run_get_projection_maps.py`：手动选点并计算每个相机的投影矩阵
- `run_get_weight_matrices.py`：生成拼接权重矩阵和 mask
- `run_live_demo.py`：实时读取多路相机并显示拼接结果
- `test_cameras.py`：检测并预览本机可用摄像头
- `surround_view/`：核心功能模块，包括相机模型、线程、拼接、工具函数等
- `yaml/`：相机参数和投影参数
- `images/`：示例输入图像

项目通道命名采用六路方案：

- `front`
- `front_left`
- `front_right`
- `left`
- `right`
- `back`


# Environment Setup

推荐使用 Miniconda：

```bash
cd /Users/apple/Documents/dev/projectsCode/Ship-360-View-Monitoring-System-main
conda env create -f environment.yml
conda activate ship360-surround-view
```

如果你想手动安装：

```bash
conda create -n ship360 python=3.9 -y
conda activate ship360
conda install -c conda-forge numpy pillow pyqt opencv
```

或者在已有环境中使用：

```bash
pip install -r requirements.txt
```

依赖详情见 `INSTALL.md`。


# Dependencies

本项目当前代码实际依赖：

- Python 3.9
- numpy
- opencv
- Pillow
- PyQt5

注意：

- 不要使用 `opencv-python-headless`
- 本项目使用了 `cv2.imshow()` 等 GUI 能力
- `run_live_demo.py` 中部分摄像头采集逻辑依赖 GStreamer / Linux 环境


# Quick Start

1. 验证环境

```bash
python -c "import cv2, numpy, PIL, PyQt5; print('environment ok')"
```

2. 标定相机

```bash
python run_calibrate_camera.py -i 0 -grid 9x6 -r 640x480 -o yaml/front.yaml -fisheye
```

3. 计算投影矩阵

```bash
python run_get_projection_maps.py -camera front -scale 0.7 0.8 -shift -150 -100
```

4. 生成拼接权重

```bash
python run_get_weight_matrices.py
```

5. 实时预览

```bash
python run_live_demo.py
```

开始实时预览前，请先确认：

- `yaml/front.yaml`、`yaml/front_left.yaml`、`yaml/front_right.yaml`、`yaml/left.yaml`、`yaml/right.yaml`、`yaml/back.yaml` 中已经有可用的 `camera_matrix`、`dist_coeffs` 和 `project_matrix`
- 项目根目录下已经生成了 `weights.png` 和 `masks.png`
- [surround_view/param_settings.py](/Users/apple/Documents/dev/projectsCode/Ship-360-View-Monitoring-System-main/surround_view/param_settings.py) 里的相机名称顺序与 [run_live_demo.py](/Users/apple/Documents/dev/projectsCode/Ship-360-View-Monitoring-System-main/run_live_demo.py) 的 `camera_ids`、`flip_methods` 一一对齐


# Real-time Pipeline

实时运行时，代码主流程可以概括为：

1. `CaptureThread`
   负责从多路摄像头采集原始图像。

2. `CameraProcessingThread`
   对每一路图像执行去畸变、投影和方向统一。

3. `ProjectedImageBuffer`
   等待各处理线程都完成当前帧，再把这一组投影图一起交给下一阶段。

4. `BirdView`
   对多路投影图做亮度平衡、拼接、白平衡和主体区域覆盖，生成最终鸟瞰图。

5. 主线程
   调用 `cv2.imshow()` 实时显示拼接结果，并打印各线程 FPS。


# Notes

- 如果只是做标定、投影和离线拼接测试，普通电脑通常就够用。
- 如果要跑实时多路摄像头，尤其是 CSI 摄像头，通常还需要 Linux、GStreamer 和正确的驱动支持。
- 如果运行时报 `Missing project_matrix`，说明对应 yaml 还没完成投影矩阵标定。
- 更完整的安装说明见 `INSTALL.md`。

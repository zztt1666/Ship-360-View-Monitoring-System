# Miniconda 环境配置说明

本文档整理了本项目的 Python 环境、依赖安装方式和常用运行命令。

## 1. 项目依赖

根据代码中的实际 `import`，本项目核心依赖如下：

- Python 3.9
- numpy
- opencv
- Pillow
- PyQt5

说明：

- `cv2` 用于图像处理、标定、显示窗口和摄像头读取。
- `PyQt5` 主要用于线程和同步控制。
- 不要使用 `opencv-python-headless`，因为本项目需要 `cv2.imshow()` 等图形界面能力。

项目中已提供两份依赖文件：

- `environment.yml`：推荐给 `conda` 使用
- `requirements.txt`：可选，给 `pip` 使用


## 2. 使用 Miniconda 创建环境

如果你已经安装好 Miniconda，进入项目目录后执行：

```bash
cd /Users/apple/Documents/dev/projectsCode/Ship-360-View-Monitoring-System-main
conda env create -f environment.yml
conda activate ship360-surround-view
```

如果你想手动创建环境，也可以：

```bash
conda create -n ship360 python=3.9 -y
conda activate ship360
conda install -c conda-forge numpy pillow pyqt opencv
```


## 3. 使用 pip 安装

如果你已经进入某个 Conda 环境，也可以直接使用：

```bash
pip install -r requirements.txt
```


## 4. 验证环境是否安装成功

执行下面命令：

```bash
python -c "import cv2, numpy, PIL, PyQt5; print('environment ok')"
```

如果终端输出 `environment ok`，说明基础依赖已经安装完成。


## 5. 常用运行命令

推荐执行顺序：

1. 先检查摄像头设备号
2. 再做相机标定
3. 再做投影矩阵标定
4. 再生成权重矩阵和 masks
5. 最后运行实时预览

### 5.1 检查摄像头

自动搜索可用设备：

```bash
python test_cameras.py
```

指定设备并设置预览分辨率：

```bash
python test_cameras.py --devices 0 1 2 3 4 5 -r 1280x720
```


### 5.2 相机标定

```bash
python run_calibrate_camera.py -i 0 -grid 9x6 -r 640x480 -o yaml/front.yaml -fisheye
```

常用参数：

- `-i`：摄像头编号
- `-grid`：棋盘格角点数量，例如 `9x6`
- `-r`：分辨率，例如 `640x480`
- `-o`：输出标定参数文件
- `-fisheye`：鱼眼相机时加上这个参数
- `-flip`：图像翻转方式
- `--no_gst`：不使用 GStreamer 采集时可加


### 5.3 获取投影矩阵

```bash
python run_get_projection_maps.py -camera front -scale 0.7 0.8 -shift -150 -100
```

执行完成后，会把以下内容写回对应的 `yaml/*.yaml` 文件：

- `project_matrix`
- `scale_xy`
- `shift_xy`


### 5.4 生成权重矩阵

```bash
python run_get_weight_matrices.py
```

该命令会生成：

- `weights.png`
- `masks.png`


### 5.5 实时预览

```bash
python run_live_demo.py
```

注意：

- 运行前需要先准备好多路 yaml 的标定参数和投影矩阵（六路项目建议至少包含 `front/front_left/front_right/left/right/back`）
- 还需要先生成 `weights.png` 和 `masks.png`
- [surround_view/param_settings.py](/Users/apple/Documents/dev/projectsCode/Ship-360-View-Monitoring-System-main/surround_view/param_settings.py) 里的相机名称顺序，必须与 [run_live_demo.py](/Users/apple/Documents/dev/projectsCode/Ship-360-View-Monitoring-System-main/run_live_demo.py) 中 `camera_ids`、`flip_methods` 的顺序严格对齐


## 6. 运行环境说明

本项目更适合在 Linux 环境运行（推荐 Ubuntu）。

如果你只是做：

- 标定
- 投影矩阵生成
- 拼接逻辑测试

那么普通电脑上的 Conda 环境通常就够了。

如果你要运行 `run_live_demo.py` 中的 CSI 摄像头实时采集，则除了 Python 环境外，通常还需要：

- 系统安装 GStreamer
- OpenCV 支持 GStreamer
- Jetson / Linux 下可用的摄像头驱动

这是因为项目中的 `surround_view/utils.py` 使用了基于 GStreamer 的摄像头管线。


## 7. YAML 参数文件说明

每个相机对应一个 `yaml/*.yaml` 文件，常见字段包括：

- `camera_matrix`：相机内参矩阵
- `dist_coeffs`：畸变系数
- `resolution`：标定分辨率
- `project_matrix`：投影矩阵
- `scale_xy`：去畸变时的缩放参数
- `shift_xy`：去畸变时的平移参数

其中：

- `camera_matrix`、`dist_coeffs` 来自 `run_calibrate_camera.py`
- `project_matrix`、`scale_xy`、`shift_xy` 来自 `run_get_projection_maps.py`

如果缺少 `project_matrix`，实时投影和拼接阶段会失败。

## 8. 依赖文件内容

### `environment.yml`

```yaml
name: ship360-surround-view
channels:
  - conda-forge
dependencies:
  - python=3.9
  - numpy>=1.21,<2.0
  - pillow>=9,<11
  - pyqt=5.15.*
  - opencv>=4.6,<5
```


### `requirements.txt`

```txt
numpy>=1.21,<2.0
opencv-python>=4.6,<5
Pillow>=9,<11
PyQt5>=5.15,<5.16
```


## 9. 推荐使用方式

推荐优先使用：

```bash
conda env create -f environment.yml
conda activate ship360-surround-view
```

因为 `opencv` 和 `pyqt` 这类包在 `conda-forge` 下通常更省心，兼容性也更好。

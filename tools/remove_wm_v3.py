#!/usr/bin/env python3
"""
OpenCV 右下角水印去除 v3
改进：纯色背景采样填充，不破坏原图质感

原理：右下角背景通常是纯色（白色/蓝色条），直接采样周围颜色填充，
     比 inpainting 更干净，不会产生模糊/马赛克痕迹。

用法：
  python remove_wm_v3.py 图片.jpg
  python remove_wm_v3.py *.jpg --x1 0.78 --y1 0.95 --x2 0.99 --y2 0.995
"""

import cv2
import numpy as np
import argparse
from pathlib import Path


def sample_background_color(img, box, sample_offset=10):
    """
    从水印区域周围采样背景色
    分别采样：上方、左方、下方的背景色
    """
    h, w = img.shape[:2]
    x1, y1, x2, y2 = box

    # 采样点：水印上方10像素处、左方10像素处、下方10像素处
    samples = []

    # 上方采样
    if y1 - sample_offset > 0:
        sample_y = y1 - sample_offset
        sample_x1 = x1 + (x2 - x1) // 4
        sample_x2 = x2 - (x2 - x1) // 4
        color_above = np.median(img[sample_y, sample_x1:sample_x2], axis=0)
        samples.append(color_above)

    # 左方采样
    if x1 - sample_offset > 0:
        sample_x = x1 - sample_offset
        sample_y1 = y1 + (y2 - y1) // 4
        sample_y2 = y2 - (y2 - y1) // 4
        color_left = np.median(img[sample_y1:sample_y2, sample_x], axis=0)
        samples.append(color_left)

    # 下方采样
    if y2 + sample_offset < h:
        sample_y = y2 + sample_offset
        sample_x1 = x1 + (x2 - x1) // 4
        sample_x2 = x2 - (x2 - x1) // 4
        color_below = np.median(img[sample_y, sample_x1:sample_x2], axis=0)
        samples.append(color_below)

    if not samples:
        # 兜底：用区域左上角的颜色
        return img[y1, x1]

    # 取中位数，避免噪声
    avg_color = np.median(samples, axis=0).astype(np.uint8)
    return avg_color


def fill_solid_background(img, box, color=None, feather_edge=True):
    """
    用纯色填充水印区域
    如果指定了color就用指定色，否则自动采样
    """
    result = img.copy()
    x1, y1, x2, y2 = box

    if color is None:
        color = sample_background_color(img, box)

    # 直接填充
    result[y1:y2, x1:x2] = color

    # 边缘羽化：上下边缘做1-2像素的渐变，避免硬边
    if feather_edge:
        feather = 2
        for i in range(feather):
            alpha = (i + 1) / (feather + 1)
            # 上边缘渐变
            result[y1 - feather + i, x1:x2] = (
                result[y1 - feather + i, x1:x2] * (1 - alpha) + color * alpha
            ).astype(np.uint8)
            # 下边缘渐变
            result[y2 + i, x1:x2] = (
                result[y2 + i, x1:x2] * (1 - alpha) + color * alpha
            ).astype(np.uint8)

    return result


def fill_with_blend(img, box, method='sample'):
    """
    智能填充：根据背景颜色渐变自动处理
    适合背景有轻微渐变（如蓝白交界）的情况
    """
    x1, y1, x2, y2 = box
    roi_h = y2 - y1
    roi_w = x2 - x1

    result = img.copy()

    # 把区域分成上下两半
    mid_y = y1 + roi_h // 2

    # 上半部分：采样上方颜色
    color_above = sample_background_color(img, (x1, y1, x2, mid_y), sample_offset=5)
    result[y1:mid_y, x1:x2] = color_above

    # 下半部分：采样下方颜色
    color_below = sample_background_color(img, (x1, mid_y, x2, y2), sample_offset=5)
    result[mid_y:y2, x1:x2] = color_below

    # 中间过渡带做渐变
    blend_h = 5
    blend_y1 = mid_y - blend_h // 2
    blend_y2 = mid_y + blend_h // 2
    for y in range(blend_y1, blend_y2):
        alpha = (y - blend_y1) / blend_h
        result[y, x1:x2] = (
            color_above * (1 - alpha) + color_below * alpha
        ).astype(np.uint8)

    return result


def process_image(input_path, output_path, box_coords, mode='sample', debug=False):
    """处理单张图片"""
    img = cv2.imread(input_path)
    if img is None:
        print(f"  [错误] 无法读取: {input_path}")
        return False

    h, w = img.shape[:2]
    x1, y1, x2, y2 = box_coords
    box = (int(w * x1), int(h * y1), int(w * x2), int(h * y2))

    print(f"  区域: ({box[0]},{box[1]})→({box[2]},{box[3]})")
    print(f"  模式: {mode}")

    if mode == 'solid':
        # 纯填充（单色）
        color = sample_background_color(img, box)
        print(f"  采样颜色: BGR={color.tolist()}")
        result = fill_solid_background(img, box)
    elif mode == 'blend':
        # 渐变填充（适合蓝白交界）
        result = fill_with_blend(img, box)
    else:
        # 自动判断：检测上下颜色差异
        color_above = sample_background_color(img, box, sample_offset=10)
        # 简单判断：如果上下亮度差异大，用blend模式
        result = fill_with_blend(img, box)

    cv2.imwrite(output_path, result, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    print(f"  已保存: {output_path}")

    if debug:
        debug_img = img.copy()
        cv2.rectangle(debug_img, (box[0], box[1]), (box[2], box[3]), (0, 0, 255), 2)
        debug_path = str(Path(output_path).with_suffix('.debug.png'))
        cv2.imwrite(debug_path, debug_img)
        print(f"  调试图: {debug_path}")

    return True


def main():
    parser = argparse.ArgumentParser(description='OpenCV 右下角水印去除 v3（纯色填充版）')
    parser.add_argument('inputs', nargs='+', help='输入图片')
    parser.add_argument('-o', '--output-dir', default='output_clean_v3',
                        help='输出目录')
    parser.add_argument('--x1', type=float, default=0.78, help='左上角x比例')
    parser.add_argument('--y1', type=float, default=0.95, help='左上角y比例')
    parser.add_argument('--x2', type=float, default=0.99, help='右下角x比例')
    parser.add_argument('--y2', type=float, default=0.995, help='右下角y比例')
    parser.add_argument('--mode', choices=['solid', 'blend', 'auto'], default='auto',
                        help='填充模式: solid=单色, blend=渐变, auto=自动判断')
    parser.add_argument('--debug', action='store_true', help='保存调试图')

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True)

    box = (args.x1, args.y1, args.x2, args.y2)

    success = 0
    for i, input_path in enumerate(args.inputs, 1):
        print(f"\n[{i}/{len(args.inputs)}] {input_path}")
        stem = Path(input_path).stem
        ext = Path(input_path).suffix or '.png'
        output_path = str(out_dir / f"{stem}_clean{ext}")

        ok = process_image(input_path, output_path, box, mode=args.mode, debug=args.debug)
        if ok:
            success += 1

    print(f"\n{'='*50}")
    print(f"完成: {success}/{len(args.inputs)} 张")
    print(f"输出: {out_dir.resolve()}")


if __name__ == '__main__':
    main()

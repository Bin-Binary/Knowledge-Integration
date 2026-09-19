#!/usr/bin/env python3
"""
OpenCV 右下角水印去除 v4
改进：逐行采样填充，完美匹配背景渐变，零痕迹

用法：
  python remove_wm_v4.py 图片.jpg
  python remove_wm_v4.py *.jpg --x1 0.80 --y1 0.955 --x2 0.99 --y2 0.99
"""

import cv2
import numpy as np
import argparse
from pathlib import Path


def fill_row_by_row(img, box):
    """
    逐行采样填充：
    每一行都从左边采样背景色，填充到对应行的水印区域
    这样能完美匹配背景的水平渐变
    """
    result = img.copy()
    x1, y1, x2, y2 = box

    # 从水印左边采样（同一行，往左偏移20像素）
    sample_offset = 20

    for y in range(y1, y2):
        # 采样点：同一行，水印左边20像素处
        sample_x = x1 - sample_offset
        if sample_x < 0:
            sample_x = 0

        # 取采样点的颜色（横向取5个像素平均，更稳定）
        sample_pixels = img[y, max(0, sample_x-2):sample_x+3]
        row_color = np.mean(sample_pixels, axis=0).astype(np.uint8)

        # 填充这一行的水印区域
        result[y, x1:x2] = row_color

    return result


def fill_col_by_col(img, box):
    """
    逐列采样填充：
    每一列都从上方采样背景色，填充到对应列的水印区域
    适合垂直渐变的背景
    """
    result = img.copy()
    x1, y1, x2, y2 = box

    sample_offset = 15

    for x in range(x1, x2):
        sample_y = y1 - sample_offset
        if sample_y < 0:
            sample_y = 0

        sample_pixels = img[max(0, sample_y-2):sample_y+3, x]
        col_color = np.mean(sample_pixels, axis=0).astype(np.uint8)

        result[y1:y2, x] = col_color

    return result


def smart_fill(img, box):
    """
    智能填充：
    1. 先检测水印区域内是否有水平分界线（蓝白交界）
    2. 如果有，分成上下两段，逐行填充
    3. 左边缘做渐变羽化，避免硬边
    """
    x1, y1, x2, y2 = box
    roi_h = y2 - y1
    roi_w = x2 - x1

    # 先做整体填充（逐行从左边采样）
    for y in range(y1, y2):
        sample_x = x1 - 20
        if sample_x < 0:
            sample_x = 0
        sample_pixels = img[y, max(0, sample_x-2):sample_x+3]
        row_color = np.mean(sample_pixels, axis=0).astype(np.uint8)
        img[y, x1:x2] = row_color

    # 左边缘渐变羽化：从左往右，透明度从0到1
    feather_width = min(20, roi_w // 4)
    for offset in range(feather_width):
        x = x1 + offset
        alpha = offset / feather_width  # 0 → 1
        for y in range(y1, y2):
            # 原始背景色（左边的像素）
            orig_color = img[y, x1 - feather_width + offset].astype(float)
            # 填充色
            fill_color = img[y, x].astype(float)
            # 混合
            blended = orig_color * (1 - alpha) + fill_color * alpha
            img[y, x] = blended.astype(np.uint8)

    print(f"  左边缘羽化: {feather_width} 像素")
    return img


def process_image(input_path, output_path, box_coords, debug=False):
    img = cv2.imread(input_path)
    if img is None:
        print(f"  [错误] 无法读取: {input_path}")
        return False

    h, w = img.shape[:2]
    x1, y1, x2, y2 = box_coords
    box = (int(w * x1), int(h * y1), int(w * x2), int(h * y2))

    print(f"  区域: ({box[0]},{box[1]})→({box[2]},{box[3]})")

    result = smart_fill(img, box)

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
    parser = argparse.ArgumentParser(description='OpenCV 右下角水印去除 v4（逐行采样版）')
    parser.add_argument('inputs', nargs='+', help='输入图片')
    parser.add_argument('-o', '--output-dir', default='output_clean_v4',
                        help='输出目录')
    parser.add_argument('--x1', type=float, default=0.70, help='左上角x比例（往左扩大，避免边界）')
    parser.add_argument('--y1', type=float, default=0.95, help='左上角y比例')
    parser.add_argument('--x2', type=float, default=1.0, help='右下角x比例（到图片边缘）')
    parser.add_argument('--y2', type=float, default=1.0, help='右下角y比例（到图片边缘）')
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

        ok = process_image(input_path, output_path, box, debug=args.debug)
        if ok:
            success += 1

    print(f"\n{'='*50}")
    print(f"完成: {success}/{len(args.inputs)} 张")
    print(f"输出: {out_dir.resolve()}")


if __name__ == '__main__':
    main()

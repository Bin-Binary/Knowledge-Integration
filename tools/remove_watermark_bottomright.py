#!/usr/bin/env python3
"""
OpenCV 水印去除工具 —— 精准去除右下角"AI豆包生成"水印
使用 Inpainting（图像修复）算法，在原图像素上直接修复，不重新生成图片。

用法：
  单张处理：python3 remove_watermark_bottomright.py input.jpg
  批量处理：python3 remove_watermark_bottomright.py *.jpg
  调整水印大小：--wm-w 0.15 --wm-h 0.04
  查看 mask 预览：--save-mask
  选择算法：--method telea 或 --method ns
  自动检测水印（文字笔画法）：--auto

# 单张处理
python3 remove_watermark_bottomright.py 你的图片.jpg

# 批量处理（所有 jpg）
python3 remove_watermark_bottomright.py *.jpg

# 先看检测框位置对不对（强烈建议第一次先跑这个）
python3 remove_watermark_bottomright.py 你的图片.jpg --save-mask

"""

import cv2
import numpy as np
import argparse
from pathlib import Path


def create_mask_bottomright(h, w, wm_w_ratio=0.14, wm_h_ratio=0.028, margin_ratio=0.012):
    """
    在右下角创建水印掩码。
    wm_w_ratio: 水印宽度占图片宽度比例，默认 14%
    wm_h_ratio: 水印高度占图片高度比例，默认 2.8%
    margin_ratio: 距离右边和底边的边距比例，默认 1.2%
    """
    mask = np.zeros((h, w), dtype=np.uint8)
    wm_w = int(w * wm_w_ratio)
    wm_h = int(h * wm_h_ratio)
    margin_x = int(w * margin_ratio)
    margin_y = int(h * margin_ratio)
    x1 = w - margin_x - wm_w
    x2 = w - margin_x
    y1 = h - margin_y - wm_h
    y2 = h - margin_y
    mask[y1:y2, x1:x2] = 255
    return mask, (x1, y1, x2, y2)


def create_mask_auto_bright(img, threshold=200):
    """
    自动检测右下角浅色水印：
    水印通常是半透明浅灰色文字，在右下角 ROI 内检测亮度异常区域。
    """
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 右下角 ROI：右边 25% × 底部 8%
    roi_w = int(w * 0.25)
    roi_h = int(h * 0.08)
    roi_x = w - roi_w
    roi_y = h - roi_h
    roi = gray[roi_y:h, roi_x:w]

    # 水印通常比背景稍浅或稍深，用自适应阈值检测
    binary = cv2.adaptiveThreshold(
        roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 21, 7
    )

    # 形态学连接文字笔画
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (4, 2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    # 去除小噪点
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    min_area = 5
    cleaned = np.zeros_like(binary)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            cleaned[labels == i] = 255

    # 膨胀确保覆盖边缘
    cleaned = cv2.dilate(cleaned, kernel, iterations=1)

    mask = np.zeros((h, w), dtype=np.uint8)
    mask[roi_y:h, roi_x:w] = cleaned
    return mask, (roi_x, roi_y, w, h)


def create_mask_color_based(img):
    """
    基于豆包水印特征颜色检测。
    豆包 AI 水印通常带有品牌色（蓝色/紫色调），在右下角区域内检测。
    """
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 右下角 ROI
    roi_w = int(w * 0.25)
    roi_h = int(h * 0.08)
    roi_x = w - roi_w
    roi_y = h - roi_h

    # 检测蓝色/紫色调（豆包品牌色范围）
    lower_blue = np.array([90, 30, 100])
    upper_blue = np.array([140, 255, 255])
    roi_hsv = hsv[roi_y:h, roi_x:w]
    color_mask = cv2.inRange(roi_hsv, lower_blue, upper_blue)

    # 形态学处理
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 2))
    color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    color_mask = cv2.dilate(color_mask, kernel, iterations=1)

    mask = np.zeros((h, w), dtype=np.uint8)
    mask[roi_y:h, roi_x:w] = color_mask
    return mask, (roi_x, roi_y, w, h)


def inpaint_watermark(img, mask, method='telea', radius=5):
    """
    使用 Inpainting 修复水印区域。
    method: 'telea' (Fast Marching Method) 或 'ns' (Navier-Stokes)
    radius: 修复邻域半径，默认 5
    """
    if method == 'ns':
        flag = cv2.INPAINT_NS
    else:
        flag = cv2.INPAINT_TELEA

    result = cv2.inpaint(img, mask, radius, flag)
    return result


def draw_debug_box(img, box, color=(0, 0, 255), thickness=2):
    """在调试图上画出水印检测框"""
    x1, y1, x2, y2 = box
    debug = img.copy()
    cv2.rectangle(debug, (x1, y1), (x2, y2), color, thickness)
    return debug


def process_image(input_path, output_path, method='telea', radius=5,
                  wm_w_ratio=0.18, wm_h_ratio=0.04, margin_ratio=0.02,
                  auto=False, color_mode=False):
    """处理单张图片"""
    img = cv2.imread(input_path)
    if img is None:
        print(f"  [错误] 无法读取: {input_path}")
        return False, None

    h, w = img.shape[:2]

    # 生成 mask
    if color_mode:
        mask, box = create_mask_color_based(img)
        mode_desc = "品牌色检测（蓝紫色调）"
    elif auto:
        mask, box = create_mask_auto_bright(img)
        mode_desc = "自动文字检测"
    else:
        mask, box = create_mask_bottomright(h, w, wm_w_ratio, wm_h_ratio, margin_ratio)
        mode_desc = f"右下角固定区域 ({wm_w_ratio*100:.0f}% × {wm_h_ratio*100:.0f}%, 边距{margin_ratio*100:.0f}%)"

    print(f"  模式: {mode_desc}")

    # 检查 mask 是否非空
    pixel_count = int(mask.sum() / 255)
    if pixel_count == 0:
        print(f"  [警告] 未检测到水印区域，跳过")
        return False, box

    print(f"  图片尺寸: {w} × {h}, 水印像素数: {pixel_count}")
    print(f"  算法: {method.upper()}, 修复半径: {radius}")

    # 修复
    result = inpaint_watermark(img, mask, method, radius)

    # 保存
    cv2.imwrite(output_path, result, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    print(f"  已保存: {output_path}")
    return True, box


def main():
    parser = argparse.ArgumentParser(description='OpenCV 右下角"AI豆包生成"水印去除工具')
    parser.add_argument('inputs', nargs='+', help='输入图片路径（支持多个）')
    parser.add_argument('-o', '--output-dir', default='output_clean',
                        help='输出目录（默认: output_clean）')
    parser.add_argument('--method', choices=['telea', 'ns'], default='telea',
                        help='修复算法: telea (快速行进法) 或 ns (纳维-斯托克斯法)，默认 telea')
    parser.add_argument('--radius', type=int, default=5,
                        help='修复邻域半径 1-20，默认 5')
    parser.add_argument('--wm-w', type=float, default=0.14,
                        help='水印宽度占图片宽度比例，默认 0.14 (14%%)')
    parser.add_argument('--wm-h', type=float, default=0.028,
                        help='水印高度占图片高度比例，默认 0.028 (2.8%%)')
    parser.add_argument('--margin', type=float, default=0.012,
                        help='距离右边和底边的边距比例，默认 0.012 (1.2%%)')
    parser.add_argument('--auto', action='store_true',
                        help='自动文字检测模式')
    parser.add_argument('--color', action='store_true',
                        help='品牌色检测模式（蓝紫色调水印）')
    parser.add_argument('--save-mask', action='store_true',
                        help='额外保存 mask 预览和检测框调试图')

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True)

    success = 0
    total = len(args.inputs)

    for i, input_path in enumerate(args.inputs, 1):
        print(f"\n[{i}/{total}] 处理: {input_path}")
        stem = Path(input_path).stem
        ext = Path(input_path).suffix or '.png'
        output_path = str(out_dir / f"{stem}_clean{ext}")

        ok, box = process_image(
            input_path, output_path,
            method=args.method,
            radius=args.radius,
            wm_w_ratio=args.wm_w,
            wm_h_ratio=args.wm_h,
            margin_ratio=args.margin,
            auto=args.auto,
            color_mode=args.color,
        )

        if ok and args.save_mask:
            img = cv2.imread(input_path)
            # 重新生成 mask 用于预览
            if args.color:
                mask, _ = create_mask_color_based(img)
            elif args.auto:
                mask, _ = create_mask_auto_bright(img)
            else:
                h, w = img.shape[:2]
                mask, box = create_mask_bottomright(h, w, args.wm_w, args.wm_h, args.margin)

            # 保存 mask 预览
            mask_path = str(out_dir / f"{stem}_mask.png")
            cv2.imwrite(mask_path, mask)
            print(f"  Mask 预览: {mask_path}")

            # 保存带检测框的调试图
            if box:
                debug = draw_debug_box(img, box)
                debug_path = str(out_dir / f"{stem}_debug_box.png")
                cv2.imwrite(debug_path, debug)
                print(f"  检测框调试图: {debug_path}")

        if ok:
            success += 1

    print(f"\n{'='*50}")
    print(f"完成: {success}/{total} 张成功")
    print(f"输出目录: {out_dir.resolve()}")


if __name__ == '__main__':
    main()

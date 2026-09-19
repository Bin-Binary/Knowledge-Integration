#!/usr/bin/env python3
"""
OpenCV 右下角"AI豆包生成"水印去除工具 v2
改进：精准文字检测 + mask羽化 + 二次修复，消除马赛克痕迹

用法：
  单张处理：python3 remove_wm_v2.py input.jpg
  批量处理：python3 remove_wm_v2.py *.jpg
  手动指定区域：--x1 0.85 --y1 0.95 --x2 0.98 --y2 0.98
  查看调试：--debug
  精细模式（推荐）：--precise
"""

import cv2
import numpy as np
import argparse
from pathlib import Path


def detect_watermark_precise(img):
    """
    精准检测右下角水印文字：
    1. 右下角ROI提取
    2. 多尺度边缘检测+自适应阈值
    3. 形态学连接文字笔画
    4. 过滤噪点
    """
    h, w = img.shape[:2]

    # 右下角 ROI：右边 30% × 底部 6%
    roi_w = int(w * 0.30)
    roi_h = int(h * 0.06)
    roi_x = w - roi_w
    roi_y = h - roi_h
    roi = img[roi_y:h, roi_x:w].copy()

    # 转灰度
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # 自适应阈值检测文字笔画
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 15, 4
    )

    # 形态学：连接笔画 + 去除噪点
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (6, 2))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close, iterations=1)

    # 连通域过滤：只保留文字大小的块
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    min_area = 3
    max_area = 500
    cleaned = np.zeros_like(closed)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if min_area <= area <= max_area:
            cleaned[labels == i] = 255

    # 稍微膨胀，确保覆盖水印边缘
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.dilate(cleaned, kernel_dilate, iterations=1)

    # 放回全图mask
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[roi_y:h, roi_x:w] = cleaned

    return mask, (roi_x, roi_y, w, h)


def create_mask_manual(h, w, x1_ratio, y1_ratio, x2_ratio, y2_ratio):
    """手动指定水印区域（比例坐标）"""
    mask = np.zeros((h, w), dtype=np.uint8)
    x1 = int(w * x1_ratio)
    y1 = int(h * y1_ratio)
    x2 = int(w * x2_ratio)
    y2 = int(h * y2_ratio)
    mask[y1:y2, x1:x2] = 255
    return mask, (x1, y1, x2, y2)


def feather_mask(mask, blur_size=5):
    """
    对mask做高斯模糊羽化，避免硬边界导致的修复痕迹/马赛克
    关键改进！
    """
    if blur_size % 2 == 0:
        blur_size += 1
    feathered = cv2.GaussianBlur(mask, (blur_size, blur_size), 0)
    # 保持核心区域全白，边缘渐变
    _, feathered = cv2.threshold(feathered, 128, 255, cv2.THRESH_BINARY)
    # 再做一次轻微模糊，让边缘更自然
    feathered = cv2.GaussianBlur(feathered, (3, 3), 0)
    return feathered


def inpaint_twostage(img, mask, method='telea', radius=3):
    """
    两阶段修复：
    第一阶段：大半径粗修
    第二阶段：小半径精修（消除马赛克）
    """
    flag = cv2.INPAINT_NS if method == 'ns' else cv2.INPAINT_TELEA

    # 第一阶段：粗修
    stage1 = cv2.inpaint(img, mask, radius + 2, flag)

    # 第二阶段：精修（用更软的mask，更小半径）
    soft_mask = cv2.GaussianBlur(mask, (5, 5), 0)
    stage2 = cv2.inpaint(stage1, soft_mask, radius, flag)

    return stage2


def process_image(input_path, output_path, method='telea', radius=3,
                  precise=False, manual_coords=None, debug=False):
    """处理单张图片"""
    img = cv2.imread(input_path)
    if img is None:
        print(f"  [错误] 无法读取: {input_path}")
        return False, None

    h, w = img.shape[:2]

    # 生成 mask
    if manual_coords:
        x1, y1, x2, y2 = manual_coords
        mask, box = create_mask_manual(h, w, x1, y1, x2, y2)
        mode_desc = f"手动区域 ({x1:.2f},{y1:.2f})→({x2:.2f},{y2:.2f})"
    elif precise:
        mask, box = detect_watermark_precise(img)
        mode_desc = "精准文字检测"
    else:
        # 默认：右下角固定区域（稍微放大一点确保覆盖）
        mask, box = create_mask_manual(h, w, 0.82, 0.95, 0.99, 0.99)
        mode_desc = "默认右下角区域"

    print(f"  模式: {mode_desc}")

    pixel_count = int(mask.sum() / 255)
    if pixel_count == 0:
        print(f"  [警告] 未检测到水印区域，跳过")
        return False, box

    print(f"  图片尺寸: {w}×{h}, 水印像素: {pixel_count}")
    print(f"  算法: {method.upper()}, 半径: {radius}")

    # 羽化mask（关键！消除马赛克）
    mask_feathered = feather_mask(mask, blur_size=5)

    # 两阶段修复
    result = inpaint_twostage(img, mask_feathered, method=method, radius=radius)

    # 保存
    cv2.imwrite(output_path, result, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    print(f"  已保存: {output_path}")

    # 保存调试文件
    if debug:
        mask_path = str(Path(output_path).with_suffix('.mask.png'))
        cv2.imwrite(mask_path, mask_feathered)

        debug_img = img.copy()
        cv2.rectangle(debug_img, (box[0], box[1]), (box[2], box[3]), (0, 0, 255), 2)
        debug_path = str(Path(output_path).with_suffix('.debug.png'))
        cv2.imwrite(debug_path, debug_img)
        print(f"  Mask: {mask_path}")
        print(f"  调试图: {debug_path}")

    return True, box


def main():
    parser = argparse.ArgumentParser(description='OpenCV 右下角水印去除 v2（无马赛克版）')
    parser.add_argument('inputs', nargs='+', help='输入图片')
    parser.add_argument('-o', '--output-dir', default='output_clean_v2',
                        help='输出目录（默认: output_clean_v2）')
    parser.add_argument('--method', choices=['telea', 'ns'], default='telea',
                        help='修复算法: telea / ns，默认 telea')
    parser.add_argument('--radius', type=int, default=3,
                        help='修复半径 1-10，默认 3（越小越细腻）')
    parser.add_argument('--precise', action='store_true',
                        help='精准文字检测模式（推荐，自动找水印）')
    parser.add_argument('--x1', type=float, help='手动指定区域：左上角x比例 (0-1)')
    parser.add_argument('--y1', type=float, help='手动指定区域：左上角y比例 (0-1)')
    parser.add_argument('--x2', type=float, help='手动指定区域：右下角x比例 (0-1)')
    parser.add_argument('--y2', type=float, help='手动指定区域：右下角y比例 (0-1)')
    parser.add_argument('--debug', action='store_true',
                        help='保存mask和调试图')

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True)

    # 检查手动坐标是否完整
    manual = None
    if all([args.x1 is not None, args.y1 is not None,
            args.x2 is not None, args.y2 is not None]):
        manual = (args.x1, args.y1, args.x2, args.y2)

    success = 0
    for i, input_path in enumerate(args.inputs, 1):
        print(f"\n[{i}/{len(args.inputs)}] {input_path}")
        stem = Path(input_path).stem
        ext = Path(input_path).suffix or '.png'
        output_path = str(out_dir / f"{stem}_clean{ext}")

        ok, _ = process_image(
            input_path, output_path,
            method=args.method,
            radius=args.radius,
            precise=args.precise,
            manual_coords=manual,
            debug=args.debug,
        )
        if ok:
            success += 1

    print(f"\n{'='*50}")
    print(f"完成: {success}/{len(args.inputs)} 张")
    print(f"输出: {out_dir.resolve()}")


if __name__ == '__main__':
    main()

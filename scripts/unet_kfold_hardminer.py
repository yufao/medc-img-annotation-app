#!/usr/bin/env python3
"""
UNet k-fold 训练与困难样本挖掘脚本

用途：
- 从带有图像与分割掩膜清单（manifest.csv）的数据集中，进行 k 折交叉验证训练 UNet。
- 在每一折验证集上计算每张图的 IoU/Dice，筛选出低于阈值的“困难样本”，记录其样本 id。

清单文件要求（CSV/TSV/Parquet 皆可，自动按扩展名推断读取方式；默认 CSV）：
- 必需列：id, image_path, mask_path
- 可选列：fold（如果提供则使用该折划分，否则自动用 KFold 划分）

输出：
- data/results/hard_samples/hard_samples.csv  包含 id, fold, iou, dice
- data/results/hard_samples/hard_sample_ids.txt  仅包含去重后的困难样本 id 列表
- data/results/hard_samples/metrics_fold_*.csv  每折验证集全量样本指标

备注：
- 本脚本只负责训练与筛样本，不落盘模型。如需落盘可加 --save-checkpoint 选项。
- 若当前项目暂未提供分割掩膜（mask_path），请先准备清单文件再运行。
"""

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Tuple, Optional, List

import numpy as np
import pandas as pd
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

from sklearn.model_selection import KFold


# -------------------------
# 基础工具
# -------------------------

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def load_image(path: str, mode: str = 'L') -> Image.Image:
    """加载图像，默认转为单通道灰度（医学图像常用）。
    mode='RGB' 可改为三通道。
    """
    img = Image.open(path)
    if mode:
        img = img.convert(mode)
    return img


def to_tensor(img: Image.Image) -> torch.Tensor:
    arr = np.array(img, dtype=np.float32)
    if arr.ndim == 2:  # H, W -> 1, H, W
        arr = arr[None, :, :]
    else:  # H, W, C -> C, H, W
        arr = arr.transpose(2, 0, 1)
    # 归一化到[0,1]
    return torch.from_numpy(arr) / 255.0


def resize(img: Image.Image, size: Tuple[int, int]) -> Image.Image:
    return img.resize(size, Image.BILINEAR)


def resize_mask(mask: Image.Image, size: Tuple[int, int]) -> Image.Image:
    # 掩膜用最近邻避免插值混淆
    return mask.resize(size, Image.NEAREST)


# -------------------------
# 数据集
# -------------------------

@dataclass
class Sample:
    sid: str
    image_path: str
    mask_path: str


class SegDataset(Dataset):
    def __init__(self, df: pd.DataFrame, image_size: Tuple[int, int] = (256, 256), image_mode: str = 'L'):
        self.df = df.reset_index(drop=True)
        self.size = image_size
        self.image_mode = image_mode

        required = {'id', 'image_path', 'mask_path'}
        if not required.issubset(self.df.columns):
            raise ValueError(f"manifest 需要列: {required}, 实际: {set(self.df.columns)}")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        sid = str(row['id'])
        img_path = str(row['image_path'])
        msk_path = str(row['mask_path'])

        img = load_image(img_path, self.image_mode)
        msk = load_image(msk_path, 'L')

        if self.size is not None:
            img = resize(img, self.size)
            msk = resize_mask(msk, self.size)

        img_t = to_tensor(img)
        msk_arr = np.array(msk, dtype=np.uint8)
        # 二值化（>0 为前景）
        msk_bin = (msk_arr > 0).astype(np.float32)
        msk_t = torch.from_numpy(msk_bin)[None, :, :]

        return {
            'id': sid,
            'image': img_t,
            'mask': msk_t,
        }


# -------------------------
# 模型（简易 UNet）
# -------------------------

class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class UNet(nn.Module):
    def __init__(self, in_channels=1, out_channels=1, base_ch: int = 32):
        super().__init__()
        # 编码器
        self.dc1 = DoubleConv(in_channels, base_ch)
        self.pool1 = nn.MaxPool2d(2)
        self.dc2 = DoubleConv(base_ch, base_ch * 2)
        self.pool2 = nn.MaxPool2d(2)
        self.dc3 = DoubleConv(base_ch * 2, base_ch * 4)
        self.pool3 = nn.MaxPool2d(2)
        self.dc4 = DoubleConv(base_ch * 4, base_ch * 8)
        self.pool4 = nn.MaxPool2d(2)

        self.bottleneck = DoubleConv(base_ch * 8, base_ch * 16)

        # 解码器
        self.up4 = nn.ConvTranspose2d(base_ch * 16, base_ch * 8, 2, stride=2)
        self.uc4 = DoubleConv(base_ch * 16, base_ch * 8)
        self.up3 = nn.ConvTranspose2d(base_ch * 8, base_ch * 4, 2, stride=2)
        self.uc3 = DoubleConv(base_ch * 8, base_ch * 4)
        self.up2 = nn.ConvTranspose2d(base_ch * 4, base_ch * 2, 2, stride=2)
        self.uc2 = DoubleConv(base_ch * 4, base_ch * 2)
        self.up1 = nn.ConvTranspose2d(base_ch * 2, base_ch, 2, stride=2)
        self.uc1 = DoubleConv(base_ch * 2, base_ch)

        self.head = nn.Conv2d(base_ch, out_channels, 1)

    def forward(self, x):
        c1 = self.dc1(x)
        p1 = self.pool1(c1)
        c2 = self.dc2(p1)
        p2 = self.pool2(c2)
        c3 = self.dc3(p2)
        p3 = self.pool3(c3)
        c4 = self.dc4(p3)
        p4 = self.pool4(c4)

        bn = self.bottleneck(p4)

        u4 = self.up4(bn)
        u4 = torch.cat([u4, c4], dim=1)
        u4 = self.uc4(u4)
        u3 = self.up3(u4)
        u3 = torch.cat([u3, c3], dim=1)
        u3 = self.uc3(u3)
        u2 = self.up2(u3)
        u2 = torch.cat([u2, c2], dim=1)
        u2 = self.uc2(u2)
        u1 = self.up1(u2)
        u1 = torch.cat([u1, c1], dim=1)
        u1 = self.uc1(u1)
        out = self.head(u1)
        return out


# -------------------------
# 损失与指标
# -------------------------

class DiceLoss(nn.Module):
    def __init__(self, eps: float = 1e-6):
        super().__init__()
        self.eps = eps

    def forward(self, logits, targets):
        probs = torch.sigmoid(logits)
        dims = (1, 2, 3)
        inter = (probs * targets).sum(dims)
        union = probs.sum(dims) + targets.sum(dims)
        dice = (2 * inter + self.eps) / (union + self.eps)
        return 1 - dice.mean()


def bce_dice_loss(logits, targets, dice_w=0.5):
    bce = F.binary_cross_entropy_with_logits(logits, targets)
    dsc = DiceLoss()(logits, targets)
    return (1 - dice_w) * bce + dice_w * dsc


def iou_score(pred, target, th: float = 0.5, eps: float = 1e-6):
    pred_bin = (pred > th).float()
    inter = (pred_bin * target).sum(dim=(1, 2, 3))
    union = pred_bin.sum(dim=(1, 2, 3)) + target.sum(dim=(1, 2, 3)) - inter
    iou = (inter + eps) / (union + eps)
    return iou


def dice_score(pred, target, th: float = 0.5, eps: float = 1e-6):
    pred_bin = (pred > th).float()
    inter = (pred_bin * target).sum(dim=(1, 2, 3))
    union = pred_bin.sum(dim=(1, 2, 3)) + target.sum(dim=(1, 2, 3))
    dice = (2 * inter + eps) / (union + eps)
    return dice


# -------------------------
# 训练与验证
# -------------------------

@dataclass
class TrainConfig:
    img_size: Tuple[int, int] = (256, 256)
    in_channels: int = 1
    base_ch: int = 32
    batch_size: int = 8
    epochs: int = 10
    lr: float = 1e-3
    num_workers: int = 2
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    seed: int = 42
    kfold: int = 5
    metric_threshold: float = 0.5  # IoU 阈值，小于即判定为困难样本
    prob_threshold: float = 0.5  # 二值化概率阈值用于指标


def set_seed(seed: int):
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def train_one_epoch(model, loader, optim, cfg: TrainConfig):
    model.train()
    losses = []
    for batch in loader:
        imgs = batch['image'].to(cfg.device)
        msks = batch['mask'].to(cfg.device)

        logits = model(imgs)
        loss = bce_dice_loss(logits, msks)

        optim.zero_grad()
        loss.backward()
        optim.step()
        losses.append(loss.item())
    return float(np.mean(losses)) if losses else 0.0


@torch.no_grad()
def validate(model, loader, cfg: TrainConfig):
    model.eval()
    all_ids: List[str] = []
    all_iou: List[float] = []
    all_dice: List[float] = []
    losses: List[float] = []
    for batch in loader:
        ids = batch['id']
        imgs = batch['image'].to(cfg.device)
        msks = batch['mask'].to(cfg.device)

        logits = model(imgs)
        probs = torch.sigmoid(logits)
        loss = bce_dice_loss(logits, msks)
        losses.append(loss.item())

        ious = iou_score(probs, msks, th=cfg.prob_threshold).cpu().numpy().tolist()
        dices = dice_score(probs, msks, th=cfg.prob_threshold).cpu().numpy().tolist()
        all_ids.extend(list(ids))
        all_iou.extend(ious)
        all_dice.extend(dices)
    return {
        'val_loss': float(np.mean(losses)) if losses else 0.0,
        'ids': all_ids,
        'iou': all_iou,
        'dice': all_dice,
    }


# -------------------------
# 主流程
# -------------------------

def read_manifest(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext == '.csv' or ext == '':
        return pd.read_csv(path)
    elif ext in ('.tsv', '.txt'):
        return pd.read_csv(path, sep='\t')
    elif ext in ('.parquet', '.pq'):
        return pd.read_parquet(path)
    else:
        raise ValueError(f"不支持的清单文件格式: {ext}")


def main():
    parser = argparse.ArgumentParser(description='UNet k-fold 困难样本挖掘')
    parser.add_argument('--manifest', type=str, required=True, help='包含 id,image_path,mask_path 的清单 CSV/TSV/Parquet')
    parser.add_argument('--img-size', type=int, nargs=2, default=(256, 256), help='输入尺寸 W H')
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--batch-size', type=int, default=8)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--kfold', type=int, default=5)
    parser.add_argument('--metric-th', type=float, default=0.5, help='IoU 阈值，低于则判定为困难样本')
    parser.add_argument('--prob-th', type=float, default=0.5, help='预测二值化阈值')
    parser.add_argument('--in-ch', type=int, default=1)
    parser.add_argument('--base-ch', type=int, default=32)
    parser.add_argument('--num-workers', type=int, default=2)
    parser.add_argument('--device', type=str, default='cuda' if torch.cuda.is_available() else 'cpu')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--outdir', type=str, default='data/results/hard_samples')
    parser.add_argument('--save-checkpoint', action='store_true', help='可选：保存每折最后的模型权重')

    args = parser.parse_args()

    ensure_dir(args.outdir)
    set_seed(args.seed)

    df = read_manifest(args.manifest)
    required = {'id', 'image_path', 'mask_path'}
    if not required.issubset(df.columns):
        raise SystemExit(f"manifest 缺少必要列: {required}，实际: {set(df.columns)}")

    # 过滤无效路径
    missing_img = ~df['image_path'].apply(lambda p: os.path.isfile(str(p)))
    missing_msk = ~df['mask_path'].apply(lambda p: os.path.isfile(str(p)))
    if missing_img.any() or missing_msk.any():
        print(f"警告：存在无效文件路径，自动剔除 {int(missing_img.sum() + missing_msk.sum())} 条。")
        df = df[~(missing_img | missing_msk)].reset_index(drop=True)
    if len(df) == 0:
        raise SystemExit('有效样本数为 0，请检查清单与路径。')

    cfg = TrainConfig(
        img_size=(args.img_size[1], args.img_size[0]) if isinstance(args.img_size, (list, tuple)) else (args.img_size, args.img_size),
        in_channels=args.in_ch,
        base_ch=args.base_ch,
        batch_size=args.batch_size,
        epochs=args.epochs,
        lr=args.lr,
        num_workers=args.num_workers,
        device=args.device,
        seed=args.seed,
        kfold=args.kfold,
        metric_threshold=args.metric_th,
        prob_threshold=args.prob_th,
    )

    print(f"使用设备: {cfg.device}")
    print(f"样本数: {len(df)}, k 折: {cfg.kfold}")

    hard_records = []  # 收集每折困难样本

    if 'fold' in df.columns:
        # 使用已有划分
        unique_folds = sorted(df['fold'].dropna().unique().tolist())
        print(f"使用 manifest 中的 fold 划分: {unique_folds}")
        for fold in unique_folds:
            train_df = df[df['fold'] != fold]
            val_df = df[df['fold'] == fold]
            hard_records.extend(run_fold(train_df, val_df, cfg, fold, args.outdir, args.save_checkpoint))
    else:
        kf = KFold(n_splits=cfg.kfold, shuffle=True, random_state=cfg.seed)
        for fold, (tr_idx, va_idx) in enumerate(kf.split(df)):
            train_df = df.iloc[tr_idx]
            val_df = df.iloc[va_idx]
            hard_records.extend(run_fold(train_df, val_df, cfg, fold, args.outdir, args.save_checkpoint))

    # 汇总与落盘
    metrics_all = pd.DataFrame(hard_records)
    if len(metrics_all) == 0:
        print('未产生任何困难样本记录。')
        # 仍输出空模板
        metrics_all.to_csv(os.path.join(args.outdir, 'hard_samples.csv'), index=False)
        open(os.path.join(args.outdir, 'hard_sample_ids.txt'), 'w').close()
        return

    metrics_all.to_csv(os.path.join(args.outdir, 'hard_samples.csv'), index=False)
    hard_ids = metrics_all.loc[metrics_all['is_hard'] == 1, 'id'].astype(str).unique().tolist()
    with open(os.path.join(args.outdir, 'hard_sample_ids.txt'), 'w') as f:
        for sid in hard_ids:
            f.write(f"{sid}\n")

    print(f"困难样本数（去重）：{len(hard_ids)}，已保存至 {os.path.join(args.outdir, 'hard_sample_ids.txt')}")


def run_fold(train_df: pd.DataFrame, val_df: pd.DataFrame, cfg: TrainConfig, fold: int, outdir: str, save_ckpt: bool):
    print(f"\n===== FOLD {fold} 训练样本 {len(train_df)}，验证样本 {len(val_df)} =====")
    train_ds = SegDataset(train_df, image_size=cfg.img_size, image_mode='L' if cfg.in_channels == 1 else 'RGB')
    val_ds = SegDataset(val_df, image_size=cfg.img_size, image_mode='L' if cfg.in_channels == 1 else 'RGB')

    train_loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True, num_workers=cfg.num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=cfg.batch_size, shuffle=False, num_workers=cfg.num_workers, pin_memory=True)

    model = UNet(in_channels=cfg.in_channels, out_channels=1, base_ch=cfg.base_ch).to(cfg.device)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.lr)

    best_val = float('inf')
    for ep in range(1, cfg.epochs + 1):
        tr_loss = train_one_epoch(model, train_loader, optimizer, cfg)
        val_out = validate(model, val_loader, cfg)
        msg = f"[Fold {fold}] Epoch {ep}/{cfg.epochs} | tr_loss {tr_loss:.4f} | val_loss {val_out['val_loss']:.4f} | val_iou_mean {np.mean(val_out['iou']):.4f}"
        print(msg)
        if val_out['val_loss'] < best_val:
            best_val = val_out['val_loss']
            best_snapshot = {
                'ids': val_out['ids'],
                'iou': val_out['iou'],
                'dice': val_out['dice'],
            }

    # 保存每折最佳指标表
    fold_df = pd.DataFrame({
        'id': best_snapshot['ids'],
        'iou': best_snapshot['iou'],
        'dice': best_snapshot['dice'],
    })
    fold_df['fold'] = fold
    fold_df['is_hard'] = (fold_df['iou'] < cfg.metric_threshold).astype(int)
    fold_csv = os.path.join(outdir, f'metrics_fold_{fold}.csv')
    fold_df.to_csv(fold_csv, index=False)
    print(f"保存验证指标: {fold_csv}")

    # 可选：保存权重（最后一轮）
    if save_ckpt:
        ckpt_path = os.path.join(outdir, f'unet_fold_{fold}.pt')
        torch.save({'model': model.state_dict(), 'cfg': cfg.__dict__}, ckpt_path)
        print(f"保存模型权重: {ckpt_path}")

    # 返回记录用于全局汇总
    return fold_df.to_dict(orient='records')


if __name__ == '__main__':
    main()

import os
import shutil
import random
from pathlib import Path

# 경로 설정
SRC_ROOT = Path("D:/foodsnap_CNN/건강관리를 위한 음식 이미지/Training/train_p")
DST_ROOT = Path("D:/foodsnap_CNN/건강관리를 위한 음식 이미지/Training/chunks")
CHUNK_SIZE_BYTES = 20 * 1024 ** 3  # 20GB
VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')

# 1. 전체 이미지 목록 수집
all_images = []
for class_dir in SRC_ROOT.iterdir():
    if class_dir.is_dir():
        for img_file in class_dir.glob("*"):
            if img_file.suffix.lower() in VALID_EXTENSIONS:
                size = img_file.stat().st_size
                all_images.append((img_file, class_dir.name, size))

print(f"총 이미지 수: {len(all_images)}")
random.shuffle(all_images)  # 무작위 셔플

# 2. 청크 단위로 나눠서 복사
chunk_idx = 1
chunk_size = 0
chunk_files = []

for img_path, class_name, file_size in all_images:
    if chunk_size + file_size > CHUNK_SIZE_BYTES:
        # 현재 청크 저장
        dst_chunk = DST_ROOT / f"train_chunk{chunk_idx}"
        print(f"✅ Chunk {chunk_idx}: {len(chunk_files)}개 이미지, {chunk_size/1024**3:.2f} GB")
        for src, cls in chunk_files:
            dst_class_dir = dst_chunk / cls
            dst_class_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst_class_dir / src.name)
        # 다음 청크로 초기화
        chunk_idx += 1
        chunk_size = 0
        chunk_files = []

    chunk_files.append((img_path, class_name))
    chunk_size += file_size

# 마지막 청크 저장
if chunk_files:
    dst_chunk = DST_ROOT / f"train_chunk{chunk_idx}"
    print(f"✅ Chunk {chunk_idx}: {len(chunk_files)}개 이미지, {chunk_size/1024**3:.2f} GB")
    for src, cls in chunk_files:
        dst_class_dir = dst_chunk / cls
        dst_class_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst_class_dir / src.name)

print("🎉 모든 청크 분할 완료!")

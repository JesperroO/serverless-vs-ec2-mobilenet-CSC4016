# model_loader.py

import os
import torch
import torchvision.models as models
import torchvision.transforms as transforms

# 关键咒语：在 torch 被使用之前，就设定好它的家
EFS_ROOT = '/mnt/efs'
CACHE_DIR = os.path.join(EFS_ROOT, 'cache')
os.environ['TORCH_HOME'] = CACHE_DIR

_model = None
_preprocess = None

def get_model():
    global _model, _preprocess
    if _model is None:
        print("Model not loaded. Initializing from EFS cache...")
        _model = models.mobilenet_v2(pretrained=True)
        _model.eval()
        _preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        print("Model and preprocessing pipeline ready.")
    return _model, _preprocess
import json
import time
import base64
import io
from PIL import Image
from model_loader import get_model
import torch

# --- 模型在 handler 之外预热 ---
print("Pre-warming model on init...")
model, preprocess = get_model()
print("Model is warm and ready.")

def handler(event, context):
    try:
        # --- 新的，解析逻辑 ---
        # 1. 解析 JSON 字符串
        body = json.loads(event['body'])
        # 2. 从 JSON 中，提取 base64 编码的图像字符串
        image_b64 = body['image']
        # 3. 将 base64 字符串，解码回，二进制字节
        image_bytes = base64.b64decode(image_b64)
        # ----------------------

        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        input_tensor = preprocess(image).unsqueeze(0)

        start_time = time.perf_counter()
        with torch.no_grad():
            output = model(input_tensor)
        end_time = time.perf_counter()
        
        latency = (end_time - start_time) * 1000

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Inference successful',
                'latency_ms': round(latency, 2)
            })
        }
    except Exception as e:
        # 打印详细的错误，以便我们知道，到底是哪一步，出了问题
        import traceback
        print(f"ERROR during inference: {e}")
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
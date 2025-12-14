import boto3
import time
import requests
import base64
import json
import numpy as np

# --- 配置 ---
FUNCTION_NAME = 'csc4160-inference-target' 
API_URL = 'https://8keg68m54a.execute-api.us-east-1.amazonaws.com/default/csc4160-inference-target' # 确认这是最新的 URL
IMAGE_PATH = 'test_images/test_image.png' # 确保存放图片的路径是对的
NUM_TRIALS = 10 # 既然是冷启动，10次够了，别跑太多

lambda_client = boto3.client('lambda', region_name='us-east-1')

def force_cold_start():
    """通过更新环境变量来强制冷启动，同时保留关键的 PYTHONPATH"""
    print("Forcing cold start...", end='', flush=True)
    lambda_client.update_function_configuration(
        FunctionName=FUNCTION_NAME,
        Environment={
            'Variables': {
                # --- 关键修正: 必须带上 PYTHONPATH ---
                'PYTHONPATH': '/mnt/efs/site-packages',
                # -----------------------------------
                'TORCH_HOME': '/mnt/efs/cache', 
                'FORCE_COLD_ID': str(time.time()) # 随机变量触发更新
            }
        }
    )
    
    # 等待更新完成 (状态变成 Active)
    while True:
        response = lambda_client.get_function(FunctionName=FUNCTION_NAME)
        status = response['Configuration']['State']
        if status == 'Active':
            break
        time.sleep(1)
        
    print(" Done.")

def invoke_api():
    try:
        # 确保图片存在
        with open(IMAGE_PATH, 'rb') as f:
            img_b64 = base64.b64encode(f.read()).decode('utf-8')
        
        payload = {'image': img_b64}
        
        start = time.time()
        # 增加超时时间，冷启动很慢
        resp = requests.post(API_URL, json=payload, timeout=60) 
        end = time.time()
        
        return (end - start) * 1000, resp.status_code
    except Exception as e:
        print(f"\nRequest failed: {e}")
        return 0, 500

latencies = []

print(f"Starting {NUM_TRIALS} cold start trials...")

for i in range(NUM_TRIALS):
    print(f"Trial {i+1}/{NUM_TRIALS}: ", end='')
    
    # 1. 强制冷启动
    force_cold_start()
    
    # 2. 调用并计时
    # 给一点点缓冲时间让 AWS 传播配置
    time.sleep(2) 
    
    latency, status = invoke_api()
    print(f"Latency = {latency:.2f} ms (Status: {status})")
    
    if status == 200:
        latencies.append(latency)
    else:
        print("Error in invocation! Check CloudWatch Logs.")

print("-" * 30)
if latencies:
    print(f"Cold Start Analysis ({len(latencies)} samples):")
    print(f"Average: {np.mean(latencies):.2f} ms")
    print(f"Median:  {np.median(latencies):.2f} ms")
    print(f"Min:     {np.min(latencies):.2f} ms")
    print(f"Max:     {np.max(latencies):.2f} ms")
else:
    print("No successful data collected.")
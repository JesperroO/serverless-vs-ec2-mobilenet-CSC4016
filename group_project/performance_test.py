import json
import queue
import requests
import time
import argparse
import csv
import threading
import numpy as np
import sys
import os
import glob
import base64

# 发送单个请求，附带一个图像文件
def send_single_request(session, url, image_path):
    try:
        with open(image_path, 'rb') as image_file:
            image_bytes = image_file.read()
            
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        
        json_payload = {
            "image": base64_string
        }

        # 在发送请求前启动计时器
        start_time = time.perf_counter()
            
        response = session.post(url, json=json_payload, timeout=30) # 设置30秒超时
            
        end_time = time.perf_counter()
            
        latency_ms = (end_time - start_time) * 1000
            
        # 如果状态码在2xx范围内，则认为请求成功
        if 200 <= response.status_code < 300:
            return (True, response.status_code, latency_ms)
        else:
            return (False, response.status_code, latency_ms)

    except requests.exceptions.RequestException as e:
        # 处理网络错误、超时等异常
        return (False, -1, -1.0)

# 工作进程
def worker(pid, url, image_path_queue, mode, value, results_queue):
    # 每个进程都必须拥有自己的Session对象，不能共享
    session = requests.Session()
    
    if mode == 'duration':
        start_time = time.time()
        end_time = start_time + value
        while time.time() < end_time:
            image_path = image_path_queue.get()
            result = send_single_request(session, url, image_path)
            results_queue.put(result)
            image_path_queue.put(image_path)
            image_path_queue.task_done()
    elif mode == 'num_requests':
        for _ in range(value):
            image_path = image_path_queue.get()
            result = send_single_request(session, url, image_path)
            results_queue.put(result)
            image_path_queue.put(image_path)
            image_path_queue.task_done()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Performance testing tool for AI model APIs.")
    parser.add_argument("--url", type=str, required=True, help="The URL of the API endpoint.")
    parser.add_argument("--image-dir", type=str, required=True, help="Path to the directory containing test images.")
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent users/processes.")
    parser.add_argument("--duration", type=int, help="Total duration of the test in seconds.")
    parser.add_argument("--num-requests", type=int, help="Total number of requests to send.")
    
    args = parser.parse_args()

    # 参数验证
    if not args.duration and not args.num_requests:
        print("Error: You must specify either --duration or --num-requests.", file=sys.stderr)
        sys.exit(1)
    if args.duration and args.num_requests:
        print("Error: You cannot specify both --duration and --num-requests.", file=sys.stderr)
        sys.exit(1)

    # 加载图片数据集
    image_extensions = ('*.jpg', '*.jpeg', '*.png')
    image_paths = []
    for ext in image_extensions:
        image_paths.extend(glob.glob(os.path.join(args.image_dir, ext)))

    if not image_paths:
        print(f"Error: No images found in directory '{args.image_dir}'.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(image_paths)} images for testing.")

    # 将图片路径放入队列
    image_path_queue = queue.Queue()
    for path in image_paths:
        image_path_queue.put(path)

    # 进行测试
    print(f"Starting test for {args.url} with concurrency: {args.concurrency}...")
    
    # results_queue = multiprocessing.Queue()
    results_queue = queue.Queue()
    threads = []
    
    mode = 'duration' if args.duration else 'num_requests'
    value = args.duration if args.duration else args.num_requests
    
    # 如果是按次数模式，将请求均分给各个工作进程
    value_per_worker = value
    if mode == 'num_requests':
        value_per_worker = value // args.concurrency
        if value % args.concurrency != 0:
            print(f"Warning: Total requests ({value}) is not perfectly divisible by concurrency ({args.concurrency}).")

    start_total_time = time.time()

    for i in range(args.concurrency):
        t = threading.Thread(target=worker, args=(i, args.url, image_path_queue, mode, value_per_worker, results_queue))
        threads.append(t)
        t.start()

    # 等待所有工作进程结束
    for t in threads:
        t.join()
        
    end_total_time = time.time()
    actual_duration = end_total_time - start_total_time

    # 数据获取
    all_results = []
    while not results_queue.empty():
        all_results.append(results_queue.get())
        
    # 数据保存
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    sanitized_url = args.url.split('//')[-1].replace('/', '_').replace(':', '_').replace('.', '_') 
    mode_str = f"duration{args.duration}s" if args.duration else f"reqs{args.num_requests}"
    filename = f"{sanitized_url}_c{args.concurrency}_{mode_str}_{timestamp}.csv"
    output_path = os.path.join(output_dir, filename)

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['request_id', 'success', 'status_code', 'latency_ms'])
        for i, result in enumerate(all_results):
            writer.writerow([i + 1, result[0], result[1], result[2]])
    print(f"\nRaw data saved to: {output_path}")

    # 摘要计算与报告，输出摘要信息 
    if not all_results:
        print("No requests were made. Please check your parameters.")
        sys.exit()

    successful_requests = [r for r in all_results if r[0]]
    failed_requests = [r for r in all_results if not r[0]]
    latencies = [r[2] for r in successful_requests if r[2] >= 0]

    # 计算各项指标
    total_reqs = len(all_results)
    success_rate = len(successful_requests) / total_reqs * 100 if total_reqs > 0 else 0
    avg_ips = len(successful_requests) / actual_duration if actual_duration > 0 else 0
    
    # 打印摘要
    print("\n" + "="*50)
    print("        Performance Test Summary")
    print("="*50)
    print(f"Target URL:       {args.url}")
    print(f"Concurrency:      {args.concurrency}")
    print(f"Actual Duration:  {actual_duration:.2f} seconds")
    print("-"*50)
    print(f"Total Requests:   {total_reqs}")
    print(f"Successful:       {len(successful_requests)} ({success_rate:.2f}%)")
    print(f"Failed:           {len(failed_requests)}")
    print("-"*50)
    print(f"Average IPS:      {avg_ips:.2f} (Inferences Per Second)")
    print("-"*50)
    if latencies:
        print(f"Min Latency:      {np.min(latencies):.2f} ms")
        print(f"Avg Latency:      {np.mean(latencies):.2f} ms")
        print(f"Max Latency:      {np.max(latencies):.2f} ms")
        print(f"P95 Latency:      {np.percentile(latencies, 95):.2f} ms")
        print(f"P99 Latency:      {np.percentile(latencies, 99):.2f} ms")
    print("="*50)
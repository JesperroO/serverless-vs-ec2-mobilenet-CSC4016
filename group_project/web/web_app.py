import base64
import csv
import json
import os
import time
from typing import Dict, Any

import requests
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "demo-secret-key"  # 用于 flash 提示


# =========================
# 后端配置：根据实际情况修改
# =========================
BACKENDS = {
    "lambda": {
        "label": "AWS Lambda",
        # 改成 API Gateway URL
        "url": "https://<api-gw>/prod/infer",
        "enabled": True,
        "use_fake": False,
    },
    # EC2 x86 实例（括号内改为实际的实例类型）
    "ec2_x86": {
        "label": "EC2-x86 (t3.medium)",
        # 使用实例的公共ip地址进行连接
        "url": "http://<x86-ip-or-domain>:5000/infer",
        "enabled": True,
        "use_fake": False,
    },
    # EC2 ARM 实例（括号内改为实际的实例类型）
    "ec2_arm": {
        "label": "EC2-ARM (t4g.medium)",
        # 使用实例的公共ip地址进行连接
        "url": "http://<arm-ip-or-domain>:5000/infer",
        "enabled": True,
        "use_fake": False,
    },
    # Local：本地模型服务（需要走HTTP配置）
    "local": {
        "label": "Local 本地模型",
        "url": "http://127.0.0.1:5000/infer",
        "enabled": False,
        "use_fake": True,
    },
}

# 超时时间
REQUEST_TIMEOUT = 15

# =========================
# Benchmark（平均性能/成本）配置
#  - DEFAULT_BENCHMARKS：没有 CSV 时使用的占位值
#  - BENCHMARKS：运行时从 summary.csv 读到的真实值（如果有）
# =========================
# Benchmark CSV 路径（可按需要修改）

BENCHMARK_CSV_PATH = "summary.csv"

# =========================
# 替换 web_app.py 中的 DEFAULT_BENCHMARKS
# 这里的 Cost 已经根据 Hezhe 和你的真实测试数据计算完毕
# =========================
DEFAULT_BENCHMARKS: Dict[str, Dict[str, float]] = {
    # AWS Lambda (Hot Warm): 
    # 優勢: 無需管理，無限彈性。 劣勢: 單次推理成本最高，且有冷啟動風險。
    "lambda": {
        "avg_latency_ms": 630.8, 
        "avg_ips": 1.58, 
        "cost_per_1m": 10.70,
        "cold_start_ms": 13271.8  # 特别标注：冷启动极慢
    },
    
    # EC2 x86 (c5.large): 
    # 冠軍: PyTorch 對 Intel AVX512 優化極好，導致速度極快，成本極低。
    "ec2_x86": {
        "avg_latency_ms": 110.5, 
        "avg_ips": 34.0, 
        "cost_per_1m": 0.69
    },
    
    # EC2 ARM (t4g.medium): 
    # 觀察: 儘管單價便宜，但由於缺乏針對性的指令集優化，推理效率較低，導致最終成本反而高於 x86。
    "ec2_arm": {
        "avg_latency_ms": 1513.3, 
        "avg_ips": 2.63, 
        "cost_per_1m": 3.55
    },
    
    # 本地測試
    "local": {"avg_latency_ms": 50.0, "avg_ips": 20.0, "cost_per_1m": 0.0},
}


def load_benchmarks(path: str) -> Dict[str, Dict[str, float]]:
    benchmarks: Dict[str, Dict[str, float]] = {}

    if not os.path.exists(path):
        print(f"[web_app] 未找到 summary.csv（路径: {path}），将使用默认 benchmark。")
        return benchmarks

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                backend = (row.get("backend") or "").strip()
                if backend not in DEFAULT_BENCHMARKS:
                    # 不在预期列表中的 backend 直接忽略
                    continue
                # 如果已经有该 backend 的记录，就跳过后续行（每个 backend 一行）
                if backend in benchmarks:
                    continue

                def get_float(key: str) -> float:
                    try:
                        return float(row.get(key) or "nan")
                    except ValueError:
                        return float("nan")

                benchmarks[backend] = {
                    "avg_latency_ms": get_float("avg_latency_ms"),
                    "avg_ips": get_float("avg_ips"),
                    "cost_per_1m": get_float("cost_per_1m"),
                }

                print(f"[web_app] 已从 {path} 载入 {backend} 的 benchmark: {benchmarks[backend]}")
    except Exception as e:
        print(f"[web_app] 读取 summary.csv 失败，将使用默认 benchmark。错误: {e}")
        return {}

    return benchmarks



BENCHMARKS = load_benchmarks(BENCHMARK_CSV_PATH)


def get_benchmark(backend_key: str) -> Dict[str, float]:
    """
    获取某个 backend 的 benchmark。
    优先使用 BENCHMARKS 中的真实数据，否则回退到 DEFAULT_BENCHMARKS。
    """
    bench = BENCHMARKS.get(backend_key)
    if bench is None:
        bench = DEFAULT_BENCHMARKS.get(backend_key, {})
    return bench


def call_backend(backend_key: str, image_bytes: bytes) -> Dict[str, Any]:
    """
    根据选择的 backend 调用真实接口或返回假数据。
    返回:
      - prediction: 本次推理结果（真实或假）
      - rt_latency_ms: 本次调用的实时延迟（真实或假）
      - bench_latency_ms / bench_ips / bench_cost_per_1m: 平均性能/成本（来自 CSV 或默认）
      - is_fake: 是否使用了假数据（包括 Local 失败回退的情况）
      - raw_response: 原始返回（调试用）
    """
    cfg = BACKENDS[backend_key]
    bench = get_benchmark(backend_key)

    # 预设的假数据结果，用于：
    #  - use_fake=True
    #  - 请求异常 / HTTP 错误
    fake_result = {
        "backend": cfg["label"],
        "prediction": "cat",                                # 假的类别结果
        "rt_latency_ms": bench.get("avg_latency_ms", 0.0),  # 假的实时延迟
        "bench_latency_ms": bench.get("avg_latency_ms"),
        "bench_ips": bench.get("avg_ips"),
        "bench_cost_per_1m": bench.get("cost_per_1m"),
        "raw_response": "(fake data based on our experiments)",
        "is_fake": True,
    }

    # 只要配置 use_fake 或没有 URL，一律走假数据，不做网络请求
    if cfg.get("use_fake", False) or not cfg.get("url"):
        return fake_result

    # 真实 HTTP 调用：请求格式与 performance_test.py 一致
    try:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = {"image": image_b64}

        start = time.perf_counter()
        resp = requests.post(
            cfg["url"],
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        end = time.perf_counter()
        rt_latency_ms = (end - start) * 1000.0

        if not (200 <= resp.status_code < 300):
            print(f"[web_app] 请求 {backend_key} 失败，HTTP {resp.status_code}")
            return fake_result

        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text}

        result = {
            "backend": cfg["label"],
            "prediction": data.get("prediction") or data.get("label") or "unknown",
            "rt_latency_ms": rt_latency_ms,
            "bench_latency_ms": bench.get("avg_latency_ms"),
            "bench_ips": bench.get("avg_ips"),
            "bench_cost_per_1m": bench.get("cost_per_1m"),
            "raw_response": json.dumps(data, ensure_ascii=False, indent=2),
            "is_fake": False,
        }
        return result

    except requests.exceptions.RequestException as e:
        # 网络错误 / 超时等：打印到控制台，不在网页显示，回退到假数据
        print(f"[web_app] 请求 {backend_key} 异常: {e}")
        return fake_result


@app.route("/", methods=["GET"])
def index():
    """首页：上传图片 + 选择后端的表单"""
    enabled_backends = {k: v for k, v in BACKENDS.items() if v.get("enabled", True)}
    return render_template(
        "index.html",
        backends=enabled_backends,
        result=None,
        image_data_uri=None,
        selected_backend=None,
    )


@app.route("/infer", methods=["POST"])
def infer():
    """处理表单提交，调用后端推理"""
    if "image" not in request.files:
        flash("请先选择一张图片。")
        return redirect(url_for("index"))

    file = request.files["image"]
    backend_key = request.form.get("backend")

    if not file or file.filename == "":
        flash("请选择有效的图片文件。")
        return redirect(url_for("index"))

    if backend_key not in BACKENDS or not BACKENDS[backend_key].get("enabled", True):
        flash("请选择有效的后端。")
        return redirect(url_for("index"))

    image_bytes = file.read()

    # 生成用于网页显示的图片 data URI（只用于前端展示，不参与请求）
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data_uri = f"data:image/jpeg;base64,{image_b64}"

    result = call_backend(backend_key, image_bytes)

    enabled_backends = {k: v for k, v in BACKENDS.items() if v.get("enabled", True)}
    return render_template(
        "index.html",
        backends=enabled_backends,
        result=result,
        image_data_uri=image_data_uri,
        selected_backend=backend_key,
    )


if __name__ == "__main__":
    # 开发环境下直接运行：python web_app.py
    app.run(host="0.0.0.0", port=8000, debug=False)


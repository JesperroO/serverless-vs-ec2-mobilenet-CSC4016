import matplotlib.pyplot as plt
import numpy as np
import os

# --- 核心数据 (Core Data) ---
# 来源: 我们的实验 CSV 和 AWS 定价页面
scenarios = ['Lambda (Hot)', 'EC2 x86 (c5)', 'EC2 ARM (t4g)']
latency = [630.8, 110.5, 1513.3]  # ms (越低越好)
throughput = [1.58, 34.0, 2.63]   # IPS (越高越好)
cost = [10.70, 0.69, 3.55]        # $ per 1M inferences (越低越好)
colors = ['#FF9900', '#4285F4', '#34A853'] # AWS Orange, Intel Blue, ARM Green

output_dir = "results"
os.makedirs(output_dir, exist_ok=True)

def save_plot(filename):
    path = os.path.join(output_dir, filename)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    print(f"Saved: {path}")
    plt.close()

# -------------------------------------------
# 图表 1: 延迟对比 (Latency Comparison)
# -------------------------------------------
plt.figure(figsize=(8, 6))
bars = plt.bar(scenarios, latency, color=colors, alpha=0.8, width=0.6)
plt.ylabel('Average Latency (ms) - Lower is Better', fontsize=12)
plt.title('Inference Latency Comparison', fontsize=14)
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 标注数值
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:.1f} ms',
             ha='center', va='bottom', fontsize=11, fontweight='bold')

save_plot('final_latency_comparison.png')

# -------------------------------------------
# 图表 2: 成本效益对比 (Cost Efficiency)
# -------------------------------------------
plt.figure(figsize=(8, 6))
bars = plt.bar(scenarios, cost, color=colors, alpha=0.8, width=0.6)
plt.ylabel('Cost per 1 Million Inferences ($) - Lower is Better', fontsize=12)
plt.title('Cost Efficiency Comparison', fontsize=14)
plt.grid(axis='y', linestyle='--', alpha=0.7)

for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'${height:.2f}',
             ha='center', va='bottom', fontsize=11, fontweight='bold')

save_plot('final_cost_comparison.png')

# -------------------------------------------
# 图表 3: 综合权衡图 (The Trade-off Map) - 类似于 Dr. Yang 的风格
# -------------------------------------------
plt.figure(figsize=(10, 7))

# 绘制散点
for i, scenario in enumerate(scenarios):
    plt.scatter(latency[i], cost[i], s=300, c=colors[i], label=scenario, edgecolors='black', alpha=0.9)
    # 添加标签
    plt.annotate(scenario, (latency[i], cost[i]), 
                 xytext=(10, 10), textcoords='offset points', fontsize=12, fontweight='bold')

# 添加 "理想区域" 的指示箭头
plt.arrow(1400, 10, -1000, -8, head_width=0.5, head_length=50, fc='gray', ec='gray', alpha=0.5)
plt.text(1000, 6, "Better (Faster & Cheaper)", color='gray', fontsize=10, rotation=30)

plt.xlabel('Average Latency (ms)', fontsize=12)
plt.ylabel('Cost per 1M Inferences ($)', fontsize=12)
plt.title('Performance vs. Cost Trade-off Landscape', fontsize=16)
plt.grid(True, linestyle='--', alpha=0.5)

# 强制 Lambda Cold Start 的幽灵数据出现在图上 (作为对比)
# 注意：这会让图的比例尺变得很大，所以我们要用断轴或者只是文字标注
# 还是文字标注比较好
plt.text(700, 10.70, "  Lambda (Cold): ~13s Latency", color='#FF9900', fontsize=10, style='italic')

save_plot('final_tradeoff_map.png')
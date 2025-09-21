# CSC4160 Assignment-1: EC2 Measurement (2 questions)

### Deadline: 23:59, Sep 22, Sunday

---

### Name: RUKAI XIAO

### Student Id: 124090729

---

## Question 1: Measure the EC2 CPU and Memory performance

1. (1 mark) Report the name of measurement tool used in your measurements (you are free to choose any open source measurement software as long as it can measure CPU and memory performance). Please describe your configuration of the measurement tool, and explain why you set such a value for each parameter. Explain what the values obtained from measurement results represent (e.g., the value of your measurement result can be the execution time for a scientific computing task, a score given by the measurement tools or something else).

    > Sysbench. I used Ubuntu 24.04 LTS to test the performance, the commands are as follows:
    > sysbench cpu --cpu-max-prime=20000 run
    > sysbench memory --memory-block-size=1K --memory-total-size=10G run

    > For CPU test, --cpu-max-prime=20000 makes the CPU compute all prime numbers up to twenty thousand. This is a pure, computationally intensive task. The value "events per second" directly quantifies the computing ability, which is the number of prime numbers calculated per second.

    > For Memory test, --memory-total-size=10G will read and write 10 GB of data in memory to test the bandwidth of the memory.The value "MiB/sec" is exactly the memory bandwidth, which quantifies the memory performance.

2. (1 mark) Run your measurement tool on general purpose `t3.medium`, `m5.large`, and `c5d.large` Linux instances, respectively, and find the performance differences among them. Launch all instances in the **US East (N. Virginia)** region. What about the differences among these instances in terms of CPU and memory performance? Please try explaining the differences.

    In order to answer this question, you need to complete the following table by filling out blanks with the measurement results corresponding to each instance type.

    | Size      | CPU performance | Memory performance |
    |-----------|-----------------|--------------------|
    | `t3.medium` |375.38 events/sec|5237.69 MiB/sec|
    | `m5.large`  |410.89 events/sec|5268.12 MiB/sec|
    | `c5d.large` |477.25 events/sec|6134.44 MiB/sec|

    > The CPU performance of c5d.large is the best, followed by m5.large, and t3.medium is the worst. The memory performance of c5d.large is also the best, followed by m5.large, and t3.medium is the worst. T3.Medium, m5.Large, c5d.Large...They're not random tags. These are three different resource allocation models designed by AWS. It's all based on virtualization: the Hypervisor splits up virtual machines into performance ratios based on the type of physical hardware you choose.
    > c5d.large: The c5 series is a compute-optimized instance type, designed for high-performance computing tasks. It uses the latest Intel Xeon Scalable processors, which provide higher clock speeds and more cores compared to the other two types. This results in better CPU performance.
    > m5.large: The m5 series is a general-purpose instance type, which balances compute, memory, and networking resources. It uses Intel Xeon Platinum processors, which are powerful but not as optimized for compute-intensive tasks as the c5 series. This results in moderate CPU performance.
    > t3.medium: The t3 series is a burstable performance instance type, which is not linearly related to CPU performance. It is designed for workloads that do not require consistent high CPU performance, such as web servers and small databases. The CPU performance can vary based on the workload, but its basic physical hardware and persistent performance design are still inferior to those of the M5 and C5D series. As a result, it has the lowest ranking (375.38 events/sec, 5237.69 MiB/sec) 


## Question 2: Measure the EC2 Network performance

1. (1 mark) The metrics of network performance include **TCP bandwidth** and **round-trip time (RTT)**. Within the same region, what network performance is experienced between instances of the same type and different types? In order to answer this question, you need to complete the following table.  

    | Type          | TCP b/w (Mbps) | RTT (ms) |
    |---------------|----------------|----------|
    | `t3.medium`-`t3.medium` |4.54 Gbits/sec|0.307 ms|
    | `m5.large`-`m5.large`  |4.95 Gbits/sec|0.371 ms|
    | `c5n.large`-`c5n.large` |4.96 Gbits/sec|0.372 ms|
    | `t3.medium`-`c5n.large`   |4.48 Gbits/sec|0.425 ms|
    | `m5.large`-`c5n.large`  |4.75 Gbits/sec|0.384 ms|
    | `m5.large`-`t3.medium` |4.46 Gbits/sec|0.432 ms|

    > The network performance is excellent between instances of the same type, with high bandwidth and low latency. The performance is slightly lower between instances of different types, but still very good. This is because instances of the same type are likely to be on the same physical hardware or in close proximity within the data center, resulting in lower latency and higher bandwidth. Instances of different types may be on different hardware or in different locations within the data center, leading to slightly higher latency and lower bandwidth.

2. (1 mark) What about the network performance for instances deployed in different regions? In order to answer this question, you need to complete the following table.

    | Connection | TCP b/w (Mbps)  | RTT (ms) |
    |------------|-----------------|--------------------|
    | N. Virginia-Oregon |0.481 Gbits/sec|61.188ms|
    | N. Virginia-N. Virginia  |4.96 Gbits/sec|0.176ms|
    | Oregon-Oregon |9.53 Gbits/sec|0.025ms|

    > Regarding RTT (61.188ms vs. ~0.2ms):
    > This huge difference originates from the fundamental limitations of physics: the speed of light.
    > Data packets traveling through fiber optic cables from N. Virginia to Oregon and back need to traverse thousands of kilometers of physical distance, which costs tens of milliseconds.
    > While intra-regional communication may only involve distances of tens of meters, resulting in sub-millisecond latency.

    > Regarding bandwidth (481 Mbits/sec vs. ~5-9 Gbits/sec):
    > Inter-regional links are shared, expensive, long-haul backbone networks that need to handle traffic from thousands of users. Therefore, the bandwidth you can be allocated is limited.
    > Intra-regional links are dedicated, ultra-high bandwidth networks within data centers. Hence, the bandwidth is more than an order of magnitude higher.

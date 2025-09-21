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

    > The CPU performance of c5d.large is the best, followed by m5.large, and t3.medium is the worst. The memory performance of c5d.large is also the best, followed by m5.large, and t3.medium is the worst. 

## Question 2: Measure the EC2 Network performance

1. (1 mark) The metrics of network performance include **TCP bandwidth** and **round-trip time (RTT)**. Within the same region, what network performance is experienced between instances of the same type and different types? In order to answer this question, you need to complete the following table.  

    | Type          | TCP b/w (Mbps) | RTT (ms) |
    |---------------|----------------|----------|
    | `t3.medium`-`t3.medium` |                |          |
    | `m5.large`-`m5.large`  |                |          |
    | `c5n.large`-`c5n.large` |                |          |
    | `t3.medium`-`c5n.large`   |                |          |
    | `m5.large`-`c5n.large`  |                |          |
    | `m5.large`-`t3.medium` |                |          |

    > Region: US East (N. Virginia)

2. (1 mark) What about the network performance for instances deployed in different regions? In order to answer this question, you need to complete the following table.

    | Connection | TCP b/w (Mbps)  | RTT (ms) |
    |------------|-----------------|--------------------|
    | N. Virginia-Oregon |                 |                    |
    | N. Virginia-N. Virginia  |                 |                    |
    | Oregon-Oregon |                 |                    |

    > All instances are `c5.large`.

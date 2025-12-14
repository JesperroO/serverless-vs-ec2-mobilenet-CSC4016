import sys
from pyspark.sql import SparkSession

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: pagerank <input_path>", file=sys.stderr)
        sys.exit(-1)

    input_path = sys.argv[1]
    iterations = 10

    spark = SparkSession.builder.appName("PythonPageRank").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # Read the data as an RDD of strings
    lines_rdd = spark.read.text(input_path).rdd.map(lambda r: r.value)

    # Filter out comments and parse into (from, [to_list]) pairs
    links = lines_rdd.filter(lambda line: not line.startswith("#")) \
                     .map(lambda line: tuple(line.split())) \
                     .distinct() \
                     .groupByKey() \
                     .cache()

    # Initialize ranks for all nodes
    ranks = links.map(lambda url_neighbors: (url_neighbors[0], 1.0))

    # Iteratively update ranks
    for i in range(iterations):
        # (url, rank / num_neighbors)
        contribs = links.join(ranks).flatMap(
            lambda url_neighbors_rank: [
                (dest, url_neighbors_rank[1][1] / len(url_neighbors_rank[1][0]))
                for dest in url_neighbors_rank[1][0]
            ]
        )
        ranks = contribs.reduceByKey(lambda x, y: x + y).mapValues(lambda rank: 0.15 + 0.85 * rank)

    # Get ranks for target nodes
    target_nodes = ['448126', '49717', '375375', '63087']
    filtered_ranks = ranks.filter(lambda x: x[0] in target_nodes).collect()

    print("--- FINAL RANKS FOR REPORT ---")
    # Sort for consistent output
    for (node, rank) in sorted(filtered_ranks):
        print(f"Node: {node}, Rank: {rank:.2f}")
    print("----------------------------")

    spark.stop()
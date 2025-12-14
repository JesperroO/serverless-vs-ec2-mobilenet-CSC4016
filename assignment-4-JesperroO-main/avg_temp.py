import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, split

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: avg_temp.py <input_path> <output_path>", file=sys.stderr)
        sys.exit(-1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    spark = SparkSession.builder.appName("TemperatureAverage").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # Read raw data (each line is a string)
    lines_df = spark.read.text(input_path)

    # Split the string. City names might contain commas, so we need a robust way.
    # The provided data format is "City Name,Temperature". Assuming city name does not contain comma.
    # A more robust solution for "City, Name, Temp" would be more complex, but this fits the assignment data.
    split_col = split(lines_df['value'], ',', 2)

    data_df = lines_df.withColumn('city_name', split_col.getItem(0)) \
                      .withColumn('temperature', split_col.getItem(1).cast("float")) \
                      .select("city_name", "temperature")

    # Group by city name and calculate the average temperature
    avg_temp_df = data_df.groupBy("city_name").avg("temperature")

    # Rename column to match output requirements
    result_df = avg_temp_df.withColumnRenamed("avg(temperature)", "average_temperature")

    # Save the result to HDFS as CSV
    result_df.coalesce(1).write.mode("overwrite").csv(output_path, header=True)

    spark.stop()
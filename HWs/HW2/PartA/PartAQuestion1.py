from pyspark.sql import SparkSession
from pyspark.sql.functions import explode
from pyspark.sql.functions import split

spark = SparkSession \
	.builder \
	.appName("StructuredNetworkWordCount") \
	.getOrCreate()


# Create DataFrame representing the stream of input lines 
# from connection to localhost:9999
# lines = spark \
# 	.readStream \
# 	.format("socket") \
# 	.option("host", "localhost") \
# 	.option("port", 9999) \
# 	.load()

# Read all the csv files written atomically in a directory
# userA, userB, timestamp, interaction
userSchema = StructType()\
	.add("userA", "integer")\
	.add("userB", "integer")\
	.add("timestamp", "string")\
	.add("interaction","string")

activity = spark \
	.readStream \
	.option("sep", ",") \
	#.schema(userSchema) \
	.csv("higgs/stage")  # Equivalent to format("csv").load("/path/to/directory")


# Split the lines into words
# words = lines.select(
# 	explode(
# 		split(lines.value, " ")
# 	).alias("word")
# )

# Generate running word count
wordCounts = activity.groupBy("interaction").count()



# Start running the query that prints the running counts to the console
query = wordCounts \
	.writeStream \
	.outputMode("complete") \
	.format("console") \
	.start()

query.awaitTermination()
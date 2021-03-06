import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import explode
from pyspark.sql.functions import split
from pyspark.sql.functions import window
from pyspark.sql.types import StructType, TimestampType

staging_dir = sys.argv[1]

spark = SparkSession \
	.builder \
	.appName("PartAQuestion3") \
	.getOrCreate()



# Read all the csv files written atomically in a directory
# userA, userB, timestamp, interaction
userSchema = StructType()\
	.add("userB", "integer")\
	
activity = spark \
	.readStream \
	.schema(userSchema) \
	.parquet(staging_dir+"/")


# Generate running word count
wordCounts = activity.groupBy("userB").count()
	
			
query = wordCounts \
	.writeStream.trigger(processingTime='10 minutes') \
	.outputMode("complete") \
	.format("console") \
	.start()

query.awaitTermination()
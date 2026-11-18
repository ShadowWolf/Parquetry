# The reader container for Spark 3.5. Build it with the Containers
# folder as the build context.
FROM apache/spark:3.5.9-java17-python3

COPY reader_server.py spark_reader.py /opt/reader/

EXPOSE 8080
# local[1] runs Spark inside the container with one worker thread. With one
# thread Spark reads a test file in a single task, which is what keeps the
# rows in file order. docs/research/spark-row-order has the measurement.
CMD ["/opt/spark/bin/spark-submit", "--master", "local[1]", "--conf", "spark.ui.enabled=false", "/opt/reader/spark_reader.py"]

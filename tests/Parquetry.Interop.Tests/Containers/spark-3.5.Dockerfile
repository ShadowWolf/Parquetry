# The reader container for Spark 3.5.
FROM apache/spark:3.5.9-java17-python3

COPY reader_server.py spark_reader.py /opt/reader/

EXPOSE 8080
CMD ["/opt/spark/bin/spark-submit", "--master", "local[2]", "--conf", "spark.ui.enabled=false", "/opt/reader/spark_reader.py"]

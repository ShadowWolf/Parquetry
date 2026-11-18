# The reader container for the current Spark 4.x release.
FROM apache/spark:4.3.0-java21-python3

COPY reader_server.py spark_reader.py /opt/reader/

EXPOSE 8080
CMD ["/opt/spark/bin/spark-submit", "--master", "local[2]", "--conf", "spark.ui.enabled=false", "/opt/reader/spark_reader.py"]

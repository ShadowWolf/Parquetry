# The reader container for pyarrow, Polars, and DuckDB. It is called the
# Python container. Build it with the Containers folder as the build context.
FROM python:3.14.10-slim

COPY python/requirements.txt /opt/reader/
RUN pip install --no-cache-dir -r /opt/reader/requirements.txt
COPY reader_server.py python_readers.py /opt/reader/

EXPOSE 8080
CMD ["python", "/opt/reader/python_readers.py"]

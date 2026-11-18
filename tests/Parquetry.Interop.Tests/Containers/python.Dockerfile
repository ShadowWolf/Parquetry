# The reader container for pyarrow, Polars, and DuckDB.
FROM python:3.14-slim

COPY requirements.txt /opt/reader/
RUN pip install --no-cache-dir -r /opt/reader/requirements.txt
COPY reader_server.py python_readers.py /opt/reader/

EXPOSE 8080
CMD ["python", "/opt/reader/python_readers.py"]

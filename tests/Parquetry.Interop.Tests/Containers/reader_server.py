"""The HTTP server that every reader container runs.

A test sends a Parquet file to a reader and gets back what the reader saw in
it: the columns, with their types, and the rows. The comparison with what was
written is done by the test, in C#.

Requests:

  GET  /health         200 when the readers are ready. Lists them and the
                       versions of the libraries in the container.
  GET  /files/<name>   The bytes of a file the container can write, such as
                       the known-good file that pyarrow writes.
  POST /read/<reader>  The request body is a Parquet file. The response is
                       the result of reading it with the named reader.

Responses to /read:

  200  {"columns": [{"name", "nativeType", "kind"}], "rows": [[...]]}
  422  {"error": "..."}  The reader could not read the file.
  500  {"error": "..."}  The server itself failed. This is a fault in the
                         test setup, and never a statement about the file.

A reader's own name for a type goes in "nativeType". "kind" is a name from
the list below that is the same for every reader, or "unknown". Each value in
a row is null or a string, so that 64-bit integers, NaN, and negative zero
survive JSON:

  bool     "true" or "false"
  int32    decimal digits
  int64    decimal digits
  float64  what Python's repr() gives: "1.5", "-0.0", "nan", "inf", "-inf"
  string   the text

This file runs on the Python that ships in the Spark images as well as on a
current one, so it uses only the standard library and no recent syntax.
"""
import json
import os
import tempfile
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8080


def encode_value(value):
    """Turns one value read from a file into null or a string."""
    if value is None:
        return None
    # bool is tested before int because a Python bool is also an int.
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return value
    raise TypeError("no encoding for a value of type " + type(value).__name__)


def serve(readers, versions, files=None):
    """Runs the server until the container stops.

    readers   maps a reader's name to a function that takes a file path and
              returns (columns, rows). columns is a list of
              (name, native type, kind). rows is a list of rows, each a
              sequence of Python values.
    versions  maps a library's name to its version, for /health.
    files     maps a file's name to a function that returns its bytes.
    """
    files = files or {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_json(200, {"readers": sorted(readers), "versions": versions})
            elif self.path.startswith("/files/") and self.path[len("/files/"):] in files:
                try:
                    body = files[self.path[len("/files/"):]]()
                except Exception:
                    self.send_json(500, {"error": traceback.format_exc()})
                    return
                self.send_body(200, "application/octet-stream", body)
            else:
                self.send_json(404, {"error": "nothing at " + self.path})

        def do_POST(self):
            name = self.path[len("/read/"):] if self.path.startswith("/read/") else None
            if name not in readers:
                self.send_json(404, {"error": "nothing at " + self.path})
                return
            data = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            handle, path = tempfile.mkstemp(suffix=".parquet")
            try:
                with os.fdopen(handle, "wb") as file:
                    file.write(data)
                try:
                    columns, rows = readers[name](path)
                except Exception as error:
                    # Only a failure inside the reader counts as "could not
                    # read the file".
                    self.send_json(422, {"error": type(error).__name__ + ": " + str(error)})
                    return
                try:
                    result = {
                        "columns": [
                            {"name": column, "nativeType": native, "kind": kind}
                            for column, native, kind in columns
                        ],
                        "rows": [[encode_value(value) for value in row] for row in rows],
                    }
                except Exception:
                    self.send_json(500, {"error": traceback.format_exc()})
                    return
                self.send_json(200, result)
            finally:
                os.remove(path)

        def send_json(self, status, value):
            self.send_body(status, "application/json", json.dumps(value).encode("utf-8"))

        def send_body(self, status, content_type, body):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            # The default writes a line per request to the container's log.
            pass

    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

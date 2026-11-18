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

  200  {"columns": [...], "rows": [[...]]}
  422  {"error": "..."}  The reader could not read the file. Only an error
                         of a type the reader's own library raises counts.
  500  {"error": "..."}  Anything else failed. The tests treat this as a
                         fault in the test setup.

The split goes by the type of the error, so it is not exact. A library can
raise one of its own error types for a cause that is not the file, such as a
Python module missing from the image, and that is answered with 422.

Each column is {"name", "nativeType", "kind", "nullable"}:

  nativeType  The reader's own name for the type, such as BIGINT.
  kind        A name from the list below that is the same for every reader,
              or "unknown" for a type that is not in the list yet.
  nullable    true or false if the reader says whether the column can hold
              nulls, and null if it does not say. Of the readers here, only
              pyarrow says.

Each value in a row is null or a string, so that 64-bit integers, NaN, and
negative zero survive JSON:

  bool     "true" or "false"
  int32    decimal digits
  int64    decimal digits
  float64  what Python's repr() gives: "1.5", "-0.0", "nan", "inf", "-inf"
  string   the text
  unknown  what Python's str() gives for the value

Adding a type means changing each place listed under "Adding a type" in
docs/architecture/testing.md.

The Spark images ship Python 3.10. This file runs there as well as on a
current Python, so it uses only the standard library and nothing newer than
Python 3.10.
"""
import json
import os
import tempfile
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8080


def _encode_bool(value):
    if not isinstance(value, bool):
        raise TypeError("expected a bool and got " + type(value).__name__)
    return "true" if value else "false"


def _encode_int(value):
    # A Python bool is also an int, and must not pass as one here.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("expected an int and got " + type(value).__name__)
    return str(value)


def _encode_float(value):
    if not isinstance(value, float):
        raise TypeError("expected a float and got " + type(value).__name__)
    return repr(value)


def _encode_string(value):
    if not isinstance(value, str):
        raise TypeError("expected a str and got " + type(value).__name__)
    return value


# How the values of a column are turned into strings, by the column's kind.
# A value of the wrong Python type for its kind is a fault in a reader's
# table of kinds, so it raises and the server answers 500.
ENCODERS = {
    "bool": _encode_bool,
    "int32": _encode_int,
    "int64": _encode_int,
    "float64": _encode_float,
    "string": _encode_string,
    "unknown": str,
}


def encode_rows(columns, rows):
    """Turns the rows a reader returned into lists of null or string."""
    encoders = [ENCODERS[kind] for _, _, kind, _ in columns]
    return [
        [None if value is None else encode(value) for encode, value in zip(encoders, row)]
        for row in rows
    ]


def serve(readers, versions, files=None):
    """Runs the server until the container stops.

    readers   maps a reader's name to (function, error types). The function
              takes a file path and returns (columns, rows). columns is a
              list of (name, native type, kind, nullable). rows is a list of
              rows, each a sequence of Python values. The error types are
              the exception classes the reader's library raises when it
              cannot read a file. Any other exception from the function is a
              fault in the server.
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
            # Without a length the body cannot be read, and reading nothing
            # would look like an empty file that every reader rejects.
            if self.headers.get("Content-Length") is None:
                self.send_json(411, {"error": "the request needs a Content-Length header"})
                return
            data = self.rfile.read(int(self.headers["Content-Length"]))
            read, reader_errors = readers[name]
            handle, path = tempfile.mkstemp(suffix=".parquet")
            try:
                with os.fdopen(handle, "wb") as file:
                    file.write(data)
                try:
                    columns, rows = read(path)
                    result = {
                        "columns": [
                            {"name": column, "nativeType": native, "kind": kind, "nullable": nullable}
                            for column, native, kind, nullable in columns
                        ],
                        "rows": encode_rows(columns, rows),
                    }
                except reader_errors as error:
                    self.send_json(422, {"error": type(error).__name__ + ": " + str(error)})
                    return
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

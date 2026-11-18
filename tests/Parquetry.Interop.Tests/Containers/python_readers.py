"""The Python container: the readers pyarrow, Polars, and DuckDB.

Each of the three has its own Parquet reader. Polars is called without its
option to read through pyarrow.
"""
import io

import duckdb
import polars
import polars.exceptions
import pyarrow
import pyarrow.parquet

from reader_server import serve

PYARROW_KINDS = {
    "bool": "bool",
    "int32": "int32",
    "int64": "int64",
    "double": "float64",
    "string": "string",
}

POLARS_KINDS = {
    "Boolean": "bool",
    "Int32": "int32",
    "Int64": "int64",
    "Float64": "float64",
    "String": "string",
}

DUCKDB_KINDS = {
    "BOOLEAN": "bool",
    "INTEGER": "int32",
    "BIGINT": "int64",
    "DOUBLE": "float64",
    "VARCHAR": "string",
}

# The exceptions each library raises when it cannot read a file. pyarrow
# raises OSError for some of them, such as a file that ends too early. A
# Polars panic is a failure inside Polars, so it also counts as Polars not
# being able to read the file.
PYARROW_ERRORS = (pyarrow.ArrowException, OSError)
POLARS_ERRORS = (polars.exceptions.PolarsError, polars.exceptions.PanicException)
DUCKDB_ERRORS = (duckdb.Error,)


def read_pyarrow(path):
    table = pyarrow.parquet.read_table(path)
    columns = [
        (field.name, str(field.type), PYARROW_KINDS.get(str(field.type), "unknown"), field.nullable)
        for field in table.schema
    ]
    values = [column.to_pylist() for column in table.columns]
    return columns, list(zip(*values))


def read_polars(path):
    frame = polars.read_parquet(path, use_pyarrow=False)
    columns = [
        (name, str(dtype), POLARS_KINDS.get(str(dtype), "unknown"), None)
        for name, dtype in frame.schema.items()
    ]
    return columns, frame.rows()


def read_duckdb(path):
    connection = duckdb.connect()
    try:
        cursor = connection.execute("SELECT * FROM read_parquet(?)", [path])
        columns = [
            (column[0], str(column[1]), DUCKDB_KINDS.get(str(column[1]), "unknown"), None)
            for column in cursor.description
        ]
        return columns, cursor.fetchall()
    finally:
        connection.close()


def read_setup_fault(path):
    """Stands in for a fault in this server's own code.

    It is not a reader. A test sends a file here to confirm that such a fault
    is answered with 500 and is not taken for a reader rejecting the file.
    """
    raise RuntimeError("a fault raised on purpose by the setup-fault reader")


def known_good_file():
    """A small file written by pyarrow with its default settings.

    The tests use it to show that every reader container works. The same
    values are written out in KnownGoodFile.cs. If the two differ, the test
    Reader_returns_what_pyarrow_wrote fails.
    """
    schema = pyarrow.schema(
        [
            pyarrow.field("id", pyarrow.int64(), nullable=False),
            pyarrow.field("flag", pyarrow.bool_()),
            pyarrow.field("count", pyarrow.int32()),
            pyarrow.field("ratio", pyarrow.float64()),
            pyarrow.field("name", pyarrow.string()),
        ]
    )
    table = pyarrow.table(
        {
            "id": [1, 2, 3, 9007199254740993, -9223372036854775808, 9223372036854775807],
            "flag": [True, False, None, True, False, None],
            "count": [10, None, -2147483648, 2147483647, 0, -1],
            "ratio": [1.5, float("nan"), None, -0.0, float("inf"), float("-inf")],
            "name": ["alpha", "", "Zoë 東京 \U0001f40e", None, "two\nlines", "beta"],
        },
        schema=schema,
    )
    sink = io.BytesIO()
    pyarrow.parquet.write_table(table, sink)
    return sink.getvalue()


if __name__ == "__main__":
    serve(
        readers={
            "pyarrow": (read_pyarrow, PYARROW_ERRORS),
            "polars": (read_polars, POLARS_ERRORS),
            "duckdb": (read_duckdb, DUCKDB_ERRORS),
            "setup-fault": (read_setup_fault, ()),
        },
        versions={
            "pyarrow": pyarrow.__version__,
            "polars": polars.__version__,
            "duckdb": duckdb.__version__,
        },
        files={"known-good.parquet": known_good_file},
    )

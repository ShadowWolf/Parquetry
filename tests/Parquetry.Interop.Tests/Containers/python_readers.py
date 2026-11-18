"""The reader container for pyarrow, Polars, and DuckDB.

Each of the three has its own Parquet reader. Polars is called without its
option to read through pyarrow.
"""
import io

import duckdb
import polars
import pyarrow
import pyarrow.parquet

from reader_server import serve

PYARROW_KINDS = {
    "bool": "bool",
    "int32": "int32",
    "int64": "int64",
    "double": "float64",
    "string": "string",
    "large_string": "string",
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


def read_pyarrow(path):
    table = pyarrow.parquet.read_table(path)
    columns = [
        (field.name, str(field.type), PYARROW_KINDS.get(str(field.type), "unknown"))
        for field in table.schema
    ]
    values = [column.to_pylist() for column in table.columns]
    return columns, list(zip(*values))


def read_polars(path):
    frame = polars.read_parquet(path, use_pyarrow=False)
    columns = [
        (name, str(dtype), POLARS_KINDS.get(str(dtype), "unknown"))
        for name, dtype in frame.schema.items()
    ]
    return columns, frame.rows()


def read_duckdb(path):
    connection = duckdb.connect()
    try:
        cursor = connection.execute("SELECT * FROM read_parquet(?)", [path])
        columns = [
            (column[0], str(column[1]), DUCKDB_KINDS.get(str(column[1]), "unknown"))
            for column in cursor.description
        ]
        return columns, cursor.fetchall()
    finally:
        connection.close()


def known_good_file():
    """A small file written by pyarrow with its default settings.

    The tests use it to show that every reader container works. The same
    values are written out in KnownGoodFile.cs, and the two must match.
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
            "id": [1, 2, 3, 4],
            "flag": [True, False, None, True],
            "count": [10, None, -2147483648, 2147483647],
            "ratio": [1.5, float("nan"), None, -0.0],
            "name": ["alpha", "", "Zoë 東京 \U0001f40e", None],
        },
        schema=schema,
    )
    sink = io.BytesIO()
    pyarrow.parquet.write_table(table, sink)
    return sink.getvalue()


if __name__ == "__main__":
    serve(
        readers={"pyarrow": read_pyarrow, "polars": read_polars, "duckdb": read_duckdb},
        versions={
            "pyarrow": pyarrow.__version__,
            "polars": polars.__version__,
            "duckdb": duckdb.__version__,
        },
        files={"known-good.parquet": known_good_file},
    )

namespace Parquetry.Interop.Tests.Readers;

/// <summary>
/// What a reader returned for a file: a table, or the error it gave when it
/// could not read the file. Exactly one of the two is set.
/// </summary>
/// <param name="Table">The columns and rows the reader saw.</param>
/// <param name="Error">The reader's error message.</param>
public sealed record ReadResult(ReaderTable? Table, string? Error);

/// <summary>
/// The contents of a file as one reader saw them.
/// </summary>
/// <param name="Columns">The columns, in the reader's order.</param>
/// <param name="Rows">
/// The rows, in the reader's order. Each value is null or has the .NET type
/// that goes with its column's <see cref="ColumnKind"/>: <see cref="bool"/>,
/// <see cref="int"/>, <see cref="long"/>, <see cref="double"/>, or
/// <see cref="string"/>. A value in a column of unknown kind is the string
/// the reader container sent.
/// </param>
public sealed record ReaderTable(IReadOnlyList<ReaderColumn> Columns, IReadOnlyList<IReadOnlyList<object?>> Rows);

/// <summary>
/// One column as a reader reported it.
/// </summary>
/// <param name="Name">The column's name.</param>
/// <param name="Kind">The column's type under a name common to all readers.</param>
/// <param name="NativeType">The reader's own name for the type, such as BIGINT.</param>
public sealed record ReaderColumn(string Name, ColumnKind Kind, string NativeType);

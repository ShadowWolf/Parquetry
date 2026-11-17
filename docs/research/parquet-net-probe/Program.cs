using System.Collections;
using System.Numerics;
using System.Reflection;
using Parquet;
using Parquet.Serialization;

var outDir = Path.Combine(AppContext.BaseDirectory, "out");
Directory.CreateDirectory(outDir);
var dt = new DateTime(2024, 5, 6, 7, 8, 9, DateTimeKind.Utc).AddTicks(1234567); // .1234567 s

await Try("enum", new EnumRow { V = Color.Green });
await Try("timespan", new TimeSpanRow { V = TimeSpan.FromTicks(36_000_000_000 + 1234567) });
await Try("timeonly", new TimeOnlyRow { V = new TimeOnly(1, 2, 3) });
await Try("char", new CharRow { V = 'x' });
await Try("biginteger", new BigIntRow { V = BigInteger.Parse("123456789012345678901234567890") });
await Try("int128", new Int128Row { V = Int128.MaxValue });
await Try("guid", new GuidRow { V = Guid.Parse("00112233-4455-6677-8899-aabbccddeeff") });
await Try("byte", new ByteRow { V = 200 });
await Try("uint", new UIntRow { V = 4000000000 });
await Try("ulong", new ULongRow { V = ulong.MaxValue });
await Try("half", new HalfRow { V = (Half)1.5 });
await Try("decimal", new DecimalRow { V = 1.23456789012345678901234567m });
await Try("datetime_utc", new DateTimeRow { V = dt });
await Try("datetime_unspecified", new DateTimeRow { V = DateTime.SpecifyKind(dt, DateTimeKind.Unspecified) });
await Try("datetimeoffset", new DateTimeOffsetRow { V = new DateTimeOffset(2024, 5, 6, 7, 8, 9, TimeSpan.FromHours(2)).AddTicks(1234567) });
await Try("string_nonnull", new StringRow { V = "a" });

async Task Try<T>(string name, T row) where T : class, new()
{
    try
    {
        var path = Path.Combine(outDir, name + ".parquet");
        await using (var fs = File.Create(path))
            await ParquetSerializer.SerializeAsync(new[] { row }, fs);
        await using var rs = File.OpenRead(path);
        await using var reader = await ParquetReader.CreateAsync(rs);
        object? meta = reader.GetType().GetProperty("Metadata", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)?.GetValue(reader);
        var schema = meta?.GetType().GetProperty("Schema")?.GetValue(meta) as IEnumerable;
        if (schema != null)
            foreach (var se in schema) Console.WriteLine($"{name}: {Dump(se!)}");
        else
            Console.WriteLine($"{name}: OK (no thrift metadata visible) schema={reader.Schema}");
        rs.Position = 0;
        var back = await ParquetSerializer.DeserializeAsync<T>(rs);
        object first = back;
        if (back is not IEnumerable<T>)
            foreach (var bp in back.GetType().GetProperties())
                if (bp.GetValue(back) is IEnumerable<T> seq) { first = seq; break; }
        var v = typeof(T).GetProperty("V")!.GetValue(((IEnumerable<T>)first).First());
        Console.WriteLine($"{name}: readback={v}" + (v is DateTime d ? $" ticks%10000000={d.Ticks % 10000000} kind={d.Kind}" : v is TimeSpan ts ? $" ticks={ts.Ticks}" : v is DateTimeOffset o ? $" ticks%10000000={o.Ticks % 10000000} offset={o.Offset}" : ""));
    }
    catch (Exception ex)
    {
        var e = ex is TargetInvocationException t && t.InnerException != null ? t.InnerException : ex;
        Console.WriteLine($"{name}: FAIL {e.GetType().Name}: {e.Message.Split('\n')[0]}");
    }
}

static string Dump(object o, int depth = 0)
{
    var parts = new List<string>();
    foreach (var p in o.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
    {
        object? val;
        try { val = p.GetValue(o); } catch { continue; }
        if (val == null) continue;
        if (val is string || val.GetType().IsPrimitive || val.GetType().IsEnum) parts.Add($"{p.Name}={val}");
        else if (depth < 3 && val is not IEnumerable) parts.Add($"{p.Name}={{{Dump(val, depth + 1)}}}");
    }
    foreach (var f in o.GetType().GetFields(BindingFlags.Public | BindingFlags.Instance))
    {
        var val = f.GetValue(o);
        if (val == null) continue;
        if (val is string || val.GetType().IsPrimitive || val.GetType().IsEnum) parts.Add($"{f.Name}={val}");
        else if (depth < 3 && val is not IEnumerable) parts.Add($"{f.Name}={{{Dump(val, depth + 1)}}}");
    }
    return string.Join(", ", parts);
}

public enum Color { Red, Green }
public class EnumRow { public Color V { get; set; } }
public class TimeSpanRow { public TimeSpan V { get; set; } }
public class TimeOnlyRow { public TimeOnly V { get; set; } }
public class CharRow { public char V { get; set; } }
public class BigIntRow { public BigInteger V { get; set; } }
public class Int128Row { public Int128 V { get; set; } }
public class GuidRow { public Guid V { get; set; } }
public class ByteRow { public byte V { get; set; } }
public class UIntRow { public uint V { get; set; } }
public class ULongRow { public ulong V { get; set; } }
public class HalfRow { public Half V { get; set; } }
public class DecimalRow { public decimal V { get; set; } }
public class DateTimeRow { public DateTime V { get; set; } }
public class DateTimeOffsetRow { public DateTimeOffset V { get; set; } }
public class StringRow { public string V { get; set; } = ""; }

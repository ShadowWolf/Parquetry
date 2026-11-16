# Types are registered by an attribute on the type or by a context class

Status: accepted
Date: 2026-11-14

## Context

The source generator needs to know which types to generate code for. Users own
some of their types and can add attributes to them. Other types come from
libraries they cannot change.

## Options considered

1. An attribute on the type. This is the least work for the user, but it
   cannot be applied to types from other assemblies.
2. A context class that lists types, as `System.Text.Json` does. This works for
   any type but adds a class to write and pass around.
3. Both.

## Decision

Both are supported and produce the same generated writer.

```csharp
// A type the user owns
[ParquetSerializable]
public partial class Order
{
    public long Id { get; set; }

    [ParquetColumn("placed_at")]
    public DateTimeOffset PlacedAt { get; set; }

    public List<OrderLine> Lines { get; set; }
}

// Types the user does not own
[ParquetSerializable(typeof(ThirdPartyDto))]
public partial class MyParquetContext : ParquetSerializerContext { }
```

## Consequences

- A type marked directly must be `partial`, so the generator can add to it.
- Column settings on a type the user does not own cannot be given as property
  attributes. They are given on the context class or in writer options.
- The generator has two ways of finding types but one way of producing code
  for them.

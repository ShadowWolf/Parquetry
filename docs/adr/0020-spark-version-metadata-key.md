# The default profile writes the Spark version key so Spark 3.x reads old dates

Status: accepted
Date: 2026-11-14

## Context

Spark 3.x handles old dates with caution because Spark 2 used a different
calendar for them. When a Parquet file contains a date before 1582-10-15 or a
timestamp before 1900-01-01, Spark 3.x looks in the file's metadata for the key
`org.apache.spark.version`. If the key is missing, Spark does not know which
calendar the writer used, and the read fails with an error asking the user to
change a Spark setting. If the key holds a version of 3.0.0 or later, Spark
reads the values as written. Spark 4.0 reads them as written without the key.

This was found in Spark's source code (`DataSourceUtils.scala`) during research
on 2026-11-14.

.NET data often contains such values. `default(DateTime)` is 0001-01-01, and it
appears wherever a date was never set. .NET uses the same calendar that Spark 3
expects, so reading the values as written is correct.

Databricks runtimes 14.3 through 16.4 are based on Spark 3.5.

## Options considered

1. Write the key by default, with an option to turn it off.
2. Leave it off by default. Files with old dates then fail in Spark 3.x with
   an error that names the Spark setting to change.
3. Do not write the key, and raise an error when a value is old enough to
   cause the problem.

## Decision

Option 1. Under the default profile, the writer adds
`org.apache.spark.version` to the file's key-value metadata. An option turns
it off.

## Consequences

- Every file from the default profile carries one key that names Spark, even
  though Spark did not write it. The `created_by` field in the footer still
  names Parquetry.
- The exact version string to write will be fixed when the feature is built,
  after testing with Spark 3.5.
- Whether Databricks behaves the same as open-source Spark here is not
  documented. The live Databricks test must cover a file with old dates.
- If Spark uses this key for other decisions when reading, those would apply
  to Parquetry files too. None were found, but the search was limited to date
  and timestamp handling. The Spark container tests are the check on this.

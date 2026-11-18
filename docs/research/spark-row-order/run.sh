#!/bin/sh
# Writes the test files with pyarrow, then reads them with Spark 3.5.9 and
# 4.3.0 in containers, with one, two, and four worker threads, and saves the
# results. Needs uv and Docker.
#
#   sh docs/research/spark-row-order/run.sh
set -eu
here=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d)
uv run --quiet --no-project --with pyarrow==26.0.1 python "$here/make_files.py" "$work" > "$here/results.txt"
cp "$here/check.py" "$work/"
for tag in 3.5.9-java17-python3 4.3.0-java21-python3
do
    for master in 'local[1]' 'local[2]' 'local[4]'
    do
        docker run --rm -v "$work":/work:ro "apache/spark:$tag" \
            /opt/spark/bin/spark-submit --master "$master" --conf spark.ui.enabled=false \
            /work/check.py /work 2>/dev/null | grep '^RESULT' >> "$here/results.txt"
    done
done
cat "$here/results.txt"

#!/bin/sh
# Writes the test files with pyarrow, then reads them with each Spark version
# in a container and saves the results. Needs uv and Docker.
#
#   sh docs/research/spark-decimal-check/run.sh
#
# Set WORK to choose where the test files go. The default is a temp folder.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
work=${WORK:-$(mktemp -d)}
mkdir -p "$work" "$here/results"
uv run --quiet --no-project --with pyarrow==26.0.1 python "$here/make_files.py" "$work" > "$here/results/files.txt"
cp "$here/check.py" "$work/"
status=0
for tag in \
    3.3.3-python3 \
    3.4.4-python3 \
    3.5.7-java17-python3 \
    4.0.5-scala2.13-java17-python3-r-ubuntu \
    4.1.4-scala2.13-java17-python3-ubuntu
do
    version=${tag%%-*}
    echo "Spark $version"
    docker run --rm -v "$work":/work:ro "apache/spark:$tag" \
        /opt/spark/bin/spark-submit --master "local[2]" /work/check.py /work \
        2>/dev/null | grep '^RESULT' > "$here/results/spark-$version.txt" || status=1
    tail -1 "$here/results/spark-$version.txt"
done
exit $status

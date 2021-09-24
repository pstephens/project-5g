#!/usr/bin/env python3

import argparse
import itertools
import json
import sys


def load_data(f):
    data = []
    for line in f:
        data.append(json.loads(line))
    return data


def Deg(r):
    return r["Deg"]


def Field(name):
    def f(r):
        return r[name]
    return f


# group on Deg
def arearange_data(data, sample_from_group):
    output = []
    for k, g in itertools.groupby(data, Deg):
        samples = list(sample_from_group(list(g)))
        if len(samples) > 0:
            output.append({
                "x": k,
                "low": min(samples),
                "high": max(samples)
            })
    return json.dumps(output)


def scatter_data(data, sample_from_row, agg):
    output = []
    for k, g in itertools.groupby(data, Deg):
        samples =  list(itertools.chain.from_iterable([sample_from_row(r) for r in list(g)]))
        if len(samples) > 0:
            output.append({
                "x": k,
                "y": agg(samples)
            })
        else:
            output.append({
                "x": k,
                "y": None
            })
    return json.dumps(output)


def write_html(f, data):
    str = \
    f"""<!doctype html>
<html>
<head><title>{data[0]["Time"]}</title></head>
<script src="https://code.highcharts.com/highcharts.js"></script>
<script src="https://code.highcharts.com/highcharts-more.js"></script>

<body>
<div id="container" style="width: 1000px; height: 1000px; margin: 0 auto"></div>
<script>
Highcharts.chart("container", {{
    chart: {{
        polar: true
    }},
    yAxis: [{{
        title: {{ text: "Elapsed (ms)"}},
        max: 500
    }}],
    series: [{{
        type: "scatter",
        name: "Ping Min",
        yAxis: 0,
        lineWidth: 2,
        data: {scatter_data(data, Field("Ping Samples"), min)}
    }},
    {{
        type: "scatter",
        name: "Ping Avg",
        yAxis: 0,
        lineWidth: 2,
        data: {scatter_data(data, Field("Ping Samples"), lambda lst: sum(lst) / len(lst))}
    }},
    {{
        type: "scatter",
        name: "Ping Max",
        yAxis: 0,
        lineWidth: 2,
        data: {scatter_data(data, Field("Ping Samples"), max)}
    }}]
}});
</script>
</body>

</html>
"""
    f.write(str)


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=argparse.FileType("r"),
                        help="Input data set, single JSON object per line")
    parser.add_argument("output", type=argparse.FileType("w"),
                        help="Output name to write html to")
    args = parser.parse_args(args)

    data = load_data(args.input)

    write_html(args.output, data)


if __name__ == "__main__":
    main(sys.argv[1:])

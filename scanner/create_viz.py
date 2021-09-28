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
n

def Values(path):
    parts = [x for x in path.split(".") if x]
    def g(r, i):
        rtype = type(r)
        if rtype is list:
            for x in r:
                for y in g(x, i):
                    yield y
        elif rtype is int or rtype is float:
            if i == len(parts):
                yield r
        elif rtype is dict:
            if i < len(parts):
                for x in g(r.get(parts[i]), i + 1):
                    yield x
        elif r is None:
            return
        else:
            raise ValueError(f"Unexpected type {rtype} encountered during traversial of path {path}")
    def f(r):
        for x in g(r, 0):
            yield x
    return f


def get_value_by_paths(data, path):
    if type(path) is list:
        return [list(Values(p)(data)) for p in path]
    else:
        return list(Values(path)(data))


# group on Deg
def scatter_data(data, path, agg):
    output = []
    for k, g in itertools.groupby(data, Deg):
        samples = get_value_by_paths(list(g), path)
        output.append({
            "x": k,
            "y": agg(samples)
        })
    return json.dumps(output)


def p(factor):
    def f(samples):
        if len(samples) < 0:
            return None

        samples.sort()
        return samples[int(round(max(0, min(len(samples) - 1, len(samples) * factor - 1))))]
    return f


def agg_min(samples):
    if len(samples) < 0:
        return None
    else:
        return min(samples)


def agg_max(samples):
    if len(samples) < 0:
        return None
    else:
        return max(samples)


def agg_ping_loss(samples):
    sent, recv = samples
    sent = sum(sent)
    recv = len(recv)
    if sent < 1:
        return None
    else:
        return (sent - recv)/recv*100


def write_html(f, data):
    str = \
    f"""<!doctype html>
<html>
<head><title>{data[0]["Time"]}</title></head>
<script src="https://code.highcharts.com/highcharts.js"></script>
<script src="https://code.highcharts.com/highcharts-more.js"></script>

<body>
<div id="container" style="width: 2000px; height: 1000px; margin: 0 auto"></div>
<script>
Highcharts.chart("container", {{
    chart: {{
        type: "scatter"
    }},
    yAxis: [{{
        title: {{ text: "Elapsed (ms)"}},
        max: 500
    }},
    {{
        title: {{ text: "Percent"}},
        max: 100
    }},
    {{
        title: {{ text: "RSRP (dBm)"}},
        max: -44,
        min: -140
    }},
    {{
        title: {{ text: "RSRQ (dBm)"}},
        max: -3,
        min: -20
    }},
    {{
        title: {{ text: "SINR (db)"}},
        max: 30,
        min: -20
    }}],
    series: [{{
        type: "scatter",
        name: "Ping Min",
        yAxis: 0,
        lineWidth: 2,
        data: {scatter_data(data, "Ping Samples", agg_min)}
    }},
    {{
        type: "scatter",
        name: "Ping P90",
        yAxis: 0,
        lineWidth: 2,
        data: {scatter_data(data, "Ping Samples", p(0.90))}
    }},
    {{
        type: "scatter",
        name: "Ping Max",
        yAxis: 0,
        lineWidth: 2,
        data: {scatter_data(data, "Ping Samples", agg_max)}
    }},
    {{
        type: "scatter",
        name: "Ping Loss",
        yAxis: 1,
        lineWidth: 2,
        data: {scatter_data(data, ["Ping Cnt", "Ping Samples"], agg_ping_loss)}
    }},
    {{
        type: "scatter",
        name: "LTE RSRP",
        yAxis: 2,
        lineWidth: 2,
        data: {scatter_data(data, "SC LTE RSRP", p(0.90))}
    }},
    {{
        type: "scatter",
        name: "NSA RSRP",
        yAxis: 2,
        lineWidth: 2,
        data: {scatter_data(data, "SC NSA RSRP", p(0.90))}
    }},
    {{
        type: "scatter",
        name: "LTE RSRQ",
        yAxis: 3,
        lineWidth: 2,
        data: {scatter_data(data, "SC LTE RSRQ", p(0.90))}
    }},
    {{
        type: "scatter",
        name: "NSA RSRQ",
        yAxis: 3,
        lineWidth: 2,
        data: {scatter_data(data, "SC NSA RSRQ", p(0.90))}
    }},
    {{
        type: "scatter",
        name: "LTE SINR",
        yAxis: 4,
        lineWidth: 2,
        data: {scatter_data(data, "SC LTE SINR", p(0.90))}
    }},
    {{
        type: "scatter",
        name: "NSA SINR",
        yAxis: 4,
        lineWidth: 2,
        data: {scatter_data(data, "SC NSA SINR", p(0.90))}
    }}
    ]
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

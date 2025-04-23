from collections import defaultdict

import altair as alt
import pandas as pd
import redis
import streamlit as st
from generate_report_priority_queue import GenerateReportPriorityQueue

r = redis.Redis()

def dump_queue(queue_name):
    return r.zrange(queue_name, 0, -1, withscores=True)

def build_dataframe(prioritization_strategy, identifier: str, queue_name: str, number: int, start: int):
    if number != 0:
        GenerateReportPriorityQueue(queue_name).prioritize_tasks(
            start=start,
            number_of_tasks=number,
            package_request_uid=identifier,
            priority_strategy=prioritization_strategy,
            counter_name=f"{queue_name}_counter")

    dump = dump_queue(queue_name)

    priorities = list({int(p) for _, p in dump})
    chart_data = pd.DataFrame.from_dict({"priorities": priorities})

    packages = defaultdict(list)

    for item, priority in dump:
        package, chunk = item.decode().split("|")
        packages[package].append((int(chunk), priority))

    for package, package_entries in packages.items():
        chart_data[package] = None
        for chunk, priority in package_entries:
            chart_data.loc[chart_data["priorities"] == priority, package] = chunk

    return chart_data


def render_bar_chart(dataframe, title):
    melted_df = dataframe.melt(id_vars=["priorities"], var_name="package", value_name="chunk")

    chart = alt.Chart(melted_df).mark_bar().encode(
        x=alt.X("priorities:O", title="Priorities"),
        xOffset="package:N",
        y=alt.Y("chunk:Q", title="Chunks"),
        color=alt.Color("package:N", legend=alt.Legend(title="Package")),
        tooltip=["package", "chunk", "priorities"]
    ).properties(
        title=title,
        width=800,
        height=250
    )

    st.altair_chart(chart, use_container_width=True)
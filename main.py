from collections import defaultdict
from math import log
from uuid import uuid4

import pandas as pd
import redis
import streamlit as st
import altair as alt

from generate_report_priority_queue import GenerateReportPriorityQueue

r = redis.Redis()


def linear_weight_priority_counter_strategy(base_priority:int,priority_counter:int, index: int, spacing: int, total_number_of_tasks: int) -> int:
    """
    Balances priorities such that large packages do not block smaller ones,
    and smaller packages do not excessively punish larger ones.
    """
    weight = max(1, int(log(total_number_of_tasks + 1, 10)))  # Use logarithmic scaling for weight

    priority = (base_priority + priority_counter) + int((index * spacing) / weight)

    return priority



def weight_priority_counter_strategy(base_priority:int, priority_counter:int, index: int, spacing: int, total_number_of_tasks: int) -> int:
    weight = max(1, int(total_number_of_tasks ** 0.5))
    priority = (base_priority + int(priority_counter)) + int((index * spacing) / weight)

    return priority


def base_priority_strategy(base_priority:int, priority_counter:int, index: int, spacing: int, total_number_of_tasks: int) -> int:
    """
    Every time a new item is added to the queue, it will punish a little bit the base_priority
    """
    return base_priority + index * spacing


strategies = [
    {"name": "Base Priority", "function": base_priority_strategy, "queue_name": "q1"},
    {"name": "Square Weight with counter", "function": weight_priority_counter_strategy, "queue_name": "q2"},
    {"name": "Linear (5) with counter", "function": linear_weight_priority_counter_strategy, "queue_name": "q3"},
]

# Generate dataset to plot
def dump_queue(queue_name):
    return r.zrange(queue_name, 0, -1, withscores=True)

def clean_chart(dataframes, queues):
    for queue in queues:
        r.delete(queue)
        r.set(f"{queue}_counter", 0)

    for d in dataframes:
        if d is not None:
            d.drop(index=d.index, inplace=True)

def clean_all():
    clean_chart(
        list(st.session_state.dataframes.values()),
        [strategy["queue_name"] for strategy in strategies]
    )
    for strategy in strategies:
        st.session_state.pop(f"dequeued_{strategy['queue_name']}", None)
    st.session_state.pop("package_number", None)

def build_dataframe(prioritization_strategy, identifier: str, queue_name: str, number: int):
    if number != 0:
        GenerateReportPriorityQueue(queue_name).prioritize_tasks(number_of_tasks=number,
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





def render_dequeued_batch(batch, index):
    batch_items = []
    for item, priority in batch:
        item_decoded = item.decode()
        identifier = item_decoded.split("|")[0]
        chunk = item_decoded.split("|")[1]
        color =  "#D3D3D3"
        size = 35
        batch_items.append(
            f"<div style='display:inline-block;text-align:center;margin-right:15px;margin-bottom:0px;'>"
            f"<div style='width:{size}px;height:{size}px;background-color:{color};'>{chunk}</div>"
            f"<div style='color:black;'>{identifier}</div>"
            f"</div>")
    st.write(f"Batch {index + 1}")
    markdown_to_write = " ".join(batch_items)
    st.markdown(markdown_to_write, unsafe_allow_html=True)
    st.divider()


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


batch_size = 10
large_size = 21 * batch_size
medium_size = 9 * batch_size
small_size = 5 * batch_size
def main():
    st.set_page_config(layout="wide")
    insert_number = st.sidebar.number_input("Number of items to add", min_value=1, max_value=100, value=5)

    if "dataframes" not in st.session_state:
        st.session_state.dataframes = {strat["queue_name"]: None for strat in strategies}
    if "package_number" not in st.session_state:
        st.session_state.package_number = 0

    if st.sidebar.button("Insert into queue"):
        insert_into_queue(insert_number)

    if st.sidebar.button("Insert L,L,M,S,M,S,S,S,S"):
        insert_into_queue(large_size)
        insert_into_queue(large_size)
        insert_into_queue(medium_size)
        insert_into_queue(small_size)
        insert_into_queue(medium_size)
        insert_into_queue(small_size)
        insert_into_queue(small_size)
        insert_into_queue(small_size)
        insert_into_queue(small_size)
    if st.sidebar.button("Insert S,S,S,M,S,L,L"):
        insert_into_queue(small_size)
        insert_into_queue(small_size)
        insert_into_queue(small_size)
        insert_into_queue(medium_size)
        insert_into_queue(small_size)
        insert_into_queue(large_size)
        insert_into_queue(large_size)
    if st.sidebar.button("Insert L,S,L,S,M,S,M,S,L"):
        insert_into_queue(large_size)
        insert_into_queue(small_size)
        insert_into_queue(large_size)
        insert_into_queue(small_size)
        insert_into_queue(medium_size)
        insert_into_queue(small_size)
        insert_into_queue(medium_size)
        insert_into_queue(small_size)
        insert_into_queue(large_size)

    dequeue_number = st.sidebar.number_input("Number to dequeue", min_value=1, max_value=100, value=5)

    if st.sidebar.button("Dequeue"):
        for strategy in strategies:
            dequeued_items = r.zpopmin(strategy["queue_name"], count=dequeue_number)
            if f"dequeued_{strategy['queue_name']}" not in st.session_state:
                st.session_state[f"dequeued_{strategy['queue_name']}"] = []
            st.session_state[f"dequeued_{strategy['queue_name']}"].append(dequeued_items)

            if st.session_state.dataframes[strategy["queue_name"]] is not None:
                st.session_state.dataframes[strategy["queue_name"]] = build_dataframe(
                    strategy["function"],
                    queue_name=strategy["queue_name"],
                    identifier="n/a",
                    number=0,
                )

    # Render charts dynamically
    for strategy in strategies:
        if st.session_state.dataframes[strategy["queue_name"]] is not None:
            render_bar_chart(st.session_state.dataframes[strategy["queue_name"]], strategy["name"])

    # Render dequeued items dynamically
    columns = st.columns(len(strategies))
    for col, strategy in zip(columns, strategies):
        with col:
            if f"dequeued_{strategy['queue_name']}" in st.session_state and st.session_state[
                f"dequeued_{strategy['queue_name']}"] is not None:
                st.title(f"{strategy['name']} Queue: dequeued")
                for i, batch in enumerate(st.session_state[f"dequeued_{strategy['queue_name']}"]):
                    render_dequeued_batch(batch, i)

    st.sidebar.button("Clean", on_click=lambda: clean_all())


def insert_into_queue(insert_number):
    identifier = f"{str(st.session_state.package_number).zfill(2)}_{uuid4().hex[:6]}"  # Generate the identifier
    for strategy in strategies:
        st.session_state.dataframes[strategy["queue_name"]] = build_dataframe(
            strategy["function"],
            queue_name=strategy["queue_name"],
            identifier=identifier,
            number=insert_number,
        )
    st.session_state.package_number += 1


if __name__ == "__main__":
    main()

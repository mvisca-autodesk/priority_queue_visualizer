import random
from collections import defaultdict
from uuid import uuid4

import pandas as pd
import redis
import streamlit as st

r = redis.Redis()


# Strategies
colors = [
    "#FF5733", "#33FF57", "#3357FF", "#FF33A1", "#A133FF", "#33FFF5", "#F5FF33", "#FF8C33", "#8C33FF", "#33FF8C",
    "#FF3333", "#33FF33", "#3333FF", "#FF33FF", "#33FFFF", "#FFFF33", "#FF6633", "#6633FF", "#33FF66", "#FF3366",
    "#66FF33", "#3366FF", "#FF9933", "#9933FF", "#33FF99", "#FF3399", "#99FF33", "#3399FF", "#FFCC33", "#CC33FF",
    "#33FFCC", "#FF33CC", "#CCFF33", "#33CCFF", "#FFAA33", "#AA33FF", "#33FFAA", "#FF33AA", "#AAFF33", "#33AAFF",
    "#FFDD33", "#DD33FF", "#33FFDD", "#FF33DD", "#DDFF33", "#33DDFF", "#FFEE33", "#EE33FF", "#33FFEE", "#FF33EE"
]

def generate_color(index:int):
    """Generate a valid random color in hex format."""
    return colors[index]


def punish_new_ones(identifier: str,
                    color: str,
                    number: int = 2,
                    base_priority: int = 0,
                    spacing: int = 10,
                    queue_name: str = "punish_queue"):
    """
    Every time a new item is added to the queue, it will punish a little bit the base_priority
    """
    priority_counter = int(r.get("priority_counter") or 0)  # type: ignore
    for i in range(1, number + 1):
        priority = (base_priority + int(priority_counter)) + i * spacing
        r.zadd(queue_name, {f"p_{identifier}_{color}|{i}": priority})

    r.incr("priority_counter")


def use_base_priority_always(identifier: str,
                             color:str,
                             number: int = 2,
                             base_priority: int = 0,
                             spacing: int = 10,
                             queue_name: str = "base_queue"):
    """
    Every time a new item is added to the queue, it will punish a little bit the base_priority
    """

    for i in range(1, number + 1):
        priority = base_priority + i * spacing
        r.zadd(queue_name, {f"p_{identifier}_{color}|{i}": priority})


# Generate dataset to plot
def dump_queue(queue_name):
    return r.zrange(queue_name, 0, -1, withscores=True)


def build_dataframe(prioritization_strategy, color:str, identifier: str, queue_name: str, number: int, base_priority: int = 0,
                    spacing: int = 10):
    if number != 0:
        prioritization_strategy(identifier=identifier,
                                color=color,
                                number=number, base_priority=base_priority, spacing=spacing,
                                queue_name=queue_name)

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


def clean_chart(dataframes, queues):
    for queue in queues:
        r.delete(queue)

    for d in dataframes:
        if d is not None:
            d.drop(index=d.index, inplace=True)

    r.set("priority_counter", 0)


def render_dequeued_batch(batches, identifier_colors):
    batch_items = []
    print(f"batches: {batches}")
    for item, priority in batches:
        item_decoded = item.decode()
        identifier = item_decoded.split("|")[0]
        color = identifier_colors.get(identifier, "#000000")
        print(f"dq:identifier: {identifier}")
        print(f"dq:colors: {identifier_colors}")

        batch_items.append(
            f"<div style='display:inline-block;text-align:center;margin-right:10px;'>"
            f"<div style='width:50px;height:50px;background-color:{color};'></div>"
            f"<div style='color:black;'>{color}</div>"
            f"<div style='color:black;'>{item_decoded}</div>"
            f"</div>")
    return " ".join(batch_items)

def main():
    st.set_page_config(layout="wide")
    number = st.sidebar.number_input("Number of items to add", min_value=1, max_value=100, value=5)

    if "s1" not in st.session_state:
        st.session_state.s1 = None
    if "s2" not in st.session_state:
        st.session_state.s2 = None
    if "identifier_colors" not in st.session_state:
        st.session_state.identifier_colors = {}

    if st.sidebar.button("Insert into queue"):
        identifier = uuid4().hex[:6]  # Generate the identifier
        if identifier not in st.session_state.identifier_colors:
            color = generate_color(len(st.session_state.identifier_colors))
            st.session_state.identifier_colors[f"p_{identifier}_{color}"] = color
        print(f"identifier: {identifier}")
        print(f"colors: {st.session_state.identifier_colors}")
        st.session_state.s1 = build_dataframe(use_base_priority_always,
                                              queue_name="q1",
                                              color=color,
                                              identifier=identifier,
                                              number=number,
                                              base_priority=0, spacing=10)
        st.session_state.s2 = build_dataframe(punish_new_ones,
                                              queue_name="q2",
                                              color=color,
                                              identifier=identifier,
                                              number=number,
                                              base_priority=0,
                                              spacing=10)

    if st.sidebar.button("Dequeue Top 5"):
        for queue in ["q1", "q2"]:
            dequeued_items = r.zpopmin(queue, count=5)
            if f"dequeued_{queue}" not in st.session_state:
                st.session_state[f"dequeued_{queue}"] = []
            st.session_state[f"dequeued_{queue}"].append(dequeued_items)

        if st.session_state.s1 is not None:
            st.session_state.s1 = build_dataframe(use_base_priority_always, queue_name="q1",
                                                  color="n/a",
                                                  identifier="n/a",
                                                  number=0, base_priority=0, spacing=10)
        if st.session_state.s2 is not None:
            st.session_state.s2 = build_dataframe(punish_new_ones, queue_name="q2",
                                                  color="n/a",
                                                  identifier="n/a",
                                                  number=0, base_priority=0, spacing=10)

    if st.session_state.s1 is not None:
        st.title("Normal Queue")
        st.bar_chart(st.session_state.s1, x="priorities", stack=False, use_container_width=True,
                     color=list(st.session_state.identifier_colors.values()))

    if st.session_state.s2 is not None:
        st.title("Punish New Ones")
        st.bar_chart(st.session_state.s2, x="priorities", stack=False, use_container_width=True,
                     color=list(st.session_state.identifier_colors.values()))

    col1, col2 = st.columns(2)

    with col1:
        if "dequeued_q1" in st.session_state and st.session_state["dequeued_q1"] is not None:
            st.title("Normal Queue:dequeued")
            for batches in st.session_state[f"dequeued_q1"]:
                st.markdown(render_dequeued_batch(batches, st.session_state.identifier_colors), unsafe_allow_html=True)

    with col2:
        if "dequeued_q2" in st.session_state and st.session_state["dequeued_q2"] is not None:
            st.title("Punish New Queue:dequeued")
            for batches in st.session_state[f"dequeued_q2"]:
                st.markdown(render_dequeued_batch(batches, st.session_state.identifier_colors), unsafe_allow_html=True)

    st.sidebar.button("Clean", on_click=lambda: (clean_chart(
        [st.session_state.s1, st.session_state.s2],
        ["q1", "q2"]),
                                                 [st.session_state.pop(f"dequeued_{queue}", None) for queue in
                                                  ["q1", "q2"]],
                                                 st.session_state.identifier_colors.clear()))


if __name__ == "__main__":
    main()

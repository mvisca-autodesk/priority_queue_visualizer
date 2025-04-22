import random
import time
from collections import defaultdict
from uuid import uuid4

import pandas as pd
import redis
import streamlit as st

r = redis.Redis()




def balanced_priority_strategy(identifier: str,
                               number: int = 2,
                               base_priority: int = 0,
                               spacing: int = 10,
                               queue_name: str = "balanced_queue"):
    """
    Balances priorities such that large packages do not block smaller ones,
    and smaller packages do not excessively punish larger ones.
    """
    priority_counter = int(r.get("priority_counter") or 0)  # type: ignore
    weight = max(1, number // 5)  # Adjust weight based on package size
    for i in range(1, number + 1):
        priority = (base_priority + int(priority_counter)) + (i * spacing) // weight
        r.zadd(queue_name, {f"p_{identifier}|{i}": priority})

    r.incr("priority_counter")


def punish_new_ones(identifier: str,
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
        r.zadd(queue_name, {f"p_{identifier}|{i}": priority})

    r.incr("priority_counter")

strategy = "Balanced Strategy"
def compare_strategy(identifier: str,
                             number: int = 2,
                             base_priority: int = 0,
                             spacing: int = 10,
                             queue_name: str = "compare_queue"):
    balanced_priority_strategy(
        identifier=identifier,
        number=number, base_priority=base_priority, spacing=spacing,
        queue_name=queue_name
    )


def use_base_priority_always(identifier: str,
                             number: int = 2,
                             base_priority: int = 0,
                             spacing: int = 10,
                             queue_name: str = "base_queue"):
    """
    Every time a new item is added to the queue, it will punish a little bit the base_priority
    """

    for i in range(1, number + 1):
        priority = base_priority + i * spacing
        r.zadd(queue_name, {f"p_{identifier}|{i}": priority})


# Generate dataset to plot
def dump_queue(queue_name):
    return r.zrange(queue_name, 0, -1, withscores=True)


def build_dataframe(prioritization_strategy, identifier: str, queue_name: str, number: int, base_priority: int = 0,
                    spacing: int = 10):
    if number != 0:
        prioritization_strategy(identifier=identifier,
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

def main():
    st.set_page_config(layout="wide")
    insert_number = st.sidebar.number_input("Number of items to add", min_value=1, max_value=100, value=5)

    if "s1" not in st.session_state:
        st.session_state.s1 = None
    if "s2" not in st.session_state:
        st.session_state.s2 = None

    if st.sidebar.button("Insert into queue"):
        insert_into_queue(insert_number)
    if st.sidebar.button("Insert Large package"):
        insert_into_queue(21)
    if st.sidebar.button("Insert Medium package"):
        insert_into_queue(9)
    if st.sidebar.button("Insert Small package"):
        insert_into_queue(5)

    dequeue_number = st.sidebar.number_input("Number to dequeue", min_value=1, max_value=100, value=5)

    if st.sidebar.button("Dequeue"):
        for queue in ["q1", "q2"]:
            dequeued_items = r.zpopmin(queue, count=dequeue_number)
            if f"dequeued_{queue}" not in st.session_state:
                st.session_state[f"dequeued_{queue}"] = []
            st.session_state[f"dequeued_{queue}"].append(dequeued_items)

        if st.session_state.s1 is not None:
            st.session_state.s1 = build_dataframe(use_base_priority_always, queue_name="q1",
                                                  identifier="n/a",
                                                  number=0, base_priority=0, spacing=10)
        if st.session_state.s2 is not None:
            st.session_state.s2 = build_dataframe(compare_strategy, queue_name="q2",
                                                  identifier="n/a",
                                                  number=0, base_priority=0, spacing=10)

    if st.session_state.s1 is not None:
        st.title("Normal Queue")
        st.bar_chart(st.session_state.s1, x="priorities", stack=False, use_container_width=True,)

    if st.session_state.s2 is not None:
        st.title(f"{strategy}")
        st.bar_chart(st.session_state.s2, x="priorities", stack=False, use_container_width=True,)

    col1, col2 = st.columns(2)

    with col1:
        if "dequeued_q1" in st.session_state and st.session_state["dequeued_q1"] is not None:
            st.title("Normal Queue:dequeued")
            for i, batch in enumerate(st.session_state[f"dequeued_q1"]):
                render_dequeued_batch(batch, i)


    with col2:
        if "dequeued_q2" in st.session_state and st.session_state["dequeued_q2"] is not None:
            st.title(f"{strategy} Queue:dequeued")
            for i, batch in enumerate(st.session_state[f"dequeued_q2"]):
                render_dequeued_batch(batch, i)

    st.sidebar.button("Clean", on_click=lambda: (clean_chart(
        [st.session_state.s1, st.session_state.s2],
        ["q1", "q2"]),
                                                 [st.session_state.pop(f"dequeued_{queue}", None) for queue in
                                                  ["q1", "q2"]],))


def insert_into_queue(insert_number):
    identifier = uuid4().hex[:6]  # Generate the identifier
    st.session_state.s1 = build_dataframe(use_base_priority_always,
                                          queue_name="q1",
                                          identifier=identifier,
                                          number=insert_number,
                                          base_priority=0, spacing=10)
    st.session_state.s2 = build_dataframe(compare_strategy,
                                          queue_name="q2",
                                          identifier=identifier,
                                          number=insert_number,
                                          base_priority=0,
                                          spacing=10)


if __name__ == "__main__":
    main()

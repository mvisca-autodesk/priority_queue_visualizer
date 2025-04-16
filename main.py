from collections import defaultdict
from uuid import uuid4

import pandas as pd
import redis
import streamlit as st

r = redis.Redis()


# Strategies

def punish_new_ones(identifier: str, number: int = 2, base_priority: int = 0, spacing: int = 10,
                    queue_name: str = "test_queue"):
    """
    Every time a new item is added to the queue, it will punish a little bit the base_priority
    """
    priority_counter = int(r.get("priority_counter") or 0)  # type: ignore
    for i in range(number):
        priority = (base_priority + int(priority_counter)) + i * spacing
        r.zadd(queue_name, {f"p_{identifier}|{i}": priority})

    r.incr("priority_counter")


def use_base_priority_always(identifier: str, number: int = 2, base_priority: int = 0, spacing: int = 10,
                             queue_name: str = "test_queue"):
    """
    Every time a new item is added to the queue, it will punish a little bit the base_priority
    """

    for i in range(number):
        priority = base_priority + i * spacing
        r.zadd(queue_name, {f"p_{identifier}|{i}": priority})


# Generate dataset to plot
def dump_queue(queue_name):
    return r.zrange(queue_name, 0, -1, withscores=True)


def build_dataframe(prioritization_strategy, identifier: str, queue_name: str, number: int, base_priority: int = 0,
                    spacing: int = 10):
    prioritization_strategy(identifier=identifier, number=number, base_priority=base_priority, spacing=spacing,
                            queue_name=queue_name)

    dump = dump_queue(queue_name)

    priorities = list({int(p) for _, p in dump})
    chart_data = pd.DataFrame.from_dict({"priorities": priorities})

    packages = defaultdict(list)

    for item, priority in dump:
        package, chunk = item.decode().split("|")
        packages[package].append(priority)

    for package, package_entries in packages.items():
        chart_data[package] = None

        for index, entry in enumerate(package_entries, start=1):
            chart_data.loc[chart_data["priorities"] == entry, package] = index

    return chart_data


def clean_chart(dataframes, queues):
    for queue in queues:
        r.delete(queue)

    for d in dataframes:
        d.drop(index=d.index, inplace=True)

    r.set("priority_counter", 0)


def main():
    st.set_page_config(layout="wide")
    identifier = uuid4().hex[:5]  # Generate the identifier
    number = st.sidebar.number_input("Number of items to add", min_value=1, max_value=100, value=5)



    if "s1" not in st.session_state:
        st.session_state.s1 = None
    if "s2" not in st.session_state:
        st.session_state.s2 = None

    if st.sidebar.button("Insert into queue"):
        st.session_state.s1 = build_dataframe(use_base_priority_always, queue_name="q1", identifier=identifier,
                                              number=number,
                                              base_priority=0, spacing=10)
        st.session_state.s2 = build_dataframe(punish_new_ones, queue_name="q2", identifier=identifier, number=number,
                                              base_priority=0, spacing=10)

    if st.session_state.s1 is not None:
        st.title("Normal Queue")
        st.bar_chart(st.session_state.s1, x="priorities", stack=False, use_container_width=True)

    if st.session_state.s2 is not None:
        st.title("Punish New Ones")
        st.bar_chart(st.session_state.s2, x="priorities", stack=False, use_container_width=True)

    st.sidebar.button("Clean", on_click=lambda: clean_chart(
        [st.session_state.s1, st.session_state.s2],
        ["q1", "q2"]))


if __name__ == "__main__":
    main()

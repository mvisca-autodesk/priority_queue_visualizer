import redis
import streamlit as st


r = redis.Redis()

def clean_chart(dataframes, queues):
    for queue in queues:
        r.delete(queue)
        r.set(f"{queue}_counter", 0)

    for d in dataframes:
        if d is not None:
            d.drop(index=d.index, inplace=True)


def clean_all(strategies):
    clean_chart(
        list(st.session_state.dataframes.values()),
        [strategy["queue_name"] for strategy in strategies]
    )
    for strategy in strategies:
        st.session_state.pop(f"dequeued_{strategy['queue_name']}", None)
    st.session_state.pop("package_number", None)
    r.flushall()
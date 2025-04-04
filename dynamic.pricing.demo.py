import streamlit as st
import datetime
import random
import pandas as pd
import pytz
import time

# Common update interval in seconds.
UPDATE_INTERVAL = 5

# --- Global Product Data (cached for performance) ---
@st.cache_resource
def get_products():
    products = [
        {
            "name": "Product A",
            "start_price": 100.0,
            "end_price": random.uniform(0.30 * 100.0, 0.70 * 100.0)
        },
        {
            "name": "Product B",
            "start_price": 200.0,
            "end_price": random.uniform(0.30 * 200.0, 0.70 * 200.0)
        }
    ]
    return products

products = get_products()

def get_cycle(current_dt):
    """
    Determines the active price degradation cycle based on Greek time.
    
    - If current time is before 5:00 AM, the cycle is from yesterday 7:00 AM to today 5:00 AM.
    - If current time is between 5:00 and 7:00 AM, the previous cycle is considered complete.
    - Otherwise, the cycle is from today 7:00 AM to tomorrow 5:00 AM.
    """
    tz = pytz.timezone("Europe/Athens")
    current_dt = current_dt.astimezone(tz)
    today = current_dt.date()
    current_time = current_dt.time()

    if current_time < datetime.time(5, 0):
        yesterday = today - datetime.timedelta(days=1)
        cycle_start = tz.localize(datetime.datetime.combine(yesterday, datetime.time(7, 0)))
        cycle_end = tz.localize(datetime.datetime.combine(today, datetime.time(5, 0)))
    elif current_time < datetime.time(7, 0):
        yesterday = today - datetime.timedelta(days=1)
        cycle_start = tz.localize(datetime.datetime.combine(yesterday, datetime.time(7, 0)))
        cycle_end = tz.localize(datetime.datetime.combine(today, datetime.time(5, 0)))
    else:
        cycle_start = tz.localize(datetime.datetime.combine(today, datetime.time(7, 0)))
        cycle_end = tz.localize(datetime.datetime.combine(today + datetime.timedelta(days=1), datetime.time(5, 0)))
    return cycle_start, cycle_end

def calculate_price(product, current_dt):
    """
    Computes the current price using a linear interpolation function:
    
    $$ f(t) = \text{start\_price} + (\text{end\_price} - \text{start\_price}) \times \frac{t - t_{\text{start}}}{t_{\text{end}} - t_{\text{start}}} $$
    
    For times between 5:00 and 7:00 AM, the final (degraded) price is returned.
    """
    tz = pytz.timezone("Europe/Athens")
    current_dt = current_dt.astimezone(tz)

    if datetime.time(5, 0) <= current_dt.time() < datetime.time(7, 0):
        return product["end_price"]

    cycle_start, cycle_end = get_cycle(current_dt)
    if current_dt < cycle_start:
        return product["start_price"]
    if current_dt > cycle_end:
        return product["end_price"]

    total_duration = (cycle_end - cycle_start).total_seconds()
    elapsed = (current_dt - cycle_start).total_seconds()
    fraction = elapsed / total_duration
    current_price = product["start_price"] + (product["end_price"] - product["start_price"]) * fraction
    return current_price

# --- Sidebar Navigation ---
page = st.sidebar.selectbox("Select Page", options=["Demo", "Console"])
tz = pytz.timezone("Europe/Athens")

if page == "Demo":
    st.title("Product Demo Page")
    demo_placeholder = st.empty()

    while True:
        loop_start = time.perf_counter()
        now = datetime.datetime.now(tz)
        demo_text = f"**Current Greek Time:** {now.strftime('%H:%M:%S')}\n\n"
        demo_text += ("Prices degrade linearly from **7:00 AM** (cycle start) to **5:00 AM** (cycle end) for all users.\n\n")
        for product in products:
            current_price = calculate_price(product, now)
            demo_text += f"**{product['name']}**: {current_price:.8f} €\n\n"
        demo_placeholder.markdown(demo_text)
        elapsed_loop = time.perf_counter() - loop_start
        time.sleep(max(UPDATE_INTERVAL - elapsed_loop, 0))

elif page == "Console":
    st.title("Console: Detailed Analytics & Full Price History")
    analytics_placeholder = st.empty()
    table_placeholder = st.empty()
    download_placeholder = st.empty()
    
    while True:
        loop_start = time.perf_counter()
        now = datetime.datetime.now(tz)
        cycle_start, cycle_end = get_cycle(now)
        total_duration = (cycle_end - cycle_start).total_seconds()
        elapsed_time = (now - cycle_start).total_seconds()
        
        # Display the linear degradation function as LaTeX.
        analytics_placeholder.latex(
            r"f(t) = \text{start\_price} + (\text{end\_price} - \text{start\_price}) \times \frac{t - t_{\text{start}}}{t_{\text{end}} - t_{\text{start}}}"
        )
        analytics_details = f"""
**Cycle Details:**

- **Cycle Start (tₛ):** {cycle_start.strftime("%H:%M:%S")}
- **Cycle End (tₑ):** {cycle_end.strftime("%H:%M:%S")}
- **Current Time (t):** {now.strftime("%H:%M:%S")}
- **Elapsed Time:** {elapsed_time:.8f} seconds
- **Total Duration:** {total_duration:.8f} seconds
        """
        st.markdown(analytics_details)
        
        # Build full price history from cycle_start to now at UPDATE_INTERVAL intervals.
        schedule = []
        current_dt = cycle_start
        while current_dt <= now:
            row = {"Time": current_dt.strftime("%H:%M:%S")}
            for product in products:
                price = calculate_price(product, current_dt)
                row[product["name"]] = f"{price:.8f} €"
            schedule.append(row)
            current_dt += datetime.timedelta(seconds=UPDATE_INTERVAL)
        
        df = pd.DataFrame(schedule)
        
        if not df.empty:
            if len(df) > 100:
                st.markdown("### First 100 Entries")
                st.dataframe(df.head(100), use_container_width=True)
                st.markdown("### Last 100 Entries")
                st.dataframe(df.tail(100), use_container_width=True)
            else:
                st.dataframe(df, use_container_width=True)
        
        # Update CSV in session state and show a download button using a unique key.
        csv = df.to_csv(index=False).encode('utf-8')
        download_placeholder.download_button(
            label="Download Full Price History",
            data=csv,
            file_name="price_history.csv",
            mime="text/csv",
            key=f"download_button_{int(time.time())}"
        )
        
        elapsed_loop = time.perf_counter() - loop_start
        time.sleep(max(UPDATE_INTERVAL - elapsed_loop, 0))

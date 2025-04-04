import streamlit as st
import datetime
import random
import pandas as pd
import pytz
import time

# --- Global Product Data (cached) ---
@st.cache_resource
def get_products():
    # Two products with fixed starting prices and randomly generated ending prices
    # within 30%-70% of the starting price.
    products = [
        {
            "name": "Product A",
            "start_price": 100,
            "end_price": random.uniform(0.30 * 100, 0.70 * 100)
        },
        {
            "name": "Product B",
            "start_price": 200,
            "end_price": random.uniform(0.30 * 200, 0.70 * 200)
        }
    ]
    return products

products = get_products()

def get_cycle(current_dt):
    """
    Determines the current price degradation cycle.
    - If current time is before 5:00 AM, the cycle is from yesterday 7:00 AM to today 5:00 AM.
    - If the time is between 5:00 AM and 7:00 AM, the previous cycle has ended.
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
    Computes the current price using linear interpolation between the starting and ending prices,
    based on the current degradation cycle.
    For times between 5:00 and 7:00, the final (degraded) price is returned.
    """
    tz = pytz.timezone("Europe/Athens")
    current_dt = current_dt.astimezone(tz)

    # For times between 5:00 and 7:00, return the final price.
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
    # Create a placeholder for the dynamic content.
    placeholder = st.empty()
    
    # Update the price every 2 seconds.
    while True:
        now = datetime.datetime.now(tz)
        text = f"Current Greek Time: {now.strftime('%H:%M:%S')}\n"
        text += "Prices degrade linearly from 7:00 AM (cycle start) to 5:00 AM (cycle end) for all users.\n\n"
        for product in products:
            current_price = calculate_price(product, now)
            text += f"{product['name']}: {current_price:.4f} €\n"
        placeholder.text(text)
        time.sleep(2)

elif page == "Console":
    st.title("Console: Price Degradation Details")
    st.write("This page displays detailed product data and a schedule of price degradation.")
    st.markdown("### Product Details")
    for product in products:
        st.write(f"**{product['name']}**: Start Price = {product['start_price']:.4f} €, "
                 f"End Price = {product['end_price']:.4f} €")
    
    st.markdown("---")
    st.markdown("### Price Schedule (Current Cycle)")
    now = datetime.datetime.now(tz)
    cycle_start, cycle_end = get_cycle(now)
    
    # Generate a schedule table with 15-minute intervals.
    schedule = []
    current_dt = cycle_start
    while current_dt <= cycle_end:
        row = {"Time": current_dt.strftime("%d-%m %H:%M")}
        for product in products:
            price = calculate_price(product, current_dt)
            row[product["name"]] = f"{price:.4f} €"
        schedule.append(row)
        current_dt += datetime.timedelta(minutes=15)
    
    df = pd.DataFrame(schedule)
    st.dataframe(df)

import streamlit as st
import datetime
import random
import pandas as pd
import pytz

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
    - If current time is between 5:00 AM and 7:00 AM, the previous cycle has ended.
    - Otherwise (>= 7:00 AM), the cycle is from today 7:00 AM to tomorrow 5:00 AM.
    """
    tz = pytz.timezone("Europe/Athens")
    current_dt = current_dt.astimezone(tz)
    today = current_dt.date()
    current_time = current_dt.time()

    if current_time < datetime.time(5, 0):
        # Cycle from yesterday 7:00 AM to today 5:00 AM.
        yesterday = today - datetime.timedelta(days=1)
        cycle_start = tz.localize(datetime.datetime.combine(yesterday, datetime.time(7, 0)))
        cycle_end = tz.localize(datetime.datetime.combine(today, datetime.time(5, 0)))
    elif current_time < datetime.time(7, 0):
        # Between 5:00 and 7:00, the previous cycle has ended.
        yesterday = today - datetime.timedelta(days=1)
        cycle_start = tz.localize(datetime.datetime.combine(yesterday, datetime.time(7, 0)))
        cycle_end = tz.localize(datetime.datetime.combine(today, datetime.time(5, 0)))
    else:
        # Current cycle: from today 7:00 AM to tomorrow 5:00 AM.
        cycle_start = tz.localize(datetime.datetime.combine(today, datetime.time(7, 0)))
        cycle_end = tz.localize(datetime.datetime.combine(today + datetime.timedelta(days=1), datetime.time(5, 0)))
    return cycle_start, cycle_end

def calculate_price(product, current_dt):
    """
    Computes the current price using linear interpolation between the starting and ending prices,
    based on the current degradation cycle.
    For times between 5:00 and 7:00, the price is fixed at the final (degraded) value.
    """
    tz = pytz.timezone("Europe/Athens")
    current_dt = current_dt.astimezone(tz)

    # If current time is between 5:00 and 7:00, return the final price.
    if datetime.time(5, 0) <= current_dt.time() < datetime.time(7, 0):
        return product["end_price"]

    cycle_start, cycle_end = get_cycle(current_dt)

    # In case the current time is outside the cycle (shouldn't occur), fallback:
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

# Current Greek time (using Europe/Athens time zone)
tz = pytz.timezone("Europe/Athens")
now = datetime.datetime.now(tz)

if page == "Demo":
    st.title("Product Demo Page")
    st.write("Current Greek Time:", now.strftime("%H:%M:%S"))
    st.write("Prices degrade linearly from 7:00 AM (cycle start) to 5:00 AM (cycle end) for all users.")
    st.markdown("---")
    # Display each product's current price based on the current time.
    for product in products:
        current_price = calculate_price(product, now)
        st.subheader(product["name"])
        st.write(f"Current Price: {current_price:.2f} €")
    st.info("Refresh the page to see updated prices based on the current time.")

elif page == "Console":
    st.title("Console: Price Degradation Details")
    st.write("This page displays detailed product data and a schedule of price degradation.")
    st.markdown("### Product Details")
    for product in products:
        st.write(f"**{product['name']}**: Start Price = {product['start_price']:.2f} €, "
                 f"End Price = {product['end_price']:.2f} €")
    
    st.markdown("---")
    st.markdown("### Price Schedule (Current Cycle)")
    cycle_start, cycle_end = get_cycle(now)
    
    # Generate a schedule table with 15-minute intervals across the current cycle.
    schedule = []
    current_dt = cycle_start
    while current_dt <= cycle_end:
        row = {"Time": current_dt.strftime("%d-%m %H:%M")}
        for product in products:
            price = calculate_price(product, current_dt)
            row[product["name"]] = f"{price:.2f} €"
        schedule.append(row)
        current_dt += datetime.timedelta(minutes=15)
    
    df = pd.DataFrame(schedule)
    st.dataframe(df)

import streamlit as st
import datetime
import random
import pytz
import time

# Set page configuration with a plant emoji favicon.
st.set_page_config(page_title="Eco Store", page_icon="🌱", layout="wide")

# Inject custom CSS for a modern, clean store look.
st.markdown(
    """
    <style>
    /* Overall background with a light gradient */
    .stApp {
        background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
    }
    /* Header styling */
    h1 {
        color: #2E7D32;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-align: center;
        padding-top: 1rem;
    }
    /* Product card styling */
    .product-card {
        background-color: #ffffff;
        padding: 1rem;
        margin: 0.5rem;
        border-radius: 10px;
        box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.15);
        text-align: center;
    }
    .product-card h3 {
        color: #33691E;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .product-card p {
        color: #555555;
        font-size: 0.9rem;
    }
    /* Button styling */
    .stButton>button {
        background-color: #66BB6A;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
    }
    /* Time info styling */
    .time-info {
        text-align: center;
        font-size: 1rem;
        color: #2E7D32;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Update interval (seconds)
UPDATE_INTERVAL = 5

# --- Global Product Data (cached) ---
@st.cache_resource
def get_products():
    return [
        {
            "name": "Eco Backpack",
            "start_price": 50.0,
            "end_price": random.uniform(0.30 * 50.0, 0.70 * 50.0)
        },
        {
            "name": "Reusable Water Bottle",
            "start_price": 20.0,
            "end_price": random.uniform(0.30 * 20.0, 0.70 * 20.0)
        },
        {
            "name": "Organic T-Shirt",
            "start_price": 30.0,
            "end_price": random.uniform(0.30 * 30.0, 0.70 * 30.0)
        },
        {
            "name": "Eco Sunglasses",
            "start_price": 40.0,
            "end_price": random.uniform(0.30 * 40.0, 0.70 * 40.0)
        }
    ]

products = get_products()

def get_cycle(current_dt):
    """
    Determines the active pricing cycle.
    The cycle starts at 05:00 (Europe/Athens time) and lasts 22 hours.
    If the current time is before 05:00, the cycle start is set to yesterday at 05:00.
    """
    tz = pytz.timezone("Europe/Athens")
    current_dt = current_dt.astimezone(tz)
    today = current_dt.date()
    if current_dt.time() >= datetime.time(5, 0):
        cycle_start = tz.localize(datetime.datetime.combine(today, datetime.time(5, 0)))
    else:
        yesterday = today - datetime.timedelta(days=1)
        cycle_start = tz.localize(datetime.datetime.combine(yesterday, datetime.time(5, 0)))
    cycle_end = cycle_start + datetime.timedelta(hours=22)
    return cycle_start, cycle_end

def get_current_scheduled_time(current_dt):
    """
    Floors the elapsed time since cycle start to the nearest UPDATE_INTERVAL.
    This produces a common scheduled calculation time for all users.
    """
    cycle_start, _ = get_cycle(current_dt)
    delta = (current_dt - cycle_start).total_seconds()
    floor_delta = int(delta // UPDATE_INTERVAL) * UPDATE_INTERVAL
    scheduled_time = cycle_start + datetime.timedelta(seconds=floor_delta)
    return scheduled_time

@st.cache_data(ttl=UPDATE_INTERVAL)
def get_global_scheduled_time():
    """
    Returns a globally cached scheduled time (floored to UPDATE_INTERVAL seconds)
    so that all users see the same calculation time.
    """
    tz = pytz.timezone("Europe/Athens")
    now = datetime.datetime.now(tz)
    return get_current_scheduled_time(now)

def calculate_price(product, scheduled_time):
    """
    Computes the price using linear interpolation based on the scheduled time:
    
    f(t) = start_price + (end_price - start_price) * ((t - t_start) / (t_end - t_start))
    
    The calculation uses the common scheduled time.
    """
    cycle_start, cycle_end = get_cycle(scheduled_time)
    total_duration = (cycle_end - cycle_start).total_seconds()
    elapsed = (scheduled_time - cycle_start).total_seconds()
    fraction = elapsed / total_duration
    price = product["start_price"] + (product["end_price"] - product["start_price"]) * fraction
    return price

# --- Main Demo: Store Page ---
st.title("Welcome to Eco Store")

# Use a placeholder to refresh the store layout every UPDATE_INTERVAL seconds.
store_placeholder = st.empty()

while True:
    tz = pytz.timezone("Europe/Athens")
    now = datetime.datetime.now(tz)
    scheduled_time = get_global_scheduled_time()
    
    with store_placeholder.container():
        # Time Information at the top
        st.markdown(
            f"""
            <div class="time-info">
                <strong>Current Greek Time:</strong> {now.strftime('%H:%M:%S')}<br>
                <strong>Sale Price Calculation Time:</strong> {scheduled_time.strftime('%H:%M:%S')}
            </div>
            """, unsafe_allow_html=True
        )
        st.markdown("<hr>", unsafe_allow_html=True)
        
        st.header("Featured Products")
        
        # Arrange product cards in a grid (2 columns)
        cols = st.columns(2)
        for idx, product in enumerate(products):
            with cols[idx % 2]:
                st.markdown(f"""<div class="product-card">""", unsafe_allow_html=True)
                # Placeholder image (replace URL with real image if available)
                image_url = f"https://via.placeholder.com/300x200.png?text={product['name'].replace(' ', '+')}"
                st.image(image_url, use_column_width=True)
                st.markdown(f"<h3>{product['name']}</h3>", unsafe_allow_html=True)
                price = calculate_price(product, scheduled_time)
                st.markdown(f"<h4>Sale Price: €{price:.2f}</h4>", unsafe_allow_html=True)
                st.write("High-quality, sustainable, and ethically produced.")
                if st.button("Buy Now", key=f"buy_{product['name']}"):
                    st.success(f"Thank you for purchasing the {product['name']}!")
                st.markdown("</div>", unsafe_allow_html=True)
        
    time.sleep(UPDATE_INTERVAL)
    store_placeholder.empty()

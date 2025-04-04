import streamlit as st
import datetime
import random
import pandas as pd
import pytz
import time

# Set page configuration with a plant emoji favicon.
st.set_page_config(page_title="Eco Store", page_icon="🌱", layout="wide")

# Ενσωμάτωση custom CSS για ένα καθαρό, φιλικό look.
st.markdown(
    """
    <style>
    /* Γενικό background με ένα ελαφρύ gradient */
    .stApp {
        background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
    }
    /* Στυλ για τα headers */
    h1 {
        color: #2E7D32;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-align: center;
        padding-top: 1rem;
    }
    /* Στυλ για τις κάρτες προϊόντων */
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
    /* Στυλ για τα κουμπιά */
    .stButton>button {
        background-color: #66BB6A;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
    }
    /* Στυλ για την πληροφορία ώρας */
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

# Update interval σε δευτερόλεπτα
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

# Λίστα με URLs εικόνων από το GitHub (αντικαταστήστε τα URLs με τα δικά σας, μετά το raw/)
image_links = {
    "Eco Backpack": "https://raw.githubusercontent.com/theodoroskourtalis/georgia.demo/main/eco.bacpac-min.png",
    "Reusable Water Bottle": "https://raw.githubusercontent.com/theodoroskourtalis/georgia.demo/main/water.bottle-min.png",
    "Organic T-Shirt": "https://raw.githubusercontent.com/theodoroskourtalis/georgia.demo/main/organic.tshirt-min.png",
    "Eco Sunglasses": "https://raw.githubusercontent.com/theodoroskourtalis/georgia.demo/main/trannos.west.png"
}

def get_cycle(current_dt):
    """
    Ορίζει τον ενεργό κύκλο τιμολόγησης.
    Ο κύκλος ξεκινά στις 05:00 (Europe/Athens) και διαρκεί 22 ώρες.
    Αν η τρέχουσα ώρα είναι πριν τις 05:00, ο κύκλος ξεκινάει χθες στις 05:00.
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
    Στρογγυλοποιεί το χρόνο που πέρασε από την έναρξη του κύκλου στο πλησιέστερο UPDATE_INTERVAL.
    Δηλαδή ορίζει έναν κοινό χρόνο υπολογισμού για όλους τους χρήστες.
    """
    cycle_start, _ = get_cycle(current_dt)
    delta = (current_dt - cycle_start).total_seconds()
    floor_delta = int(delta // UPDATE_INTERVAL) * UPDATE_INTERVAL
    scheduled_time = cycle_start + datetime.timedelta(seconds=floor_delta)
    return scheduled_time

@st.cache_data(ttl=UPDATE_INTERVAL)
def get_global_scheduled_time():
    """
    Επιστρέφει τον παγκόσμιο κοινό χρόνο υπολογισμού (πλησιέστερος στο UPDATE_INTERVAL)
    ώστε όλοι οι χρήστες να βλέπουν την ίδια τιμή.
    """
    tz = pytz.timezone("Europe/Athens")
    now = datetime.datetime.now(tz)
    return get_current_scheduled_time(now)

def calculate_price(product, scheduled_time):
    """
    Υπολογίζει την τιμή χρησιμοποιώντας γραμμική παρεμβολή με βάση τον κοινό χρόνο υπολογισμού:
    
    $$ f(t) = \text{start\_price} + (\text{end\_price} - \text{start\_price}) \times \frac{t - t_{\text{start}}}{t_{\text{end}} - t_{\text{start}}} $$
    
    Χρησιμοποιεί τον κοινό χρόνο υπολογισμού.
    """
    cycle_start, cycle_end = get_cycle(scheduled_time)
    total_duration = (cycle_end - cycle_start).total_seconds()
    elapsed = (scheduled_time - cycle_start).total_seconds()
    fraction = elapsed / total_duration
    price = product["start_price"] + (product["end_price"] - product["start_price"]) * fraction
    return price

# --- Sidebar Navigation για τις Σελίδες Demo και Console ---
page = st.sidebar.selectbox("Select Page", options=["Demo", "Console"])
tz = pytz.timezone("Europe/Athens")

if page == "Demo":
    st.title("Welcome to Eco Store")
    store_placeholder = st.empty()
    
    while True:
        now = datetime.datetime.now(tz)
        scheduled_time = get_global_scheduled_time()
        
        with store_placeholder.container():
            # Εμφάνιση χρόνου
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
            
            # Διάταξη προϊόντων σε 2 στήλες
            cols = st.columns(2)
            for idx, product in enumerate(products):
                with cols[idx % 2]:
                    st.markdown('<div class="product-card">', unsafe_allow_html=True)
                    
                    # Εμφάνιση εικόνας από το GitHub
                    image_url = image_links.get(product["name"], "https://via.placeholder.com/300x200.png")
                    st.image(image_url, use_container_width=True)
                    
                    st.markdown(f"<h3>{product['name']}</h3>", unsafe_allow_html=True)
                    price = calculate_price(product, scheduled_time)
                    st.markdown(f"<h4>Sale Price: €{price:.4f}</h4>", unsafe_allow_html=True)
                    st.write("High-quality, sustainable, and ethically produced.")
                    
                    # Χρήση μοναδικού key για το κουμπί, προσθέτοντας το scheduled time
                    button_key = f"buy_{product['name']}_{idx}_{scheduled_time.strftime('%H%M%S')}"
                    if st.button("Buy Now", key=button_key):
                        st.success(f"Thank you for purchasing the {product['name']}!")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        
        time.sleep(UPDATE_INTERVAL)
        store_placeholder.empty()

elif page == "Console":
    st.title("Console: Detailed Analytics & Full Price History")
    
    # Δημιουργία placeholders για το δυναμικό περιεχόμενο.
    latex_placeholder = st.empty()
    details_placeholder = st.empty()
    table_placeholder = st.empty()
    download_placeholder = st.empty()
    
    while True:
        now = datetime.datetime.now(tz)
        cycle_start, cycle_end = get_cycle(now)
        total_duration = (cycle_end - cycle_start).total_seconds()
        scheduled_time = get_global_scheduled_time()
        elapsed_time = (scheduled_time - cycle_start).total_seconds()
        
        latex_placeholder.latex(
            r"f(t) = \text{start\_price} + (\text{end\_price} - \text{start\_price}) \times \frac{t - t_{\text{start}}}{t_{\text{end}} - t_{\text{start}}}"
        )
        details = f"""
**Cycle Details:**

- **Cycle Start (tₛ):** {cycle_start.strftime("%H:%M:%S")}
- **Cycle End (tₑ):** {cycle_end.strftime("%H:%M:%S")}
- **Scheduled Calculation Time (t):** {scheduled_time.strftime("%H:%M:%S")}
- **Elapsed Time:** {elapsed_time:.8f} seconds
- **Total Duration:** {total_duration:.8f} seconds
        """
        details_placeholder.markdown(details)
        
        # Δημιουργία πίνακα τιμών από την έναρξη του κύκλου μέχρι το scheduled time (βήμα UPDATE_INTERVAL)
        schedule = []
        current_time = cycle_start
        while current_time <= scheduled_time:
            row = {"Time": current_time.strftime("%H:%M:%S")}
            for product in products:
                delta = (current_time - cycle_start).total_seconds()
                fraction = delta / total_duration
                price = product["start_price"] + (product["end_price"] - product["start_price"]) * fraction
                row[product["name"]] = f"{price:.4f} €"
            schedule.append(row)
            current_time += datetime.timedelta(seconds=UPDATE_INTERVAL)
        
        df = pd.DataFrame(schedule)
        if not df.empty:
            if len(df) > 100:
                table_placeholder.markdown("### First 100 Entries")
                table_placeholder.dataframe(df.head(100), use_container_width=True)
                table_placeholder.markdown("### Last 100 Entries")
                table_placeholder.dataframe(df.tail(100), use_container_width=True)
            else:
                table_placeholder.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        download_placeholder.download_button(
            label="Download Full Price History",
            data=csv,
            file_name="price_history.csv",
            mime="text/csv",
            key=f"download_{int(time.time())}"
        )
        
        time.sleep(UPDATE_INTERVAL)
        latex_placeholder.empty()
        details_placeholder.empty()
        table_placeholder.empty()
        download_placeholder.empty()

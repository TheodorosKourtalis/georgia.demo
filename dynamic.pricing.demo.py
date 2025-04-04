#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  4 23:51:31 2025

@author: thodoreskourtales
"""

import streamlit as st
import datetime
import time
import random

# Check login status using session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Please Log In")
    username = st.text_input("Enter your username:")
    if st.button("Log In"):
        st.session_state.logged_in = True
        st.session_state.username = username
        st.experimental_rerun()

# Once logged in, display login time and start the dynamic pricing
if st.session_state.logged_in:
    st.title("Dynamic Product Pricing")
    login_time = datetime.datetime.now()
    st.write(f"Welcome, {st.session_state.username}!")
    st.write("Login time:", login_time.strftime("%H:%M:%S"))
    
    # Define two products with starting prices
    products = [
        {"name": "Product A", "start_price": 100},
        {"name": "Product B", "start_price": 200}
    ]
    
    # For each product, calculate a random ending price in the specified range
    for product in products:
        product["end_price"] = random.uniform(0.30 * product["start_price"], 0.70 * product["start_price"])
    
    st.write("The prices will degrade dynamically over 60 seconds (each second = 10 minutes).")
    
    # Create a placeholder for price updates
    price_placeholder = st.empty()
    
    # Run a loop to update the prices every second for 60 seconds
    for second in range(61):  # from 0 to 60 seconds
        price_info = ""
        for product in products:
            start_price = product["start_price"]
            end_price = product["end_price"]
            # Linear degradation calculation: current price is interpolated based on elapsed seconds
            current_price = start_price + (end_price - start_price) * (second / 60)
            price_info += f"{product['name']}: {current_price:.2f} €\n"
        price_placeholder.text(price_info)
        time.sleep(1)

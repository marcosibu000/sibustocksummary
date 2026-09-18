import streamlit as st
from supabase import create_client
import os

st.set_page_config(page_title="Marcoco Stock Check", layout="mobile")

# Connect to Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

st.title(" Marcoco Stock Checker")

# Search box
search = st.text_input("Search Product Code or Name")

if search:
    # Query Supabase
    result = supabase.table("inventory_summary").select("*").ilike("item", f"%{search}%").limit(20).execute()
    
    for item in result.data:
        with st.container():
            # Display Image
            if item.get('image_url'):
                st.image(item['image_url'], width=150)
            
            st.subheader(item.get('item', 'N/A'))
            st.write(f"**Stock:** {item.get('stock', 0)}")
            st.write(f"**Price A:** RM {item.get('price_a', 0)}")
            st.write(f"**Price B:** RM {item.get('price_b', 0)}")
            st.divider()
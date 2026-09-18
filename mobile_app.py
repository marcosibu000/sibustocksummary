import streamlit as st
import os
from supabase import create_client
import pandas as pd

# 1. Page Configuration (Fixed: removed invalid "mobile" layout)
st.set_page_config(page_title="Marcoco Stock Check", page_icon="📦", layout="wide")

# 2. Connect to Supabase using Environment Variables
# Streamlit Cloud will inject these from the "Advanced settings"
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    st.error("⚠️ Missing Supabase credentials. Please check Streamlit Advanced Settings.")
    st.stop()

supabase = create_client(supabase_url, supabase_key)

# 3. UI Layout
st.title("📦 Marcoco Stock Checker")
st.markdown("Search for product codes or names to check real-time stock and pricing.")

# Search box
search_query = st.text_input("🔍 Enter Product Code or Name", placeholder="e.g., 23-801BFS")

if search_query:
    with st.spinner("Fetching data from cloud..."):
        try:
            # Query the inventory_summary table we synced earlier
            # Using ilike for case-insensitive partial matching
            result = supabase.table("inventory_summary").select("*").ilike("item", f"%{search_query}%").limit(50).execute()
            
            data = result.data
            
            if not data:
                st.info("No products found matching your search.")
            else:
                # Display results in a mobile-friendly grid
                for item in data:
                    with st.container():
                        # Create two columns: Image on left, Details on right
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            # Construct image URL (adjust the base URL if needed)
                            # Assuming the image filename matches the IRCode or item code
                            image_code = item.get('item', '').replace(' ', '') # Clean up spaces for URL
                            image_url = f"https://sibu.marcoco.uk/{image_code}.jpg"
                            
                            st.image(image_url, width=150, use_container_width=False)
                        
                        with col2:
                            st.subheader(item.get('item', 'Unknown Item'))
                            st.write(f"**Description:** {item.get('description', 'N/A')}")
                            
                            # Stock Info
                            stock = item.get('stock', 0)
                            stock_color = "green" if stock > 0 else "red"
                            st.markdown(f"**Stock:** <span style='color:{stock_color}; font-weight:bold;'>{stock}</span>", unsafe_allow_html=True)
                            
                            # Prices
                            st.write(f"**Price A:** RM {item.get('price_a', 0):,.2f}")
                            st.write(f"**Price B:** RM {item.get('price_b', 0):,.2f}")
                            
                            st.divider()
                            
        except Exception as e:
            st.error(f"Database error: {str(e)}")
else:
    st.info("👆 Please enter a product code or name above to begin searching.")

# Footer
st.markdown("---")
st.caption("Marcoco Inventory System v1.0 | Powered by Supabase & Streamlit")
import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
from google.oauth2 import service_account

# --- 1. 頁面設定 ---
st.set_page_config(page_title="功課紀錄本", page_icon="📚", layout="centered")
st.title("📚 學生功課紀錄本")

# CSS: 樣式設定 (強制黑色文字)
st.markdown("""
<style>
    .hw-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .hw-done {
        border-left: 5px solid #00cc66 !important;
        background-color: #f0fff4 !important;
    }
    /* 確保文字在深色模式下可見 */
    .hw-text { color: #000000 !important; }
    .hw-sub { 
        font-weight: bold; 
        font-size: 1.1em; 
        color: #333333 !important; 
    }
    .hw-meta { font-size: 0.85em; color: #666666 !important; }
    
    .block-container { padding-bottom: 50px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 連線設定 ---
def get_connection():
    try:
        # 拆解變數以防斷行
        s_conn = st.secrets["connections"]["gsheets"]
        key_info = s_conn["service_account_info"]
        sheet_url = s_conn["spreadsheet"]
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = service_account.Credentials.from_service_account_info(
            key_info, scopes=scopes
        )
        client = gspread.authorize(creds)
        return client.open_by_url(sheet_url).sheet1
    except Exception as e:
        st.error(f"連線失敗: {e}")
        st

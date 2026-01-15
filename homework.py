import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
from google.oauth2 import service_account

# --- 1. 頁面設定 ---
st.set_page_config(page_title="功課紀錄本", page_icon="📚", layout="centered")
st.title("📚 學生功課紀錄本")

# CSS: 美化卡片與狀態
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
    .hw-subject { font-weight: bold; font-size: 1.1em; color: #333; }
    .hw-date { font-size: 0.85em; color: #666; }
    .hw-content { margin-top: 8px; font-size: 1em; }
    .block-container { padding-bottom: 50px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 連線設定 ---
def get_connection():
    try:
        # 拆開寫，避免複製時斷行
        conn = st.secrets["connections"]["gsheets"]
        info = conn["service_account_info"]
        url = conn["spreadsheet"]
        
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        return client.open_by_url(url).sheet1
    except Exception as e:
        st.error(f"連線失敗: {e}")
        st.stop()

sheet = get_connection()

# 讀取資料
try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data if data else [], columns=["ID", "科目", "指派日期", "繳交期限", "內容", "備註", "狀態"])
except:
    df = pd.DataFrame()

# --- 3. 介面分頁 ---
tab1, tab2 = st.tabs(["📝 登記作業", "📋 作業清單"])

# ==========================================
# 分頁 1: 登記作業
# ==========================================
with tab1:
    st.subheader("新增一項作業")
    
    with st.form("hw_form", clear_on_submit=True):
        subjects = [
            "國文", "英文", "數學",
            "自然 - 生物", "自然 - 物理",
            "社會 - 地理", "社會 - 歷史", "社會 - 公民"
        ]
        col_sub, col_date = st.columns([1, 1])
        with col_sub:
            subject = st.selectbox("科目", subjects)
        with col_date:
            assign_date = st.date_input("指派日期", date.today())
        
        st.write("繳交期限")
        c1, c2 = st.columns(2)
        with c1:
            due_date = st.date_input("截止日期", date.today())
        with c2:
            due_time = st.time_input("截止時間", datetime.now().time())
        
        content = st.text_
                            
                            # 2. 搜尋這個 ID 在第幾行 (轉成字串比對最安全)
                            # index() 也是從 0 開始，所以要 +1
                            # 但因為 all_ids 包含標題，所以其實 ID=1 應該在 index 1 (Row 2)
                            # 所以這裡的 logic 是：找到這個 ID 在 list 中的位置，該位置+1 就是 Row Number
                            search_id = str(row
                        sheet.update_cell(target_row, 7, "已完成") # 更新G欄狀態
                        st.toast("太棒了！又完成一項作業！")
                        st.rerun()
    else:
        st.info("還沒有任何作業紀錄喔！")
      

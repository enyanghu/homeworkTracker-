import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
from google.oauth2 import service_account

# --- 1. 頁面設定 ---
st.set_page_config(page_title="功課紀錄本", page_icon="📚", layout="centered")
st.title("📚 學生功課紀錄本")

# CSS: 樣式設定 (強制黑色文字，解決深色模式看不見的問題)
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
    .hw-text { color: #000000 !important; font-size: 1em; margin-top: 8px; }
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
        st.stop()

sheet = get_connection()

# --- 讀取資料 ---
try:
    raw = sheet.get_all_values()
    cols = ["ID", "科目", "指派日期", "繳交期限", "內容", "備註", "狀態"]
    
    if len(raw) > 1:
        # 有資料：跳過標題列
        df = pd.DataFrame(raw[1:], columns=cols)
        df = df.fillna("") # 填補空值
    else:
        # 無資料：建立空表
        df = pd.DataFrame(columns=cols)
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
        subs = [
            "國文", "英文", "數學",
            "自然 - 生物", "自然 - 物理",
            "社會 - 地理", "社會 - 歷史", "社會 - 公民"
        ]
        c1, c2 = st.columns([1, 1])
        with c1:
            subject = st.selectbox("科目", subs)
        with c2:
            assign_date = st.date_input("指派日期", date.today())
        
        st.write("繳交期限")
        c3, c4 = st.columns(2)
        with c3:
            due_date = st.date_input("截止日期", date.today())
        with c4:
            due_time = st.time_input("截止時間", datetime.now().time())
        
        content = st.text_area("作業內容", height=100)
        note = st.text_input("備註 (選填)")
        
        # 按鈕
        submitted = st.form_submit_button("💾 儲存", use_container_width=True)

    if submitted and content:
        try:
            # 資料準備
            t_str = due_time.strftime('%H:%M')
            due_str = f"{due_date} {t_str}"
            a_str = str(assign_date)
            new_id = len(df) + 1
            
            # 寫入 (拆成短行)
            row_data = [
                new_id, subject, a_str, due_str, content, note, "未完成"
            ]
            sheet.append_row(row_data)
            
            st.success(f"已新增：{subject}")
            st.rerun()
        except Exception as e:
            st.error(f"儲存失敗：{e}")

# ==========================================
# 分頁 2: 作業清單
# ==========================================
with tab2:
    st.subheader("待辦作業一覽")
    
    if not df.empty:
        opts = ["全部", "未完成", "已完成"]
        filter_status = st.radio("顯示狀態", opts, horizontal=True)
        
        # 篩選資料
        df_show = df.copy()
        if filter_status == "未完成":
            df_show = df_show[df_show['狀態'] != "已完成"]
        elif filter_status == "已完成":
            df_show = df_show[df_show['狀態'] == "已完成"]
            
        if df_show.empty:
            st.info("沒有相關作業 🎉")
        else:
            for i, row in df_show.iterrows():
                # 取出變數 (簡短化)
                rid = str(row['ID'])
                sub = row['科目']
                d_day = row['繳交期限']
                cont = row['內容']
                nt = row['備註']
                stat = row['狀態']
                
                is_done = (stat == "已完成")
                icon = "✅" if is_done else "⏳"
                cls_name = "hw-card hw-done" if is_done else "hw-card"

                # --- HTML 拼裝 (極短句模式，防止手機複製斷行) ---
                h = ""
                h += f'<div class="{cls_name}">'
                h += f'<div class="hw-sub">{icon} {sub}</div>'
                h += f'<div class="hw-meta">期限：<b>{d_day}</b></div>'
                h += f'<div class="hw-text">{cont}</div>'
                h += f'<div style="color:gray; font-size:0.8em;">備註：{nt}</div>'
                h += '</div>'
                
                st.markdown(h, unsafe_allow_html=True)
                
                # --- 按鈕功能 ---
                if not is_done:
                    if st.button("完成", key=f"btn_{rid}"):
                        try:
                            # 重新抓取 ID 欄位
                            id_list = sheet.col_values(1)
                            # 確保都是字串
                            str_ids = [str(x) for x in id_list]
                            
                            if rid in str_ids:
                                # 找到位置 (+1 是因為 list index 從 0 開始)
                                row_idx = str_ids.index(rid) + 1
                                # 更新第 7 欄 (狀態)
                                sheet.update_cell(row_idx, 7, "已完成")
                                st.toast("完成作業！")
                                st.rerun()
                            else:
                                st.error("找不到該 ID")
                        except Exception as e:
                            st.error(f"更新錯誤: {e}")
    else:
        st.info("目前沒有資料")

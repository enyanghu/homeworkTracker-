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
    /* 強制指定標題為深灰色，避免在深色模式下變白 */
    .hw-subject { font-weight: bold; font-size: 1.1em; color: #333333 !important; }
    
    /* 強制指定日期為灰色 */
    .hw-date { font-size: 0.85em; color: #666666 !important; }
    
    /* 👇 修正重點在這裡！強制指定內容為黑色，並保留換行 */
    .hw-content { 
        margin-top: 8px; 
        font-size: 1em; 
        color: #000000 !important; 
        font-weight: 500;
        white-space: pre-wrap; /* 讓內容可以換行顯示 */
    }
    
    .block-container { padding-bottom: 50px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 連線設定 ---
def get_connection():
    try:
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

# --- 讀取資料 (自動適應版) ---
try:
    # 使用 get_all_values() 抓取原始資料，避免標題對不上的問題
    raw_data = sheet.get_all_values()
    
    if len(raw_data) > 1:
        headers = raw_data[0]
        rows = raw_data[1:]
        # 強制指定欄位名稱，對應 Google Sheet 的第 1 到 7 欄
        df = pd.DataFrame(rows, columns=["ID", "科目", "指派日期", "繳交期限", "內容", "備註", "狀態"])
        df = df.fillna("")
    else:
        df = pd.DataFrame(columns=["ID", "科目", "指派日期", "繳交期限", "內容", "備註", "狀態"])
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
        
        content = st.text_area("作業內容", height=100, placeholder="例如：講義 P.20 ~ P.25")
        note = st.text_input("備註 (選填)", placeholder="例如：要記得帶圖畫紙")
        
        submitted = st.form_submit_button("💾 儲存作業", use_container_width=True)

    if submitted and content:
        try:
            due_str = f"{due_date} {due_time.strftime('%H:%M')}"
            assign_str = str(assign_date)
            new_id = len(df) + 1
            
            # 寫入
            sheet.append_row([
                new_id, subject, assign_str, due_str, content, note, "未完成"
            ])
            st.success(f"已新增：{subject} 作業！")
            st.rerun()
        except Exception as e:
            st.error(f"儲存失敗：{e}")

# ==========================================
# 分頁 2: 作業清單
# ==========================================
with tab2:
    st.subheader("待辦作業一覽")
    
    if not df.empty:
        filter_status = st.radio("顯示狀態", ["全部", "未完成", "已完成"], horizontal=True)
        
        df_display = df.copy()
        if filter_status == "未完成":
            df_display = df_display[df_display['狀態'] != "已完成"]
        elif filter_status == "已完成":
            df_display = df_display[df_display['狀態'] == "已完成"]
            
        if df_display.empty:
            st.info("目前沒有相關作業 🎉")
        else:
            for index, row in df_display.iterrows():
                status_class = "hw-done" if row['狀態'] == "已完成" else ""
                status_icon = "✅" if row['狀態'] == "已完成" else "⏳"
                
                # HTML 卡片顯示
                html_card = f"""
                <div class="hw-card {status_class}">
                    <div class="hw-subject">{status_icon} {row['科目']}</div>
                    <div class="hw-date">
                        📅 指派：{row['指派日期']} <br>
                        ⏰ 期限：<b>{row['繳交期限']}</b>
                    </div>
                    <div class="hw-content">{row['內容']}</div>
                    <div style="color:gray; font-size:0.8em; margin-top:5px;">備註：{row['備註']}</div>
                </div>
                """
                st.markdown(html_card, unsafe_allow_html=True)
                
                # 按鈕與更新邏輯
                if row['狀態'] != "已完成":
                    if st.button("標記為完成", key=f"done_{row['ID']}"):
                        try:
                            all_ids = sheet.col_values(1)
                            search_id = str(row['ID'])
                            str_ids = [str(x) for x in all_ids]
                            
                            if search_id in str_ids:
                                target_row = str_ids.index(search_id) + 1
                                # 更新第 7 欄 (狀態)
                                sheet.update_cell(target_row, 7, "已完成")
                                st.toast("太棒了！又完成一項作業！")
                                st.rerun()
                            else:
                                st.error("找不到這筆作業 ID")
                                
                        except Exception as e:
                            st.error(f"更新失敗: {e}")
    else:
        st.info("還沒有任何作業紀錄喔！")
                            # 2. 定位並更新
                            search_id = str(row['ID'])
                            str_ids = [str(x) for x in all_ids]
                            
                            if search_id in str_ids:
                                target_row = str_ids.index(search_id) + 1
                                # 這裡更新的是第 7 欄 (G欄)，請確認 G欄標題是「狀態」
                                sheet.update_cell(target_row, 7, "已完成")
                                st.toast("太棒了！又完成一項作業！")
                                st.rerun()
                            else:
                                st.error("找不到這筆作業 ID")
                                
                        except Exception as e:
                            st.error(f"更新失敗: {e}")
    else:
        st.info("還沒有任何作業紀錄喔！")

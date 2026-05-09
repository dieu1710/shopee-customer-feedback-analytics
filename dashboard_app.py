import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import concurrent.futures
from google import genai

# Cấu hình trang
st.set_page_config(page_title="DASHBOARD", layout="wide")
st.title("📊 CUSTOMER FEEDBACK ANALYTICS")
st.markdown("---")

# Mapping tên sản phẩm & Khía cạnh
PRODUCT_NAMES = {1: "Dosen", 2: "Gutek", 3: "Ugreen", 4: "Baseus", 5: "Goojodoq", 6: "SiamBoost", 7: "Azeada", 8: "Orsen", 9: "Uneed", 10: "Hoco"}
ASPECT_NAMES = {'DungLuong': 'Dung lượng', 'TocDoSac': 'Tốc độ sạc', 'NhietDo': 'Nhiệt độ', 'ThietKe': 'Thiết kế', 'KichThuoc': 'Kích thước', 'CongKetNoi': 'Cổng kết nối', 'GiaCa': 'Giá cả', 'DichVu': 'Dịch vụ'}
KHIA_CANH_CHINH = list(ASPECT_NAMES.keys())
COLOR_MAP = {'Tích cực': '#00CC96', 'Tiêu cực': '#EF553B', 'Trung lập': '#636EFA'}

@st.cache_data
def load_data():
    all_data = []
    for i in range(1, 11):
        file_path = os.path.join(str(i), "shopee_final_dataset_absa.xlsx")
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
                df['Ma_San_Pham'] = PRODUCT_NAMES.get(i, f"SP {i}")
                all_data.append(df)
            except: pass
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

@st.cache_data
def load_data_super_strict():
    all_data = []
    for i in range(1, 11):
        file_path = os.path.join(str(i), "shopee_reviews_super_strict.xlsx")
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
                df['Ma_San_Pham'] = PRODUCT_NAMES.get(i, f"SP {i}")
                all_data.append(df)
            except: pass
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

df = load_data()
df_super_strict = load_data_super_strict()

if df.empty:
    st.error("❌ Không tìm thấy dữ liệu! Hãy đảm bảo 10 folder đã chứa file kết quả.")
else:
    # --- Menu Sidebar ---
    st.sidebar.header("Lọc dữ liệu")
    
    # 1. TẠO DANH SÁCH SẢN PHẨM (ĐÃ XÓA HOÀN TOÀN TỪ "TẤT CẢ")
    danh_sach_sp = sorted(df['Ma_San_Pham'].unique(), key=lambda x: list(PRODUCT_NAMES.values()).index(x) if x in PRODUCT_NAMES.values() else 999)
    sp_chon = st.sidebar.selectbox("Chọn sản phẩm", danh_sach_sp)
    
    st.sidebar.markdown("---")
    st.sidebar.header("Tích hợp AI Gemini")
    api_key = st.sidebar.text_input("🔑 Nhập Gemini API Key", type="password", help="Dùng SDK google.genai mới nhất.")

    # 2. LỌC DỮ LIỆU THEO ĐÚNG SẢN PHẨM ĐƯỢC CHỌN
    df_filtered = df[df['Ma_San_Pham'] == sp_chon]

    df_aspect = df_filtered.copy()
    if not df_aspect.empty and 'Khia_Canh' in df_aspect.columns:
        df_aspect['Khia_Canh'] = df_aspect['Khia_Canh'].str.split(', ')
        df_aspect = df_aspect.explode('Khia_Canh')
        df_aspect['Khia_Canh'] = df_aspect['Khia_Canh'].str.strip()
        df_aspect = df_aspect[df_aspect['Khia_Canh'].isin(KHIA_CANH_CHINH)]
        df_aspect['Khia_Canh_VN'] = df_aspect['Khia_Canh'].map(ASPECT_NAMES)

    # --- KPI tổng quan ---
    tong_so = len(df_filtered)
    tich_cuc = len(df_filtered[df_filtered['Cam_Xuc'] == 'Tích cực'])
    tieu_cuc = len(df_filtered[df_filtered['Cam_Xuc'] == 'Tiêu cực'])
    ty_le_tc = round((tich_cuc / tong_so * 100) if tong_so > 0 else 0, 1)

    col1, col2, col3, col4, col5 = st.columns([1,1,1,1,2])
    col1.metric("Số bình luận", f"{tong_so:,}")
    col2.metric("🟢 Tích cực", f"{tich_cuc:,}")
    col3.metric("🔴 Tiêu cực", f"{tieu_cuc:,}")
    col4.metric("⭐ Điểm trung bình", f"{round(df_filtered['rating_star'].mean(), 1)} / 5")
    
    with col5:
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = ty_le_tc,
            number = {'suffix': "%"},
            title = {'text': "Chỉ số hài lòng", 'font': {'size': 14}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': "#00CC96" if ty_le_tc > 60 else "#EF553B"},
                'steps': [{'range': [0, 40], 'color': "#FFD1D1"}, {'range': [40, 70], 'color': "#FFF2CC"}, {'range': [70, 100], 'color': "#D5E8D4"}]
            }
        ))
        fig_gauge.update_layout(height=180, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("---")

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.subheader("1. Tỷ lệ cảm xúc tổng thể")
        pie_data = df_filtered['Cam_Xuc'].value_counts().reset_index()
        pie_data.columns = ['Cảm xúc', 'Số lượng']
        fig_pie = px.pie(pie_data, values='Số lượng', names='Cảm xúc', hole=0.4, color='Cảm xúc', color_discrete_map=COLOR_MAP)
        st.plotly_chart(fig_pie, use_container_width=True)

    with row1_col2:
        st.subheader("2. Biểu đồ mạng nhện")
        if not df_aspect.empty:
            radar_data = df_aspect.groupby(['Khia_Canh_VN', 'Cam_Xuc']).size().unstack(fill_value=0)
            if 'Tích cực' not in radar_data: radar_data['Tích cực'] = 0
            radar_data['Tong'] = radar_data.sum(axis=1)
            radar_data['% Tích cực'] = (radar_data['Tích cực'] / radar_data['Tong']) * 100
            fig_radar = go.Figure(data=go.Scatterpolar(r=radar_data['% Tích cực'].tolist(), theta=radar_data.index.tolist(), fill='toself', line_color='#636EFA'))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("Chưa đủ dữ liệu vẽ mạng nhện.")

    st.markdown("---")

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        st.subheader("3. Chi tiết cảm xúc theo khía cạnh")
        if not df_aspect.empty:
            aspect_sentiment = df_aspect.groupby(['Khia_Canh_VN', 'Cam_Xuc']).size().reset_index(name='Số lượng')
            fig_aspect = px.bar(aspect_sentiment, y='Khia_Canh_VN', x='Số lượng', color='Cam_Xuc', orientation='h', barmode='stack', color_discrete_map=COLOR_MAP)
            fig_aspect.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_aspect, use_container_width=True)

    with row2_col2:
        st.subheader("4. Bản đồ cấu trúc phàn nàn / khen ngợi")
        if not df_aspect.empty:
            fig_tree = px.treemap(df_aspect, path=[px.Constant("Dữ liệu"), 'Cam_Xuc', 'Khia_Canh_VN'], color='Cam_Xuc', color_discrete_map=COLOR_MAP)
            fig_tree.update_traces(root_color="lightgrey")
            st.plotly_chart(fig_tree, use_container_width=True)

    st.markdown("---")

    row3_col1, row3_col2 = st.columns(2)
    with row3_col1:
        st.subheader("5. Phân bố sao đánh giá")
        star_data = df_filtered['rating_star'].value_counts().sort_index().reset_index()
        star_data.columns = ['Số sao', 'Số lượng']
        all_stars = pd.DataFrame({'Số sao': [1, 2, 3, 4, 5]})
        star_data = pd.merge(all_stars, star_data, on='Số sao', how='left').fillna(0)
        fig_star = px.bar(star_data, x='Số sao', y='Số lượng', text='Số lượng', color='Số sao', color_continuous_scale='Blues')
        fig_star.update_traces(textposition='outside', texttemplate='%{text}')
        fig_star.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=1), yaxis_title="Số lượng")
        st.plotly_chart(fig_star, use_container_width=True)

    with row3_col2:
        st.subheader("6. Ma trận điểm yếu (% phàn nàn)")
        if not df_aspect.empty:
            df_negative = df_aspect[df_aspect['Cam_Xuc'] == 'Tiêu cực']
            if not df_negative.empty:
                pivot_neg = pd.crosstab(df_negative['Ma_San_Pham'], df_negative['Khia_Canh_VN'], normalize='index') * 100
                fig_heat = px.imshow(pivot_neg.round(1), text_auto='.1f', aspect="auto", color_continuous_scale='Reds', labels=dict(x="Khía cạnh phàn nàn", y="Sản phẩm", color="Tỷ lệ %"))
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.success("🎉 Sản phẩm này không có bình luận tiêu cực nào!")
        else:
            st.info("Chưa đủ dữ liệu.")

# ==============================================================================
    # 7 & 8. TÍNH TOÁN DỮ LIỆU VÀ CHẠY AI SONG SONG (MULTITHREADING)
    # ==============================================================================
    # Mục 7 và 8 đã đổi chỗ cho nhau
    # --- Chuẩn bị dữ liệu Mục 7 ---
    critical_issues = pd.Series(dtype=float)
    if 'df_negative' in locals() and not df_negative.empty:
        neg_pct = df_negative['Khia_Canh_VN'].value_counts(normalize=True) * 100
        critical_issues = neg_pct[neg_pct > 13.0]

    # --- Chuẩn bị dữ liệu Mục 8 ---
    impact_df = pd.DataFrame()
    if 'df_aspect' in locals() and not df_aspect.empty:
        impact_df = df_aspect[df_aspect['Cam_Xuc'] == 'Tiêu cực'].groupby('Khia_Canh_VN').agg(
            So_luong=('rating_star', 'count'),
            Sao_trung_binh=('rating_star', 'mean')
        ).reset_index()
        impact_df = impact_df[impact_df['So_luong'] >= 3].sort_values(by='Sao_trung_binh', ascending=True)

    # --- Khởi tạo biến lưu kết quả AI ---
    ai_result_7 = None
    ai_result_8 = None
    
    # --- Hàm gọi API chung ---
    def fetch_gemini(prompt_text):
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_text)
        return response.text

    # --- THỰC THI CHẠY AI SONG SONG ---
    if api_key:
        with st.spinner("🧠 AI Gemini đang phân tích dữ liệu đa luồng (chẩn đoán lỗi & phân tích tác động)..."):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_7 = None
                future_8 = None
                
                # Nạp luồng 1 (Mục 7)
                if not critical_issues.empty:
                    thong_ke_loi_7 = "\n".join([f"- Lỗi {idx+1}: {issue} ({pct:.1f}%)" for idx, (issue, pct) in enumerate(critical_issues.items())])
                    prompt_7 = f"""
                    Bạn là Giám đốc vận hành phân tích sạc dự phòng '{sp_chon}'.
                    Lỗi nghiêm trọng (>13%):
                    {thong_ke_loi_7}
                    Không cần giới thiệu, hãy vào luôn phần nội dung.
                   Yêu cầu trình bày súc tích bằng gạch đầu dòng:
                        1. Đưa ra phương án giải quyết dứt điểm cho TỪNG khía cạnh theo ĐÚNG thứ tự ưu tiên trên.
                        2. Lỗi nào có phần trăm (%) cao nhất phải được nhấn mạnh và đưa ra giải pháp mạnh tay nhất.
                        3. Lỗi có phần trăm thấp hơn thì đưa ra giải pháp về marketing/CSKH.
                        4. Trình bày cực kỳ súc tích bằng gạch đầu dòng, không dài dòng.
                    """
                    future_7 = executor.submit(fetch_gemini, prompt_7)
                
                # Nạp luồng 2 (Mục 8)
                if not impact_df.empty:
                    impact_stats = "\n".join([f"- Lỗi {row['Khia_Canh_VN']}: {row['Sao_trung_binh']:.2f} sao ({row['So_luong']} lượt)." for _, row in impact_df.iterrows()])
                    worst_aspect = impact_df.iloc[0]['Khia_Canh_VN']
                    best_aspect = impact_df.iloc[-1]['Khia_Canh_VN']
                    
                    prompt_8 = f"""
                    Phân tích tác động điểm sao của sạc '{sp_chon}'. Dữ liệu:
                    {impact_stats}
                    
                    Yêu cầu trả lời súc tích, ĐÚNG 3 gạch đầu dòng, KHÔNG mở/kết bài lan man:
                    - 🔴 Tử huyệt ({worst_aspect}): Nêu 1 câu lý do tại sao lỗi này khiến khách hàng tức giận chấm sao thấp nhất.
                    - 🟡 Điểm trừ nhẹ ({best_aspect}): Nêu 1 câu lý do tại sao khách vẫn châm chước chấm điểm khá hơn.
                    - 💡 Chốt hạ: 1 câu nhận định cốt lõi về tâm lý khách hàng khi đánh giá sản phẩm này.
                    """
                    future_8 = executor.submit(fetch_gemini, prompt_8)
                
                # Lấy kết quả
                if future_7:
                    try: ai_result_7 = future_7.result()
                    except Exception as e: ai_result_7 = f"❌ Lỗi API: {e}"
                
                if future_8:
                    try: ai_result_8 = future_8.result()
                    except Exception as e: ai_result_8 = f"❌ Lỗi API: {e}"

    # ==============================================================================
    # HIỂN THỊ GIAO DIỆN MỤC 8
    # ==============================================================================
    st.markdown("---")
    st.subheader("🎯 7. Phân tích tác động đến sự hài lòng")
    st.markdown("*Đo lường mức độ bất mãn của khách hàng: Khi chê một khía cạnh, họ sẽ chấm bao nhiêu sao?*")

    if not impact_df.empty:
        fig_impact = px.bar(impact_df, x='Sao_trung_binh', y='Khia_Canh_VN', orientation='h',
                            text='Sao_trung_binh', labels={'Sao_trung_binh': 'Điểm sao trung bình (1-5)', 'Khia_Canh_VN': 'Khía cạnh'},
                            color='Sao_trung_binh', color_continuous_scale='Reds_r')
        fig_impact.update_traces(texttemplate='%{text:.2f} ⭐', textposition='outside', cliponaxis=False)
        fig_impact.update_layout(xaxis=dict(range=[0, 5]), margin=dict(l=30, r=20, t=40, b=40), coloraxis_colorbar=dict(x=1.12))
        st.plotly_chart(fig_impact, use_container_width=True)

        if ai_result_8:
            if "❌ Lỗi" in ai_result_8: st.error(ai_result_8)
            else:
                st.info("💡 **Kết luận phân tích tác động từ AI:**")
                st.markdown(ai_result_8)
        elif not api_key:
            st.info("*(Nhập API Key để AI phân tích tâm lý chấm điểm của khách hàng)*")
            st.write(f"**Tử huyệt:** Khía cạnh **{impact_df.iloc[0]['Khia_Canh_VN']}** đang gây ra sự bất mãn lớn nhất, khiến khách hàng đánh giá rất thấp ở mức **{impact_df.iloc[0]['Sao_trung_binh']:.2f} sao**.")
    else:
        st.info("Cần ít nhất 3 bình luận tiêu cực cho một khía cạnh để thuật toán đo lường tác động khách quan.")

    # ==============================================================================
    # HIỂN THỊ GIAO DIỆN MỤC 7
    # ==============================================================================
    st.markdown("---")
    st.subheader("🤖 8. Hệ thống chẩn đoán & Đề xuất trọng tâm")
    
    if not critical_issues.empty:
        st.error(f"**⚠️ Cảnh báo:** Phát hiện **{len(critical_issues)} khía cạnh** vượt ngưỡng phàn nàn báo động (13%).")
        for issue, pct in critical_issues.items():
            st.write(f"- Khía cạnh **{issue}**: Chiếm **{pct:.1f}%** tổng số phàn nàn.")
        
        st.markdown("💡 **PHƯƠNG ÁN HÀNH ĐỘNG:**")
        if ai_result_7:
            if "❌ Lỗi" in ai_result_7: st.error(ai_result_7)
            else: st.markdown(ai_result_7)
        elif not api_key:
            st.info("*(Gợi ý: Nhập API Key ở thanh bên trái để AI tự động thiết kế chiến lược phân tích sâu hơn)*")
            for issue, pct in critical_issues.items():
                st.markdown(f"**🔴 ƯU TIÊN XỬ LÝ: {issue} ({pct:.1f}%)**")
                
                if issue == "Dung lượng":
                    st.write("- **Sản phẩm:** Kiểm tra lại cell pin thực tế từ xưởng, đảm bảo hiệu suất chuyển đổi (Rated Capacity) đạt chuẩn.")
                    st.write("- **Marketing:** Ghi rõ thông số 'Dung lượng định mức' trên mô tả Shopee để tránh khách hàng kỳ vọng sai lệch gây thất vọng.")
                elif issue == "Tốc độ sạc":
                    st.write("- **Kỹ thuật:** Rà soát tính tương thích của chip sạc nhanh (PD/QC) với các dòng smartphone đời mới nhất.")
                    st.write("- **CSKH:** Bổ sung hình ảnh hướng dẫn khách hàng dùng đúng loại củ và cáp sạc hỗ trợ công suất cao để kích hoạt sạc nhanh.")
                elif issue == "Nhiệt độ":
                    st.write("- **Kỹ thuật (Khẩn cấp):** Rủi ro an toàn cao! Kiểm tra ngay cảm biến NTC và mạch bảo vệ quá nhiệt để phòng chống cháy nổ.")
                    st.write("- **CSKH:** Chủ động liên hệ thu hồi hoặc đổi mới lập tức cho những khách hàng báo lỗi sạc bị nóng ran.")
                elif issue == "Thiết kế":
                    st.write("- **Sản phẩm:** Đánh giá lại chất liệu vỏ (cân nhắc chuyển từ nhựa bóng dễ trầy xước sang nhựa nhám chống bám vân tay).")
                    st.write("- **Marketing:** Cập nhật video và ảnh thực tế chụp cận cảnh bề mặt chất liệu lên gian hàng.")
                elif issue == "Kích thước":
                    st.write("- **Marketing:** Bổ sung ảnh chụp cầm sản phẩm trên tay, đặt cạnh điện thoại để khách hàng dễ hình dung trước khi đặt mua.")
                    st.write("- **CSKH:** Tư vấn kỹ về trọng lượng đối với những khách hàng có nhu cầu mua sạc gọn nhẹ để mang đi du lịch.")
                elif issue == "Cổng kết nối":
                    st.write("- **Kỹ thuật:** Rà soát khâu gia công phần cứng, khắc phục tình trạng lỏng lẻo hoặc kẹt rít của các cổng Type-C/USB-A.")
                    st.write("- **CSKH:** Thiết lập quy trình 1-đổi-1 nhanh chóng cho các đơn hàng báo lỗi cổng sạc chập chờn.")
                elif issue == "Giá cả":
                    st.write("- **Sales/Marketing:** Khảo sát lại mức giá của đối thủ cùng phân khúc. Thay vì giảm giá trực tiếp, có thể tạo các combo bán kèm (tặng cáp sạc, túi đựng) để tăng giá trị cảm nhận.")
                elif issue == "Dịch vụ":
                    st.write("- **Vận hành:** Siết chặt khâu đóng gói (thêm mút chống sốc), kiểm tra chéo vận đơn để chấm dứt tình trạng giao sai màu, sai mẫu.")
                    st.write("- **CSKH:** Tăng tốc độ phản hồi khiếu nại hư hỏng do vận chuyển, chủ động gửi tặng mã giảm giá đền bù để xoa dịu khách.")
                else:
                    st.write("- **Hành động:** Rà soát lại toàn bộ quy trình kiểm soát chất lượng (QA/QC) nội bộ cho khía cạnh này.")
    else:
        st.success("✅ **Trạng thái an toàn:** Các lỗi phân tán đều, không có khía cạnh nào vượt mức báo động (>13%).")
    # --- Dữ liệu thô ---
    st.markdown("---")
    st.subheader("🔍 9. Chi tiết bình luận thô")
    df_super_display = df_super_strict[df_super_strict['Ma_San_Pham'] == sp_chon]
    st.dataframe(df_super_display[['Ma_San_Pham', 'rating_star', 'review_text']])
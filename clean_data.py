import pandas as pd
import re
import os

def super_strict_filter_with_logs(input_file):
    print(f"--- BẮT ĐẦU LỌC VÀ LƯU NHẬT KÝ XÓA FILE: {input_file} ---")
    
    if not os.path.exists(input_file):
        print(f"❌ Không tìm thấy file {input_file}")
        return

    df = pd.read_excel(input_file, engine='openpyxl')
    initial_count = len(df)
    print(f"Số lượng dòng ban đầu: {initial_count}")

    # --- CÁC BỘ TỪ KHÓA ---
    pb_must_have = [
        'pin', 'sạc', 'mah', 'dung lượng', 'cáp', 'dây', 'cổng', 
        'type c', 'type-c', 'usb', 'vào điện', 'tụt', 'baseus', 
        'nóng', 'cầm tay', 'samsung', 'iphone', 'ipad', 'điện thoại',
        'tệ', 'giao hàng','giao', 'đóng gói', 'sac', 'mau', 'giá', 'sử dụng',
        'dùng', 'tiện', 'ổn', 'chất lượng', 'đáng tiền', 'hàng chính hãng', 'hàng xịn',
        'dỏm', 'giá', 'lâu', 'điện', 'màu', 'đẹp', 'xấu', 'màu', 'xước', 
        'trầy', 'vỏ', 'nhựa', 'kim loại', 'nhựa', 'màn_hình', 'thiết_kế', 'nặng', 
        'nhẹ', 'to', 'nhỏ', 'gọn', 'cầm tay', 'chắc tay', 'dày', 'mỏng', 'kích thước', 
        'dây', 'cáp', 'cổng', 'type c', 'usb', 'cắm', 'kết nối', 'đầu sạc', 'đầu cáp',
        'nóng', 'ấm', 'nhiệt', 'tỏa nhiệt', 'cháy', 'nổ', 'an toàn', 'mát', 'lạnh',
        'nhanh', 'chậm', 'tốc độ', 'vào điện', 'vào pin', 'sạc đầy', 'hiệu suất'
    ]

    kill_keywords = [
        'nhận xu', 'minh họa', 'chống trôi', 'không liên quan', 'k liên quan', 'xu'
        'da', 'mụn', 'thơm', 'mùi', 'kem', 'nivia', 'nivea',
        'áo', 'quần', 'váy', 'vải', 'size', 'mặc', 'form', 'giày', 'dép', 'chỉ thừa',
        'đồ ăn', 'thuốc', 'uống', 'bệnh', 'thymomodulin', 'chua', 'ngọt'
    ]

    generic_words = [
        
    ]

    def evaluate_review(text):
        if pd.isna(text): 
            return False, "Dữ liệu trống"
            
        text_lower = str(text).lower()
        
        # Lột bỏ văn mẫu Shopee
        text_lower = re.sub(r'(đúng với mô tả|chất lượng sản phẩm|thời gian giao hàng|hữu ích\?).*?:?', '', text_lower)
        text_padded = f" {text_lower} "

        # LỚP LỌC 1: Từ khóa tử hình
        for kw in kill_keywords:
            if f" {kw} " in text_padded:
                return False, f"Chứa từ khóa rác/lạc đề: '{kw}'"

        # LỚP LỌC 2: Từ khóa bắt buộc
        if not any(kw in text_padded for kw in pb_must_have):
            return False, "Không nhắc đến khía cạnh sạc dự phòng (pin, sạc, cáp...)"

        # LỚP LỌC 3: Đánh giá độ dài lõi
        core_text = text_lower
        for gw in generic_words:
            core_text = core_text.replace(gw, '')
            
        core_text = re.sub(r'[^a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]', ' ', core_text)
        meaningful_words = [w for w in core_text.split() if len(w) > 0]
        
        if len(meaningful_words) < 3:
            return False, "Bình luận quá chung chung/xã giao (không đủ ý)"

        return True, "Hợp lệ"

    # --- ÁP DỤNG BỘ LỌC VÀ LẤY KẾT QUẢ ---
    # Tạo 2 cột mới để chứa kết quả (True/False) và Lý do
    evaluations = df['review_text'].apply(evaluate_review)
    df['is_useful'] = [res[0] for res in evaluations]
    df['ly_do_xoa'] = [res[1] for res in evaluations]

    # --- PHÂN TÁCH DỮ LIỆU ---
    # 1. Tập dữ liệu SẠCH (Giữ nguyên cấu trúc, bỏ cột lý do)
    df_clean = df[df['is_useful'] == True].copy()
    df_clean = df_clean.drop(columns=['is_useful', 'ly_do_xoa'])
    df_clean = df_clean.drop_duplicates(subset=['review_text'])
    
    # 2. Tập dữ liệu BỊ XÓA (Giữ lại cột lý do để xem)
    df_deleted = df[df['is_useful'] == False].copy()
    df_deleted = df_deleted.drop(columns=['is_useful'])

    print(f"\nThống kê kết quả:")
    print(f"✅ Giữ lại: {len(df_clean)} bình luận chất lượng cao.")
    print(f"❌ Xóa bỏ: {len(df_deleted)} bình luận nhiễu/rác.")

    # --- XUẤT RA 2 FILE EXCEL ---
    # Lấy thư mục từ input_file để lưu output vào cùng thư mục
    folder_path = os.path.dirname(input_file)
    if folder_path == '':
        folder_path = '.'
    
    output_clean = os.path.join(folder_path, 'shopee_reviews_super_strict.xlsx')
    output_deleted = os.path.join(folder_path, 'shopee_deleted_logs.xlsx')
    
    df_clean.to_excel(output_clean, index=False, engine='openpyxl')
    df_deleted.to_excel(output_deleted, index=False, engine='openpyxl')
    
    print(f"\nĐÃ HOÀN TẤT!")
    print(f"- File dữ liệu chuẩn để chạy mô hình: {output_clean}")
    print(f"- File danh sách các bình luận bị loại: {output_deleted} (Mở file này để kiểm tra lý do xóa)")

# Thực thi chương trình cho các thư mục 1-10
print("=" * 50)
print("KHỞI ĐỘNG XỬ LÝ STRICT FILTER CHO CÁC THƯ MỤC")
print("=" * 50)

for folder_num in range(1, 11):
    folder_path = str(folder_num)
    input_file = os.path.join(folder_path, 'shopee_product_reviews_final.xlsx')
    
    if not os.path.exists(input_file):
        print(f"\n⚠️ Thư mục {folder_path}: File {input_file} không tồn tại. Bỏ qua...")
        continue
    
    print(f"\n{'='*50}")
    print(f"🔄 ĐANG XỬ LÝ THƯ MỤC: {folder_path}")
    print(f"{'='*50}")
    
    super_strict_filter_with_logs(input_file)

print("\n" + "="*50)
print("✅ ĐÃ HOÀN THÀNH STRICT FILTER CHO TẤT CẢ THƯ MỤC!")
print("="*50)
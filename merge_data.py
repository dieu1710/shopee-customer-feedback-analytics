import pandas as pd
import re
import os

# Tập hợp các từ khóa spam thường gặp
spam_keywords = [
    'nhận xu', 'tính chất minh họa', 'tính chất nhận xu', 
    'chống trôi', 'k liên quan', 'không liên quan', 'hình ảnh chỉ',
    'hình ảnh mang tính chất', 'thơ ca'
]

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'\n+', ' ', text) # Chuyển xuống dòng thành khoảng trắng
    text = re.sub(r'\s+', ' ', text).strip() # Xóa khoảng trắng thừa
    return text

def is_useful(text):
    # Loại bỏ bình luận quá ngắn (dưới 4 từ)
    if len(text.split()) < 4:
        return False
        
    # Lọc spam nhận xu
    if any(keyword in text for keyword in spam_keywords):
        return False
        
    # Lọc spam kéo dài phím (ví dụ: đẹppppppppp)
    if any(len(word) > 15 for word in text.split()):
        return False
        
    return True

print("--- BẮT ĐẦU LÀM SẠCH VÀ GỘP DỮ LIỆU EXCEL TỪ CÁC THƯ MỤC ---")

# Xử lý từng thư mục (1-10)
for folder_num in range(1, 11):
    folder_path = str(folder_num)
    
    if not os.path.exists(folder_path):
        print(f"\n⚠️ Thư mục '{folder_path}' không tồn tại. Bỏ qua...")
        continue
    
    print(f"\n{'='*50}")
    print(f"🔄 ĐANG XỬ LÝ THƯ MỤC: {folder_path}")
    print(f"{'='*50}")
    
    all_data = []
    
    # Số đếm file được bắt đầu từ 0
    for index, i in enumerate(range(1, 6), 0):
        # Tìm file xlsx trong từng thư mục
        file_path = os.path.join(folder_path, f'shopee_product_reviews_{i}.xlsx')
                
        if not os.path.exists(file_path):
            print(f"[{index}] ⚠️ Không tìm thấy file {file_path}. Bỏ qua...")
            continue

        try:
            # Đọc dữ liệu từ file Excel
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Chỉ lấy 2 cột gốc cần thiết và loại bỏ dòng rỗng
            if 'review_text' not in df.columns:
                print(f"[{index}] ⚠️ File {file_path} thiếu cột 'review_text'. Bỏ qua...")
                continue
                
            df = df.dropna(subset=['review_text']).copy()
            
            # Làm sạch chuỗi
            df['cleaned_text'] = df['review_text'].apply(clean_text)
            
            # Lọc các bình luận hữu ích
            df_filtered = df[df['cleaned_text'].apply(is_useful)].copy()
            
            # Ghi đè lại cột review_text bằng dữ liệu đã làm sạch
            df_filtered['review_text'] = df_filtered['cleaned_text']
            
            # Thêm cột số sao
            df_filtered['rating_star'] = i
            
            # Chỉ định chính xác 2 cột 
            df_final = df_filtered[['rating_star', 'review_text']]
            
            all_data.append(df_final)
            print(f"[{index}] ✅ Đã lọc xong {file_path}: Giữ lại {len(df_final)} bình luận.")
            
        except Exception as e:
            print(f"[{index}] ❌ Lỗi khi xử lý file {file_path}: {e}")

    # Gộp và xuất file cho thư mục hiện tại
    if all_data:
        master_df = pd.concat(all_data, ignore_index=True)
        
        # Loại bỏ các bình luận trùng lặp hoàn toàn
        master_df = master_df.drop_duplicates(subset=['review_text'])
        
        output_file = os.path.join(folder_path, 'shopee_product_reviews_final.xlsx')
        
        # Lưu ra file Excel mới trong thư mục tương ứng
        master_df.to_excel(output_file, index=False, engine='openpyxl')
        
        print(f"✅ THÀNH CÔNG! Thư mục {folder_path}: {len(master_df)} dòng dữ liệu chuẩn")
        print(f"   Kết quả lưu tại: {output_file}")
    else:
        print(f"❌ Thư mục {folder_path}: Không có dữ liệu để xử lý.")

print("\n" + "="*50)
print("✅ ĐÃ HOÀN THÀNH XỬ LÝ TẤT CẢ CÁC THƯ MỤC!")
print("="*50)
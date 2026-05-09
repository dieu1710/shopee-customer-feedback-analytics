import pandas as pd
import re
import os
from underthesea import word_tokenize
from transformers import pipeline
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

def advanced_absa_pipeline(input_file):
    print("--- KHỞI ĐỘNG HỆ THỐNG PHÂN TÍCH TOÀN DIỆN ---")
    df = pd.read_excel(input_file, engine='openpyxl')
    
    # 1. HÀM TÁCH VẾ CÂU (CLAUSE SPLITTING)
    def split_into_clauses(text):
        if pd.isna(text): return []
        text = str(text).lower()
        
        # Lột bỏ văn mẫu của Shopee trước khi tách
        text = re.sub(r'(đúng với mô tả|chất lượng sản phẩm|thời gian giao hàng).*?:?', '', text)
        
        # Thay thế các từ nối trái ngược và dấu câu bằng ký tự phân tách "|"
        # Các từ: nhưng, mà, tuy nhiên, với lại, còn...
        text = re.sub(r'\b(nhưng|mà|tuy nhiên|mặc dù|với lại|còn|mỗi tội)\b', '|', text)
        text = re.sub(r'[,.;!]+', '|', text)
        
        # Lấy các vế câu có độ dài đủ để phân tích (> 2 chữ)
        clauses = [c.strip() for c in text.split('|') if len(c.strip().split()) >= 2]
        return clauses

    print("1. Đang chặt nhỏ các bình luận dài thành từng vế ý nghĩa...")
    split_records = []
    for _, row in df.iterrows():
        clauses = split_into_clauses(row['review_text'])
        for clause in clauses:
            split_records.append({
                'review_text_goc': row['review_text'],
                've_cau_đon': clause,
                'rating_star': row['rating_star']
            })
            
    df_split = pd.DataFrame(split_records)
    print(f"-> Từ {len(df)} bình luận gốc, đã tách thành {len(df_split)} vế câu độc lập.")

    # 2. HÀM TIỀN XỬ LÝ NLP (TÁCH TỪ CHUẨN PHO-BERT)
    stop_words = set(['bị', 'cái', 'cần', 'chỉ', 'chiếc', 'cho', 'cứ', 'của', 'cùng', 'đã', 'đang', 'đây', 'để', 'đều', 'do', 'đó', 'được', 'là', 'lại', 'lúc', 'này', 'nên', 'nếu', 'ngay', 'như', 'những', 'phải', 'qua', 'ra', 'rằng', 'rồi', 'sau', 'sẽ', 'sự', 'tại', 'theo', 'thì', 'từ', 'và', 'vào', 'vậy', 'vì', 'việc', 'với', 'nhé', 'ạ', 'nha', 'á'])

    def nlp_clean(text):
        # Chỉ giữ lại chữ cái
        text = re.sub(r'[^a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        # Tách từ tiếng Việt
        tokens = word_tokenize(text, format="text").split()
        # Xóa stop words
        clean_tokens = [w for w in tokens if w not in stop_words]
        return " ".join(clean_tokens)

    print("2. Đang chuẩn hóa tiếng Việt (Word Segmentation)...")
    df_split['nlp_text'] = df_split['ve_cau_đon'].apply(nlp_clean)
    
    # Bỏ đi các vế sau khi lọc rác không còn chữ nào
    df_split = df_split[df_split['nlp_text'].str.strip() != '']

    # 3. GÁN NHÃN 8 KHÍA CẠNH
    aspect_dict_8 = {
        'DungLuong': ['dung_lượng', 'mah', 'ảo', 'lần', 'hết_pin', 'tụt', 'chai', 'giảm_pin', 'pin_ảo', 'pin_chai'],
        'TocDoSac': ['nhanh', 'chậm', 'tốc_độ', 'vào_điện', 'vào_pin', 'sạc_đầy', 'hiệu_suất', 'sạc_nhanh', 'sạc_chậm'],
        'NhietDo': ['nóng', 'ấm', 'nhiệt', 'tỏa_nhiệt', 'cháy', 'nổ', 'an_toàn', 'mát', 'lạnh'],
        'ThietKe': ['đẹp', 'xấu', 'màu', 'xước', 'trầy', 'vỏ', 'nhựa', 'kim_loại', 'màn_hình', 'thiết_kế'],
        'KichThuoc': ['nặng', 'nhẹ', 'to', 'nhỏ', 'gọn', 'cầm_tay', 'chắc_tay', 'dày', 'mỏng', 'kích_thước'],
        'CongKetNoi': ['dây', 'cáp', 'cổng', 'type_c', 'usb', 'cắm', 'kết_nối', 'đầu_sạc', 'đầu_cáp'],
        'GiaCa': ['giá', 'rẻ', 'đắt', 'tiền', 'mua', 'hợp_lý', 'đáng_giá', 'không_đắt', 'hời', 'đắt_đỏ', 'giá_cả'],
        'DichVu': ['dịch_vụ', 'hỗ_trợ', 'tư_vấn', 'đổi_trả', 'bảo_hành', 'giao_hàng', 'đóng_gói', 'shop', 'shipper', 'ship']
    }

    def assign_aspect(text):
        found = [asp for asp, kws in aspect_dict_8.items() if any(k in text for k in kws)]
        if not found and any(k in text for k in ['pin', 'sạc']):
            return "DungLuong"
        return ", ".join(found) if found else "Khac"

    df_split['Khia_Canh'] = df_split['nlp_text'].apply(assign_aspect)
    
    # Chỉ giữ lại các vế câu có chứa khía cạnh cụ thể
    df_split = df_split[df_split['Khia_Canh'] != 'Khac'].copy()

    # 4. CHẤM ĐIỂM CẢM XÚC (PHOBERT)
    print("3. Đang tải mô hình PhoBERT để chấm điểm cảm xúc từng vế...")
    analyzer = pipeline("sentiment-analysis", model="wonrax/phobert-base-vietnamese-sentiment", tokenizer="wonrax/phobert-base-vietnamese-sentiment", max_length=256, truncation=True)
    
    tqdm.pandas()
    def get_sentiment(text):
        try:
            res = analyzer(str(text))[0]
            return res['label']
        except: return "NEU"

    print("Đang AI đang đọc và dán nhãn...")
    df_split['Cam_Xuc'] = df_split['nlp_text'].progress_apply(get_sentiment)
    df_split['Cam_Xuc'] = df_split['Cam_Xuc'].map({'POS': 'Tích cực', 'NEG': 'Tiêu cực', 'NEU': 'Trung lập'})

    # 5. XUẤT FILE KẾT QUẢ
    # Lấy thư mục từ input_file để lưu output vào cùng thư mục
    folder_path = os.path.dirname(input_file)
    if folder_path == '':
        folder_path = '.'
    
    output_file = os.path.join(folder_path, 'shopee_final_dataset_absa.xlsx')
    
    # Sắp xếp lại cột cho trực quan
    final_cols = [ 'rating_star', 'review_text_goc', 've_cau_đon', 'nlp_text', 'Khia_Canh', 'Cam_Xuc']
    df_split = df_split[final_cols]
    
    df_split.to_excel(output_file, index=False, engine='openpyxl')
    print(f"\n🎉 HOÀN TẤT! Dữ liệu đã sẵn sàng để vẽ biểu đồ tại: {output_file}")

# Thực thi chương trình cho các thư mục 1-10
print("=" * 50)
print("KHỞI ĐỘNG XỬ LÝ ABSA LABELING CHO CÁC THƯ MỤC")
print("=" * 50)

for folder_num in range(1, 11):
    folder_path = str(folder_num)
    input_file = os.path.join(folder_path, 'shopee_reviews_super_strict.xlsx')
    
    if not os.path.exists(input_file):
        print(f"\n⚠️ Thư mục {folder_path}: File {input_file} không tồn tại. Bỏ qua...")
        continue
    
    print(f"\n{'='*50}")
    print(f"🔄 ĐANG XỬ LÝ THƯ MỤC: {folder_path}")
    print(f"{'='*50}")
    
    advanced_absa_pipeline(input_file)

print("\n" + "="*50)
print("✅ ĐÃ HOÀN THÀNH LABELING CHO TẤT CẢ THƯ MỤC!")
print("="*50)
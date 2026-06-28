# shopee-customer-feedback-analytics

## 🚀 Tổng quan kiến trúc
Hệ thống này tự động xử lý hàng vạn bình luận phi cấu trúc của khách hàng đối với ngành hàng sạc dự phòng. Hệ thống thực hiện bóc tách từng câu phức thành các khía cạnh độc lập (Dung lượng, Tốc độ sạc, Thiết kế...), sử dụng **PhoBERT** để phân loại cảm xúc và **Gemini AI** để đề xuất chiến lược vận hành cho nhà quản lý.

## ⚙️ Yêu cầu hệ thống
* **Ngôn ngữ:** Python 3.9+
* **Thư viện cốt lõi:** `pandas`, `openpyxl`, `underthesea`, `transformers`, `streamlit`, `plotly`, `google-genai`.
* **Cài đặt môi trường:**
  ```bash
  pip install -r requirements.txt

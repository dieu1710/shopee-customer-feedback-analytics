# Phân tích các yếu tố tác động đến sự hài lòng của khách hàng trên sàn thương mại điện tử thông qua khai phá dữ liệu bình luận

Hệ thống được thiết kế để xử lý hàng vạn dòng bình luận phi cấu trúc của khách hàng đối với 10 thương hiệu sạc dự phòng trên Shopee, từ đó trực quan hóa điểm yếu sản phẩm và sinh các chiến lược vận hành thông qua LLM.

---

## 🛠 Thống số kỹ thuật & Công nghệ sử dụng
* **Ngôn ngữ lập trình:** Python 3.9+
* **Giao diện & Trực quan hóa:** Streamlit, Plotly
* **Xử lý ngôn ngữ tự nhiên (NLP):**
  * Tách từ tiếng Việt: `underthesea`
  * Mô hình phân loại cảm xúc: `PhoBERT-base-vietnamese-sentiment` (via Hugging Face `transformers`)
* **AI Tạo sinh (GenAI):** Google Gemini 2.5 Flash API

---

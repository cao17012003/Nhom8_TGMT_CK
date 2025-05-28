# 🏠 Virtual Interior Designer

**Ứng dụng AI tiên tiến cho thiết kế nội thất thông minh**

Virtual Interior Designer là một ứng dụng web sử dụng 4 công nghệ AI tiên tiến để giúp bạn dễ dàng chỉnh sửa và thiết kế không gian nội thất. Không chỉ **xóa vật thể cũ** mà còn có thể **sinh nội thất mới** với chất lượng chuyên nghiệp.

![Virtual Interior Designer](https://img.shields.io/badge/AI-Powered-blue) ![Django](https://img.shields.io/badge/Django-4.2-green) ![Python](https://img.shields.io/badge/Python-3.8+-yellow) ![License](https://img.shields.io/badge/License-MIT-red)

## ✨ Tính năng chính

### 🎯 **Xóa vật thể thông minh**

- **SAM (Segment Anything Model)**: Phân đoạn vật thể chính xác với một cú click
- **LaMa (Large Mask Inpainting)**: Phục hồi nền tự nhiên và hài hòa

### 🪄 **Sinh nội thất mới với AI**

- **Stable Diffusion**: Tạo ra nội thất mới thay thế vật thể đã xóa
- **AI Prompt Generator**: Tự động tạo prompt từ ảnh tham khảo
- **20+ loại nội thất**: Sofa, giường, bàn, đèn, cây cảnh, tranh trang trí...

### 🎨 **Giao diện hiện đại**

- **Glass Morphism Design**: Thiết kế trong suốt hiện đại
- **GSAP Animations**: Hiệu ứng mượt mà 60fps
- **Responsive**: Tối ưu cho mọi thiết bị

## 🚀 Demo

```bash
# Truy cập ứng dụng
http://127.0.0.1:8000/

# Các trang chính
├── Trang chủ: /
├── Tải ảnh: /upload/
├── Chỉnh sửa: /edit/<id>/
└── Giới thiệu: /about/
```

## 🛠️ Công nghệ sử dụng

### **AI Models**

- **SAM (Meta AI)**: Segment Anything Model cho phân đoạn vật thể
- **LaMa**: Large Mask Inpainting cho phục hồi nền
- **Stable Diffusion**: Text-to-Image generation cho sinh nội thất
- **AI Vision**: Prompt generation từ ảnh tham khảo

### **Backend**

- **Django 4.2**: Web framework Python
- **OpenCV**: Xử lý hình ảnh
- **NumPy**: Tính toán khoa học
- **Pillow**: Thao tác ảnh

### **Frontend**

- **Bootstrap 5.3**: UI framework responsive
- **GSAP 3.12**: Animation library
- **Font Awesome 6.4**: Icon library
- **Google Fonts**: Typography (Inter, Poppins)

## 📦 Cài đặt

### **⚠️ Yêu cầu quan trọng - Clone model trước khi cài đặt**

**Trước khi cài đặt ứng dụng, bạn PHẢI clone model LaMa về máy:**

```bash
# Clone LaMa model từ repository chính thức
git clone https://github.com/advimman/lama.git lama-with-refiner

# Hoặc từ mirror nếu link chính không hoạt động
git clone https://github.com/saic-mdal/lama.git lama-with-refiner
```

**Lưu ý quan trọng:**

- 📁 Thư mục `lama-with-refiner` phải nằm trong thư mục gốc của dự án
- 🔗 Model này cần thiết để chức năng xóa/phục hồi nền hoạt động
- 📊 Kích thước: ~10MB (chứa model weights và code)
- 🌐 Cần kết nối internet để download lần đầu

```
virtual_interior_designer/
├── lama-with-refiner/          # ← Thư mục này phải có!
│   ├── saicinpainting/
│   ├── models/
│   └── configs/
├── interior_app/
├── manage.py
└── ...
```

### **Yêu cầu hệ thống**

- Python 3.8+
- Django 4.2+
- 4GB RAM (khuyến nghị 8GB)
- GPU (tùy chọn, cho Stable Diffusion)

### **1. Clone repository**

```bash
git clone https://github.com/your-username/virtual-interior-designer.git
cd virtual-interior-designer
```

### **2. Tạo môi trường ảo**

```bash
   python -m venv venv

# Windows
   venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### **3. Cài đặt dependencies**

```bash
   pip install -r requirements.txt
```

### **4. Cấu hình database**

```bash
python manage.py makemigrations
python manage.py migrate
```

### **5. Tạo superuser (tùy chọn)**

```bash
python manage.py createsuperuser
```

### **6. Chạy server**

#### **Cách 1: Sử dụng run_server.bat (Khuyến nghị)**

```bash
   cmd /c run_server.bat
```

Hoặc nhấp đúp vào file `run_server.bat` trong thư mục dự án.

Script sẽ tự động:

- Kích hoạt môi trường ảo
- Thiết lập PYTHONPATH cần thiết
- Khởi động Django server

#### **Cách 2: Chạy thủ công**

```bash
python manage.py runserver
```

Truy cập: `http://127.0.0.1:8000/`

### **📝 Về file run_server.bat**

File `run_server.bat` là script tự động giúp khởi động server một cách dễ dàng:

```batch
@echo off
echo Starting Virtual Interior Designer Server...
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Set Python path
set PYTHONPATH=%CD%

REM Start Django server
echo Starting Django development server...
python manage.py runserver

pause
```

**Lợi ích:**

- ✅ Tự động kích hoạt môi trường ảo
- ✅ Thiết lập PYTHONPATH đúng
- ✅ Khởi động server với một lệnh
- ✅ Không cần nhớ nhiều lệnh

## 📋 Cách sử dụng

### **Quy trình cơ bản (4 bước)**

1. **📤 Tải lên ảnh**

   - Drag & drop hoặc chọn file ảnh phòng
   - Hỗ trợ JPG, PNG, GIF (tối đa 10MB)

2. **🖱️ Chọn vật thể**

   - Click vào vật thể muốn xóa hoặc thay thế
   - SAM tự động phân đoạn chính xác

3. **⚡ Xóa hoặc thay thế**

   - **Xóa**: LaMa phục hồi nền tự nhiên
   - **Thay thế**: Stable Diffusion sinh nội thất mới

4. **💾 Tải kết quả**
   - Download ảnh đã chỉnh sửa
   - Chất lượng cao, giữ nguyên độ phân giải

### **Tính năng AI nâng cao**

#### **🤖 AI Prompt Generator**

```python
# Upload ảnh tham khảo → AI tự tạo prompt
input: sofa_reference.jpg
output: "modern gray sectional sofa, fabric upholstery,
         contemporary living room, soft lighting,
         minimalist design, high quality"
```

#### **🎨 Stable Diffusion**

```python
# Sinh nội thất từ prompt
prompt: "wooden dining table, oak material,
         rectangular shape, modern design"
result: realistic_dining_table.jpg
```

## 📁 Cấu trúc dự án

```
virtual_interior_designer/
├── 📁 interior_app/
│   ├── 📁 templates/interior_app/
│   │   ├── 🌐 base.html          # Template cơ sở
│   │   ├── 🏠 index.html         # Trang chủ
│   │   ├── 📤 upload.html        # Tải ảnh
│   │   ├── ✏️ edit.html          # Chỉnh sửa
│   │   └── ℹ️ about.html         # Giới thiệu
│   ├── 📁 static/
│   │   ├── 🎨 css/
│   │   │   ├── main.css          # CSS chính
│   │   │   └── animations.css    # GSAP animations
│   │   └── 📜 js/
│   │       └── main.js           # JavaScript chính
│   ├── 📁 models/               # AI models
│   ├── 🐍 views.py             # Django views
│   ├── 🔗 urls.py              # URL routing
│   └── 🎛️ models.py            # Database models
├── 📁 media/                   # Uploaded images
├── 📁 static/                  # Static files
├── ⚙️ settings.py              # Django settings
├── 🚀 run_server.bat           # Script khởi động server
├── 📋 requirements.txt         # Dependencies
└── 📖 README.md               # Documentation
```

## 🎨 Danh sách nội thất hỗ trợ

| Loại                     | Mô tả                      | Icon           |
| ------------------------ | -------------------------- | -------------- |
| 🛋️ **Sofa & Ghế**        | Sofa, ghế bành, ghế đơn    | `fa-couch`     |
| 🛏️ **Giường & Nệm**      | Giường ngủ, nệm, gối       | `fa-bed`       |
| 🪑 **Bàn & Tủ**          | Bàn ăn, tủ quần áo, kệ     | `fa-table`     |
| 💡 **Đèn chiếu sáng**    | Đèn chùm, đèn bàn, đèn sàn | `fa-lightbulb` |
| 📺 **Thiết bị điện tử**  | TV, loa, máy tính          | `fa-tv`        |
| 🌱 **Cây cảnh**          | Cây trong nhà, chậu hoa    | `fa-seedling`  |
| 🖼️ **Tranh & Trang trí** | Tranh ảnh, đồ trang trí    | `fa-image`     |
| ➕ **Và nhiều hơn nữa**  | Liên tục cập nhật          | `fa-plus`      |

## 🔧 API Endpoints

```python
# Main URLs
GET  /                    # Trang chủ
GET  /upload/            # Form tải ảnh
POST /upload/            # Xử lý upload
GET  /edit/<int:id>/     # Trang chỉnh sửa
POST /process/           # Xử lý AI
GET  /about/             # Giới thiệu
GET  /guide/             # Hướng dẫn

# API Endpoints
POST /api/segment/       # SAM segmentation
POST /api/inpaint/       # LaMa inpainting
POST /api/generate/      # Stable Diffusion
POST /api/prompt/        # AI Prompt Generator
```

## ⚡ Performance

### **Thời gian xử lý**

- **SAM Segmentation**: ~2-3 giây
- **LaMa Inpainting**: ~5-10 giây
- **Stable Diffusion**: ~30-60 giây
- **AI Prompt Generation**: ~5-10 giây

### **Yêu cầu phần cứng**

```yaml
Minimum:
  RAM: 4GB
  Storage: 2GB
  CPU: Intel i5 / AMD Ryzen 5

Recommended:
  RAM: 8GB+
  Storage: 5GB+
  GPU: NVIDIA GTX 1060+ (cho Stable Diffusion)
  CPU: Intel i7 / AMD Ryzen 7
```

## 🐛 Troubleshooting

### **Lỗi thường gặp**

#### **1. ModuleNotFoundError**

```bash
# Cài đặt lại dependencies
pip install -r requirements.txt
```

#### **2. CUDA out of memory**

```python
# Giảm batch size trong settings
STABLE_DIFFUSION_BATCH_SIZE = 1
```

#### **3. File upload quá lớn**

```python
# Tăng giới hạn trong settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
```

#### **4. GSAP animations không hoạt động**

```html
<!-- Kiểm tra CDN trong base.html -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
```

#### **5. run_server.bat không hoạt động**

```bash
# Kiểm tra môi trường ảo đã được tạo
python -m venv venv

# Kiểm tra file run_server.bat có tồn tại
dir run_server.bat

# Chạy thủ công nếu cần
venv\Scripts\activate
python manage.py runserver
```

```bash
# Dùng model runwayml/stable-diffusion-inpainting chạy trên githup
# Bước 1 : Lấy NGROK_AUTH_TOKEN trên ngrok
# Bước 2 : Mở google colab điền NGROK_AUTH_TOKEN và chạy Demo.ipynb
# Bước 3 lấy link (ví dụ : https://7c9a-35-240-239-226.ngrok-free.app) và điền vào frontend phần sinh ảnh và dùng chức năng
```

## 🔮 Roadmap

### **✅ Đã hoàn thành**

- [x] SAM + LaMa integration
- [x] Stable Diffusion integration
- [x] AI Prompt Generator
- [x] Modern UI với GSAP
- [x] 20+ furniture types
- [x] Responsive design

### **🔄 Đang phát triển**

- [ ] Thay đổi màu sắc tường, sàn nhà
- [ ] Thư viện nội thất 3D
- [ ] Đề xuất thiết kế AI
- [ ] AR/VR preview mode
- [ ] Mobile app
- [ ] API public

### **🎯 Tương lai**

- [ ] Real-time collaboration
- [ ] Cloud processing
- [ ] Premium features
- [ ] Marketplace nội thất

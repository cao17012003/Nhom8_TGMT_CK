/**
 * Main JavaScript for Virtual Interior Designer
 */

// Đợi tải trang xong
document.addEventListener('DOMContentLoaded', function() {
    // Khởi tạo các thành phần UI chung
    initCommonUI();
    
    // Khởi tạo các tính năng cụ thể cho từng trang
    if (document.getElementById('upload-form')) {
        initUploadPage();
    }
    
    if (document.getElementById('image-canvas')) {
        initEditPage();
    }
});

/**
 * Khởi tạo các thành phần UI chung cho toàn bộ ứng dụng
 */
function initCommonUI() {
    // Thêm hiệu ứng smooth scroll cho các liên kết
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Thêm hiệu ứng hiển thị/ẩn navbar khi cuộn
    let lastScrollTop = 0;
    const navbar = document.querySelector('.header-container');
    
    if (navbar) {
        window.addEventListener('scroll', function() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                // Cuộn xuống
                navbar.style.top = '-100px';
            } else {
                // Cuộn lên
                navbar.style.top = '0';
            }
            
            lastScrollTop = scrollTop;
        });
    }
}

/**
 * Khởi tạo trang tải lên ảnh
 */
function initUploadPage() {
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('image-upload');
    const browseButton = document.getElementById('browse-button');
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');
    const uploadButton = document.getElementById('upload-button');
    
    // Không có các phần tử cần thiết, thoát khỏi hàm
    if (!dropArea || !fileInput || !browseButton) return;
    
    // Mở hộp thoại khi nhấp vào nút chọn file
    browseButton.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Xử lý sự kiện kéo thả
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropArea.classList.add('border', 'border-primary');
    }
    
    function unhighlight() {
        dropArea.classList.remove('border', 'border-primary');
    }
    
    // Xử lý khi kéo thả file
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            updateImagePreview(files[0]);
        }
    }
    
    // Xử lý khi chọn file
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            updateImagePreview(fileInput.files[0]);
        }
    });
    
    // Hiển thị xem trước ảnh
    function updateImagePreview(file) {
        if (file.type.match('image.*')) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                previewContainer.classList.remove('d-none');
                uploadButton.disabled = false;
            }
            
            reader.readAsDataURL(file);
        }
    }
}

/**
 * Khởi tạo trang chỉnh sửa ảnh
 */
function initEditPage() {
    // Các phần tử DOM
    const originalImage = document.getElementById('original-image');
    const canvas = document.getElementById('image-canvas');
    if (!canvas || !originalImage) return;
    
    const ctx = canvas.getContext('2d');
    const segmentButton = document.getElementById('segment-button');
    const inpaintButton = document.getElementById('inpaint-button');
    const downloadButton = document.getElementById('download-button');
    const resetButton = document.getElementById('reset-button');
    const resultContainer = document.getElementById('result-container');
    const resultImage = document.getElementById('result-image');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    
    // Biến lưu trữ trạng thái
    let clickPoints = [];
    let segmented = false;
    let processingMode = false;
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    
    // Thiết lập canvas khi ảnh tải xong
    originalImage.onload = function() {
        canvas.width = originalImage.naturalWidth;
        canvas.height = originalImage.naturalHeight;
        
        // Hiển thị canvas, ẩn ảnh gốc
        canvas.style.display = 'block';
        originalImage.style.display = 'none';
        
        // Vẽ ảnh lên canvas
        ctx.drawImage(originalImage, 0, 0);
    };
    
    // Xử lý sự kiện click trên canvas
    canvas.addEventListener('click', function(e) {
        if (processingMode) return;
        
        // Tính toán vị trí click
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        
        const x = (e.clientX - rect.left) * scaleX;
        const y = (e.clientY - rect.top) * scaleY;
        
        // Thêm điểm click
        clickPoints.push([Math.round(x), Math.round(y)]);
        
        // Vẽ điểm đánh dấu
        ctx.fillStyle = 'red';
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();
        
        // Cho phép phân đoạn nếu có ít nhất 1 điểm
        if (clickPoints.length > 0 && !segmented) {
            segmentButton.disabled = false;
        }
    });
    
    // Xử lý nút phân đoạn vật thể
    if (segmentButton) {
        segmentButton.addEventListener('click', function() {
            if (clickPoints.length === 0) {
                alert('Vui lòng click vào vật thể bạn muốn xóa');
                return;
            }
            
            // Hiển thị loading
            loadingOverlay.classList.remove('d-none');
            loadingText.textContent = 'Đang xác định vật thể...';
            processingMode = true;
            
            // Gửi yêu cầu phân đoạn
            fetch('/api/segment/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    points: clickPoints
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Tạo ảnh mới từ dữ liệu Base64
                    const tempImage = new Image();
                    tempImage.onload = function() {
                        // Xóa canvas và vẽ lại kết quả phân đoạn
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.drawImage(tempImage, 0, 0, canvas.width, canvas.height);
                        
                        // Cập nhật trạng thái
                        segmented = true;
                        inpaintButton.disabled = false;
                        
                        // Ẩn loading
                        loadingOverlay.classList.add('d-none');
                        processingMode = false;
                    };
                    tempImage.src = data.visualization;
                } else {
                    alert('Lỗi: ' + data.error);
                    loadingOverlay.classList.add('d-none');
                    processingMode = false;
                }
            })
            .catch(error => {
                alert('Đã xảy ra lỗi: ' + error);
                loadingOverlay.classList.add('d-none');
                processingMode = false;
            });
        });
    }
    
    // Xử lý nút inpaint
    if (inpaintButton) {
        inpaintButton.addEventListener('click', function() {
            if (!segmented) {
                alert('Vui lòng chọn vật thể trước khi xóa');
                return;
            }
            
            // Hiển thị loading
            loadingOverlay.classList.remove('d-none');
            loadingText.textContent = 'Đang xóa vật thể và phục hồi nền...';
            processingMode = true;
            
            // Gửi yêu cầu inpaint
            fetch('/api/inpaint/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Hiển thị kết quả
                    resultImage.src = data.result_url;
                    resultContainer.classList.remove('d-none');
                    downloadButton.disabled = false;
                    
                    // Ẩn loading
                    loadingOverlay.classList.add('d-none');
                    processingMode = false;
                } else {
                    alert('Lỗi: ' + data.error);
                    loadingOverlay.classList.add('d-none');
                    processingMode = false;
                }
            })
            .catch(error => {
                alert('Đã xảy ra lỗi: ' + error);
                loadingOverlay.classList.add('d-none');
                processingMode = false;
            });
        });
    }
    
    // Xử lý nút tải về
    if (downloadButton) {
        downloadButton.addEventListener('click', function() {
            window.location.href = '/download/';
        });
    }
    
    // Xử lý nút đặt lại
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            // Đặt lại canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(originalImage, 0, 0);
            
            // Đặt lại trạng thái
            clickPoints = [];
            segmented = false;
            inpaintButton.disabled = true;
            resultContainer.classList.add('d-none');
            downloadButton.disabled = true;
        });
    }
} 
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import os
import json
import tempfile
import uuid
from .models_ai.sam.segmentation import ObjectSegmentation
from .models_ai.lama.inpainting import Inpainting
from .models_ai.grabcut.grabcut_segmentation import GrabCutSegmentation
from .utils.stable_diffusion_service import StableDiffusionService
from .utils.image_analysis_service import ImageAnalysisService
import base64
import cv2
import numpy as np

def index(request):
    """Trang chủ của ứng dụng"""
    return render(request, 'interior_app/index.html')

def about(request):
    """Trang giới thiệu về dự án"""
    return render(request, 'interior_app/about.html')

def upload_image(request):
    """Xử lý upload ảnh và lưu vào session"""
    if request.method == 'POST' and request.FILES.get('image'):
        # Lấy file ảnh
        image_file = request.FILES['image']
        
        # Tạo thư mục tạm nếu chưa có
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Tạo ID phiên cho người dùng
        session_id = request.session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['session_id'] = session_id
        
        # Lưu ảnh với tên duy nhất
        image_name = f"{session_id}_original.jpg"
        image_path = os.path.join(upload_dir, image_name)
        
        with open(image_path, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)
        
        # Lưu đường dẫn ảnh vào session
        request.session['original_image'] = image_path
        
        # Khởi tạo list mask rỗng
        request.session['mask_paths'] = []
        
        return redirect('edit_image')
    
    return render(request, 'interior_app/upload.html')

def edit_image(request):
    """Trang chỉnh sửa ảnh"""
    # Kiểm tra xem đã có ảnh chưa
    image_path = request.session.get('original_image')
    if not image_path or not os.path.exists(image_path):
        return redirect('upload_image')
    
    # Lấy URL tương đối cho template
    relative_path = os.path.relpath(image_path, settings.MEDIA_ROOT)
    # Đảm bảo sử dụng dấu / cho URL thay vì \ trên Windows
    relative_path = relative_path.replace('\\', '/')
    image_url = settings.MEDIA_URL + relative_path
    
    context = {
        'image_url': image_url
    }
    return render(request, 'interior_app/edit.html', context)

def segment_object(request):
    """API phân đoạn vật thể từ click chuột"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Lấy thông tin ảnh và điểm click
        image_path = request.session.get('original_image')
        points = data.get('points', [])
        
        if not image_path or not os.path.exists(image_path) or not points:
            return JsonResponse({'error': 'Ảnh không tồn tại hoặc không có điểm được chọn'}, status=400)
        
        try:
            # Khởi tạo mô hình SAM
            segmentation = ObjectSegmentation()
            
            # Đọc ảnh
            image = cv2.imread(image_path)
            if image is None:
                return JsonResponse({'error': 'Không thể đọc ảnh'}, status=400)
            
            # Chuyển đổi sang định dạng RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Phân đoạn
            mask, score = segmentation.segment_from_points(image_rgb, points)
            
            # Lưu mask vào thư mục tạm
            session_id = request.session.get('session_id')
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            
            # Tạo tên mask duy nhất cho từng vật thể
            mask_id = uuid.uuid4().hex[:8]
            mask_name = f"{session_id}_mask_{mask_id}.png"
            mask_path = os.path.join(upload_dir, mask_name)
            
            # Lưu mask
            cv2.imwrite(mask_path, (mask * 255).astype(np.uint8))
            
            # Lấy danh sách các mask hiện có
            mask_paths = request.session.get('mask_paths', [])
            mask_paths.append(mask_path)
            
            # Cập nhật danh sách mask vào session
            request.session['mask_paths'] = mask_paths
            
            # Tạo ảnh trực quan với vùng đã chọn
            visualization = image.copy()
            visualization[mask] = visualization[mask] * 0.5 + np.array([0, 255, 0], dtype=np.uint8) * 0.5
            
            # Chuyển đổi sang base64 để hiển thị
            _, buffer = cv2.imencode('.jpg', visualization)
            visualization_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Lấy URL tương đối cho mask
            relative_path = os.path.relpath(mask_path, settings.MEDIA_ROOT)
            # Đảm bảo sử dụng dấu / cho URL thay vì \ trên Windows
            relative_path = relative_path.replace('\\', '/')
            mask_url = settings.MEDIA_URL + relative_path
            
            return JsonResponse({
                'success': True,
                'visualization': f"data:image/jpeg;base64,{visualization_base64}",
                'mask_url': mask_url,
                'score': float(score)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Phương thức không được hỗ trợ'}, status=405)

def combine_masks(mask_paths):
    """Kết hợp nhiều mask thành một mask duy nhất"""
    if not mask_paths:
        return None
        
    # Đọc mask đầu tiên để lấy kích thước
    first_mask = cv2.imread(mask_paths[0], cv2.IMREAD_GRAYSCALE)
    if first_mask is None:
        return None
        
    # Tạo mask kết hợp với cùng kích thước
    combined_mask = np.zeros_like(first_mask)
    
    # Kết hợp tất cả mask
    for mask_path in mask_paths:
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if mask is not None:
            # Thêm mask vào mask kết hợp
            combined_mask = np.maximum(combined_mask, mask)
    
    return combined_mask

def inpaint_image(request):
    """API xóa vật thể và phục hồi nền"""
    if request.method == 'POST':
        # Lấy đường dẫn ảnh từ session
        image_path = request.session.get('original_image')
        
        # Lấy danh sách các mask từ session hoặc từ request
        data = json.loads(request.body) if request.body else {}
        mask_urls = data.get('masks', [])
        
        if mask_urls:
            # Chuyển đổi từ URL sang đường dẫn local
            mask_paths = []
            for url in mask_urls:
                # Trích xuất tên file từ URL
                filename = os.path.basename(url)
                mask_path = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)
                if os.path.exists(mask_path):
                    mask_paths.append(mask_path)
        else:
            # Sử dụng danh sách mask từ session
            mask_paths = request.session.get('mask_paths', [])
        
        if not image_path or not os.path.exists(image_path):
            return JsonResponse({'error': 'Ảnh không tồn tại'}, status=400)
        
        if not mask_paths:
            return JsonResponse({'error': 'Chưa có vật thể nào được chọn'}, status=400)
        
        try:
            # Kết hợp tất cả mask thành một
            combined_mask = combine_masks(mask_paths)
            if combined_mask is None:
                return JsonResponse({'error': 'Không thể kết hợp các mask'}, status=400)
            
            # Lưu mask kết hợp vào file tạm
            session_id = request.session.get('session_id')
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            combined_mask_name = f"{session_id}_combined_mask.png"
            combined_mask_path = os.path.join(upload_dir, combined_mask_name)
            
            cv2.imwrite(combined_mask_path, combined_mask)
            
            # Khởi tạo mô hình inpainting
            inpainting = Inpainting()
            
            # Tạo đường dẫn cho ảnh kết quả
            result_name = f"{session_id}_result.jpg"
            result_path = os.path.join(upload_dir, result_name)
            
            # Thực hiện inpainting
            inpainting.inpaint_image(image_path, combined_mask_path, result_path)
            
            # Lưu đường dẫn kết quả vào session
            request.session['result_path'] = result_path
            
            # Trả về URL tương đối cho kết quả
            relative_path = os.path.relpath(result_path, settings.MEDIA_ROOT)
            # Đảm bảo sử dụng dấu / cho URL thay vì \ trên Windows
            relative_path = relative_path.replace('\\', '/')
            result_url = settings.MEDIA_URL + relative_path
            
            return JsonResponse({
                'success': True,
                'result_url': result_url
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Phương thức không được hỗ trợ'}, status=405)

def download_result(request):
    """Tải xuống ảnh kết quả"""
    result_path = request.session.get('result_path')
    
    if not result_path or not os.path.exists(result_path):
        return HttpResponse('Chưa có kết quả để tải xuống', status=400)
    
    with open(result_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='image/jpeg')
        response['Content-Disposition'] = 'attachment; filename="interior_result.jpg"'
        return response

def set_colab_url(request):
    """Cập nhật URL Colab ngrok"""
    if request.method == 'POST':
        data = json.loads(request.body)
        colab_url = data.get('url', '').strip()
        
        if not colab_url:
            return JsonResponse({'error': 'URL không được để trống'}, status=400)
        
        # Kiểm tra định dạng URL
        if not colab_url.startswith(('http://', 'https://')):
            colab_url = 'https://' + colab_url
        
        # Lưu URL vào session
        request.session['colab_url'] = colab_url
        
        # Kiểm tra kết nối
        sd_service = StableDiffusionService(colab_url)
        status = sd_service.check_colab_status()
        
        return JsonResponse({
            'success': True,
            'url': colab_url,
            'status': status
        })
    
    return JsonResponse({'error': 'Phương thức không được hỗ trợ'}, status=405)

def check_colab_status(request):
    """Kiểm tra trạng thái kết nối Colab"""
    colab_url = request.session.get('colab_url')
    
    if not colab_url:
        return JsonResponse({
            'status': 'disconnected',
            'message': 'Chưa cấu hình URL Colab'
        })
    
    sd_service = StableDiffusionService(colab_url)
    status = sd_service.check_colab_status()
    
    return JsonResponse(status)

def generate_furniture(request):
    """API sinh nội thất mới bằng Stable Diffusion"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Lấy thông tin từ request
        prompt = data.get('prompt', '').strip()
        negative_prompt = data.get('negative_prompt', '').strip()
        num_inference_steps = data.get('num_inference_steps', 20)
        guidance_scale = data.get('guidance_scale', 7.5)
        strength = data.get('strength', 0.8)
        mask_urls = data.get('masks', [])
        
        # Kiểm tra prompt
        if not prompt:
            return JsonResponse({'error': 'Vui lòng nhập mô tả nội thất muốn sinh'}, status=400)
        
        # Lấy đường dẫn ảnh từ session
        image_path = request.session.get('original_image')
        if not image_path or not os.path.exists(image_path):
            return JsonResponse({'error': 'Ảnh không tồn tại'}, status=400)
        
        # Xử lý mask
        if mask_urls:
            # Chuyển đổi từ URL sang đường dẫn local
            mask_paths = []
            for url in mask_urls:
                filename = os.path.basename(url)
                mask_path = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)
                if os.path.exists(mask_path):
                    mask_paths.append(mask_path)
        else:
            # Sử dụng danh sách mask từ session
            mask_paths = request.session.get('mask_paths', [])
        
        if not mask_paths:
            return JsonResponse({'error': 'Chưa có vùng nào được chọn để thay thế'}, status=400)
        
        try:
            # Kết hợp tất cả mask thành một
            combined_mask = combine_masks(mask_paths)
            if combined_mask is None:
                return JsonResponse({'error': 'Không thể kết hợp các mask'}, status=400)
            
            # Lưu mask kết hợp
            session_id = request.session.get('session_id')
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            combined_mask_name = f"{session_id}_sd_mask.png"
            combined_mask_path = os.path.join(upload_dir, combined_mask_name)
            
            cv2.imwrite(combined_mask_path, combined_mask)
            
            # Lấy URL Colab
            colab_url = request.session.get('colab_url')
            if not colab_url:
                return JsonResponse({'error': 'Chưa cấu hình URL Colab'}, status=400)
            
            # Khởi tạo service và sinh ảnh
            sd_service = StableDiffusionService(colab_url)
            result = sd_service.generate_furniture(
                image_path=image_path,
                mask_path=combined_mask_path,
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                strength=strength
            )
            
            if result['success']:
                # Lưu đường dẫn kết quả vào session
                request.session['sd_result_path'] = result['result_path']
                
                # Trả về URL tương đối cho kết quả
                relative_path = os.path.relpath(result['result_path'], settings.MEDIA_ROOT)
                # Đảm bảo sử dụng dấu / cho URL thay vì \ trên Windows
                relative_path = relative_path.replace('\\', '/')
                result_url = settings.MEDIA_URL + relative_path
                
                return JsonResponse({
                    'success': True,
                    'result_url': result_url,
                    'processing_time': result.get('processing_time', 0),
                    'prompt': prompt
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                })
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Phương thức không được hỗ trợ'}, status=405)

def get_furniture_suggestions(request):
    """Lấy gợi ý prompt cho các loại nội thất"""
    suggestions = {
        'sofa': [
            'modern comfortable sofa, contemporary design, high quality',
            'luxury leather sofa, elegant style, premium furniture',
            'minimalist sofa, clean lines, scandinavian design',
            'vintage sofa, retro style, classic furniture'
        ],
        'chair': [
            'ergonomic office chair, modern design, comfortable',
            'dining chair, wooden frame, elegant style',
            'armchair, cozy reading chair, comfortable seating',
            'bar stool, modern kitchen chair, sleek design'
        ],
        'table': [
            'coffee table, modern design, glass top',
            'dining table, wooden surface, family gathering',
            'side table, minimalist design, functional',
            'desk, workspace furniture, organized setup'
        ],
        'bed': [
            'comfortable bed, modern bedroom, cozy atmosphere',
            'king size bed, luxury bedding, hotel style',
            'minimalist bed frame, clean design, peaceful',
            'vintage bed, classic style, elegant bedroom'
        ],
        'cabinet': [
            'storage cabinet, organized space, modern design',
            'kitchen cabinet, functional storage, clean lines',
            'display cabinet, showcase furniture, elegant',
            'wardrobe, bedroom storage, spacious design'
        ],
        'bookshelf': [
            'wooden bookshelf, library style, organized books',
            'modern floating shelves, minimalist design',
            'built-in bookcase, floor to ceiling, elegant',
            'vintage bookshelf, classic library furniture'
        ],
        'tv_stand': [
            'modern TV stand, entertainment center, sleek design',
            'wooden TV console, rustic style, media storage',
            'floating TV unit, wall mounted, contemporary',
            'vintage TV cabinet, retro style, classic furniture'
        ],
        'dresser': [
            'bedroom dresser, wooden finish, elegant storage',
            'modern chest of drawers, minimalist design',
            'vintage dresser, antique style, classic furniture',
            'white dresser, clean lines, scandinavian style'
        ],
        'nightstand': [
            'bedside table, modern design, functional storage',
            'wooden nightstand, rustic style, cozy bedroom',
            'floating nightstand, wall mounted, space saving',
            'vintage bedside cabinet, classic bedroom furniture'
        ],
        'mirror': [
            'large wall mirror, modern frame, elegant reflection',
            'vintage mirror, ornate frame, classic style',
            'round mirror, minimalist design, contemporary',
            'full length mirror, bedroom furniture, functional'
        ],
        'lamp': [
            'table lamp, modern design, warm lighting',
            'floor lamp, contemporary style, ambient light',
            'pendant light, hanging fixture, elegant illumination',
            'desk lamp, task lighting, functional design'
        ],
        'curtain': [
            'elegant curtains, flowing fabric, window treatment',
            'modern blinds, clean lines, light control',
            'sheer curtains, soft light, airy atmosphere',
            'blackout curtains, bedroom privacy, cozy environment'
        ],
        'rug': [
            'area rug, modern pattern, comfortable flooring',
            'persian rug, traditional design, elegant carpet',
            'minimalist rug, neutral colors, scandinavian style',
            'vintage carpet, classic pattern, warm atmosphere'
        ],
        'plant': [
            'indoor plant, green foliage, natural decoration',
            'potted tree, large plant, living room accent',
            'hanging plants, vertical garden, fresh air',
            'succulent collection, small plants, modern decor'
        ],
        'artwork': [
            'wall art, modern painting, artistic decoration',
            'framed photograph, gallery wall, personal touch',
            'abstract artwork, contemporary style, colorful accent',
            'vintage poster, retro decoration, classic style'
        ],
        'cushion': [
            'throw pillows, decorative cushions, cozy comfort',
            'floor cushions, casual seating, relaxed atmosphere',
            'accent pillows, colorful decoration, soft furnishing',
            'outdoor cushions, patio furniture, weather resistant'
        ],
        'vase': [
            'decorative vase, elegant centerpiece, artistic accent',
            'ceramic vase, handcrafted pottery, natural beauty',
            'glass vase, transparent design, modern decoration',
            'vintage vase, antique style, classic ornament'
        ],
        'clock': [
            'wall clock, modern timepiece, functional decoration',
            'vintage clock, antique style, classic timekeeping',
            'digital clock, contemporary design, modern technology',
            'grandfather clock, traditional style, elegant furniture'
        ],
        'basket': [
            'storage basket, woven design, organized living',
            'laundry basket, functional storage, bedroom utility',
            'decorative basket, natural fiber, rustic charm',
            'toy basket, kids storage, playroom organization'
        ],
        'ottoman': [
            'storage ottoman, functional seating, modern design',
            'leather ottoman, luxury furniture, elegant accent',
            'fabric ottoman, soft seating, comfortable rest',
            'vintage ottoman, classic style, traditional furniture'
        ]
    }
    
    return JsonResponse({'suggestions': suggestions})

def download_sd_result(request):
    """Tải xuống ảnh kết quả từ Stable Diffusion"""
    result_path = request.session.get('sd_result_path')
    
    if not result_path or not os.path.exists(result_path):
        return HttpResponse('Chưa có kết quả Stable Diffusion để tải xuống', status=400)
    
    with open(result_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='image/jpeg')
        response['Content-Disposition'] = 'attachment; filename="sd_interior_result.jpg"'
        return response

def upload_reference_image(request):
    """Upload ảnh tham khảo để AI phân tích và tạo prompt"""
    if request.method == 'POST' and request.FILES.get('reference_image'):
        try:
            # Lấy file ảnh
            image_file = request.FILES['reference_image']
            
            # Tạo thư mục tạm nếu chưa có
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Tạo ID phiên cho người dùng
            session_id = request.session.get('session_id')
            if not session_id:
                session_id = str(uuid.uuid4())
                request.session['session_id'] = session_id
            
            # Lưu ảnh tham khảo
            reference_name = f"{session_id}_reference.jpg"
            reference_path = os.path.join(upload_dir, reference_name)
            
            with open(reference_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)
            
            # Lưu đường dẫn ảnh tham khảo vào session
            request.session['reference_image'] = reference_path
            
            # Trả về URL tương đối cho ảnh tham khảo
            relative_path = os.path.relpath(reference_path, settings.MEDIA_ROOT)
            # Đảm bảo sử dụng dấu / cho URL thay vì \ trên Windows
            relative_path = relative_path.replace('\\', '/')
            reference_url = settings.MEDIA_URL + relative_path
            
            return JsonResponse({
                'success': True,
                'reference_url': reference_url,
                'message': 'Upload ảnh tham khảo thành công'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Phương thức không được hỗ trợ hoặc không có file'}, status=405)

def analyze_reference_image(request):
    """Phân tích ảnh tham khảo và tạo prompt chi tiết"""
    if request.method == 'POST':
        try:
            # Lấy đường dẫn ảnh tham khảo từ session
            reference_path = request.session.get('reference_image')
            
            if not reference_path or not os.path.exists(reference_path):
                return JsonResponse({'error': 'Chưa có ảnh tham khảo để phân tích'}, status=400)
            
            # Lấy API key từ request hoặc environment
            data = json.loads(request.body) if request.body else {}
            api_key = data.get('api_key') or os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                return JsonResponse({
                    'error': 'Chưa cấu hình API key. Vui lòng nhập API key OpenAI hoặc thêm OPENAI_API_KEY vào environment variables.'
                }, status=400)
            
            # Khởi tạo service phân tích ảnh
            analysis_service = ImageAnalysisService(api_key)
            
            # Phân tích ảnh
            result = analysis_service.analyze_furniture_image(reference_path)
            
            if result['success']:
                analysis_data = result['analysis']
                
                # Tạo enhanced prompt
                enhanced_prompt = analysis_service.create_enhanced_prompt(analysis_data)
                
                # Tạo negative prompt suggestions
                furniture_type = analysis_data.get('furniture_type', 'unknown')
                negative_prompt = analysis_service.get_negative_prompt_suggestions(furniture_type)
                
                # Lưu kết quả phân tích vào session
                request.session['analysis_result'] = {
                    'analysis_data': analysis_data,
                    'enhanced_prompt': enhanced_prompt,
                    'negative_prompt': negative_prompt
                }
                
                return JsonResponse({
                    'success': True,
                    'analysis': analysis_data,
                    'enhanced_prompt': enhanced_prompt,
                    'negative_prompt': negative_prompt,
                    'raw_response': result.get('raw_response', '')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                })
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Dữ liệu JSON không hợp lệ'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Phương thức không được hỗ trợ'}, status=405)

def get_analysis_result(request):
    """Lấy kết quả phân tích đã lưu trong session"""
    analysis_result = request.session.get('analysis_result')
    
    if not analysis_result:
        return JsonResponse({
            'success': False,
            'error': 'Chưa có kết quả phân tích nào'
        })
    
    return JsonResponse({
        'success': True,
        'result': analysis_result
    })

def grabcut_rectangle(request):
    """API phân đoạn bằng GrabCut với hình chữ nhật"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Lấy thông tin ảnh và rectangle
        image_path = request.session.get('original_image')
        rect = data.get('rectangle')  # [x, y, width, height]
        iterations = data.get('iterations', 5)
        
        if not image_path or not os.path.exists(image_path):
            return JsonResponse({'error': 'Ảnh không tồn tại'}, status=400)
        
        if not rect or len(rect) != 4:
            return JsonResponse({'error': 'Thông tin rectangle không hợp lệ'}, status=400)
        
        try:
            # Khởi tạo mô hình GrabCut
            grabcut = GrabCutSegmentation()
            
            # Đọc ảnh
            image = cv2.imread(image_path)
            if image is None:
                return JsonResponse({'error': 'Không thể đọc ảnh'}, status=400)
            
            # Chuyển đổi rectangle thành tuple
            rect_tuple = tuple(rect)
            
            # Phân đoạn bằng GrabCut
            mask, score = grabcut.segment_with_rectangle(image, rect_tuple, iterations)
            
            if mask is None:
                return JsonResponse({'error': 'Không thể tạo mask bằng GrabCut'}, status=400)
            
            # Lưu mask vào thư mục tạm
            session_id = request.session.get('session_id')
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            
            # Tạo tên mask duy nhất
            mask_id = uuid.uuid4().hex[:8]
            mask_name = f"{session_id}_grabcut_rect_{mask_id}.png"
            mask_path = os.path.join(upload_dir, mask_name)
            
            # Lưu mask
            cv2.imwrite(mask_path, (mask * 255).astype(np.uint8))
            
            # Lấy danh sách các mask hiện có
            mask_paths = request.session.get('mask_paths', [])
            mask_paths.append(mask_path)
            
            # Cập nhật danh sách mask vào session
            request.session['mask_paths'] = mask_paths
            
            # Tạo ảnh trực quan với vùng đã chọn
            visualization = image.copy()
            visualization[mask.astype(bool)] = visualization[mask.astype(bool)] * 0.5 + np.array([0, 255, 0], dtype=np.uint8) * 0.5
            
            # Chuyển đổi sang base64 để hiển thị
            _, buffer = cv2.imencode('.jpg', visualization)
            visualization_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Lấy URL tương đối cho mask
            relative_path = os.path.relpath(mask_path, settings.MEDIA_ROOT)
            # Đảm bảo sử dụng dấu / cho URL thay vì \ trên Windows
            relative_path = relative_path.replace('\\', '/')
            mask_url = settings.MEDIA_URL + relative_path
            
            return JsonResponse({
                'success': True,
                'visualization': f"data:image/jpeg;base64,{visualization_base64}",
                'mask_url': mask_url,
                'score': float(score),
                'method': 'grabcut_rectangle'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Phương thức không được hỗ trợ'}, status=405)

def grabcut_strokes(request):
    """API phân đoạn bằng GrabCut với strokes (vẽ)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Lấy thông tin ảnh và strokes
        image_path = request.session.get('original_image')
        foreground_strokes = data.get('foreground_strokes', [])
        background_strokes = data.get('background_strokes', [])
        iterations = data.get('iterations', 5)
        
        if not image_path or not os.path.exists(image_path):
            return JsonResponse({'error': 'Ảnh không tồn tại'}, status=400)
        
        if not foreground_strokes and not background_strokes:
            return JsonResponse({'error': 'Cần ít nhất một stroke để phân đoạn'}, status=400)
        
        try:
            # Khởi tạo mô hình GrabCut
            grabcut = GrabCutSegmentation()
            
            # Đọc ảnh
            image = cv2.imread(image_path)
            if image is None:
                return JsonResponse({'error': 'Không thể đọc ảnh'}, status=400)
            
            # Tạo mask từ strokes
            init_mask = grabcut.create_mask_from_strokes(
                image.shape,
                foreground_strokes,
                background_strokes
            )
            
            # Phân đoạn bằng GrabCut
            mask, score = grabcut.segment_with_mask_init(image, init_mask, iterations)
            
            if mask is None:
                return JsonResponse({'error': 'Không thể tạo mask bằng GrabCut'}, status=400)
            
            # Lưu mask vào thư mục tạm
            session_id = request.session.get('session_id')
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            
            # Tạo tên mask duy nhất
            mask_id = uuid.uuid4().hex[:8]
            mask_name = f"{session_id}_grabcut_strokes_{mask_id}.png"
            mask_path = os.path.join(upload_dir, mask_name)
            
            # Lưu mask
            cv2.imwrite(mask_path, (mask * 255).astype(np.uint8))
            
            # Lấy danh sách các mask hiện có
            mask_paths = request.session.get('mask_paths', [])
            mask_paths.append(mask_path)
            
            # Cập nhật danh sách mask vào session
            request.session['mask_paths'] = mask_paths
            
            # Tạo ảnh trực quan với vùng đã chọn
            visualization = image.copy()
            visualization[mask.astype(bool)] = visualization[mask.astype(bool)] * 0.5 + np.array([0, 255, 0], dtype=np.uint8) * 0.5
            
            # Chuyển đổi sang base64 để hiển thị
            _, buffer = cv2.imencode('.jpg', visualization)
            visualization_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Lấy URL tương đối cho mask
            relative_path = os.path.relpath(mask_path, settings.MEDIA_ROOT)
            # Đảm bảo sử dụng dấu / cho URL thay vì \ trên Windows
            relative_path = relative_path.replace('\\', '/')
            mask_url = settings.MEDIA_URL + relative_path
            
            return JsonResponse({
                'success': True,
                'visualization': f"data:image/jpeg;base64,{visualization_base64}",
                'mask_url': mask_url,
                'score': float(score),
                'method': 'grabcut_strokes'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Phương thức không được hỗ trợ'}, status=405)

def refine_grabcut_mask(request):
    """API tinh chỉnh mask GrabCut với strokes bổ sung"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Lấy thông tin ảnh và mask hiện tại
        image_path = request.session.get('original_image')
        mask_url = data.get('mask_url')
        foreground_strokes = data.get('foreground_strokes', [])
        background_strokes = data.get('background_strokes', [])
        iterations = data.get('iterations', 3)
        
        if not image_path or not os.path.exists(image_path):
            return JsonResponse({'error': 'Ảnh không tồn tại'}, status=400)
        
        if not mask_url:
            return JsonResponse({'error': 'Không có mask để tinh chỉnh'}, status=400)
        
        if not foreground_strokes and not background_strokes:
            return JsonResponse({'error': 'Cần ít nhất một stroke để tinh chỉnh'}, status=400)
        
        try:
            # Lấy đường dẫn mask từ URL
            filename = os.path.basename(mask_url)
            mask_path = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)
            
            if not os.path.exists(mask_path):
                return JsonResponse({'error': 'Mask không tồn tại'}, status=400)
            
            # Khởi tạo mô hình GrabCut
            grabcut = GrabCutSegmentation()
            
            # Đọc ảnh và mask hiện tại
            image = cv2.imread(image_path)
            current_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            
            if image is None or current_mask is None:
                return JsonResponse({'error': 'Không thể đọc ảnh hoặc mask'}, status=400)
            
            # Chuyển mask về binary format
            current_mask = (current_mask > 127).astype(np.uint8)
            
            # Tinh chỉnh mask
            refined_mask, score = grabcut.refine_mask(
                image, 
                current_mask,
                foreground_strokes,
                background_strokes,
                iterations
            )
            
            if refined_mask is None:
                return JsonResponse({'error': 'Không thể tinh chỉnh mask'}, status=400)
            
            # Lưu mask đã tinh chỉnh
            session_id = request.session.get('session_id')
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            
            # Tạo tên mask mới
            mask_id = uuid.uuid4().hex[:8]
            new_mask_name = f"{session_id}_grabcut_refined_{mask_id}.png"
            new_mask_path = os.path.join(upload_dir, new_mask_name)
            
            # Lưu mask đã tinh chỉnh
            cv2.imwrite(new_mask_path, (refined_mask * 255).astype(np.uint8))
            
            # Cập nhật danh sách mask (thay thế mask cũ bằng mask mới)
            mask_paths = request.session.get('mask_paths', [])
            if mask_path in mask_paths:
                mask_index = mask_paths.index(mask_path)
                mask_paths[mask_index] = new_mask_path
            else:
                mask_paths.append(new_mask_path)
            
            request.session['mask_paths'] = mask_paths
            
            # Tạo ảnh trực quan với vùng đã chọn
            visualization = image.copy()
            visualization[refined_mask.astype(bool)] = visualization[refined_mask.astype(bool)] * 0.5 + np.array([0, 255, 0], dtype=np.uint8) * 0.5
            
            # Chuyển đổi sang base64 để hiển thị
            _, buffer = cv2.imencode('.jpg', visualization)
            visualization_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Lấy URL tương đối cho mask mới
            relative_path = os.path.relpath(new_mask_path, settings.MEDIA_ROOT)
            # Đảm bảo sử dụng dấu / cho URL thay vì \ trên Windows
            relative_path = relative_path.replace('\\', '/')
            new_mask_url = settings.MEDIA_URL + relative_path
            
            return JsonResponse({
                'success': True,
                'visualization': f"data:image/jpeg;base64,{visualization_base64}",
                'mask_url': new_mask_url,
                'score': float(score),
                'method': 'grabcut_refined'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Phương thức không được hỗ trợ'}, status=405)

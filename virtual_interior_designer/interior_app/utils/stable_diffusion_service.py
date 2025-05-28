import requests
import base64
import json
import time
from io import BytesIO
from PIL import Image
import numpy as np
import cv2
from django.conf import settings
import os

class StableDiffusionService:
    """Service để giao tiếp với Google Colab chạy Stable Diffusion inpainting"""
    
    def __init__(self, colab_url=None):
        # URL của ngrok tunnel từ Google Colab
        self.colab_url = colab_url or getattr(settings, 'STABLE_DIFFUSION_COLAB_URL', None)
        self.timeout = 300  # 5 phút timeout
        
    def set_colab_url(self, url):
        """Cập nhật URL của Colab"""
        self.colab_url = url
        
    def encode_image_to_base64(self, image_path):
        """Chuyển đổi ảnh thành base64"""
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def decode_base64_to_image(self, base64_string, output_path):
        """Chuyển đổi base64 thành ảnh và lưu"""
        image_data = base64.b64decode(base64_string)
        with open(output_path, 'wb') as f:
            f.write(image_data)
    
    def generate_furniture(self, image_path, mask_path, prompt, negative_prompt="", 
                          num_inference_steps=20, guidance_scale=7.5, strength=0.8):
        """
        Sinh nội thất mới sử dụng Stable Diffusion inpainting
        
        Args:
            image_path: Đường dẫn ảnh gốc
            mask_path: Đường dẫn mask (vùng cần thay thế)
            prompt: Mô tả nội thất muốn sinh
            negative_prompt: Mô tả những gì không muốn
            num_inference_steps: Số bước inference
            guidance_scale: Độ mạnh của guidance
            strength: Độ mạnh của inpainting
            
        Returns:
            dict: Kết quả chứa đường dẫn ảnh sinh ra hoặc lỗi
        """
        
        if not self.colab_url:
            return {
                'success': False,
                'error': 'Chưa cấu hình URL Colab. Vui lòng cập nhật URL ngrok từ Colab.'
            }
        
        try:
            # Đọc và encode ảnh
            image_base64 = self.encode_image_to_base64(image_path)
            mask_base64 = self.encode_image_to_base64(mask_path)
            
            # Chuẩn bị dữ liệu gửi
            payload = {
                'image': image_base64,
                'mask': mask_base64,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'num_inference_steps': num_inference_steps,
                'guidance_scale': guidance_scale,
                'strength': strength
            }
            
            # Gửi request đến Colab
            response = requests.post(
                f"{self.colab_url}/generate",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    # Lưu ảnh kết quả
                    session_id = os.path.basename(image_path).split('_')[0]
                    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
                    result_name = f"{session_id}_sd_result.jpg"
                    result_path = os.path.join(upload_dir, result_name)
                    
                    # Decode và lưu ảnh
                    self.decode_base64_to_image(result['image'], result_path)
                    
                    return {
                        'success': True,
                        'result_path': result_path,
                        'processing_time': result.get('processing_time', 0)
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', 'Lỗi không xác định từ Colab')
                    }
            else:
                return {
                    'success': False,
                    'error': f'Lỗi HTTP {response.status_code}: {response.text}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Timeout: Colab mất quá nhiều thời gian để xử lý'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Không thể kết nối đến Colab. Kiểm tra URL ngrok.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Lỗi: {str(e)}'
            }
    
    def check_colab_status(self):
        """Kiểm tra trạng thái Colab"""
        if not self.colab_url:
            return {
                'status': 'disconnected',
                'message': 'Chưa cấu hình URL Colab'
            }
        
        try:
            response = requests.get(f"{self.colab_url}/status", timeout=10)
            if response.status_code == 200:
                return {
                    'status': 'connected',
                    'message': 'Colab đang hoạt động',
                    'details': response.json()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Colab trả về lỗi {response.status_code}'
                }
        except Exception as e:
            return {
                'status': 'disconnected',
                'message': f'Không thể kết nối: {str(e)}'
            }
    
    def get_available_models(self):
        """Lấy danh sách các model có sẵn trên Colab"""
        if not self.colab_url:
            return {'success': False, 'error': 'Chưa cấu hình URL Colab'}
        
        try:
            response = requests.get(f"{self.colab_url}/models", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)} 
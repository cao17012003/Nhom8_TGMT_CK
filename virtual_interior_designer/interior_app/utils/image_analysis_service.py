import requests
import base64
import json
import os
from typing import Dict, Any

class ImageAnalysisService:
    """Service để phân tích ảnh nội thất và tạo prompt chi tiết sử dụng GPT-4o"""
    
    def __init__(self, api_key: str = None):
        """
        Khởi tạo service với API key
        
        Args:
            api_key: API key cho OpenAI GPT-4o
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        
    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Chuyển đổi ảnh thành base64
        
        Args:
            image_path: Đường dẫn đến file ảnh
            
        Returns:
            Chuỗi base64 của ảnh
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Lỗi đọc ảnh: {str(e)}")
    
    def analyze_furniture_image(self, image_path: str) -> Dict[str, Any]:
        """
        Phân tích ảnh nội thất và tạo prompt chi tiết
        
        Args:
            image_path: Đường dẫn đến ảnh nội thất
            
        Returns:
            Dictionary chứa thông tin phân tích và prompt
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'Chưa cấu hình API key. Vui lòng thêm OPENAI_API_KEY vào environment variables.'
            }
        
        try:
            # Chuyển đổi ảnh thành base64
            base64_image = self.encode_image_to_base64(image_path)
            
            # Tạo prompt cho AI
            system_prompt = """Bạn là một chuyên gia thiết kế nội thất. Hãy phân tích ảnh nội thất được cung cấp và tạo ra một mô tả chi tiết, chính xác để sử dụng cho Stable Diffusion inpainting.

Yêu cầu:
1. Mô tả chi tiết về kiểu dáng, màu sắc, chất liệu của nội thất
2. Mô tả phong cách thiết kế (modern, vintage, minimalist, luxury, etc.)
3. Mô tả về kích thước và tỷ lệ
4. Mô tả về ánh sáng và bóng đổ
5. Sử dụng từ khóa chất lượng cao cho Stable Diffusion

Trả về kết quả dưới dạng JSON với format:
{
    "furniture_type": "loại nội thất (sofa, chair, table, bed, cabinet)",
    "detailed_prompt": "mô tả chi tiết cho Stable Diffusion",
    "style": "phong cách thiết kế",
    "materials": ["danh sách chất liệu"],
    "colors": ["danh sách màu sắc chính"],
    "keywords": ["từ khóa chất lượng cao"]
}"""

            user_prompt = "Hãy phân tích ảnh nội thất này và tạo prompt chi tiết cho Stable Diffusion."
            
            # Gửi request đến OpenAI API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            response = requests.post(self.openai_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                
                try:
                    # Parse JSON response từ AI
                    analysis_data = json.loads(ai_response)
                    
                    return {
                        'success': True,
                        'analysis': analysis_data,
                        'raw_response': ai_response
                    }
                except json.JSONDecodeError:
                    # Nếu AI không trả về JSON hợp lệ, tạo prompt từ text response
                    return {
                        'success': True,
                        'analysis': {
                            'furniture_type': 'unknown',
                            'detailed_prompt': ai_response,
                            'style': 'modern',
                            'materials': [],
                            'colors': [],
                            'keywords': ['high quality', 'detailed', 'realistic']
                        },
                        'raw_response': ai_response
                    }
            else:
                error_msg = f"API Error: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', {}).get('message', error_msg)
                    except:
                        error_msg = response.text[:200]
                
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Timeout: API không phản hồi trong thời gian cho phép'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Lỗi kết nối API: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Lỗi không xác định: {str(e)}'
            }
    
    def create_enhanced_prompt(self, analysis_data: Dict[str, Any], user_modifications: str = "") -> str:
        """
        Tạo prompt nâng cao từ kết quả phân tích
        
        Args:
            analysis_data: Dữ liệu phân tích từ AI
            user_modifications: Các chỉnh sửa từ người dùng
            
        Returns:
            Prompt được tối ưu hóa cho Stable Diffusion
        """
        base_prompt = analysis_data.get('detailed_prompt', '')
        keywords = analysis_data.get('keywords', [])
        
        # Thêm từ khóa chất lượng cao
        quality_keywords = [
            'high quality', 'detailed', 'realistic', 'professional photography',
            'interior design', 'modern furniture', 'clean composition',
            'good lighting', 'sharp focus', '8k resolution'
        ]
        
        # Kết hợp tất cả
        enhanced_prompt = base_prompt
        
        if user_modifications:
            enhanced_prompt += f", {user_modifications}"
        
        # Thêm keywords
        all_keywords = keywords + quality_keywords
        if all_keywords:
            enhanced_prompt += f", {', '.join(all_keywords)}"
        
        return enhanced_prompt
    
    def get_negative_prompt_suggestions(self, furniture_type: str) -> str:
        """
        Tạo negative prompt phù hợp với loại nội thất
        
        Args:
            furniture_type: Loại nội thất
            
        Returns:
            Negative prompt được đề xuất
        """
        base_negative = [
            'blurry', 'low quality', 'distorted', 'deformed', 'ugly',
            'bad anatomy', 'extra limbs', 'missing parts', 'broken',
            'dirty', 'damaged', 'old', 'worn out', 'scratched'
        ]
        
        furniture_specific = {
            'sofa': ['uncomfortable', 'torn fabric', 'sagging cushions'],
            'chair': ['unstable', 'broken legs', 'uncomfortable seating'],
            'table': ['uneven surface', 'wobbly', 'scratched top'],
            'bed': ['unmade', 'dirty sheets', 'broken frame'],
            'cabinet': ['broken doors', 'missing handles', 'cluttered'],
            'bookshelf': ['empty shelves', 'disorganized books', 'unstable structure'],
            'tv_stand': ['cable mess', 'unstable base', 'inadequate storage'],
            'dresser': ['stuck drawers', 'missing knobs', 'uneven surface'],
            'nightstand': ['cluttered top', 'broken drawer', 'unstable'],
            'mirror': ['cracked glass', 'distorted reflection', 'broken frame'],
            'lamp': ['flickering light', 'broken shade', 'exposed wires'],
            'curtain': ['wrinkled fabric', 'uneven hanging', 'faded colors'],
            'rug': ['stained surface', 'frayed edges', 'curled corners'],
            'plant': ['wilted leaves', 'dead branches', 'overwatered soil'],
            'artwork': ['crooked hanging', 'faded colors', 'damaged frame'],
            'cushion': ['flat padding', 'stained fabric', 'misshapen form'],
            'vase': ['cracked ceramic', 'chipped edges', 'unstable base'],
            'clock': ['wrong time', 'broken hands', 'cracked face'],
            'basket': ['broken weave', 'frayed edges', 'collapsed structure'],
            'ottoman': ['worn fabric', 'unstable legs', 'flat cushioning']
        }
        
        specific_negative = furniture_specific.get(furniture_type, [])
        all_negative = base_negative + specific_negative
        
        return ', '.join(all_negative) 
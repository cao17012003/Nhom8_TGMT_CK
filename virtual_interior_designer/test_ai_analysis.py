#!/usr/bin/env python3
"""
Script test tính năng AI phân tích ảnh nội thất
Sử dụng để kiểm tra ImageAnalysisService
"""

import os
import sys
from pathlib import Path

# Thêm đường dẫn project vào Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual_interior_designer.settings')

import django
django.setup()

from interior_app.utils.image_analysis_service import ImageAnalysisService

def test_image_analysis():
    """Test phân tích ảnh với ImageAnalysisService"""
    
    # Kiểm tra API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Chưa cấu hình OPENAI_API_KEY")
        print("Vui lòng set environment variable:")
        print("export OPENAI_API_KEY='sk-your-api-key-here'")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Khởi tạo service
    service = ImageAnalysisService(api_key)
    
    # Test với ảnh mẫu (nếu có)
    test_image_path = "test_furniture.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"❌ Không tìm thấy ảnh test: {test_image_path}")
        print("Vui lòng đặt một ảnh nội thất tên 'test_furniture.jpg' trong thư mục gốc")
        return False
    
    print(f"✅ Tìm thấy ảnh test: {test_image_path}")
    
    # Thực hiện phân tích
    print("🔄 Đang phân tích ảnh...")
    result = service.analyze_furniture_image(test_image_path)
    
    if result['success']:
        print("✅ Phân tích thành công!")
        
        analysis = result['analysis']
        print("\n📊 Kết quả phân tích:")
        print(f"   Loại nội thất: {analysis.get('furniture_type', 'N/A')}")
        print(f"   Phong cách: {analysis.get('style', 'N/A')}")
        print(f"   Chất liệu: {', '.join(analysis.get('materials', []))}")
        print(f"   Màu sắc: {', '.join(analysis.get('colors', []))}")
        print(f"   Keywords: {', '.join(analysis.get('keywords', []))}")
        
        print(f"\n📝 Prompt chi tiết:")
        print(f"   {analysis.get('detailed_prompt', 'N/A')}")
        
        # Test enhanced prompt
        enhanced = service.create_enhanced_prompt(analysis, "with soft lighting")
        print(f"\n✨ Enhanced prompt:")
        print(f"   {enhanced}")
        
        # Test negative prompt
        furniture_type = analysis.get('furniture_type', 'unknown')
        negative = service.get_negative_prompt_suggestions(furniture_type)
        print(f"\n🚫 Negative prompt:")
        print(f"   {negative}")
        
        return True
    else:
        print(f"❌ Lỗi phân tích: {result['error']}")
        return False

def test_api_connection():
    """Test kết nối API OpenAI"""
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Chưa cấu hình OPENAI_API_KEY")
        return False
    
    import requests
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test với API đơn giản
    test_payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 5
    }
    
    try:
        print("🔄 Đang test kết nối API...")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Kết nối API thành công!")
            return True
        else:
            print(f"❌ Lỗi API: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi kết nối: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Test AI Image Analysis Service")
    print("=" * 50)
    
    # Test 1: Kết nối API
    print("\n1️⃣ Test kết nối API OpenAI:")
    api_ok = test_api_connection()
    
    if not api_ok:
        print("\n❌ Không thể tiếp tục test do lỗi API")
        sys.exit(1)
    
    # Test 2: Phân tích ảnh
    print("\n2️⃣ Test phân tích ảnh:")
    analysis_ok = test_image_analysis()
    
    # Kết quả
    print("\n" + "=" * 50)
    if api_ok and analysis_ok:
        print("🎉 Tất cả test đều PASS!")
        print("✅ Tính năng AI phân tích ảnh hoạt động tốt")
    else:
        print("❌ Một số test FAILED")
        print("🔧 Vui lòng kiểm tra lại cấu hình")
    
    print("\n📚 Hướng dẫn sử dụng:")
    print("   1. Đảm bảo có OPENAI_API_KEY")
    print("   2. Upload ảnh nội thất chất lượng tốt")
    print("   3. Sử dụng trong ứng dụng web") 
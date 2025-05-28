import os
import sys
import cv2
import numpy as np
import torch
import yaml
from django.conf import settings
import tempfile

class Inpainting:
    def __init__(self, lama_model_path=None):
        """
        Khởi tạo module inpainting để phục hồi nền khi xóa vật thể
        
        Args:
            lama_model_path: Đường dẫn đến thư mục chứa mô hình LaMa
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Đường dẫn đến thư mục lama-with-refiner
        if lama_model_path is None:
            self.lama_model_path = getattr(settings, 'LAMA_MODEL_PATH', 
                                          os.path.join(settings.BASE_DIR, '..', '..', 'big-lama'))
        else:
            self.lama_model_path = lama_model_path
            
        self.model = None
        
        # Thêm đường dẫn đến lama-with-refiner vào sys.path - sử dụng đường dẫn tuyệt đối
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.lama_with_refiner_path = os.path.join(parent_dir, '..', 'lama-with-refiner')
        if os.path.exists(self.lama_with_refiner_path) and self.lama_with_refiner_path not in sys.path:
            sys.path.append(self.lama_with_refiner_path)
            print(f"Đã thêm {self.lama_with_refiner_path} vào Python path")
    
    def initialize_model(self):
        """Khởi tạo mô hình LaMa khi cần thiết"""
        if self.model is not None:
            return
            
        print("Đang khởi tạo mô hình LaMa...")
        
        try:
            # Import động các module cần thiết từ lama-with-refiner
            from omegaconf import OmegaConf
            from omegaconf.dictconfig import DictConfig
            from omegaconf.base import ContainerMetadata
            from pytorch_lightning.callbacks import ModelCheckpoint

            # Đảm bảo pickle có thể load các class này
            torch.serialization.add_safe_globals([ModelCheckpoint, DictConfig, ContainerMetadata, dict])
            
            # Import các module khác
            from saicinpainting.training.trainers import load_checkpoint
            
            # Cấu hình đường dẫn đến checkpoint
            train_config_path = os.path.join(self.lama_model_path, 'config.yaml')
            checkpoint_path = os.path.join(self.lama_model_path, 'models', 'best.ckpt')
            
            # Đọc cấu hình
            with open(train_config_path, 'r') as f:
                train_config = OmegaConf.create(yaml.safe_load(f))
            
            # Cấu hình mô hình chỉ dùng để dự đoán, không huấn luyện
            train_config.training_model.predict_only = True
            train_config.visualizer.kind = 'noop'
            
            # Tải mô hình
            print(f"Đang tải mô hình từ {checkpoint_path}...")
            model = load_checkpoint(train_config, checkpoint_path, strict=False, map_location='cpu')
            model.freeze()
            model.to(self.device)
            
            self.model = model
            print("Đã khởi tạo mô hình LaMa thành công")
            
        except Exception as e:
            print(f"Lỗi khi khởi tạo mô hình LaMa: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def inpaint_image(self, image_path, mask_path, output_path=None, refine=True):
        """
        Xóa vật thể và phục hồi nền
        
        Args:
            image_path: Đường dẫn đến ảnh đầu vào
            mask_path: Đường dẫn đến mask (vùng cần xóa)
            output_path: Đường dẫn để lưu ảnh kết quả
            refine: Có sử dụng refinement hay không
            
        Returns:
            output_path: Đường dẫn đến ảnh kết quả
        """
        print(f"Đang xử lý ảnh từ: {image_path}")
        print(f"Với mặt nạ từ: {mask_path}")
        
        # Tạo đường dẫn đầu ra nếu chưa có
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), 'inpainted_result.png')
        
        # Đảm bảo thư mục đầu ra tồn tại
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Đọc ảnh và mask
        print("Đang đọc ảnh và mặt nạ...")
        image = cv2.imread(image_path)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        
        if image is None:
            raise ValueError(f"Không thể đọc file ảnh: {image_path}")
        
        if mask is None:
            raise ValueError(f"Không thể đọc file mặt nạ: {mask_path}")
        
        print(f"Kích thước ảnh: {image.shape}")
        print(f"Kích thước mặt nạ: {mask.shape}")
        
        # Tiền xử lý mask
        kernel = np.ones((15, 15), np.uint8)  # Kernel lớn hơn cho vùng xóa
        mask = cv2.dilate(mask, kernel, iterations=2)  # Mở rộng mask
        mask = (mask > 0).astype(np.uint8) * 255  # Nhị phân hóa
        
        # Khởi tạo mô hình nếu chưa
        self.initialize_model()
        
        # Chuẩn bị input cho mô hình
        image_tensor = torch.from_numpy(image.transpose(2, 0, 1)).float() / 255.0
        mask_tensor = torch.from_numpy(mask).float() / 255.0
        mask_tensor = mask_tensor.unsqueeze(0).unsqueeze(0)  # Add batch and channel dimensions
        
        # Đảm bảo mask nhị phân
        mask_tensor = (mask_tensor > 0.5).float()
        
        # Tạo ảnh đã masked
        masked_image = image_tensor.unsqueeze(0) * (1 - mask_tensor)
        
        # Đệm thành bội số của 8 nếu cần
        h, w = masked_image.shape[2], masked_image.shape[3]
        pad_h = (8 - h % 8) % 8
        pad_w = (8 - w % 8) % 8
        if pad_h > 0 or pad_w > 0:
            masked_image = torch.nn.functional.pad(masked_image, (0, pad_w, 0, pad_h))
            mask_tensor = torch.nn.functional.pad(mask_tensor, (0, pad_w, 0, pad_h))
        
        # Chuyển đến device
        masked_image = masked_image.to(self.device)
        mask_tensor = mask_tensor.to(self.device)
        
        # Inpainting
        print("Đang thực hiện inpainting...")
        try:
            with torch.no_grad():
                # Đầu vào cho mô hình là ảnh đã masked + mask
                model_input = torch.cat([masked_image, mask_tensor], dim=1)
                output = self.model.generator(model_input)
                
                # Loại bỏ padding nếu đã thêm
                if pad_h > 0 or pad_w > 0:
                    output = output[:, :, :h, :w]
                
                # Chuyển sang numpy
                result = output[0].permute(1, 2, 0).detach().cpu().numpy()
                
                # Clip và chuyển sang uint8
                result = np.clip(result * 255, 0, 255).astype(np.uint8)
                
            print("Inpainting hoàn tất")
        except Exception as e:
            print(f"Lỗi khi inpainting: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
        # Hậu xử lý kết quả
        print("Hậu xử lý kết quả...")
        
        # Chuyển kết quả về BGR cho OpenCV
        result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
        
        # Tạo mask mờ để pha trộn mềm mại
        mask_blurred = cv2.GaussianBlur(mask, (21, 21), 0)
        mask_blurred = mask_blurred / 255.0
        
        # Pha trộn kết quả với ảnh gốc
        blended_result = image.copy()
        
        # Chỉ thay thế vùng được đánh dấu trong mask
        for c in range(3):
            blended_result[:, :, c] = (mask_blurred * result_bgr[:, :, c] + 
                                      (1 - mask_blurred) * image[:, :, c]).astype(np.uint8)
        
        # Hiệu chỉnh màu cho nhất quán
        kernel = np.ones((5, 5), np.uint8)
        mask_border = cv2.dilate(mask, kernel, iterations=2) - mask
        if np.sum(mask_border) > 0:
            for c in range(3):
                # Tính sự khác biệt màu ở biên
                orig_border_mean = np.mean(image[:, :, c][mask_border > 0])
                inpaint_border_mean = np.mean(result_bgr[:, :, c][mask_border > 0])
                color_diff = orig_border_mean - inpaint_border_mean
                
                # Điều chỉnh màu
                blended_result[:, :, c] = np.clip(
                    blended_result[:, :, c] + mask_blurred * color_diff, 0, 255
                ).astype(np.uint8)
        
        # Lưu kết quả
        cv2.imwrite(output_path, blended_result)
        print(f"Đã lưu kết quả vào {output_path}")
        
        return output_path 
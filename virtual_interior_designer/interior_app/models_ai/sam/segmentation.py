import numpy as np
import cv2
from segment_anything import SamPredictor, sam_model_registry
import torch
import os
from django.conf import settings
import tempfile

class ObjectSegmentation:
    def __init__(self, model_type="vit_h", checkpoint_path=None):
        """
        Khởi tạo mô hình SAM cho phân đoạn vật thể
        
        Args:
            model_type: Loại mô hình SAM (vit_h, vit_l, vit_b)
            checkpoint_path: Đường dẫn đến file checkpoint
        """
        if checkpoint_path is None:
            # Sử dụng đường dẫn mặc định trong settings hoặc thư mục hiện tại
            checkpoint_path = getattr(settings, 'SAM_CHECKPOINT_PATH', 
                                    os.path.join(settings.BASE_DIR, '..', '..', 'sam_vit_h_4b8939.pth'))
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Khởi tạo SAM trên thiết bị: {self.device}")
        
        # Tải mô hình SAM
        self.model = sam_model_registry[model_type](checkpoint=checkpoint_path)
        self.model.to(device=self.device)
        self.predictor = SamPredictor(self.model)
        
    def segment_from_points(self, image, points, labels=None):
        """
        Phân đoạn vật thể từ các điểm đánh dấu
        
        Args:
            image: Ảnh numpy (H, W, 3) định dạng RGB
            points: Mảng các điểm [(x, y), ...] 
            labels: Nhãn cho mỗi điểm (1=foreground, 0=background)
            
        Returns:
            mask: Mặt nạ phân đoạn (H, W) boolean
            score: Điểm tin cậy
        """
        # Chuẩn bị dữ liệu đầu vào
        if not isinstance(image, np.ndarray):
            raise ValueError("Image must be a numpy array")
        
        # Chuyển đổi BGR sang RGB nếu cần
        if image.shape[2] == 3 and image.dtype == np.uint8:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image
        else:
            rgb_image = image
            
        # Chuẩn bị điểm đánh dấu
        input_points = np.array(points)
        if labels is None:
            # Mặc định tất cả điểm là foreground (1)
            input_labels = np.ones(len(points))
        else:
            input_labels = np.array(labels)
            
        # Đặt ảnh cho predictor
        self.predictor.set_image(rgb_image)
        
        # Dự đoán phân đoạn
        masks, scores, _ = self.predictor.predict(
            point_coords=input_points,
            point_labels=input_labels,
            multimask_output=True  # Trả về nhiều mặt nạ
        )
        
        # Lấy mask tốt nhất dựa trên điểm
        best_mask_idx = np.argmax(scores)
        best_mask = masks[best_mask_idx]
        best_score = scores[best_mask_idx]
        
        return best_mask, best_score
    
    def segment_from_click(self, image_path, output_mask_path=None, interactive=False):
        """
        Phân đoạn vật thể từ thao tác click chuột (interactive mode)
        hoặc từ điểm đánh dấu có sẵn
        
        Args:
            image_path: Đường dẫn đến file ảnh đầu vào
            output_mask_path: Đường dẫn để lưu mask kết quả
            interactive: Nếu True, hiển thị giao diện click chuột
            
        Returns:
            mask_path: Đường dẫn đến file mask đã lưu
        """
        # Đọc ảnh đầu vào
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Không thể đọc ảnh từ {image_path}")
        
        if output_mask_path is None:
            # Tạo đường dẫn tạm thời nếu không có đường dẫn đầu ra
            output_mask_path = os.path.join(tempfile.gettempdir(), 'mask.png')
        
        if interactive:
            # Chế độ tương tác với người dùng
            mask = self._interactive_segmentation(image, output_mask_path)
        else:
            # Giả lập click tại giữa ảnh (điểm mặc định)
            h, w = image.shape[:2]
            points = [[w//2, h//2]]  # Điểm ở giữa ảnh
            
            # Chuyển sang RGB cho SAM
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Phân đoạn
            self.predictor.set_image(image_rgb)
            masks, scores, _ = self.predictor.predict(
                point_coords=np.array(points),
                point_labels=np.array([1]),  # 1 = foreground
                multimask_output=True
            )
            
            # Lấy mặt nạ tốt nhất
            mask = masks[np.argmax(scores)]
            
            # Lưu mask
            mask_image = (mask * 255).astype(np.uint8)
            cv2.imwrite(output_mask_path, mask_image)
            
        return output_mask_path
    
    def _interactive_segmentation(self, image, output_path):
        """
        Cho phép người dùng click chuột để chọn vật thể cần phân đoạn
        
        Args:
            image: Ảnh numpy
            output_path: Đường dẫn lưu kết quả
            
        Returns:
            mask: Mặt nạ phân đoạn
        """
        # Chuyển đổi sang RGB cho SAM
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.predictor.set_image(image_rgb)
        
        # Khởi tạo biến lưu trữ điểm click
        param = {"points": [], "clicked": False}
        
        # Hàm xử lý sự kiện click chuột
        def get_point(event, x, y, flags, p):
            if event == cv2.EVENT_LBUTTONDOWN:
                p["points"].append([x, y])
                p["clicked"] = True
        
        # Tạo cửa sổ hiển thị và thiết lập callback
        cv2.namedWindow("Select Object")
        cv2.setMouseCallback("Select Object", get_point, param)
        
        print("Click vào vật thể cần phân đoạn. Nhấn 'q' để xác nhận.")
        
        while True:
            # Hiển thị ảnh với các điểm đã click
            display_img = image.copy()
            for point in param["points"]:
                cv2.circle(display_img, (point[0], point[1]), 5, (0, 255, 0), -1)
            cv2.imshow("Select Object", display_img)
            
            # Kiểm tra phím nhấn
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") and param["clicked"]:
                break
        
        cv2.destroyAllWindows()
        
        if not param["points"]:
            print("Không có điểm nào được chọn!")
            return None
        
        # Dự đoán phân đoạn từ các điểm đã chọn
        input_points = np.array(param["points"])
        input_labels = np.ones(len(input_points))  # Tất cả là foreground
        
        masks, scores, _ = self.predictor.predict(
            point_coords=input_points,
            point_labels=input_labels,
            multimask_output=True
        )
        
        # Lấy mặt nạ tốt nhất
        best_mask = masks[np.argmax(scores)]
        
        # Lưu mặt nạ
        mask_image = (best_mask * 255).astype(np.uint8)
        cv2.imwrite(output_path, mask_image)
        
        # Hiển thị kết quả
        result = image.copy()
        result[best_mask] = result[best_mask] * 0.5 + np.array([0, 255, 0], dtype=np.uint8) * 0.5
        cv2.imshow("Segmentation Result", result)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        print(f"Đã lưu mask vào {output_path}")
        return best_mask 
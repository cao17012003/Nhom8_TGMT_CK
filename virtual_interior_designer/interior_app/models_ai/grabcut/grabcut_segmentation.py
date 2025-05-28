import cv2
import numpy as np

class GrabCutSegmentation:
    """
    GrabCut segmentation class for interactive image segmentation
    Allows users to create masks by drawing rectangles or painting areas
    """
    
    def __init__(self):
        """Initialize GrabCut segmentation"""
        self.GC_BGD = 0  # Background
        self.GC_FGD = 1  # Foreground
        self.GC_PR_BGD = 2  # Probably background
        self.GC_PR_FGD = 3  # Probably foreground
        
    def segment_with_rectangle(self, image, rect, num_iterations=5):
        """
        Segment image using rectangle initialization
        
        Args:
            image: Input image (BGR format)
            rect: Rectangle coordinates (x, y, width, height)
            num_iterations: Number of GrabCut iterations
            
        Returns:
            mask: Binary mask (0 for background, 1 for foreground)
            score: Confidence score (approximate)
        """
        try:
            # Convert to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                img = image.copy()
            else:
                img = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
            # Initialize mask
            mask = np.zeros(img.shape[:2], np.uint8)
            
            # Background and foreground models
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            # Apply GrabCut
            cv2.grabCut(img, mask, rect, bgd_model, fgd_model, num_iterations, cv2.GC_INIT_WITH_RECT)
            
            # Create binary mask (foreground and probably foreground)
            binary_mask = np.where((mask == self.GC_FGD) | (mask == self.GC_PR_FGD), 1, 0)
            
            # Calculate approximate confidence score
            foreground_pixels = np.sum(binary_mask)
            total_pixels = binary_mask.shape[0] * binary_mask.shape[1]
            score = min(0.9, foreground_pixels / total_pixels * 2)  # Approximate score
            
            return binary_mask.astype(np.uint8), score
            
        except Exception as e:
            print(f"Error in GrabCut rectangle segmentation: {e}")
            return None, 0.0
    
    def segment_with_mask_init(self, image, init_mask, num_iterations=5):
        """
        Segment image using mask initialization
        
        Args:
            image: Input image (BGR format)
            init_mask: Initial mask with values:
                - 0: Background
                - 1: Foreground
                - 2: Probably background
                - 3: Probably foreground
            num_iterations: Number of GrabCut iterations
            
        Returns:
            mask: Binary mask (0 for background, 1 for foreground)
            score: Confidence score (approximate)
        """
        try:
            # Convert to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                img = image.copy()
            else:
                img = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
            # Copy the initial mask
            mask = init_mask.copy()
            
            # Background and foreground models
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            # Apply GrabCut
            cv2.grabCut(img, mask, None, bgd_model, fgd_model, num_iterations, cv2.GC_INIT_WITH_MASK)
            
            # Create binary mask (foreground and probably foreground)
            binary_mask = np.where((mask == self.GC_FGD) | (mask == self.GC_PR_FGD), 1, 0)
            
            # Calculate approximate confidence score
            foreground_pixels = np.sum(binary_mask)
            total_pixels = binary_mask.shape[0] * binary_mask.shape[1]
            score = min(0.9, foreground_pixels / total_pixels * 2)  # Approximate score
            
            return binary_mask.astype(np.uint8), score
            
        except Exception as e:
            print(f"Error in GrabCut mask segmentation: {e}")
            return None, 0.0
    
    def create_mask_from_strokes(self, image_shape, foreground_strokes=None, background_strokes=None):
        """
        Create initial mask from user strokes
        
        Args:
            image_shape: Shape of the image (height, width)
            foreground_strokes: List of foreground stroke paths [(x1,y1), (x2,y2), ...]
            background_strokes: List of background stroke paths [(x1,y1), (x2,y2), ...]
            
        Returns:
            mask: Initial mask for GrabCut
        """
        height, width = image_shape[:2]
        mask = np.full((height, width), self.GC_PR_BGD, dtype=np.uint8)  # Default: probably background
        
        # Draw foreground strokes
        if foreground_strokes:
            for stroke in foreground_strokes:
                if len(stroke) >= 2:
                    points = np.array(stroke, dtype=np.int32)
                    cv2.polylines(mask, [points], False, self.GC_FGD, thickness=5)
        
        # Draw background strokes
        if background_strokes:
            for stroke in background_strokes:
                if len(stroke) >= 2:
                    points = np.array(stroke, dtype=np.int32)
                    cv2.polylines(mask, [points], False, self.GC_BGD, thickness=5)
        
        return mask
    
    def refine_mask(self, image, current_mask, foreground_strokes=None, background_strokes=None, num_iterations=3):
        """
        Refine existing mask with additional user input
        
        Args:
            image: Input image (BGR format)
            current_mask: Current binary mask
            foreground_strokes: Additional foreground strokes
            background_strokes: Additional background strokes
            num_iterations: Number of refinement iterations
            
        Returns:
            mask: Refined binary mask
            score: Confidence score
        """
        try:
            # Convert binary mask to GrabCut mask format
            grabcut_mask = np.where(current_mask == 1, self.GC_PR_FGD, self.GC_PR_BGD).astype(np.uint8)
            
            # Add user strokes
            if foreground_strokes:
                for stroke in foreground_strokes:
                    if len(stroke) >= 2:
                        points = np.array(stroke, dtype=np.int32)
                        cv2.polylines(grabcut_mask, [points], False, self.GC_FGD, thickness=5)
            
            if background_strokes:
                for stroke in background_strokes:
                    if len(stroke) >= 2:
                        points = np.array(stroke, dtype=np.int32)
                        cv2.polylines(grabcut_mask, [points], False, self.GC_BGD, thickness=5)
            
            # Apply GrabCut with mask initialization
            return self.segment_with_mask_init(image, grabcut_mask, num_iterations)
            
        except Exception as e:
            print(f"Error in mask refinement: {e}")
            return current_mask, 0.5 
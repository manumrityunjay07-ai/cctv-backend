import cv2
from ultralytics import YOLO

class VideoDetector:
    def __init__(self, model_name="yolov8n.pt"):
        # Load YOLOv8 model (using nano for hackathon speed)
        self.model = YOLO(model_name)
    
    def process_frame(self, frame):
        """
        Run detection on a single frame.
        Returns: 
            results: ultralytics Results object
            annotated_frame: Frame with bounding boxes drawn
        """
        # Run inference
        # Classes: 0 is person. We mainly care about people for CCTV search.
        results = self.model(frame, classes=[0], verbose=False)[0]
        
        # Visualize the results on the frame
        annotated_frame = results.plot()
        
        return results, annotated_frame
    
    def process_video_generator(self, video_path):
        """
        Generator that yields annotated frames and detection data.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error opening video file {video_path}")
            return
            
        while cap.isOpened():
            success, frame = cap.read()
            if success:
                results, annotated_frame = self.process_frame(frame)
                yield {
                    'frame': annotated_frame,
                    'boxes': results.boxes.xyxy.cpu().numpy(),
                    'confidences': results.boxes.conf.cpu().numpy(),
                    'classes': results.boxes.cls.cpu().numpy()
                }
            else:
                break
                
        cap.release()

if __name__ == "__main__":
    # Test script if run directly
    print("YOLO Detection module loaded.")

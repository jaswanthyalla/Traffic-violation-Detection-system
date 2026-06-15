"""
Video Reader Module
Handles reading video files and webcam streams
"""
import cv2
import os
from pathlib import Path
from typing import Tuple, Optional

class VideoReader:
    """Class to handle video reading from files or camera"""
    
    def __init__(self, video_path: Optional[str] = None):
        """
        Initialize video reader
        
        Args:
            video_path: Path to video file, None for webcam
        """
        self.video_path = video_path
        self.cap = None
        self.fps = 30
        self.width = 640
        self.height = 480
        self.total_frames = 0
        
    def open(self) -> bool:
        """Open video file or webcam"""
        if self.video_path and os.path.exists(self.video_path):
            self.cap = cv2.VideoCapture(self.video_path)
            print(f"Opened video: {self.video_path}")
        else:
            self.cap = cv2.VideoCapture(0)
            print("Opened webcam")
            
        if not self.cap.isOpened():
            print("Error: Could not open video source")
            return False
            
        # Get video properties
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        return True
    
    def read_frame(self):
        """Read next frame from video"""
        if self.cap is None:
            return False, None
        return self.cap.read()
    
    def get_properties(self) -> dict:
        """Get video properties"""
        return {
            'fps': self.fps,
            'width': self.width,
            'height': self.height,
            'total_frames': self.total_frames
        }
    
    def release(self):
        """Release video resources"""
        if self.cap:
            self.cap.release()

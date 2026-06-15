"""
OCR Reader Module
Reads text from license plates
"""
import cv2
import numpy as np
from typing import Optional
import re

class OCRReader:
    """Class for reading license plate numbers"""
    
    def __init__(self):
        """Initialize OCR reader"""
        self.plate_pattern = re.compile(r'[A-Z0-9]{2,10}')
        
    def read_plate(self, plate_region: np.ndarray) -> Optional[str]:
        """
        Read license plate number from region
        
        Args:
            plate_region: Cropped plate image
            
        Returns:
            Plate number string or None
        """
        if plate_region.size == 0:
            return None
        
        # Preprocess plate image
        processed = self._preprocess_plate(plate_region)
        
        # In production, use EasyOCR or similar
        # For now, return a placeholder with detected pattern
        plate_number = self._extract_text(processed)
        
        return plate_number
    
    @staticmethod
    def _preprocess_plate(plate_region: np.ndarray) -> np.ndarray:
        """
        Preprocess plate image for OCR
        
        Args:
            plate_region: Original plate region
            
        Returns:
            Preprocessed image
        """
        # Resize for better OCR
        plate = cv2.resize(plate_region, (300, 100))
        
        # Convert to grayscale
        gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply threshold
        _, binary = cv2.threshold(enhanced, 150, 255, cv2.THRESH_BINARY)
        
        return binary
    
    def _extract_text(self, processed: np.ndarray) -> Optional[str]:
        """
        Extract text from processed plate image
        
        Args:
            processed: Processed plate image
            
        Returns:
            Extracted text or None
        """
        # This is a placeholder implementation
        # In production, use EasyOCR:
        # try:
        #     import easyocr
        #     reader = easyocr.Reader(['en'])
        #     results = reader.readtext(processed)
        #     text = ''.join([r[1] for r in results])
        #     return text.strip()
        # except Exception as e:
        #     return None
        
        # Simulated OCR for demonstration
        import random
        import string
        prefix = "".join(random.choices(string.ascii_uppercase, k=2))
        nums = "".join(random.choices(string.digits, k=2))
        chars = "".join(random.choices(string.ascii_uppercase, k=2))
        last = "".join(random.choices(string.digits, k=4))
        return f"{prefix}{nums}{chars}{last}"
    
    def validate_plate(self, plate_number: Optional[str]) -> bool:
        """
        Validate if extracted text looks like a plate number
        
        Args:
            plate_number: Extracted plate number
            
        Returns:
            True if valid plate format
        """
        if not plate_number:
            return False
        
        # Plate should be alphanumeric, 2-10 characters
        return bool(self.plate_pattern.match(plate_number.strip()))

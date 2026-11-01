import numpy as np
import cv2
from typing import Tuple, Optional, List, Union
import time
import logging
from pathlib import Path
import pickle

# Get logger for this module
logger = logging.getLogger(__name__)

class FaceRecognitionSystem:
    """Face recognition system using OpenCV's LBPH Face Recognizer."""
    
    _instance = None
    _encodings_cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FaceRecognitionSystem, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        
        logger.info("Initializing face recognition system...")
        
        try:
            # Initialize OpenCV face detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                raise ValueError("Failed to load face cascade classifier")
            
            # Initialize LBPH Face Recognizer
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            
            # Configure settings
            self.frame_skip = 2
            self.detection_threshold = 70  # Lower means stricter matching
            self.min_neighbors = 5
            self.scale_factor = 1.1
            self.min_face_size = (30, 30)
            
            # Initialize cache
            self._encodings_cache = {}
            self._load_encodings_cache()
            
            self._initialized = True
            logger.info("Face recognition system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing face recognition system: {str(e)}")
            raise RuntimeError(f"Failed to initialize face recognition system: {str(e)}")

    def _load_encodings_cache(self):
        """Load cached face encodings from disk"""
        try:
            cache_file = Path("app/data/cache/face_encodings_cache.pkl")
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    old_cache = pickle.load(f)
                    # Verify and convert cached encodings
                    self._encodings_cache = {}
                    for key, encoding in old_cache.items():
                        if isinstance(encoding, np.ndarray):
                            # Ensure consistent size
                            resized = cv2.resize(encoding, (100, 100))
                            self._encodings_cache[key] = resized
                    logger.info(f"Loaded and verified {len(self._encodings_cache)} cached face encodings")
            else:
                self._encodings_cache = {}
                cache_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to load encodings cache: {e}")
            self._encodings_cache = {}

    def save_encoding_to_cache(self, key: str, encoding: np.ndarray) -> bool:
        """Save a face encoding to the cache"""
        try:
            if encoding is None:
                return False
                
            # Ensure consistent encoding format
            encoding = cv2.resize(encoding, (100, 100))
            self._encodings_cache[key] = encoding
            
            # Save to disk
            cache_file = Path("app/data/cache/face_encodings_cache.pkl")
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'wb') as f:
                pickle.dump(self._encodings_cache, f)
            logger.info(f"Saved face encoding to cache for key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving encoding to cache: {e}")
            return False

    def get_face_encoding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Get face encoding from an image."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=self.scale_factor,
                minNeighbors=self.min_neighbors,
                minSize=self.min_face_size
            )
            
            if len(faces) != 1:
                return None
            
            # Extract the face ROI
            x, y, w, h = faces[0]
            face_roi = gray[y:y+h, x:x+w]
            
            # Normalize face
            face_roi = cv2.equalizeHist(face_roi)
            face_roi = cv2.resize(face_roi, (100, 100))
            
            return face_roi
            
        except Exception as e:
            logger.error(f"Error getting face encoding: {str(e)}")
            return None

    def verify_face(self, image1: np.ndarray, image2: np.ndarray) -> Tuple[bool, float]:
        """Compare two faces and return if they match."""
        try:
            # Get face encodings
            face1 = self.get_face_encoding(image1)
            face2 = self.get_face_encoding(image2)
            
            if face1 is None or face2 is None:
                logger.warning("Failed to detect face in one or both images")
                return False, 0.0
            
            # Ensure both faces have the same shape
            if face1.shape != face2.shape:
                logger.warning(f"Face shape mismatch: {face1.shape} vs {face2.shape}")
                # Resize to match if needed
                face2 = cv2.resize(face2, (face1.shape[1], face1.shape[0]))
            
            # Create a new recognizer instance for this comparison
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            
            # Train with first face
            recognizer.train([face1], np.array([1]))
            
            # Predict second face
            label, confidence = recognizer.predict(face2)
            
            # Convert confidence to similarity score (0-1)
            # LBPH confidence score is distance-based, lower is better
            similarity = max(0, min(100 - confidence, 100)) / 100
            
            # Check if faces match using threshold
            is_match = confidence < self.detection_threshold
            
            if is_match:
                logger.info(f"Face verification successful with confidence: {confidence:.2f}")
            else:
                logger.info(f"Face verification failed with confidence: {confidence:.2f}")
            
            return is_match, similarity
            
        except Exception as e:
            logger.error(f"Error verifying face: {str(e)}")
            return False, 0.0

    def capture_face(self) -> Tuple[bool, Optional[np.ndarray], str]:
        """Capture a face from the webcam."""
        cap = None
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return False, None, "Failed to open webcam"
            
            frame_count = 0
            start_time = time.time()
            best_frame = None
            best_quality = 0
            
            while time.time() - start_time < 10:  # 10 second timeout
                ret, frame = cap.read()
                if not ret:
                    continue
                
                frame_count += 1
                if frame_count % self.frame_skip != 0:
                    continue
                
                # Detect faces
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=self.scale_factor,
                    minNeighbors=self.min_neighbors,
                    minSize=self.min_face_size
                )
                
                if len(faces) == 1:
                    x, y, w, h = faces[0]
                    # Normalize and resize the single detected face ROI
                    face_roi = gray[y:y+h, x:x+w]
                    face_roi = cv2.equalizeHist(face_roi)
                    face_roi = cv2.resize(face_roi, (100, 100))

                    # Estimate quality based on face size and position
                    quality = self._estimate_face_quality(frame, (y, x+w, y+h, x))
                    if quality > best_quality:
                        best_quality = quality
                        best_face = face_roi.copy()
            
            if best_face is not None:
                return True, best_face, "Face captured successfully"
            return False, None, "No suitable face detected"
            
        except Exception as e:
            return False, None, f"Error capturing face: {str(e)}"
        finally:
            if cap is not None:
                cap.release()

    def _estimate_face_quality(self, frame: np.ndarray, face_location: tuple) -> float:
        """Estimate the quality of a captured face."""
        img_height, img_width = frame.shape[:2]
        top, right, bottom, left = face_location
        
        # Calculate face size relative to image
        face_width = right - left
        face_height = bottom - top
        size_score = min(face_width / img_width, face_height / img_height)
        
        # Calculate face centering
        face_center_x = (left + right) / 2
        face_center_y = (top + bottom) / 2
        center_score = 1 - (abs(face_center_x - img_width/2) / img_width + 
                        abs(face_center_y - img_height/2) / img_height) / 2
        
        # Combine scores (70% size, 30% centering)
        return 0.7 * size_score + 0.3 * center_score
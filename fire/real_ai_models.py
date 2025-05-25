#!/usr/bin/env python3
"""
Real AI Models for Fire NOC System
Implements actual machine learning models for document verification and analysis
"""

import cv2
import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
import pickle
import os
import pytesseract
from PIL import Image
import re
import json
from datetime import datetime

class DocumentClassifier:
    """AI Model for Document Type Classification"""
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.model_path = 'models/document_classifier.pkl'
        self.vectorizer_path = 'models/document_vectorizer.pkl'
        
    def create_training_data(self):
        """Create training data for document classification"""
        # Sample training data - you can expand this with real documents
        training_data = [
            # Aadhaar Card patterns
            ("aadhaar card government of india unique identification authority", "aadhaar"),
            ("xxxx xxxx xxxx 1234 male dob address", "aadhaar"),
            ("uid aadhaar enrollment number", "aadhaar"),
            
            # PAN Card patterns
            ("income tax department government of india permanent account number", "pan"),
            ("pan abcde1234f father name date of birth", "pan"),
            ("permanent account number card", "pan"),
            
            # Building Plan patterns
            ("architectural drawing floor plan elevation section", "building_plan"),
            ("site plan building layout dimensions scale", "building_plan"),
            ("construction drawing blueprint structural plan", "building_plan"),
            
            # Safety Certificate patterns
            ("fire safety certificate issued by fire department", "safety_certificate"),
            ("safety compliance certificate building safety", "safety_certificate"),
            ("fire prevention certificate emergency systems", "safety_certificate"),
            
            # Business License patterns
            ("trade license municipal corporation business registration", "business_license"),
            ("shop establishment license commercial permit", "business_license"),
            ("business registration certificate company license", "business_license"),
            
            # Insurance Document patterns
            ("insurance policy fire insurance coverage premium", "insurance"),
            ("general insurance company policy number coverage", "insurance"),
            ("fire insurance certificate property coverage", "insurance"),
        ]
        
        return training_data
    
    def train_model(self):
        """Train the document classification model"""
        print("🤖 Training Document Classification Model...")
        
        # Create training data
        training_data = self.create_training_data()
        
        # Prepare data
        texts = [item[0] for item in training_data]
        labels = [item[1] for item in training_data]
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        X = self.vectorizer.fit_transform(texts)
        
        # Train Random Forest classifier
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, labels)
        
        # Save model
        os.makedirs('models', exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(self.vectorizer_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
        
        print("✅ Document Classification Model Trained Successfully!")
        return True
    
    def load_model(self):
        """Load trained model"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(self.vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            return True
        except:
            return False
    
    def classify_document(self, text):
        """Classify document type from extracted text"""
        if not self.model or not self.vectorizer:
            if not self.load_model():
                self.train_model()
        
        # Preprocess text
        text = text.lower().strip()
        
        # Vectorize text
        X = self.vectorizer.transform([text])
        
        # Predict
        prediction = self.model.predict(X)[0]
        confidence = max(self.model.predict_proba(X)[0])
        
        return {
            'document_type': prediction,
            'confidence': float(confidence),
            'timestamp': datetime.now().isoformat()
        }

class SafetyEquipmentDetector:
    """AI Model for Safety Equipment Detection in Images/Videos"""
    
    def __init__(self):
        self.model = None
        self.model_path = 'models/safety_detector.h5'
        self.classes = ['fire_extinguisher', 'smoke_detector', 'emergency_exit', 'fire_alarm', 'sprinkler']
        
    def create_cnn_model(self):
        """Create CNN model for safety equipment detection"""
        model = keras.Sequential([
            keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(224, 224, 3)),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Conv2D(64, (3, 3), activation='relu'),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Conv2D(128, (3, 3), activation='relu'),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Flatten(),
            keras.layers.Dense(512, activation='relu'),
            keras.layers.Dropout(0.5),
            keras.layers.Dense(len(self.classes), activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train_model(self):
        """Train safety equipment detection model"""
        print("🤖 Training Safety Equipment Detection Model...")
        
        # Create model
        self.model = self.create_cnn_model()
        
        # Generate synthetic training data (in real scenario, use actual images)
        X_train = np.random.random((1000, 224, 224, 3))
        y_train = keras.utils.to_categorical(np.random.randint(0, len(self.classes), 1000), len(self.classes))
        
        # Train model
        self.model.fit(X_train, y_train, epochs=10, batch_size=32, validation_split=0.2, verbose=1)
        
        # Save model
        os.makedirs('models', exist_ok=True)
        self.model.save(self.model_path)
        
        print("✅ Safety Equipment Detection Model Trained Successfully!")
        return True
    
    def load_model(self):
        """Load trained model"""
        try:
            self.model = keras.models.load_model(self.model_path)
            return True
        except:
            return False
    
    def detect_equipment(self, image_path):
        """Detect safety equipment in image"""
        if not self.model:
            if not self.load_model():
                self.train_model()
        
        try:
            # Load and preprocess image
            img = cv2.imread(image_path)
            img = cv2.resize(img, (224, 224))
            img = img / 255.0
            img = np.expand_dims(img, axis=0)
            
            # Predict
            predictions = self.model.predict(img)
            predicted_class = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class])
            
            return {
                'detected_equipment': self.classes[predicted_class],
                'confidence': confidence,
                'all_predictions': {self.classes[i]: float(predictions[0][i]) for i in range(len(self.classes))},
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'error': str(e),
                'detected_equipment': 'unknown',
                'confidence': 0.0
            }

class ComplianceAnalyzer:
    """AI Model for Compliance Analysis"""
    
    def __init__(self):
        self.model = None
        self.model_path = 'models/compliance_analyzer.pkl'
        
    def create_training_data(self):
        """Create training data for compliance analysis"""
        # Features: [area_sqft, occupancy_count, fire_extinguishers, emergency_exits, smoke_detectors]
        # Label: compliance_score (0-100)
        training_data = [
            ([1000, 50, 5, 2, 10], 95),  # Good compliance
            ([500, 25, 2, 1, 5], 85),    # Average compliance
            ([2000, 100, 3, 1, 8], 60),  # Poor compliance
            ([1500, 75, 8, 3, 15], 98),  # Excellent compliance
            ([800, 40, 1, 1, 3], 45),    # Very poor compliance
            # Add more training examples...
        ]
        
        return training_data
    
    def train_model(self):
        """Train compliance analysis model"""
        print("🤖 Training Compliance Analysis Model...")
        
        # Create training data
        training_data = self.create_training_data()
        
        # Prepare data
        X = np.array([item[0] for item in training_data])
        y = np.array([item[1] for item in training_data])
        
        # Train SVM model
        self.model = SVC(kernel='rbf', gamma='scale')
        self.model.fit(X, y)
        
        # Save model
        os.makedirs('models', exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        print("✅ Compliance Analysis Model Trained Successfully!")
        return True
    
    def load_model(self):
        """Load trained model"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            return True
        except:
            return False
    
    def analyze_compliance(self, features):
        """Analyze compliance based on features"""
        if not self.model:
            if not self.load_model():
                self.train_model()
        
        # Predict compliance score
        score = self.model.predict([features])[0]
        
        # Generate recommendations
        recommendations = self.generate_recommendations(features, score)
        
        return {
            'compliance_score': float(score),
            'recommendations': recommendations,
            'risk_level': self.get_risk_level(score),
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_recommendations(self, features, score):
        """Generate recommendations based on analysis"""
        recommendations = []
        
        area, occupancy, extinguishers, exits, detectors = features
        
        # Calculate ratios
        extinguisher_ratio = extinguishers / (area / 1000)  # per 1000 sqft
        exit_ratio = exits / (occupancy / 50)  # per 50 people
        detector_ratio = detectors / (area / 500)  # per 500 sqft
        
        if extinguisher_ratio < 1:
            recommendations.append("Install additional fire extinguishers")
        if exit_ratio < 1:
            recommendations.append("Add more emergency exits")
        if detector_ratio < 1:
            recommendations.append("Install more smoke detectors")
        if score < 70:
            recommendations.append("Immediate safety improvements required")
        
        return recommendations
    
    def get_risk_level(self, score):
        """Determine risk level based on score"""
        if score >= 90:
            return "Low Risk"
        elif score >= 70:
            return "Medium Risk"
        elif score >= 50:
            return "High Risk"
        else:
            return "Critical Risk"

class RealAIEngine:
    """Main AI Engine that combines all models"""
    
    def __init__(self):
        self.document_classifier = DocumentClassifier()
        self.safety_detector = SafetyEquipmentDetector()
        self.compliance_analyzer = ComplianceAnalyzer()
        
    def train_all_models(self):
        """Train all AI models"""
        print("🚀 Training All AI Models...")
        
        # Train document classifier
        self.document_classifier.train_model()
        
        # Train safety equipment detector
        self.safety_detector.train_model()
        
        # Train compliance analyzer
        self.compliance_analyzer.train_model()
        
        print("🎉 All AI Models Trained Successfully!")
        
    def analyze_document(self, file_path):
        """Complete document analysis using AI"""
        try:
            # Extract text using OCR
            img = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(img)
            
            # Classify document type
            classification = self.document_classifier.classify_document(extracted_text)
            
            # Detect safety equipment if it's an image
            equipment_detection = self.safety_detector.detect_equipment(file_path)
            
            return {
                'extracted_text': extracted_text,
                'classification': classification,
                'equipment_detection': equipment_detection,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def analyze_compliance(self, application_data):
        """Analyze compliance for an application"""
        try:
            # Extract features from application data
            features = [
                application_data.get('area_sqft', 1000),
                application_data.get('occupancy_count', 50),
                application_data.get('fire_extinguishers', 2),
                application_data.get('emergency_exits', 1),
                application_data.get('smoke_detectors', 5)
            ]
            
            # Analyze compliance
            compliance_result = self.compliance_analyzer.analyze_compliance(features)
            
            return compliance_result
            
        except Exception as e:
            return {
                'error': str(e),
                'compliance_score': 0,
                'risk_level': 'Unknown'
            }

# Global AI Engine instance
ai_engine = RealAIEngine()

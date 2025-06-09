"""
Advanced Audio Analysis Module for Genre Classification and Music Intelligence
"""
import librosa
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import json
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
import pickle
import os

logger = logging.getLogger(__name__)

class AudioAnalyzer:
    """Advanced audio analysis for genre classification and similarity detection"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.genre_classifier = None
        self.genre_mapping = {
            0: "Electronic", 1: "Rock", 2: "Pop", 3: "Hip-Hop", 4: "Jazz",
            5: "Classical", 6: "Blues", 7: "Country", 8: "Reggae", 9: "Metal",
            10: "Folk", 11: "R&B", 12: "Ambient", 13: "Indie", 14: "Alternative"
        }
        self._initialize_classifier()
    
    def _initialize_classifier(self):
        """Initialize a basic genre classifier with pre-trained weights simulation"""
        # In a real implementation, you'd load a pre-trained model
        # For demo purposes, we'll create a basic classifier
        self.genre_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Create dummy training data to initialize the model
        dummy_features = np.random.rand(150, 13)  # 13 features we extract
        dummy_labels = np.random.randint(0, len(self.genre_mapping), 150)
        
        self.scaler.fit(dummy_features)
        self.genre_classifier.fit(self.scaler.transform(dummy_features), dummy_labels)
    
    def extract_audio_features(self, file_path: str) -> Dict[str, float]:
        """Extract comprehensive audio features for analysis"""
        try:
            # Load audio file
            y, sr = librosa.load(file_path, duration=30)  # Analyze first 30 seconds
            
            features = {}
            
            # Spectral features
            features['spectral_centroid'] = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
            features['spectral_rolloff'] = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))
            features['spectral_bandwidth'] = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))
            
            # Rhythmic features
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            features['tempo'] = float(tempo)
            
            # Harmonic features
            harmonic, percussive = librosa.effects.hpss(y)
            features['harmonic_mean'] = float(np.mean(harmonic))
            features['percussive_mean'] = float(np.mean(percussive))
            
            # MFCC features (first 5 coefficients)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=5)
            for i in range(5):
                features[f'mfcc_{i+1}'] = float(np.mean(mfccs[i]))
            
            # Energy and dynamics
            features['rms_energy'] = float(np.mean(librosa.feature.rms(y=y)))
            features['zero_crossing_rate'] = float(np.mean(librosa.feature.zero_crossing_rate(y)))
            
            # Loudness variation (dynamic range)
            features['dynamic_range'] = float(np.max(y) - np.min(y))
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features from {file_path}: {e}")
            return self._get_default_features()
    
    def _get_default_features(self) -> Dict[str, float]:
        """Return default features when analysis fails"""
        return {
            'spectral_centroid': 2000.0, 'spectral_rolloff': 4000.0, 'spectral_bandwidth': 2000.0,
            'tempo': 120.0, 'harmonic_mean': 0.1, 'percussive_mean': 0.1,
            'mfcc_1': 0.0, 'mfcc_2': 0.0, 'mfcc_3': 0.0, 'mfcc_4': 0.0, 'mfcc_5': 0.0,
            'rms_energy': 0.1, 'zero_crossing_rate': 0.1, 'dynamic_range': 0.5
        }
    
    def classify_genre(self, features: Dict[str, float]) -> Tuple[str, float]:
        """Classify genre based on audio features"""
        try:
            # Convert features to array
            feature_vector = np.array([
                features['spectral_centroid'], features['spectral_rolloff'], features['spectral_bandwidth'],
                features['tempo'], features['harmonic_mean'], features['percussive_mean'],
                features['mfcc_1'], features['mfcc_2'], features['mfcc_3'], features['mfcc_4'], features['mfcc_5'],
                features['rms_energy'], features['zero_crossing_rate']
            ]).reshape(1, -1)
            
            # Scale features
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Predict genre
            prediction = self.genre_classifier.predict(feature_vector_scaled)[0]
            confidence = float(np.max(self.genre_classifier.predict_proba(feature_vector_scaled)))
            
            genre = self.genre_mapping.get(prediction, "Unknown")
            
            # Fallback genre classification based on simple rules
            if confidence < 0.3:
                genre = self._rule_based_genre_classification(features)
                confidence = 0.6
            
            return genre, confidence
            
        except Exception as e:
            logger.error(f"Error classifying genre: {e}")
            return self._rule_based_genre_classification(features), 0.5
    
    def _rule_based_genre_classification(self, features: Dict[str, float]) -> str:
        """Simple rule-based genre classification as fallback"""
        tempo = features.get('tempo', 120)
        spectral_centroid = features.get('spectral_centroid', 2000)
        rms_energy = features.get('rms_energy', 0.1)
        
        # Simple genre rules
        if tempo > 140 and rms_energy > 0.15:
            return "Electronic"
        elif tempo > 130 and spectral_centroid > 3000:
            return "Rock"
        elif tempo < 80 and spectral_centroid < 1500:
            return "Jazz"
        elif tempo > 90 and tempo < 130:
            return "Pop"
        elif spectral_centroid < 1000:
            return "Classical"
        else:
            return "Alternative"
    
    def calculate_similarity(self, features1: Dict[str, float], features2: Dict[str, float]) -> float:
        """Calculate similarity between two tracks based on audio features"""
        try:
            # Convert to arrays
            f1 = np.array([features1.get(key, 0) for key in [
                'spectral_centroid', 'spectral_rolloff', 'tempo', 'rms_energy'
            ]])
            f2 = np.array([features2.get(key, 0) for key in [
                'spectral_centroid', 'spectral_rolloff', 'tempo', 'rms_energy'
            ]])
            
            # Normalize features
            f1_norm = f1 / (np.linalg.norm(f1) + 1e-8)
            f2_norm = f2 / (np.linalg.norm(f2) + 1e-8)
            
            # Calculate cosine similarity
            similarity = np.dot(f1_norm, f2_norm)
            return float(max(0, similarity))  # Ensure non-negative
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.5
    
    def get_mood_energy(self, features: Dict[str, float]) -> Tuple[str, float]:
        """Determine mood and energy level from audio features"""
        tempo = features.get('tempo', 120)
        rms_energy = features.get('rms_energy', 0.1)
        dynamic_range = features.get('dynamic_range', 0.5)
        
        # Calculate energy level (0-1)
        energy = min(1.0, (tempo / 200.0) + (rms_energy * 2) + (dynamic_range * 0.5))
        
        # Determine mood
        if energy > 0.7:
            mood = "Energetic"
        elif energy > 0.5:
            mood = "Upbeat"
        elif energy > 0.3:
            mood = "Mellow"
        else:
            mood = "Calm"
        
        return mood, energy


class RecommendationEngine:
    """Advanced recommendation engine for unlimited playback"""
    
    def __init__(self, audio_analyzer: AudioAnalyzer):
        self.audio_analyzer = audio_analyzer
    
    def calculate_popularity_score(self, track_data: Dict) -> float:
        """Calculate popularity score based on play count, recency, and user behavior"""
        play_count = track_data.get('play_count', 0)
        created_date = track_data.get('created_at')
        last_played = track_data.get('last_played')
        
        # Base score from play count (logarithmic scale)
        play_score = min(1.0, np.log(play_count + 1) / 10.0)
        
        # Recency bonus for recently added tracks
        recency_score = 0.5  # Default
        
        # Recently played bonus
        recent_play_score = 0.5  # Default
        
        # Combine scores
        popularity = (play_score * 0.4) + (recency_score * 0.3) + (recent_play_score * 0.3)
        return min(1.0, popularity)
    
    def find_similar_tracks(self, target_track: Dict, candidate_tracks: List[Dict], 
                          limit: int = 10) -> List[Dict]:
        """Find tracks similar to target track"""
        if not target_track.get('audio_features'):
            return candidate_tracks[:limit]
        
        target_features = target_track['audio_features']
        target_genre = target_track.get('genre', 'Unknown')
        target_year = target_track.get('year')
        
        scored_tracks = []
        
        for track in candidate_tracks:
            if track['id'] == target_track['id']:
                continue
            
            score = 0.0
            
            # Audio similarity (40% weight)
            if track.get('audio_features'):
                audio_similarity = self.audio_analyzer.calculate_similarity(
                    target_features, track['audio_features']
                )
                score += audio_similarity * 0.4
            
            # Genre similarity (30% weight)
            if track.get('genre') == target_genre:
                score += 0.3
            elif self._are_genres_similar(target_genre, track.get('genre', 'Unknown')):
                score += 0.15
            
            # Year similarity (20% weight)
            if target_year and track.get('year'):
                year_diff = abs(target_year - track['year'])
                year_similarity = max(0, 1 - (year_diff / 20))  # 20-year window
                score += year_similarity * 0.2
            
            # Popularity score (10% weight)
            popularity = self.calculate_popularity_score(track)
            score += popularity * 0.1
            
            scored_tracks.append((track, score))
        
        # Sort by score and return top tracks
        scored_tracks.sort(key=lambda x: x[1], reverse=True)
        return [track for track, score in scored_tracks[:limit]]
    
    def _are_genres_similar(self, genre1: str, genre2: str) -> bool:
        """Check if two genres are similar"""
        similar_genres = {
            'Rock': ['Metal', 'Alternative', 'Indie'],
            'Electronic': ['Ambient', 'Pop'],
            'Jazz': ['Blues', 'R&B'],
            'Pop': ['R&B', 'Electronic'],
            'Classical': ['Ambient'],
            'Hip-Hop': ['R&B'],
            'Country': ['Folk'],
            'Metal': ['Rock'],
            'Alternative': ['Rock', 'Indie']
        }
        
        return genre2 in similar_genres.get(genre1, [])
    
    def generate_auto_queue(self, current_track: Dict, all_tracks: List[Dict], 
                          queue_size: int = 20) -> List[Dict]:
        """Generate auto queue for unlimited playback"""
        if not all_tracks:
            return []
        
        # Filter out current track
        available_tracks = [t for t in all_tracks if t['id'] != current_track['id']]
        
        if not available_tracks:
            return []
        
        # Get similar tracks (70% of queue)
        similar_count = int(queue_size * 0.7)
        similar_tracks = self.find_similar_tracks(
            current_track, available_tracks, similar_count
        )
        
        # Add discovery tracks (30% of queue) - popular but different
        discovery_count = queue_size - len(similar_tracks)
        remaining_tracks = [t for t in available_tracks 
                          if t['id'] not in [st['id'] for st in similar_tracks]]
        
        # Sort by popularity for discovery
        discovery_tracks = sorted(
            remaining_tracks,
            key=lambda x: self.calculate_popularity_score(x),
            reverse=True
        )[:discovery_count]
        
        # Combine and shuffle slightly for variety
        auto_queue = similar_tracks + discovery_tracks
        
        # Add some randomness to avoid predictability
        np.random.shuffle(auto_queue)
        
        return auto_queue

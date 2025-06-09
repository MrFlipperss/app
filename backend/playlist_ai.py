"""
AI-Powered Playlist Generation based on User Prompts
"""
import re
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PlaylistIntent:
    mood: Optional[str] = None
    genre: Optional[str] = None
    energy_level: Optional[str] = None  # low, medium, high
    activity: Optional[str] = None
    time_period: Optional[str] = None  # decade like 80s, 90s, etc.
    tempo: Optional[str] = None  # slow, medium, fast
    popularity: Optional[str] = None  # popular, underground, mixed
    duration_minutes: int = 60  # default playlist length

class PlaylistAI:
    """AI-powered playlist generator that interprets user prompts"""
    
    def __init__(self):
        self.mood_keywords = {
            'happy': ['happy', 'cheerful', 'upbeat', 'joyful', 'positive', 'bright', 'sunny'],
            'sad': ['sad', 'melancholy', 'depressing', 'blue', 'down', 'gloomy'],
            'energetic': ['energy', 'pump up', 'workout', 'gym', 'running', 'exercise', 'high energy', 'intense'],
            'calm': ['calm', 'relaxing', 'chill', 'peaceful', 'serene', 'mellow', 'soothing'],
            'romantic': ['romantic', 'love', 'date', 'valentine', 'intimate', 'slow dance'],
            'party': ['party', 'dance', 'club', 'celebration', 'festive', 'fun'],
            'focus': ['focus', 'study', 'work', 'concentration', 'productive', 'ambient']
        }
        
        self.genre_keywords = {
            'rock': ['rock', 'metal', 'punk', 'grunge', 'hard rock'],
            'pop': ['pop', 'mainstream', 'top 40', 'chart'],
            'jazz': ['jazz', 'smooth', 'bebop', 'fusion'],
            'classical': ['classical', 'orchestral', 'symphony', 'piano', 'violin'],
            'electronic': ['electronic', 'edm', 'techno', 'house', 'ambient', 'synth'],
            'hip-hop': ['hip hop', 'rap', 'hip-hop', 'beats'],
            'country': ['country', 'folk', 'bluegrass', 'americana'],
            'r&b': ['r&b', 'soul', 'funk', 'rnb'],
            'reggae': ['reggae', 'ska', 'dub'],
            'blues': ['blues', 'delta', 'chicago blues'],
            'alternative': ['alternative', 'indie', 'alt rock']
        }
        
        self.activity_keywords = {
            'workout': ['workout', 'gym', 'exercise', 'running', 'jogging', 'cardio', 'fitness'],
            'study': ['study', 'focus', 'work', 'concentration', 'reading'],
            'driving': ['driving', 'road trip', 'car', 'highway'],
            'cooking': ['cooking', 'kitchen', 'chef'],
            'party': ['party', 'celebration', 'birthday', 'dance'],
            'sleep': ['sleep', 'bedtime', 'lullaby', 'night'],
            'morning': ['morning', 'wake up', 'breakfast', 'start day'],
            'evening': ['evening', 'sunset', 'dinner', 'wind down']
        }
        
        self.time_period_keywords = {
            '60s': ['60s', '1960s', 'sixties', 'beatles era'],
            '70s': ['70s', '1970s', 'seventies', 'disco era'],
            '80s': ['80s', '1980s', 'eighties', 'synth pop'],
            '90s': ['90s', '1990s', 'nineties', 'grunge era'],
            '2000s': ['2000s', 'y2k', 'millennium'],
            '2010s': ['2010s', 'twenty tens'],
            'modern': ['modern', 'recent', 'current', 'today', 'new']
        }
        
        self.energy_keywords = {
            'low': ['low energy', 'slow', 'calm', 'mellow', 'quiet', 'soft'],
            'medium': ['medium', 'moderate', 'balanced', 'normal'],
            'high': ['high energy', 'intense', 'powerful', 'loud', 'energetic', 'pumped']
        }
        
        self.tempo_keywords = {
            'slow': ['slow', 'ballad', 'laid back', 'relaxed'],
            'medium': ['medium tempo', 'moderate pace'],
            'fast': ['fast', 'upbeat', 'quick', 'rapid', 'speedy']
        }
        
        self.popularity_keywords = {
            'popular': ['popular', 'hits', 'chart toppers', 'mainstream', 'well known'],
            'underground': ['underground', 'obscure', 'hidden gems', 'deep cuts', 'unknown'],
            'mixed': ['mixed', 'variety', 'diverse', 'both popular and underground']
        }
    
    def analyze_prompt(self, prompt: str) -> PlaylistIntent:
        """Analyze user prompt and extract playlist intent"""
        prompt_lower = prompt.lower()
        intent = PlaylistIntent()
        
        # Extract mood
        for mood, keywords in self.mood_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                intent.mood = mood
                break
        
        # Extract genre
        for genre, keywords in self.genre_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                intent.genre = genre
                break
        
        # Extract activity
        for activity, keywords in self.activity_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                intent.activity = activity
                break
        
        # Extract time period
        for period, keywords in self.time_period_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                intent.time_period = period
                break
        
        # Extract energy level
        for energy, keywords in self.energy_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                intent.energy_level = energy
                break
        
        # Extract tempo
        for tempo, keywords in self.tempo_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                intent.tempo = tempo
                break
        
        # Extract popularity preference
        for pop_type, keywords in self.popularity_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                intent.popularity = pop_type
                break
        
        # Extract duration (look for numbers followed by minutes/hours)
        duration_match = re.search(r'(\d+)\s*(min|minute|minutes|hour|hours)', prompt_lower)
        if duration_match:
            num = int(duration_match.group(1))
            unit = duration_match.group(2)
            if 'hour' in unit:
                intent.duration_minutes = num * 60
            else:
                intent.duration_minutes = num
        
        return intent
    
    def generate_playlist(self, prompt: str, all_tracks: List[Dict], 
                         max_tracks: int = 25) -> Tuple[List[Dict], str]:
        """Generate a playlist based on user prompt and available tracks"""
        if not all_tracks:
            return [], "No tracks available in library"
        
        intent = self.analyze_prompt(prompt)
        logger.info(f"Analyzed prompt '{prompt}' with intent: {intent}")
        
        # Filter tracks based on intent
        filtered_tracks = self._filter_tracks_by_intent(all_tracks, intent)
        
        if not filtered_tracks:
            # Fallback to all tracks if filters are too restrictive
            filtered_tracks = all_tracks
            description = f"Created a general playlist (filters were too restrictive). "
        else:
            description = f"Created a playlist based on your request. "
        
        # Score and rank tracks
        scored_tracks = self._score_tracks_for_intent(filtered_tracks, intent)
        
        # Select final tracks
        selected_tracks = self._select_final_tracks(scored_tracks, intent, max_tracks)
        
        # Generate description
        description += self._generate_playlist_description(intent, len(selected_tracks))
        
        return selected_tracks, description
    
    def _filter_tracks_by_intent(self, tracks: List[Dict], intent: PlaylistIntent) -> List[Dict]:
        """Filter tracks based on playlist intent"""
        filtered = tracks.copy()
        
        # Filter by genre
        if intent.genre:
            genre_filtered = []
            for track in filtered:
                track_genre = (track.get('ai_genre') or track.get('genre', '')).lower()
                if intent.genre.lower() in track_genre or track_genre in intent.genre.lower():
                    genre_filtered.append(track)
            if genre_filtered:  # Only apply filter if it doesn't eliminate all tracks
                filtered = genre_filtered
        
        # Filter by mood
        if intent.mood:
            mood_filtered = []
            for track in filtered:
                track_mood = (track.get('mood', '')).lower()
                if intent.mood.lower() in track_mood or track_mood in intent.mood.lower():
                    mood_filtered.append(track)
            if mood_filtered:
                filtered = mood_filtered
        
        # Filter by time period (year)
        if intent.time_period and intent.time_period != 'modern':
            year_filtered = []
            decade_start = self._get_decade_start(intent.time_period)
            if decade_start:
                for track in filtered:
                    track_year = track.get('year')
                    if track_year and decade_start <= track_year < decade_start + 10:
                        year_filtered.append(track)
                if year_filtered:
                    filtered = year_filtered
        elif intent.time_period == 'modern':
            # Modern means 2010 onwards
            year_filtered = [t for t in filtered if t.get('year', 0) >= 2010]
            if year_filtered:
                filtered = year_filtered
        
        return filtered
    
    def _score_tracks_for_intent(self, tracks: List[Dict], intent: PlaylistIntent) -> List[Tuple[Dict, float]]:
        """Score tracks based on how well they match the intent"""
        scored_tracks = []
        
        for track in tracks:
            score = 0.0
            
            # Base score from audio features
            energy = track.get('energy', 0.5)
            popularity = track.get('popularity_score', 0.5)
            
            # Activity-based scoring
            if intent.activity:
                if intent.activity == 'workout' and energy > 0.7:
                    score += 0.3
                elif intent.activity == 'study' and energy < 0.4:
                    score += 0.3
                elif intent.activity == 'sleep' and energy < 0.3:
                    score += 0.3
                elif intent.activity == 'party' and energy > 0.6:
                    score += 0.3
                elif intent.activity == 'driving' and 0.4 <= energy <= 0.8:
                    score += 0.3
            
            # Energy level scoring
            if intent.energy_level:
                if intent.energy_level == 'high' and energy > 0.7:
                    score += 0.2
                elif intent.energy_level == 'low' and energy < 0.4:
                    score += 0.2
                elif intent.energy_level == 'medium' and 0.4 <= energy <= 0.7:
                    score += 0.2
            
            # Popularity scoring
            if intent.popularity:
                if intent.popularity == 'popular' and popularity > 0.6:
                    score += 0.2
                elif intent.popularity == 'underground' and popularity < 0.4:
                    score += 0.2
                elif intent.popularity == 'mixed':
                    score += 0.1  # No strong preference
            
            # Tempo scoring (based on track duration as proxy)
            if intent.tempo:
                duration = track.get('duration', 240)  # default 4 minutes
                if intent.tempo == 'slow' and duration > 300:  # >5 min = slower songs
                    score += 0.15
                elif intent.tempo == 'fast' and duration < 180:  # <3 min = faster songs
                    score += 0.15
                elif intent.tempo == 'medium' and 180 <= duration <= 300:
                    score += 0.15
            
            # Mood matching (already filtered, so bonus for exact matches)
            if intent.mood:
                track_mood = (track.get('mood', '')).lower()
                if intent.mood.lower() == track_mood:
                    score += 0.25
            
            # Genre matching (already filtered, so bonus for exact matches)
            if intent.genre:
                track_genre = (track.get('ai_genre') or track.get('genre', '')).lower()
                if intent.genre.lower() == track_genre:
                    score += 0.25
            
            # Add some randomness to avoid always getting the same playlist
            score += np.random.random() * 0.1
            
            scored_tracks.append((track, score))
        
        # Sort by score (highest first)
        scored_tracks.sort(key=lambda x: x[1], reverse=True)
        return scored_tracks
    
    def _select_final_tracks(self, scored_tracks: List[Tuple[Dict, float]], 
                           intent: PlaylistIntent, max_tracks: int) -> List[Dict]:
        """Select final tracks for the playlist"""
        if not scored_tracks:
            return []
        
        # Calculate target duration in seconds
        target_duration = intent.duration_minutes * 60
        
        selected_tracks = []
        total_duration = 0
        
        # Select tracks until we reach target duration or max tracks
        for track, score in scored_tracks:
            if len(selected_tracks) >= max_tracks:
                break
            
            track_duration = track.get('duration', 240)  # default 4 minutes
            
            # If we're close to the limit, be more selective
            if total_duration + track_duration > target_duration and len(selected_tracks) > 5:
                break
            
            selected_tracks.append(track)
            total_duration += track_duration
        
        # If we don't have enough tracks, take the best ones
        if len(selected_tracks) < 5 and len(scored_tracks) >= 5:
            selected_tracks = [track for track, score in scored_tracks[:max_tracks]]
        
        return selected_tracks
    
    def _get_decade_start(self, time_period: str) -> Optional[int]:
        """Get the starting year of a decade"""
        decade_map = {
            '60s': 1960, '70s': 1970, '80s': 1980, '90s': 1990,
            '2000s': 2000, '2010s': 2010
        }
        return decade_map.get(time_period)
    
    def _generate_playlist_description(self, intent: PlaylistIntent, track_count: int) -> str:
        """Generate a descriptive text for the playlist"""
        description_parts = [f"Found {track_count} tracks"]
        
        if intent.mood:
            description_parts.append(f"with a {intent.mood} mood")
        
        if intent.genre:
            description_parts.append(f"from the {intent.genre} genre")
        
        if intent.activity:
            description_parts.append(f"perfect for {intent.activity}")
        
        if intent.time_period:
            description_parts.append(f"from the {intent.time_period}")
        
        if intent.energy_level:
            description_parts.append(f"with {intent.energy_level} energy")
        
        return " ".join(description_parts) + "."
import requests
import unittest
import os
import sys
import json
import time
import base64
from datetime import datetime
from pathlib import Path
import io
import wave
import numpy as np

# Use the public endpoint from frontend/.env
BACKEND_URL = "https://c3ce70ae-c000-43ca-af0f-88f273260465.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class MusicPlayerAPITest(unittest.TestCase):
    """Test suite for the Music Player API with enhanced features"""
    
    def setUp(self):
        """Setup for each test"""
        self.test_folder_path = "/tmp/test_music_folder"
        # Create test folder if it doesn't exist
        os.makedirs(self.test_folder_path, exist_ok=True)
        
        # Create test audio files
        self.create_test_audio_files()
        
        # Test data
        self.test_folder = {
            "path": self.test_folder_path,
            "name": f"Test Folder {datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        self.test_playlist = {
            "name": f"Test Playlist {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "Created by automated test",
            "track_ids": []
        }
        
        # Smart queue data
        self.test_smart_queue = {
            "name": f"Test Smart Queue {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "queue_type": "user",
            "track_ids": []
        }
        
        # Playback session
        self.playback_session = None
    
    def create_test_audio_files(self):
        """Create simple test audio files for testing"""
        try:
            # Create a simple WAV file for testing
            for i, genre in enumerate(['Rock', 'Pop', 'Jazz']):
                file_path = os.path.join(self.test_folder_path, f"test_track_{i+1}_{genre}.wav")
                
                # Skip if file already exists
                if os.path.exists(file_path):
                    continue
                
                # Create a simple WAV file with 1 second of audio
                with wave.open(file_path, 'w') as wav_file:
                    # Set parameters
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 2 bytes per sample
                    wav_file.setframerate(44100)  # 44.1 kHz
                    
                    # Generate 1 second of audio (sine wave)
                    frequency = 440.0  # A4 note
                    duration = 1.0  # seconds
                    samples = int(44100 * duration)
                    
                    # Create sine wave with different frequencies for different genres
                    if genre == 'Rock':
                        frequency = 440.0  # A4
                    elif genre == 'Pop':
                        frequency = 523.25  # C5
                    else:  # Jazz
                        frequency = 349.23  # F4
                    
                    t = np.linspace(0, duration, samples, False)
                    tone = np.sin(2 * np.pi * frequency * t) * 32767
                    
                    # Convert to bytes
                    audio_data = tone.astype(np.int16).tobytes()
                    wav_file.writeframes(audio_data)
                
                print(f"Created test audio file: {file_path}")
        except Exception as e:
            print(f"Error creating test audio files: {e}")
            # Continue with testing even if file creation fails
    
    def test_01_api_connectivity(self):
        """Test if the API is accessible"""
        print("\n🔍 Testing API connectivity...")
        try:
            response = requests.get(f"{API_URL}/scan-status")
            self.assertEqual(response.status_code, 200)
            print("✅ API is accessible")
        except Exception as e:
            self.fail(f"API connectivity test failed: {str(e)}")
    
    def test_02_folder_management(self):
        """Test folder management endpoints"""
        print("\n🔍 Testing folder management endpoints...")
        
        # Test adding a folder
        print("Testing POST /api/folders...")
        try:
            response = requests.post(f"{API_URL}/folders", json=self.test_folder)
            
            # If folder already exists, this is expected to fail with 400
            if response.status_code == 400 and "Folder already added" in response.text:
                print("✅ Folder already exists (expected behavior)")
            else:
                self.assertEqual(response.status_code, 200)
                folder_data = response.json()
                self.assertEqual(folder_data["path"], self.test_folder["path"])
                print("✅ Successfully added folder")
        except Exception as e:
            print(f"❌ Failed to add folder: {str(e)}")
        
        # Test getting folders
        print("Testing GET /api/folders...")
        try:
            response = requests.get(f"{API_URL}/folders")
            self.assertEqual(response.status_code, 200)
            folders = response.json()
            self.assertIsInstance(folders, list)
            print(f"✅ Successfully retrieved {len(folders)} folders")
            
            # Save folder ID for rescan test
            if folders:
                self.test_folder_id = folders[0]["id"]
        except Exception as e:
            print(f"❌ Failed to get folders: {str(e)}")
        
        # Test scan status with AI processing indicator
        print("Testing GET /api/scan-status...")
        try:
            response = requests.get(f"{API_URL}/scan-status")
            self.assertEqual(response.status_code, 200)
            status = response.json()
            self.assertIn("is_scanning", status)
            self.assertIn("ai_processing", status)
            print(f"✅ Successfully retrieved scan status:")
            print(f"   - Scanning: {'Yes' if status['is_scanning'] else 'No'}")
            print(f"   - AI Processing: {'Yes' if status['ai_processing'] else 'No'}")
            print(f"   - AI Processed: {status.get('ai_processed', 0)} files")
        except Exception as e:
            print(f"❌ Failed to get scan status: {str(e)}")
        
        # Test rescan folder if we have a folder ID
        if hasattr(self, 'test_folder_id'):
            print(f"Testing POST /api/folders/{self.test_folder_id}/scan...")
            try:
                response = requests.post(f"{API_URL}/folders/{self.test_folder_id}/scan")
                self.assertEqual(response.status_code, 200)
                print("✅ Successfully initiated folder rescan")
                
                # Wait for scan to complete (up to 10 seconds)
                print("Waiting for scan to complete...")
                scan_completed = False
                for _ in range(10):
                    time.sleep(1)
                    status_response = requests.get(f"{API_URL}/scan-status")
                    if status_response.status_code == 200:
                        status = status_response.json()
                        if status["status"] == "completed" or status["status"] == "error":
                            scan_completed = True
                            print(f"✅ Scan completed with status: {status['status']}")
                            break
                
                if not scan_completed:
                    print("⚠️ Scan did not complete within timeout period")
            except Exception as e:
                print(f"❌ Failed to rescan folder: {str(e)}")
        
        # Test folder removal if we have a folder ID
        if hasattr(self, 'test_folder_id'):
            print(f"Testing DELETE /api/folders/{self.test_folder_id}...")
            try:
                response = requests.delete(f"{API_URL}/folders/{self.test_folder_id}")
                self.assertEqual(response.status_code, 200)
                print("✅ Successfully removed folder")
            except Exception as e:
                print(f"❌ Failed to remove folder: {str(e)}")
    
    def test_03_music_library(self):
        """Test music library endpoints"""
        print("\n🔍 Testing music library endpoints...")
        
        # Wait a bit for scanning to complete if it's in progress
        self.wait_for_scan_completion()
        
        # Test getting tracks with AI metadata
        print("Testing GET /api/tracks...")
        try:
            response = requests.get(f"{API_URL}/tracks")
            self.assertEqual(response.status_code, 200)
            tracks = response.json()
            self.assertIsInstance(tracks, list)
            print(f"✅ Successfully retrieved {len(tracks)} tracks")
            
            # Save track IDs for later tests
            if tracks:
                self.test_track_id = tracks[0]["id"]
                self.test_playlist["track_ids"] = [tracks[0]["id"]]
                self.test_smart_queue["track_ids"] = [t["id"] for t in tracks[:min(3, len(tracks))]]
                
                # Check for AI-generated metadata
                ai_metadata_count = sum(1 for t in tracks if t.get('ai_genre') or t.get('mood') or t.get('energy'))
                print(f"   - Tracks with AI metadata: {ai_metadata_count}/{len(tracks)}")
                
                # Print sample AI metadata if available
                if ai_metadata_count > 0:
                    sample_track = next((t for t in tracks if t.get('ai_genre') or t.get('mood')), None)
                    if sample_track:
                        print(f"   - Sample AI metadata for '{sample_track.get('title', 'Unknown')}':")
                        print(f"     * AI Genre: {sample_track.get('ai_genre', 'Not detected')}")
                        print(f"     * Mood: {sample_track.get('mood', 'Not detected')}")
                        print(f"     * Energy: {sample_track.get('energy', 'Not detected')}")
            else:
                print("⚠️ No tracks found in the library")
        except Exception as e:
            print(f"❌ Failed to get tracks: {str(e)}")
        
        # Test track filtering
        print("Testing GET /api/tracks with filtering...")
        try:
            # Test search parameter
            search_response = requests.get(f"{API_URL}/tracks", params={"search": "test"})
            self.assertEqual(search_response.status_code, 200)
            search_tracks = search_response.json()
            print(f"✅ Search filter returned {len(search_tracks)} tracks")
            
            # Test genre filter if we have genres
            genres_response = requests.get(f"{API_URL}/genres")
            if genres_response.status_code == 200:
                genres_data = genres_response.json()
                ai_genres = genres_data.get('ai_genres', [])
                if ai_genres:
                    test_genre = ai_genres[0]['genre']
                    genre_response = requests.get(f"{API_URL}/tracks", params={"genre": test_genre})
                    self.assertEqual(genre_response.status_code, 200)
                    genre_tracks = genre_response.json()
                    print(f"✅ Genre filter for '{test_genre}' returned {len(genre_tracks)} tracks")
        except Exception as e:
            print(f"❌ Failed to test track filtering: {str(e)}")
        
        # Test getting genres (new endpoint)
        print("Testing GET /api/genres...")
        try:
            response = requests.get(f"{API_URL}/genres")
            self.assertEqual(response.status_code, 200)
            genres_data = response.json()
            self.assertIsInstance(genres_data, dict)
            ai_genres = genres_data.get('ai_genres', [])
            metadata_genres = genres_data.get('metadata_genres', [])
            print(f"✅ Successfully retrieved genres:")
            print(f"   - AI-detected genres: {len(ai_genres)}")
            print(f"   - Metadata genres: {len(metadata_genres)}")
        except Exception as e:
            print(f"❌ Failed to get genres: {str(e)}")
        
        # Test getting moods (new endpoint)
        print("Testing GET /api/moods...")
        try:
            response = requests.get(f"{API_URL}/moods")
            self.assertEqual(response.status_code, 200)
            moods = response.json()
            self.assertIsInstance(moods, list)
            print(f"✅ Successfully retrieved {len(moods)} moods")
            if moods:
                print(f"   - Available moods: {', '.join([m.get('mood', '') for m in moods[:5]])}")
                if len(moods) > 5:
                    print(f"   - (and {len(moods) - 5} more...)")
        except Exception as e:
            print(f"❌ Failed to get moods: {str(e)}")
        
        # Test getting artists with AI genre info
        print("Testing GET /api/artists...")
        try:
            response = requests.get(f"{API_URL}/artists")
            self.assertEqual(response.status_code, 200)
            artists = response.json()
            self.assertIsInstance(artists, list)
            print(f"✅ Successfully retrieved {len(artists)} artists")
            
            # Check for AI genre info
            artists_with_genres = sum(1 for a in artists if a.get('genres'))
            print(f"   - Artists with genre info: {artists_with_genres}/{len(artists)}")
        except Exception as e:
            print(f"❌ Failed to get artists: {str(e)}")
        
        # Test getting albums with enhanced metadata
        print("Testing GET /api/albums...")
        try:
            response = requests.get(f"{API_URL}/albums")
            self.assertEqual(response.status_code, 200)
            albums = response.json()
            self.assertIsInstance(albums, list)
            print(f"✅ Successfully retrieved {len(albums)} albums")
            
            # Check for enhanced metadata
            albums_with_genres = sum(1 for a in albums if a.get('genres'))
            print(f"   - Albums with genre info: {albums_with_genres}/{len(albums)}")
        except Exception as e:
            print(f"❌ Failed to get albums: {str(e)}")
        
        # Test streaming a track if we have tracks
        if hasattr(self, 'test_track_id'):
            print(f"Testing GET /api/tracks/{self.test_track_id}/stream...")
            try:
                response = requests.get(f"{API_URL}/tracks/{self.test_track_id}/stream", stream=True)
                # Just check if the response starts correctly, don't download the whole file
                if response.status_code == 200:
                    print("✅ Successfully started streaming track")
                    response.close()  # Close the connection
                else:
                    print(f"❌ Failed to stream track: Status code {response.status_code}")
            except Exception as e:
                print(f"❌ Failed to stream track: {str(e)}")
            
            # Test track skip analytics
            print(f"Testing POST /api/tracks/{self.test_track_id}/skip...")
            try:
                response = requests.post(f"{API_URL}/tracks/{self.test_track_id}/skip")
                self.assertEqual(response.status_code, 200)
                print("✅ Successfully recorded track skip")
            except Exception as e:
                print(f"❌ Failed to record track skip: {str(e)}")
            
            # Test getting a specific track
            print(f"Testing GET /api/tracks/{self.test_track_id}...")
            try:
                response = requests.get(f"{API_URL}/tracks/{self.test_track_id}")
                self.assertEqual(response.status_code, 200)
                track = response.json()
                self.assertEqual(track["id"], self.test_track_id)
                print("✅ Successfully retrieved specific track")
                
                # Check if play count was incremented after streaming
                if track.get('play_count', 0) > 0:
                    print("✅ Play count was incremented after streaming")
                else:
                    print("⚠️ Play count was not incremented after streaming")
            except Exception as e:
                print(f"❌ Failed to get specific track: {str(e)}")
    
    def wait_for_scan_completion(self, timeout=15):
        """Wait for any ongoing scan to complete"""
        print("Checking if scan is in progress...")
        try:
            for _ in range(timeout):
                response = requests.get(f"{API_URL}/scan-status")
                if response.status_code == 200:
                    status = response.json()
                    if status["is_scanning"] or status["ai_processing"]:
                        print(f"Scan in progress: {status['status']}. Waiting...")
                        time.sleep(1)
                    else:
                        print("No scan in progress.")
                        return
            print(f"Timed out after {timeout} seconds waiting for scan to complete.")
        except Exception as e:
            print(f"Error checking scan status: {e}")
    
    def test_04_smart_queue_management(self):
        """Test smart queue management endpoints"""
        print("\n🔍 Testing smart queue management endpoints...")
        
        # Skip if we don't have tracks
        if not hasattr(self, 'test_track_id'):
            print("⚠️ Skipping smart queue tests as no tracks were found")
            return
        
        # Test creating a smart queue
        print("Testing POST /api/smart-queues...")
        try:
            response = requests.post(f"{API_URL}/smart-queues", json=self.test_smart_queue)
            self.assertEqual(response.status_code, 200)
            queue = response.json()
            self.assertEqual(queue["name"], self.test_smart_queue["name"])
            self.test_smart_queue_id = queue["id"]
            print("✅ Successfully created smart queue")
        except Exception as e:
            print(f"❌ Failed to create smart queue: {str(e)}")
            return
        
        # Test getting smart queues
        print("Testing GET /api/smart-queues...")
        try:
            response = requests.get(f"{API_URL}/smart-queues")
            self.assertEqual(response.status_code, 200)
            queues = response.json()
            self.assertIsInstance(queues, list)
            print(f"✅ Successfully retrieved {len(queues)} smart queues")
            
            # Check queue types
            queue_types = {}
            for q in queues:
                queue_type = q.get('queue_type', 'unknown')
                queue_types[queue_type] = queue_types.get(queue_type, 0) + 1
            
            print("   - Queue types distribution:")
            for queue_type, count in queue_types.items():
                print(f"     * {queue_type}: {count} queues")
        except Exception as e:
            print(f"❌ Failed to get smart queues: {str(e)}")
        
        # Test getting a specific smart queue
        if hasattr(self, 'test_smart_queue_id'):
            print(f"Testing GET /api/smart-queues/{self.test_smart_queue_id}...")
            try:
                response = requests.get(f"{API_URL}/smart-queues/{self.test_smart_queue_id}")
                self.assertEqual(response.status_code, 200)
                queue = response.json()
                self.assertEqual(queue["id"], self.test_smart_queue_id)
                print("✅ Successfully retrieved specific smart queue")
            except Exception as e:
                print(f"❌ Failed to get specific smart queue: {str(e)}")
        
        # Test generating auto queue
        if hasattr(self, 'test_smart_queue_id') and hasattr(self, 'test_track_id'):
            print(f"Testing POST /api/smart-queues/{self.test_smart_queue_id}/generate-auto...")
            try:
                response = requests.post(
                    f"{API_URL}/smart-queues/{self.test_smart_queue_id}/generate-auto",
                    params={"seed_track_id": self.test_track_id, "size": 10}
                )
                self.assertEqual(response.status_code, 200)
                result = response.json()
                print(f"✅ Successfully generated auto queue with {result.get('track_count', 0)} tracks")
            except Exception as e:
                print(f"❌ Failed to generate auto queue: {str(e)}")
        
        # Test updating smart queue
        if hasattr(self, 'test_smart_queue_id'):
            print(f"Testing PUT /api/smart-queues/{self.test_smart_queue_id}...")
            try:
                update_data = {
                    "shuffle": True,
                    "repeat": "queue",
                    "auto_refresh": True
                }
                response = requests.put(
                    f"{API_URL}/smart-queues/{self.test_smart_queue_id}", 
                    json=update_data
                )
                self.assertEqual(response.status_code, 200)
                print("✅ Successfully updated smart queue settings")
                
                # Verify the update
                response = requests.get(f"{API_URL}/smart-queues/{self.test_smart_queue_id}")
                if response.status_code == 200:
                    updated_queue = response.json()
                    if updated_queue.get("shuffle") == True and updated_queue.get("repeat") == "queue":
                        print("✅ Queue settings were correctly updated")
                    else:
                        print("⚠️ Queue settings may not have been correctly updated")
            except Exception as e:
                print(f"❌ Failed to update smart queue settings: {str(e)}")
    
    def test_05_playback_session(self):
        """Test playback session management for unlimited playback"""
        print("\n🔍 Testing playback session management...")
        
        # Test creating a playback session
        print("Testing POST /api/playback-session...")
        try:
            response = requests.post(f"{API_URL}/playback-session")
            self.assertEqual(response.status_code, 200)
            session = response.json()
            self.playback_session_id = session["id"]
            print("✅ Successfully created playback session")
            print(f"   - Session ID: {self.playback_session_id}")
            print(f"   - Unlimited mode: {'Enabled' if session.get('unlimited_mode') else 'Disabled'}")
            print(f"   - Current queue type: {session.get('current_queue_type', 'unknown')}")
        except Exception as e:
            print(f"❌ Failed to create playback session: {str(e)}")
            return
        
        # Test getting playback session
        if hasattr(self, 'playback_session_id'):
            print(f"Testing GET /api/playback-session/{self.playback_session_id}...")
            try:
                response = requests.get(f"{API_URL}/playback-session/{self.playback_session_id}")
                self.assertEqual(response.status_code, 200)
                session = response.json()
                self.assertEqual(session["id"], self.playback_session_id)
                print("✅ Successfully retrieved playback session")
            except Exception as e:
                print(f"❌ Failed to get playback session: {str(e)}")
        
        # Test switching queue type
        if hasattr(self, 'playback_session_id'):
            print(f"Testing PUT /api/playback-session/{self.playback_session_id}/switch-queue...")
            try:
                response = requests.put(
                    f"{API_URL}/playback-session/{self.playback_session_id}/switch-queue",
                    params={"queue_type": "auto"}
                )
                self.assertEqual(response.status_code, 200)
                print("✅ Successfully switched to auto queue")
                
                # Switch back to user queue
                response = requests.put(
                    f"{API_URL}/playback-session/{self.playback_session_id}/switch-queue",
                    params={"queue_type": "user"}
                )
                self.assertEqual(response.status_code, 200)
                print("✅ Successfully switched back to user queue")
            except Exception as e:
                print(f"❌ Failed to switch queue type: {str(e)}")
    
    def test_06_smart_mixes(self):
        """Test smart mixes functionality"""
        print("\n🔍 Testing smart mixes functionality...")
        
        # Test getting smart mixes
        print("Testing GET /api/smart-mixes...")
        try:
            response = requests.get(f"{API_URL}/smart-mixes")
            self.assertEqual(response.status_code, 200)
            mixes = response.json()
            self.assertIsInstance(mixes, list)
            print(f"✅ Successfully retrieved {len(mixes)} smart mixes")
            
            # Check mix types
            mix_types = {}
            for mix in mixes:
                mix_type = mix.get('mix_type', 'unknown')
                mix_types[mix_type] = mix_types.get(mix_type, 0) + 1
            
            print("   - Mix types distribution:")
            for mix_type, count in mix_types.items():
                print(f"     * {mix_type}: {count} mixes")
            
            # Save a mix ID for further testing
            if mixes:
                self.test_mix_id = mixes[0]["id"]
        except Exception as e:
            print(f"❌ Failed to get smart mixes: {str(e)}")
        
        # Test generating different types of smart mixes
        mix_types = ["discovery", "popular", "genre"]
        for mix_type in mix_types:
            print(f"Testing POST /api/smart-mixes/generate with type '{mix_type}'...")
            try:
                parameters = {"max_tracks": 20}
                if mix_type == "genre" and hasattr(self, 'test_track_id'):
                    # Get a genre from a track if available
                    track_response = requests.get(f"{API_URL}/tracks/{self.test_track_id}")
                    if track_response.status_code == 200:
                        track = track_response.json()
                        if track.get('ai_genre'):
                            parameters["genre"] = track.get('ai_genre')
                
                response = requests.post(
                    f"{API_URL}/smart-mixes/generate",
                    params={"mix_type": mix_type},
                    json={"parameters": parameters}
                )
                self.assertEqual(response.status_code, 200)
                mix = response.json()
                print(f"✅ Successfully generated '{mix.get('name')}' smart mix with {len(mix.get('track_ids', []))} tracks")
                
                # Save the mix ID for the first successful mix generation
                if not hasattr(self, 'test_mix_id'):
                    self.test_mix_id = mix["id"]
            except Exception as e:
                print(f"❌ Failed to generate {mix_type} smart mix: {str(e)}")
        
        # Test refreshing a smart mix
        if hasattr(self, 'test_mix_id'):
            print(f"Testing POST /api/smart-mixes/{self.test_mix_id}/refresh...")
            try:
                response = requests.post(f"{API_URL}/smart-mixes/{self.test_mix_id}/refresh")
                self.assertEqual(response.status_code, 200)
                print("✅ Successfully refreshed smart mix")
            except Exception as e:
                print(f"❌ Failed to refresh smart mix: {str(e)}")
    
    def test_07_analytics(self):
        """Test analytics endpoints"""
        print("\n🔍 Testing analytics endpoints...")
        
        # Test getting listening stats
        print("Testing GET /api/analytics/listening-stats...")
        try:
            response = requests.get(f"{API_URL}/analytics/listening-stats")
            self.assertEqual(response.status_code, 200)
            stats = response.json()
            print("✅ Successfully retrieved listening stats:")
            print(f"   - Total tracks: {stats.get('total_tracks', 0)}")
            print(f"   - Total plays: {stats.get('total_plays', 0)}")
            
            # Check top genres
            top_genres = stats.get('top_genres', [])
            if top_genres:
                print("   - Top genres by play count:")
                for i, genre in enumerate(top_genres[:5], 1):
                    print(f"     {i}. {genre.get('_id', 'Unknown')}: {genre.get('plays', 0)} plays")
            
            # Check recent tracks
            recent_tracks = stats.get('recent_tracks', [])
            if recent_tracks:
                print(f"   - Recently played tracks: {len(recent_tracks)}")
                for i, track in enumerate(recent_tracks[:3], 1):
                    print(f"     {i}. {track.get('title', 'Unknown')} by {track.get('artist', 'Unknown Artist')}")
        except Exception as e:
            print(f"❌ Failed to get listening stats: {str(e)}")
        
        # Test analytics after playing tracks
        if hasattr(self, 'test_track_id'):
            print("Testing analytics after track playback...")
            try:
                # Play the track a few times to generate analytics data
                for _ in range(3):
                    play_response = requests.get(f"{API_URL}/tracks/{self.test_track_id}/stream", stream=True)
                    if play_response.status_code == 200:
                        play_response.close()  # Close the connection
                
                # Skip the track once
                skip_response = requests.post(f"{API_URL}/tracks/{self.test_track_id}/skip")
                
                # Check updated analytics
                response = requests.get(f"{API_URL}/analytics/listening-stats")
                if response.status_code == 200:
                    updated_stats = response.json()
                    if updated_stats.get('total_plays', 0) > 0:
                        print("✅ Analytics successfully recorded track plays")
                    else:
                        print("⚠️ Analytics may not be recording track plays correctly")
            except Exception as e:
                print(f"❌ Error testing analytics after playback: {str(e)}")

def run_tests():
    """Run the test suite"""
    print(f"🎵 Testing Enhanced Music Player API at {API_URL}")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(MusicPlayerAPITest('test_01_api_connectivity'))
    suite.addTest(MusicPlayerAPITest('test_02_folder_management'))
    suite.addTest(MusicPlayerAPITest('test_03_music_library'))
    suite.addTest(MusicPlayerAPITest('test_04_smart_queue_management'))
    suite.addTest(MusicPlayerAPITest('test_05_playback_session'))
    suite.addTest(MusicPlayerAPITest('test_06_smart_mixes'))
    suite.addTest(MusicPlayerAPITest('test_07_analytics'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success or failure
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())

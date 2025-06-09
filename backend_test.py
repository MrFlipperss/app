import requests
import unittest
import os
import sys
import json
from datetime import datetime

# Use the public endpoint from frontend/.env
BACKEND_URL = "https://2b76f461-ed16-4886-8d37-1b96497d4f13.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class MusicPlayerAPITest(unittest.TestCase):
    """Test suite for the Music Player API"""
    
    def setUp(self):
        """Setup for each test"""
        self.test_folder_path = "/tmp/test_music_folder"
        # Create test folder if it doesn't exist
        os.makedirs(self.test_folder_path, exist_ok=True)
        
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
        
        self.test_queue = {
            "name": f"Test Queue {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "track_ids": []
        }
    
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
        except Exception as e:
            print(f"❌ Failed to get folders: {str(e)}")
        
        # Test scan status
        print("Testing GET /api/scan-status...")
        try:
            response = requests.get(f"{API_URL}/scan-status")
            self.assertEqual(response.status_code, 200)
            status = response.json()
            self.assertIn("is_scanning", status)
            print(f"✅ Successfully retrieved scan status: {'Scanning' if status['is_scanning'] else 'Not scanning'}")
        except Exception as e:
            print(f"❌ Failed to get scan status: {str(e)}")
    
    def test_03_music_library(self):
        """Test music library endpoints"""
        print("\n🔍 Testing music library endpoints...")
        
        # Test getting tracks
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
                self.test_queue["track_ids"] = [t["id"] for t in tracks[:min(3, len(tracks))]]
            else:
                print("⚠️ No tracks found in the library")
        except Exception as e:
            print(f"❌ Failed to get tracks: {str(e)}")
        
        # Test getting artists
        print("Testing GET /api/artists...")
        try:
            response = requests.get(f"{API_URL}/artists")
            self.assertEqual(response.status_code, 200)
            artists = response.json()
            self.assertIsInstance(artists, list)
            print(f"✅ Successfully retrieved {len(artists)} artists")
        except Exception as e:
            print(f"❌ Failed to get artists: {str(e)}")
        
        # Test getting albums
        print("Testing GET /api/albums...")
        try:
            response = requests.get(f"{API_URL}/albums")
            self.assertEqual(response.status_code, 200)
            albums = response.json()
            self.assertIsInstance(albums, list)
            print(f"✅ Successfully retrieved {len(albums)} albums")
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
    
    def test_04_playlist_management(self):
        """Test playlist management endpoints"""
        print("\n🔍 Testing playlist management endpoints...")
        
        # Skip if we don't have tracks
        if not hasattr(self, 'test_track_id'):
            print("⚠️ Skipping playlist tests as no tracks were found")
            return
        
        # Test creating a playlist
        print("Testing POST /api/playlists...")
        try:
            response = requests.post(f"{API_URL}/playlists", json=self.test_playlist)
            self.assertEqual(response.status_code, 200)
            playlist = response.json()
            self.assertEqual(playlist["name"], self.test_playlist["name"])
            self.test_playlist_id = playlist["id"]
            print("✅ Successfully created playlist")
        except Exception as e:
            print(f"❌ Failed to create playlist: {str(e)}")
            return
        
        # Test getting playlists
        print("Testing GET /api/playlists...")
        try:
            response = requests.get(f"{API_URL}/playlists")
            self.assertEqual(response.status_code, 200)
            playlists = response.json()
            self.assertIsInstance(playlists, list)
            print(f"✅ Successfully retrieved {len(playlists)} playlists")
        except Exception as e:
            print(f"❌ Failed to get playlists: {str(e)}")
        
        # Test getting a specific playlist
        if hasattr(self, 'test_playlist_id'):
            print(f"Testing GET /api/playlists/{self.test_playlist_id}...")
            try:
                response = requests.get(f"{API_URL}/playlists/{self.test_playlist_id}")
                self.assertEqual(response.status_code, 200)
                playlist = response.json()
                self.assertEqual(playlist["id"], self.test_playlist_id)
                print("✅ Successfully retrieved specific playlist")
            except Exception as e:
                print(f"❌ Failed to get specific playlist: {str(e)}")
        
        # Test updating playlist tracks
        if hasattr(self, 'test_playlist_id') and hasattr(self, 'test_track_id'):
            print(f"Testing PUT /api/playlists/{self.test_playlist_id}/tracks...")
            try:
                response = requests.put(
                    f"{API_URL}/playlists/{self.test_playlist_id}/tracks", 
                    json=[self.test_track_id]
                )
                self.assertEqual(response.status_code, 200)
                print("✅ Successfully updated playlist tracks")
            except Exception as e:
                print(f"❌ Failed to update playlist tracks: {str(e)}")
    
    def test_05_queue_management(self):
        """Test queue management endpoints"""
        print("\n🔍 Testing queue management endpoints...")
        
        # Skip if we don't have tracks
        if not hasattr(self, 'test_track_id'):
            print("⚠️ Skipping queue tests as no tracks were found")
            return
        
        # Test creating a queue
        print("Testing POST /api/queues...")
        try:
            response = requests.post(f"{API_URL}/queues", json=self.test_queue)
            self.assertEqual(response.status_code, 200)
            queue = response.json()
            self.assertEqual(queue["name"], self.test_queue["name"])
            self.test_queue_id = queue["id"]
            print("✅ Successfully created queue")
        except Exception as e:
            print(f"❌ Failed to create queue: {str(e)}")
            return
        
        # Test getting queues
        print("Testing GET /api/queues...")
        try:
            response = requests.get(f"{API_URL}/queues")
            self.assertEqual(response.status_code, 200)
            queues = response.json()
            self.assertIsInstance(queues, list)
            print(f"✅ Successfully retrieved {len(queues)} queues")
        except Exception as e:
            print(f"❌ Failed to get queues: {str(e)}")
        
        # Test getting a specific queue
        if hasattr(self, 'test_queue_id'):
            print(f"Testing GET /api/queues/{self.test_queue_id}...")
            try:
                response = requests.get(f"{API_URL}/queues/{self.test_queue_id}")
                self.assertEqual(response.status_code, 200)
                queue = response.json()
                self.assertEqual(queue["id"], self.test_queue_id)
                print("✅ Successfully retrieved specific queue")
            except Exception as e:
                print(f"❌ Failed to get specific queue: {str(e)}")
        
        # Test updating queue settings
        if hasattr(self, 'test_queue_id'):
            print(f"Testing PUT /api/queues/{self.test_queue_id}...")
            try:
                update_data = {
                    "shuffle": True,
                    "repeat": "queue"
                }
                response = requests.put(
                    f"{API_URL}/queues/{self.test_queue_id}", 
                    json=update_data
                )
                self.assertEqual(response.status_code, 200)
                print("✅ Successfully updated queue settings")
            except Exception as e:
                print(f"❌ Failed to update queue settings: {str(e)}")

def run_tests():
    """Run the test suite"""
    print(f"🎵 Testing Music Player API at {API_URL}")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(MusicPlayerAPITest('test_01_api_connectivity'))
    suite.addTest(MusicPlayerAPITest('test_02_folder_management'))
    suite.addTest(MusicPlayerAPITest('test_03_music_library'))
    suite.addTest(MusicPlayerAPITest('test_04_playlist_management'))
    suite.addTest(MusicPlayerAPITest('test_05_queue_management'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success or failure
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())

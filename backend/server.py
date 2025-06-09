from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import asyncio
import json
from mutagen import File as MutagenFile
from mutagen.id3 import ID3NoHeaderError
import magic
import hashlib
import io
import base64
from PIL import Image
import sys
from pathlib import Path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
from audio_analyzer import AudioAnalyzer, RecommendationEngine
from playlist_ai import PlaylistAI
import numpy as np

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize AI components
audio_analyzer = AudioAnalyzer()
recommendation_engine = RecommendationEngine(audio_analyzer)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enhanced Models
class MusicFolder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    path: str
    name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MusicFolderCreate(BaseModel):
    path: str
    name: Optional[str] = None

class Track(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str
    filename: str
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    track_number: Optional[int] = None
    duration: Optional[float] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    file_format: str
    file_size: int
    artwork_data: Optional[str] = None
    # AI-Enhanced fields
    audio_features: Optional[Dict[str, float]] = None
    ai_genre: Optional[str] = None
    ai_genre_confidence: Optional[float] = None
    mood: Optional[str] = None
    energy: Optional[float] = None
    popularity_score: Optional[float] = None
    # Analytics
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_played: Optional[datetime] = None
    play_count: int = 0
    skip_count: int = 0
    like_score: Optional[float] = None

class SmartQueue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    queue_type: str  # "user", "auto", "mix"
    track_ids: List[str] = []
    current_index: int = 0
    shuffle: bool = False
    repeat: str = "none"  # none, track, queue
    # Smart features
    seed_track_id: Optional[str] = None
    generation_params: Optional[Dict[str, Any]] = None
    auto_refresh: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PlaybackSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_queue_id: Optional[str] = None
    auto_queue_id: Optional[str] = None
    current_track_id: Optional[str] = None
    current_queue_type: str = "user"  # "user" or "auto"
    unlimited_mode: bool = True
    session_start: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

class SmartMix(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    track_ids: List[str] = []
    mix_type: str  # "genre", "mood", "year", "energy", "discovery"
    parameters: Dict[str, Any] = {}
    auto_generated: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    refreshed_at: datetime = Field(default_factory=datetime.utcnow)

class Playlist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    track_ids: List[str] = []
    is_auto_generated: bool = False
    mood: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    track_ids: List[str] = []

class ScanStatus(BaseModel):
    is_scanning: bool = False
    current_folder: Optional[str] = None
    processed_files: int = 0
    total_files: int = 0
    status: str = "idle"
    ai_processing: bool = False
    ai_processed: int = 0

# Global scan status
scan_status = ScanStatus()

# Helper functions
def extract_audio_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from audio file"""
    try:
        audio_file = MutagenFile(file_path)
        if audio_file is None:
            return {}
        
        metadata = {}
        
        # Common metadata
        metadata['title'] = audio_file.get('TIT2', [str(Path(file_path).stem)])[0] if audio_file.get('TIT2') else str(Path(file_path).stem)
        metadata['artist'] = audio_file.get('TPE1', ['Unknown Artist'])[0] if audio_file.get('TPE1') else 'Unknown Artist'
        metadata['album'] = audio_file.get('TALB', ['Unknown Album'])[0] if audio_file.get('TALB') else 'Unknown Album'
        metadata['album_artist'] = audio_file.get('TPE2', [metadata['artist']])[0] if audio_file.get('TPE2') else metadata['artist']
        metadata['genre'] = audio_file.get('TCON', ['Unknown'])[0] if audio_file.get('TCON') else 'Unknown'
        
        # Try to get year
        year_tag = audio_file.get('TDRC') or audio_file.get('TYER')
        if year_tag:
            try:
                metadata['year'] = int(str(year_tag[0])[:4])
            except:
                metadata['year'] = None
        
        # Track number
        track_tag = audio_file.get('TRCK')
        if track_tag:
            try:
                track_str = str(track_tag[0]).split('/')[0]
                metadata['track_number'] = int(track_str)
            except:
                metadata['track_number'] = None
        
        # Duration and quality info
        if hasattr(audio_file, 'info'):
            metadata['duration'] = getattr(audio_file.info, 'length', 0.0)
            metadata['bitrate'] = getattr(audio_file.info, 'bitrate', 0)
            metadata['sample_rate'] = getattr(audio_file.info, 'sample_rate', 0)
        
        # Extract artwork
        artwork_data = None
        if hasattr(audio_file, 'tags') and audio_file.tags:
            for key in ['APIC:', 'APIC:Cover', 'APIC:Front Cover']:
                if key in audio_file.tags:
                    try:
                        artwork_bytes = audio_file.tags[key].data
                        artwork_data = base64.b64encode(artwork_bytes).decode('utf-8')
                        break
                    except:
                        continue
        
        metadata['artwork_data'] = artwork_data
        
        return metadata
    except Exception as e:
        logger.error(f"Error extracting metadata from {file_path}: {e}")
        return {}

def get_file_format(file_path: str) -> str:
    """Determine file format"""
    try:
        mime = magic.from_file(file_path, mime=True)
        if 'flac' in mime:
            return 'FLAC'
        elif 'mpeg' in mime or 'mp3' in mime:
            return 'MP3'
        elif 'wav' in mime:
            return 'WAV'
        elif 'ogg' in mime:
            return 'OGG'
        else:
            return Path(file_path).suffix.upper().lstrip('.')
    except:
        return Path(file_path).suffix.upper().lstrip('.')

async def process_audio_intelligence(track_id: str):
    """Process audio intelligence for a track in background"""
    try:
        track = await db.tracks.find_one({"id": track_id})
        if not track:
            return
        
        # Extract audio features
        features = audio_analyzer.extract_audio_features(track['file_path'])
        
        # Classify genre
        ai_genre, confidence = audio_analyzer.classify_genre(features)
        
        # Get mood and energy
        mood, energy = audio_analyzer.get_mood_energy(features)
        
        # Calculate popularity score
        popularity = recommendation_engine.calculate_popularity_score(track)
        
        # Update track with AI data
        update_data = {
            'audio_features': features,
            'ai_genre': ai_genre,
            'ai_genre_confidence': confidence,
            'mood': mood,
            'energy': energy,
            'popularity_score': popularity
        }
        
        await db.tracks.update_one(
            {"id": track_id},
            {"$set": update_data}
        )
        
        logger.info(f"Processed AI features for track {track['title']} - Genre: {ai_genre} ({confidence:.2f})")
        
    except Exception as e:
        logger.error(f"Error processing audio intelligence for track {track_id}: {e}")

async def scan_folder_for_music(folder_path: str):
    """Enhanced scan with AI processing"""
    global scan_status
    supported_extensions = {'.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac'}
    
    try:
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Count total files first
        all_files = list(folder_path.rglob('*'))
        music_files = [f for f in all_files if f.suffix.lower() in supported_extensions]
        
        scan_status.total_files = len(music_files)
        scan_status.processed_files = 0
        scan_status.ai_processed = 0
        scan_status.status = "scanning"
        scan_status.is_scanning = True
        scan_status.ai_processing = False
        
        track_ids_for_ai = []
        
        for file_path in music_files:
            try:
                scan_status.current_folder = str(file_path.parent)
                
                # Check if file already exists in database
                existing_track = await db.tracks.find_one({"file_path": str(file_path)})
                if existing_track:
                    scan_status.processed_files += 1
                    if not existing_track.get('audio_features'):
                        track_ids_for_ai.append(existing_track['id'])
                    continue
                
                # Extract metadata
                metadata = extract_audio_metadata(str(file_path))
                file_format = get_file_format(str(file_path))
                file_size = file_path.stat().st_size
                
                # Create track object
                track_data = {
                    "id": str(uuid.uuid4()),
                    "file_path": str(file_path),
                    "filename": file_path.name,
                    "file_format": file_format,
                    "file_size": file_size,
                    "created_at": datetime.utcnow(),
                    "play_count": 0,
                    "skip_count": 0,
                    **metadata
                }
                
                # Insert into database
                await db.tracks.insert_one(track_data)
                track_ids_for_ai.append(track_data['id'])
                scan_status.processed_files += 1
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                continue
        
        scan_status.status = "ai_processing"
        scan_status.is_scanning = False
        scan_status.ai_processing = True
        
        # Process AI features in background
        for track_id in track_ids_for_ai:
            try:
                await process_audio_intelligence(track_id)
                scan_status.ai_processed += 1
            except Exception as e:
                logger.error(f"Error in AI processing: {e}")
                continue
        
        scan_status.ai_processing = False
        scan_status.status = "completed"
        logger.info(f"Scan completed. Processed {scan_status.processed_files} files with AI analysis")
        
        # Generate initial smart mixes
        await generate_smart_mixes()
        
    except Exception as e:
        scan_status.status = "error"
        scan_status.is_scanning = False
        scan_status.ai_processing = False
        logger.error(f"Error scanning folder {folder_path}: {e}")

async def generate_smart_mixes():
    """Generate automatic smart mixes based on the music library"""
    try:
        tracks = await db.tracks.find({}).to_list(1000)
        if len(tracks) < 5:
            return
        
        # Clear existing auto-generated mixes
        await db.smart_mixes.delete_many({"auto_generated": True})
        
        # Generate genre-based mixes
        genres = {}
        for track in tracks:
            genre = track.get('ai_genre') or track.get('genre', 'Unknown')
            if genre not in genres:
                genres[genre] = []
            genres[genre].append(track['id'])
        
        for genre, track_ids in genres.items():
            if len(track_ids) >= 5:  # Minimum tracks for a mix
                mix = SmartMix(
                    name=f"{genre} Mix",
                    description=f"Auto-generated mix featuring {genre} tracks",
                    track_ids=track_ids[:50],  # Limit to 50 tracks
                    mix_type="genre",
                    parameters={"genre": genre}
                )
                await db.smart_mixes.insert_one(mix.dict())
        
        # Generate mood-based mixes
        moods = {}
        for track in tracks:
            mood = track.get('mood', 'Unknown')
            if mood not in moods:
                moods[mood] = []
            moods[mood].append(track['id'])
        
        for mood, track_ids in moods.items():
            if len(track_ids) >= 5:
                mix = SmartMix(
                    name=f"{mood} Mood",
                    description=f"Auto-generated mix for {mood.lower()} listening",
                    track_ids=track_ids[:50],
                    mix_type="mood",
                    parameters={"mood": mood}
                )
                await db.smart_mixes.insert_one(mix.dict())
        
        # Generate energy-based mixes
        high_energy = [t['id'] for t in tracks if t.get('energy', 0.5) > 0.7]
        low_energy = [t['id'] for t in tracks if t.get('energy', 0.5) < 0.3]
        
        if len(high_energy) >= 5:
            mix = SmartMix(
                name="High Energy",
                description="Energetic tracks to get you moving",
                track_ids=high_energy[:50],
                mix_type="energy",
                parameters={"energy": "high"}
            )
            await db.smart_mixes.insert_one(mix.dict())
        
        if len(low_energy) >= 5:
            mix = SmartMix(
                name="Chill Vibes",
                description="Relaxing tracks for calm moments",
                track_ids=low_energy[:50],
                mix_type="energy",
                parameters={"energy": "low"}
            )
            await db.smart_mixes.insert_one(mix.dict())
        
        logger.info("Generated smart mixes successfully")
        
    except Exception as e:
        logger.error(f"Error generating smart mixes: {e}")

# Music folder management endpoints
@api_router.post("/folders", response_model=MusicFolder)
async def add_music_folder(folder_data: MusicFolderCreate):
    """Add a new music folder to scan"""
    folder_path = Path(folder_data.path)
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Folder path does not exist")
    
    if not folder_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")
    
    # Check if folder already exists
    existing_folder = await db.music_folders.find_one({"path": folder_data.path})
    if existing_folder:
        raise HTTPException(status_code=400, detail="Folder already added")
    
    folder_name = folder_data.name or folder_path.name
    folder = MusicFolder(
        path=folder_data.path,
        name=folder_name
    )
    
    await db.music_folders.insert_one(folder.dict())
    
    # Start scanning in background
    asyncio.create_task(scan_folder_for_music(folder_data.path))
    
    return folder

@api_router.get("/folders", response_model=List[MusicFolder])
async def get_music_folders():
    """Get all music folders"""
    folders = await db.music_folders.find({"is_active": True}).to_list(1000)
    return [MusicFolder(**folder) for folder in folders]

@api_router.delete("/folders/{folder_id}")
async def remove_music_folder(folder_id: str):
    """Remove a music folder"""
    result = await db.music_folders.update_one(
        {"id": folder_id},
        {"$set": {"is_active": False}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    return {"message": "Folder removed successfully"}

@api_router.post("/folders/{folder_id}/scan")
async def rescan_folder(folder_id: str):
    """Rescan a specific folder"""
    folder = await db.music_folders.find_one({"id": folder_id, "is_active": True})
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Start scanning in background
    asyncio.create_task(scan_folder_for_music(folder["path"]))
    
    return {"message": "Scan started"}

@api_router.get("/scan-status", response_model=ScanStatus)
async def get_scan_status():
    """Get current scan status"""
    return scan_status

# Enhanced music library endpoints
@api_router.get("/tracks", response_model=List[Track])
async def get_tracks(limit: int = 100, offset: int = 0, search: Optional[str] = None, 
                    genre: Optional[str] = None, mood: Optional[str] = None):
    """Get tracks with enhanced filtering"""
    query = {}
    
    if search:
        query = {
            "$or": [
                {"title": {"$regex": search, "$options": "i"}},
                {"artist": {"$regex": search, "$options": "i"}},
                {"album": {"$regex": search, "$options": "i"}},
                {"ai_genre": {"$regex": search, "$options": "i"}}
            ]
        }
    
    if genre:
        if "$and" not in query:
            query["$and"] = []
        query["$and"].append({
            "$or": [
                {"genre": genre},
                {"ai_genre": genre}
            ]
        })
    
    if mood:
        if "$and" not in query:
            query["$and"] = []
        query["$and"].append({"mood": mood})
    
    tracks = await db.tracks.find(query).skip(offset).limit(limit).to_list(limit)
    return [Track(**track) for track in tracks]

@api_router.get("/tracks/{track_id}", response_model=Track)
async def get_track(track_id: str):
    """Get a specific track"""
    track = await db.tracks.find_one({"id": track_id})
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return Track(**track)

@api_router.get("/tracks/{track_id}/stream")
async def stream_track(track_id: str):
    """Stream audio file with enhanced analytics"""
    track = await db.tracks.find_one({"id": track_id})
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    file_path = Path(track["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Update play count and analytics
    await db.tracks.update_one(
        {"id": track_id},
        {
            "$inc": {"play_count": 1},
            "$set": {"last_played": datetime.utcnow()}
        }
    )
    
    # Update popularity score
    popularity = recommendation_engine.calculate_popularity_score(track)
    await db.tracks.update_one(
        {"id": track_id},
        {"$set": {"popularity_score": popularity}}
    )
    
    return FileResponse(
        path=str(file_path),
        media_type=f"audio/{track['file_format'].lower()}",
        filename=track["filename"]
    )

@api_router.post("/tracks/{track_id}/skip")
async def track_skipped(track_id: str):
    """Record track skip for analytics"""
    await db.tracks.update_one(
        {"id": track_id},
        {"$inc": {"skip_count": 1}}
    )
    return {"message": "Skip recorded"}

@api_router.get("/artists")
async def get_artists():
    """Get all artists with AI genre info"""
    artists = await db.tracks.distinct("artist")
    artist_data = []
    
    for artist in artists:
        if artist and artist != "Unknown Artist":
            # Get genres for this artist
            artist_tracks = await db.tracks.find({"artist": artist}).to_list(100)
            genres = list(set([t.get('ai_genre') or t.get('genre') for t in artist_tracks if t.get('ai_genre') or t.get('genre')]))
            
            artist_data.append({
                "name": artist,
                "genres": genres,
                "track_count": len(artist_tracks)
            })
    
    return artist_data

@api_router.get("/albums")
async def get_albums(artist: Optional[str] = None):
    """Get albums with enhanced metadata"""
    match_stage = {}
    if artist:
        match_stage["artist"] = artist
    
    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})
    
    pipeline.extend([
        {
            "$group": {
                "_id": {
                    "album": "$album",
                    "artist": "$album_artist"
                },
                "track_count": {"$sum": 1},
                "artwork_data": {"$first": "$artwork_data"},
                "genres": {"$addToSet": "$ai_genre"},
                "year": {"$first": "$year"},
                "total_duration": {"$sum": "$duration"}
            }
        },
        {
            "$project": {
                "album": "$_id.album",
                "artist": "$_id.artist",
                "track_count": 1,
                "artwork_data": 1,
                "genres": 1,
                "year": 1,
                "total_duration": 1,
                "_id": 0
            }
        }
    ])
    
    albums = await db.tracks.aggregate(pipeline).to_list(1000)
    return albums

@api_router.get("/genres")
async def get_genres():
    """Get all genres with track counts"""
    # Get AI-detected genres
    ai_genres = await db.tracks.aggregate([
        {"$match": {"ai_genre": {"$ne": None}}},
        {"$group": {"_id": "$ai_genre", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(100)
    
    # Get metadata genres
    meta_genres = await db.tracks.aggregate([
        {"$match": {"genre": {"$ne": None, "$ne": "Unknown"}}},
        {"$group": {"_id": "$genre", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(100)
    
    return {
        "ai_genres": [{"genre": g["_id"], "count": g["count"]} for g in ai_genres],
        "metadata_genres": [{"genre": g["_id"], "count": g["count"]} for g in meta_genres]
    }

@api_router.get("/moods")
async def get_moods():
    """Get all detected moods"""
    moods = await db.tracks.aggregate([
        {"$match": {"mood": {"$ne": None}}},
        {"$group": {"_id": "$mood", "count": {"$sum": 1}, "avg_energy": {"$avg": "$energy"}}},
        {"$sort": {"count": -1}}
    ]).to_list(100)
    
    return [{"mood": m["_id"], "count": m["count"], "avg_energy": m.get("avg_energy", 0.5)} for m in moods]

# Smart Queue Management
@api_router.post("/smart-queues", response_model=SmartQueue)
async def create_smart_queue(queue_data: Dict[str, Any]):
    """Create a smart queue"""
    queue = SmartQueue(
        name=queue_data.get("name", "New Queue"),
        queue_type=queue_data.get("queue_type", "user"),
        track_ids=queue_data.get("track_ids", []),
        generation_params=queue_data.get("generation_params", {})
    )
    await db.smart_queues.insert_one(queue.dict())
    return queue

@api_router.get("/smart-queues", response_model=List[SmartQueue])
async def get_smart_queues():
    """Get all smart queues"""
    queues = await db.smart_queues.find().to_list(1000)
    return [SmartQueue(**queue) for queue in queues]

@api_router.get("/smart-queues/{queue_id}", response_model=SmartQueue)
async def get_smart_queue(queue_id: str):
    """Get a specific smart queue"""
    queue = await db.smart_queues.find_one({"id": queue_id})
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    return SmartQueue(**queue)

@api_router.post("/smart-queues/{queue_id}/generate-auto")
async def generate_auto_queue(queue_id: str, seed_track_id: str, size: int = 20):
    """Generate auto queue based on seed track"""
    # Get seed track
    seed_track = await db.tracks.find_one({"id": seed_track_id})
    if not seed_track:
        raise HTTPException(status_code=404, detail="Seed track not found")
    
    # Get all tracks for recommendations
    all_tracks = await db.tracks.find({}).to_list(1000)
    
    # Generate auto queue
    auto_queue_tracks = recommendation_engine.generate_auto_queue(
        seed_track, all_tracks, size
    )
    
    # Update queue
    await db.smart_queues.update_one(
        {"id": queue_id},
        {
            "$set": {
                "track_ids": [t['id'] for t in auto_queue_tracks],
                "seed_track_id": seed_track_id,
                "queue_type": "auto",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Auto queue generated", "track_count": len(auto_queue_tracks)}

@api_router.put("/smart-queues/{queue_id}")
async def update_smart_queue(queue_id: str, update_data: Dict[str, Any]):
    """Update smart queue"""
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.smart_queues.update_one(
        {"id": queue_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Queue not found")
    
    return {"message": "Queue updated"}

# Playback Session Management
@api_router.post("/playback-session", response_model=PlaybackSession)
async def create_playback_session():
    """Create new playback session for unlimited playback"""
    session = PlaybackSession()
    await db.playback_sessions.insert_one(session.dict())
    return session

@api_router.get("/playback-session/{session_id}", response_model=PlaybackSession)
async def get_playback_session(session_id: str):
    """Get playback session"""
    session = await db.playback_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return PlaybackSession(**session)

@api_router.put("/playback-session/{session_id}/switch-queue")
async def switch_queue_type(session_id: str, queue_type: str):
    """Switch between user and auto queue"""
    if queue_type not in ["user", "auto"]:
        raise HTTPException(status_code=400, detail="Invalid queue type")
    
    result = await db.playback_sessions.update_one(
        {"id": session_id},
        {
            "$set": {
                "current_queue_type": queue_type,
                "last_activity": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": f"Switched to {queue_type} queue"}

# Smart Mixes
@api_router.get("/smart-mixes", response_model=List[SmartMix])
async def get_smart_mixes():
    """Get all smart mixes"""
    mixes = await db.smart_mixes.find().to_list(1000)
    return [SmartMix(**mix) for mix in mixes]

@api_router.post("/smart-mixes/generate")
async def generate_smart_mix(mix_type: str, parameters: Dict[str, Any]):
    """Generate a new smart mix"""
    tracks = await db.tracks.find({}).to_list(1000)
    
    if mix_type == "discovery":
        # Discovery mix: random selection of less-played tracks
        discovery_tracks = [t for t in tracks if t.get('play_count', 0) < 3]
        selected_tracks = np.random.choice(discovery_tracks, size=min(30, len(discovery_tracks)), replace=False).tolist()
    elif mix_type == "popular":
        # Popular tracks mix
        popular_tracks = sorted(tracks, key=lambda x: x.get('popularity_score', 0), reverse=True)
        selected_tracks = popular_tracks[:30]
    else:
        # Generic mix
        selected_tracks = np.random.choice(tracks, size=min(30, len(tracks)), replace=False).tolist()
    
    mix = SmartMix(
        name=f"{mix_type.title()} Mix",
        description=f"Auto-generated {mix_type} mix",
        track_ids=[t['id'] for t in selected_tracks],
        mix_type=mix_type,
        parameters=parameters
    )
    
    await db.smart_mixes.insert_one(mix.dict())
    return mix

@api_router.post("/smart-mixes/{mix_id}/refresh")
async def refresh_smart_mix(mix_id: str):
    """Refresh smart mix with new tracks"""
    mix = await db.smart_mixes.find_one({"id": mix_id})
    if not mix:
        raise HTTPException(status_code=404, detail="Mix not found")
    
    # Regenerate mix based on original parameters
    await generate_smart_mix(mix["mix_type"], mix["parameters"])
    
    return {"message": "Mix refreshed"}

# Legacy playlist endpoints (maintained for compatibility)
@api_router.post("/playlists", response_model=Playlist)
async def create_playlist(playlist_data: PlaylistCreate):
    """Create a new playlist"""
    playlist = Playlist(**playlist_data.dict())
    await db.playlists.insert_one(playlist.dict())
    return playlist

@api_router.get("/playlists", response_model=List[Playlist])
async def get_playlists():
    """Get all playlists"""
    playlists = await db.playlists.find().to_list(1000)
    return [Playlist(**playlist) for playlist in playlists]

@api_router.get("/playlists/{playlist_id}", response_model=Playlist)
async def get_playlist(playlist_id: str):
    """Get a specific playlist"""
    playlist = await db.playlists.find_one({"id": playlist_id})
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return Playlist(**playlist)

@api_router.put("/playlists/{playlist_id}/tracks")
async def update_playlist_tracks(playlist_id: str, track_ids: List[str]):
    """Update playlist tracks"""
    result = await db.playlists.update_one(
        {"id": playlist_id},
        {
            "$set": {
                "track_ids": track_ids,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    return {"message": "Playlist updated"}

# Analytics and insights
@api_router.get("/analytics/listening-stats")
async def get_listening_stats():
    """Get comprehensive listening statistics"""
    total_tracks = await db.tracks.count_documents({})
    total_plays = await db.tracks.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$play_count"}}}
    ]).to_list(1)
    
    # Top genres by play count
    top_genres = await db.tracks.aggregate([
        {"$match": {"ai_genre": {"$ne": None}}},
        {"$group": {"_id": "$ai_genre", "plays": {"$sum": "$play_count"}, "tracks": {"$sum": 1}}},
        {"$sort": {"plays": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Recently played
    recent_tracks = await db.tracks.find(
        {"last_played": {"$ne": None}},
        sort=[("last_played", -1)],
        limit=10
    ).to_list(10)
    
    return {
        "total_tracks": total_tracks,
        "total_plays": total_plays[0]["total"] if total_plays else 0,
        "top_genres": top_genres,
        "recent_tracks": [Track(**track) for track in recent_tracks]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

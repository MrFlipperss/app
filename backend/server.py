from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile
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
from datetime import datetime
import asyncio
import json
from mutagen import File as MutagenFile
from mutagen.id3 import ID3NoHeaderError
import magic
import hashlib
import io
import base64
from PIL import Image

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_played: Optional[datetime] = None
    play_count: int = 0

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

class Queue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    track_ids: List[str] = []
    current_index: int = 0
    shuffle: bool = False
    repeat: str = "none"  # none, track, queue
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ScanStatus(BaseModel):
    is_scanning: bool = False
    current_folder: Optional[str] = None
    processed_files: int = 0
    total_files: int = 0
    status: str = "idle"

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

async def scan_folder_for_music(folder_path: str):
    """Scan folder for music files"""
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
        scan_status.status = "scanning"
        scan_status.is_scanning = True
        
        for file_path in music_files:
            try:
                scan_status.current_folder = str(file_path.parent)
                
                # Check if file already exists in database
                existing_track = await db.tracks.find_one({"file_path": str(file_path)})
                if existing_track:
                    scan_status.processed_files += 1
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
                    **metadata
                }
                
                # Insert into database
                await db.tracks.insert_one(track_data)
                scan_status.processed_files += 1
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                continue
        
        scan_status.status = "completed"
        scan_status.is_scanning = False
        logger.info(f"Scan completed. Processed {scan_status.processed_files} files")
        
    except Exception as e:
        scan_status.status = "error"
        scan_status.is_scanning = False
        logger.error(f"Error scanning folder {folder_path}: {e}")

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

# Music library endpoints
@api_router.get("/tracks", response_model=List[Track])
async def get_tracks(limit: int = 100, offset: int = 0, search: Optional[str] = None):
    """Get tracks with optional search"""
    query = {}
    
    if search:
        query = {
            "$or": [
                {"title": {"$regex": search, "$options": "i"}},
                {"artist": {"$regex": search, "$options": "i"}},
                {"album": {"$regex": search, "$options": "i"}}
            ]
        }
    
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
    """Stream audio file"""
    track = await db.tracks.find_one({"id": track_id})
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    file_path = Path(track["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Update play count
    await db.tracks.update_one(
        {"id": track_id},
        {
            "$inc": {"play_count": 1},
            "$set": {"last_played": datetime.utcnow()}
        }
    )
    
    return FileResponse(
        path=str(file_path),
        media_type=f"audio/{track['file_format'].lower()}",
        filename=track["filename"]
    )

@api_router.get("/artists")
async def get_artists():
    """Get all artists"""
    artists = await db.tracks.distinct("artist")
    return [{"name": artist} for artist in artists if artist and artist != "Unknown Artist"]

@api_router.get("/albums")
async def get_albums(artist: Optional[str] = None):
    """Get albums, optionally filtered by artist"""
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
                "artwork_data": {"$first": "$artwork_data"}
            }
        },
        {
            "$project": {
                "album": "$_id.album",
                "artist": "$_id.artist",
                "track_count": 1,
                "artwork_data": 1,
                "_id": 0
            }
        }
    ])
    
    albums = await db.tracks.aggregate(pipeline).to_list(1000)
    return albums

# Playlist endpoints
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

# Queue management endpoints
@api_router.post("/queues", response_model=Queue)
async def create_queue(queue_data: Dict[str, Any]):
    """Create a new queue"""
    queue = Queue(
        name=queue_data.get("name", "New Queue"),
        track_ids=queue_data.get("track_ids", [])
    )
    await db.queues.insert_one(queue.dict())
    return queue

@api_router.get("/queues", response_model=List[Queue])
async def get_queues():
    """Get all queues"""
    queues = await db.queues.find().to_list(1000)
    return [Queue(**queue) for queue in queues]

@api_router.get("/queues/{queue_id}", response_model=Queue)
async def get_queue(queue_id: str):
    """Get a specific queue"""
    queue = await db.queues.find_one({"id": queue_id})
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    return Queue(**queue)

@api_router.put("/queues/{queue_id}")
async def update_queue(queue_id: str, update_data: Dict[str, Any]):
    """Update queue settings"""
    result = await db.queues.update_one(
        {"id": queue_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Queue not found")
    
    return {"message": "Queue updated"}

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

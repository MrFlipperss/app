import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Icons as components
const PlayIcon = () => (
  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
    <path d="M8 5v14l11-7z"/>
  </svg>
);

const PauseIcon = () => (
  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
    <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
  </svg>
);

const SkipNextIcon = () => (
  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
    <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
  </svg>
);

const SkipPrevIcon = () => (
  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
    <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
  </svg>
);

const ShuffleIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
  </svg>
);

const RepeatIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>
  </svg>
);

const VolumeIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
  </svg>
);

const MusicIcon = () => (
  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
  </svg>
);

const FolderIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M10 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2h-8l-2-2z"/>
  </svg>
);

const SearchIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
  </svg>
);

function App() {
  // State management
  const [currentView, setCurrentView] = useState('library');
  const [tracks, setTracks] = useState([]);
  const [artists, setArtists] = useState([]);
  const [albums, setAlbums] = useState([]);
  const [playlists, setPlaylists] = useState([]);
  const [folders, setFolders] = useState([]);
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [queue, setQueue] = useState([]);
  const [currentQueueIndex, setCurrentQueueIndex] = useState(0);
  const [shuffle, setShuffle] = useState(false);
  const [repeat, setRepeat] = useState('none'); // none, track, queue
  const [searchQuery, setSearchQuery] = useState('');
  const [scanStatus, setScanStatus] = useState(null);
  const [newFolderPath, setNewFolderPath] = useState('');
  const [theme, setTheme] = useState('dark');

  const audioRef = useRef(null);

  // Load initial data
  useEffect(() => {
    loadLibraryData();
    loadFolders();
    checkScanStatus();
  }, []);

  // Audio event listeners
  useEffect(() => {
    if (audioRef.current) {
      const audio = audioRef.current;
      
      const updateTime = () => setCurrentTime(audio.currentTime);
      const updateDuration = () => setDuration(audio.duration);
      const handleEnded = () => handleNextTrack();
      
      audio.addEventListener('timeupdate', updateTime);
      audio.addEventListener('loadedmetadata', updateDuration);
      audio.addEventListener('ended', handleEnded);
      
      return () => {
        audio.removeEventListener('timeupdate', updateTime);
        audio.removeEventListener('loadedmetadata', updateDuration);
        audio.removeEventListener('ended', handleEnded);
      };
    }
  }, [currentTrack]);

  // Audio volume control
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, [volume]);

  const loadLibraryData = async () => {
    try {
      const [tracksRes, artistsRes, albumsRes, playlistsRes] = await Promise.all([
        axios.get(`${API}/tracks?limit=1000`),
        axios.get(`${API}/artists`),
        axios.get(`${API}/albums`),
        axios.get(`${API}/playlists`)
      ]);
      
      setTracks(tracksRes.data);
      setArtists(artistsRes.data);
      setAlbums(albumsRes.data);
      setPlaylists(playlistsRes.data);
    } catch (error) {
      console.error('Error loading library data:', error);
    }
  };

  const loadFolders = async () => {
    try {
      const response = await axios.get(`${API}/folders`);
      setFolders(response.data);
    } catch (error) {
      console.error('Error loading folders:', error);
    }
  };

  const checkScanStatus = async () => {
    try {
      const response = await axios.get(`${API}/scan-status`);
      setScanStatus(response.data);
      
      if (response.data.is_scanning) {
        setTimeout(checkScanStatus, 2000);
      }
    } catch (error) {
      console.error('Error checking scan status:', error);
    }
  };

  const addFolder = async () => {
    if (!newFolderPath.trim()) return;
    
    try {
      await axios.post(`${API}/folders`, { path: newFolderPath.trim() });
      setNewFolderPath('');
      loadFolders();
      checkScanStatus();
    } catch (error) {
      console.error('Error adding folder:', error);
      alert('Failed to add folder. Please check the path exists.');
    }
  };

  const playTrack = (track, trackQueue = null) => {
    setCurrentTrack(track);
    
    if (trackQueue) {
      setQueue(trackQueue);
      const index = trackQueue.findIndex(t => t.id === track.id);
      setCurrentQueueIndex(index >= 0 ? index : 0);
    }
    
    if (audioRef.current) {
      audioRef.current.src = `${API}/tracks/${track.id}/stream`;
      audioRef.current.load();
      audioRef.current.play().then(() => {
        setIsPlaying(true);
      }).catch(error => {
        console.error('Error playing track:', error);
      });
    }
  };

  const togglePlayPause = () => {
    if (!audioRef.current || !currentTrack) return;
    
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => {
        setIsPlaying(true);
      }).catch(error => {
        console.error('Error playing track:', error);
      });
    }
  };

  const handleNextTrack = () => {
    if (repeat === 'track' && currentTrack) {
      playTrack(currentTrack, queue);
      return;
    }
    
    if (queue.length > 0) {
      let nextIndex = shuffle ? 
        Math.floor(Math.random() * queue.length) : 
        currentQueueIndex + 1;
      
      if (nextIndex >= queue.length) {
        if (repeat === 'queue') {
          nextIndex = 0;
        } else {
          setIsPlaying(false);
          return;
        }
      }
      
      setCurrentQueueIndex(nextIndex);
      playTrack(queue[nextIndex], queue);
    }
  };

  const handlePrevTrack = () => {
    if (queue.length > 0) {
      let prevIndex = shuffle ? 
        Math.floor(Math.random() * queue.length) : 
        currentQueueIndex - 1;
      
      if (prevIndex < 0) {
        prevIndex = repeat === 'queue' ? queue.length - 1 : 0;
      }
      
      setCurrentQueueIndex(prevIndex);
      playTrack(queue[prevIndex], queue);
    }
  };

  const seekTo = (percentage) => {
    if (audioRef.current && duration) {
      const time = (percentage / 100) * duration;
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const filteredTracks = tracks.filter(track =>
    track.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    track.artist?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    track.album?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className={`app ${theme}`}>
      <div className="app-layout">
        {/* Sidebar */}
        <div className="sidebar">
          <div className="sidebar-header">
            <div className="logo">
              <MusicIcon />
              <h1>Music Player</h1>
            </div>
          </div>
          
          <nav className="sidebar-nav">
            <button 
              className={`nav-item ${currentView === 'library' ? 'active' : ''}`}
              onClick={() => setCurrentView('library')}
            >
              <MusicIcon />
              Your Library
            </button>
            
            <button 
              className={`nav-item ${currentView === 'folders' ? 'active' : ''}`}
              onClick={() => setCurrentView('folders')}
            >
              <FolderIcon />
              Music Folders
            </button>
          </nav>
          
          <div className="playlists-section">
            <h3>Playlists</h3>
            {playlists.map(playlist => (
              <button key={playlist.id} className="playlist-item">
                {playlist.name}
              </button>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="main-content">
          <div className="content-header">
            <div className="search-bar">
              <SearchIcon />
              <input
                type="text"
                placeholder="Search songs, artists, or albums..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            
            <button 
              className="theme-toggle"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>

          {/* Content Area */}
          <div className="content-area">
            {currentView === 'library' && (
              <div className="library-view">
                <div className="section-header">
                  <h2>Your Music Library</h2>
                  <p>{tracks.length} songs available</p>
                </div>
                
                {scanStatus?.is_scanning && (
                  <div className="scan-status">
                    <div className="scan-progress">
                      <div className="progress-bar">
                        <div 
                          className="progress-fill"
                          style={{ width: `${(scanStatus.processed_files / scanStatus.total_files) * 100}%` }}
                        />
                      </div>
                      <p>Scanning: {scanStatus.processed_files}/{scanStatus.total_files} files</p>
                    </div>
                  </div>
                )}
                
                <div className="tracks-grid">
                  {filteredTracks.map(track => (
                    <div key={track.id} className="track-card">
                      <div 
                        className="track-artwork"
                        onClick={() => playTrack(track, filteredTracks)}
                      >
                        {track.artwork_data ? (
                          <img 
                            src={`data:image/jpeg;base64,${track.artwork_data}`}
                            alt={track.album || 'Album artwork'}
                          />
                        ) : (
                          <div className="no-artwork">
                            <MusicIcon />
                          </div>
                        )}
                        <div className="play-overlay">
                          <PlayIcon />
                        </div>
                      </div>
                      
                      <div className="track-info">
                        <h4 className="track-title">{track.title || track.filename || 'Unknown Title'}</h4>
                        <p className="track-artist">{track.artist || 'Unknown Artist'}</p>
                        <p className="track-album">{track.album || 'Unknown Album'}</p>
                        <div className="track-meta">
                          <span className="format">{track.file_format}</span>
                          {track.bitrate && track.bitrate > 0 && <span>{track.bitrate} kbps</span>}
                          {track.sample_rate && track.sample_rate > 0 && <span>{Math.round(track.sample_rate/1000)}kHz</span>}
                          <span>{formatTime(track.duration)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {filteredTracks.length === 0 && tracks.length > 0 && searchQuery && (
                  <div className="no-results">
                    <p>No tracks found matching "{searchQuery}"</p>
                  </div>
                )}
                
                {tracks.length === 0 && !scanStatus?.is_scanning && (
                  <div className="empty-library">
                    <div className="empty-icon">
                      <MusicIcon />
                    </div>
                    <h3>No music found</h3>
                    <p>Add a music folder to get started!</p>
                    <button 
                      className="add-folder-btn"
                      onClick={() => setCurrentView('folders')}
                    >
                      Add Music Folder
                    </button>
                  </div>
                )}
              </div>
            )}

            {currentView === 'folders' && (
              <div className="folders-view">
                <div className="section-header">
                  <h2>Music Folders</h2>
                  <p>Manage your music directories</p>
                </div>
                
                <div className="add-folder">
                  <input
                    type="text"
                    placeholder="Enter folder path (e.g., /home/user/Music)"
                    value={newFolderPath}
                    onChange={(e) => setNewFolderPath(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addFolder()}
                  />
                  <button onClick={addFolder}>Add Folder</button>
                </div>
                
                <div className="folders-list">
                  {folders.map(folder => (
                    <div key={folder.id} className="folder-item">
                      <FolderIcon />
                      <div className="folder-info">
                        <h4>{folder.name}</h4>
                        <p>{folder.path}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Player Bar */}
      {currentTrack && (
        <div className="player-bar">
          <div className="current-track-info">
            <div className="track-artwork-small">
              {currentTrack.artwork_data ? (
                <img 
                  src={`data:image/jpeg;base64,${currentTrack.artwork_data}`}
                  alt={currentTrack.album}
                />
              ) : (
                <MusicIcon />
              )}
            </div>
            <div className="track-details">
              <h4>{currentTrack.title}</h4>
              <p>{currentTrack.artist}</p>
            </div>
          </div>

          <div className="player-controls">
            <div className="control-buttons">
              <button 
                className={`control-btn ${shuffle ? 'active' : ''}`}
                onClick={() => setShuffle(!shuffle)}
              >
                <ShuffleIcon />
              </button>
              
              <button className="control-btn" onClick={handlePrevTrack}>
                <SkipPrevIcon />
              </button>
              
              <button className="play-pause-btn" onClick={togglePlayPause}>
                {isPlaying ? <PauseIcon /> : <PlayIcon />}
              </button>
              
              <button className="control-btn" onClick={handleNextTrack}>
                <SkipNextIcon />
              </button>
              
              <button 
                className={`control-btn ${repeat !== 'none' ? 'active' : ''}`}
                onClick={() => {
                  const modes = ['none', 'track', 'queue'];
                  const currentIndex = modes.indexOf(repeat);
                  setRepeat(modes[(currentIndex + 1) % modes.length]);
                }}
              >
                <RepeatIcon />
              </button>
            </div>

            <div className="progress-section">
              <span className="time">{formatTime(currentTime)}</span>
              <div 
                className="progress-bar"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const percentage = ((e.clientX - rect.left) / rect.width) * 100;
                  seekTo(percentage);
                }}
              >
                <div 
                  className="progress-fill"
                  style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
                />
              </div>
              <span className="time">{formatTime(duration)}</span>
            </div>
          </div>

          <div className="volume-section">
            <VolumeIcon />
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={volume}
              onChange={(e) => setVolume(parseFloat(e.target.value))}
              className="volume-slider"
            />
          </div>
        </div>
      )}

      {/* Hidden audio element */}
      <audio ref={audioRef} />
    </div>
  );
}

export default App;
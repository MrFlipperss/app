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

const SmartIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
  </svg>
);

const QueueIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9H9V9h10v2zm-4 4H9v-2h6v2zm4-8H9V5h10v2z"/>
  </svg>
);

const InfiniteIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M18.6 6.62c-1.44 0-2.8.56-3.77 1.53L12 10.66 10.17 8.83c-.97-.97-2.33-1.53-3.77-1.53C4.9 7.3 3.5 8.7 3.5 10.4c0 .94.37 1.85 1.03 2.52l7.47 7.47 7.47-7.47c.66-.67 1.03-1.58 1.03-2.52 0-1.7-1.4-3.1-3.1-3.1z"/>
  </svg>
);

function App() {
  // Enhanced state management
  const [currentView, setCurrentView] = useState('library');
  const [tracks, setTracks] = useState([]);
  const [artists, setArtists] = useState([]);
  const [albums, setAlbums] = useState([]);
  const [playlists, setPlaylists] = useState([]);
  const [smartMixes, setSmartMixes] = useState([]);
  const [aiPlaylists, setAiPlaylists] = useState([]);
  const [folders, setFolders] = useState([]);
  const [genres, setGenres] = useState([]);
  const [moods, setMoods] = useState([]);
  
  // Player state
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  
  // Two-queue system (YouTube Music style)
  const [userQueue, setUserQueue] = useState([]);
  const [autoQueue, setAutoQueue] = useState([]);
  const [currentQueueType, setCurrentQueueType] = useState('user'); // 'user' or 'auto'
  const [currentQueueIndex, setCurrentQueueIndex] = useState(0);
  const [unlimitedMode, setUnlimitedMode] = useState(true);
  const [playbackSession, setPlaybackSession] = useState(null);
  
  // Controls
  const [shuffle, setShuffle] = useState(false);
  const [repeat, setRepeat] = useState('none');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [selectedMood, setSelectedMood] = useState('');
  
  // UI state
  const [scanStatus, setScanStatus] = useState(null);
  const [newFolderPath, setNewFolderPath] = useState('');
  const [theme, setTheme] = useState('dark');
  const [showQueue, setShowQueue] = useState(false);
  const [stats, setStats] = useState(null);
  const [showAiPlaylist, setShowAiPlaylist] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiPromptSuggestions, setAiPromptSuggestions] = useState([]);
  const [isGeneratingPlaylist, setIsGeneratingPlaylist] = useState(false);

  const audioRef = useRef(null);

  // Load initial data
  useEffect(() => {
    loadLibraryData();
    loadFolders();
    loadSmartData();
    loadAiPlaylists();
    loadAiPromptSuggestions();
    checkScanStatus();
    createPlaybackSession();
    loadStats();
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
  }, [currentTrack, currentQueueType, userQueue, autoQueue]);

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

  const loadSmartData = async () => {
    try {
      const [genresRes, moodsRes, mixesRes] = await Promise.all([
        axios.get(`${API}/genres`),
        axios.get(`${API}/moods`),
        axios.get(`${API}/smart-mixes`)
      ]);
      
      setGenres(genresRes.data.ai_genres || []);
      setMoods(moodsRes.data);
      setSmartMixes(mixesRes.data);
    } catch (error) {
      console.error('Error loading smart data:', error);
    }
  };

  const loadAiPlaylists = async () => {
    try {
      const response = await axios.get(`${API}/ai-playlists`);
      setAiPlaylists(response.data);
    } catch (error) {
      console.error('Error loading AI playlists:', error);
    }
  };

  const loadAiPromptSuggestions = async () => {
    try {
      const response = await axios.get(`${API}/ai-playlists/suggestions/prompts`);
      setAiPromptSuggestions(response.data.suggestions || []);
    } catch (error) {
      console.error('Error loading AI prompt suggestions:', error);
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

  const loadStats = async () => {
    try {
      const response = await axios.get(`${API}/analytics/listening-stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const createPlaybackSession = async () => {
    try {
      const response = await axios.post(`${API}/playback-session`);
      setPlaybackSession(response.data);
    } catch (error) {
      console.error('Error creating playback session:', error);
    }
  };

  const checkScanStatus = async () => {
    try {
      const response = await axios.get(`${API}/scan-status`);
      setScanStatus(response.data);
      
      if (response.data.is_scanning || response.data.ai_processing) {
        setTimeout(checkScanStatus, 2000);
      } else if (response.data.status === 'completed') {
        // Reload data after scan completion
        loadLibraryData();
        loadSmartData();
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

  const generateAutoQueue = async (seedTrackId) => {
    if (!unlimitedMode || !playbackSession) return;
    
    try {
      // Create a new smart queue for auto-generation
      const queueResponse = await axios.post(`${API}/smart-queues`, {
        name: "Auto Queue",
        queue_type: "auto"
      });
      
      const queueId = queueResponse.data.id;
      
      // Generate auto queue based on current track
      await axios.post(`${API}/smart-queues/${queueId}/generate-auto`, null, {
        params: { seed_track_id: seedTrackId, size: 50 }
      });
      
      // Get the generated queue
      const generatedQueueResponse = await axios.get(`${API}/smart-queues/${queueId}`);
      const generatedQueue = generatedQueueResponse.data;
      
      // Get track details for the queue
      const queueTracks = await Promise.all(
        generatedQueue.track_ids.slice(0, 20).map(async (trackId) => {
          try {
            const trackResponse = await axios.get(`${API}/tracks/${trackId}`);
            return trackResponse.data;
          } catch {
            return null;
          }
        })
      );
      
      const validQueueTracks = queueTracks.filter(track => track !== null);
      setAutoQueue(validQueueTracks);
      
      console.log(`Generated auto queue with ${validQueueTracks.length} tracks`);
    } catch (error) {
      console.error('Error generating auto queue:', error);
    }
  };

  const playTrack = async (track, trackQueue = null, queueType = 'user') => {
    setCurrentTrack(track);
    
    if (trackQueue) {
      if (queueType === 'user') {
        setUserQueue(trackQueue);
        setCurrentQueueType('user');
        const index = trackQueue.findIndex(t => t.id === track.id);
        setCurrentQueueIndex(index >= 0 ? index : 0);
        
        // Generate auto queue for unlimited playback
        if (unlimitedMode) {
          await generateAutoQueue(track.id);
        }
      } else {
        setAutoQueue(trackQueue);
        setCurrentQueueType('auto');
        const index = trackQueue.findIndex(t => t.id === track.id);
        setCurrentQueueIndex(index >= 0 ? index : 0);
      }
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

  const handleNextTrack = async () => {
    const currentQueue = currentQueueType === 'user' ? userQueue : autoQueue;
    
    if (repeat === 'track' && currentTrack) {
      playTrack(currentTrack, currentQueue, currentQueueType);
      return;
    }
    
    let nextIndex = shuffle ? 
      Math.floor(Math.random() * currentQueue.length) : 
      currentQueueIndex + 1;
    
    // Handle queue transitions for unlimited playback
    if (nextIndex >= currentQueue.length) {
      if (currentQueueType === 'user' && unlimitedMode && autoQueue.length > 0) {
        // Switch to auto queue
        setCurrentQueueType('auto');
        setCurrentQueueIndex(0);
        await playTrack(autoQueue[0], autoQueue, 'auto');
        return;
      } else if (repeat === 'queue') {
        nextIndex = 0;
      } else {
        // Generate new auto queue if we're at the end of auto queue
        if (currentQueueType === 'auto' && unlimitedMode && currentTrack) {
          await generateAutoQueue(currentTrack.id);
          if (autoQueue.length > 0) {
            setCurrentQueueIndex(0);
            await playTrack(autoQueue[0], autoQueue, 'auto');
            return;
          }
        }
        setIsPlaying(false);
        return;
      }
    }
    
    setCurrentQueueIndex(nextIndex);
    await playTrack(currentQueue[nextIndex], currentQueue, currentQueueType);
  };

  const handlePrevTrack = async () => {
    const currentQueue = currentQueueType === 'user' ? userQueue : autoQueue;
    
    let prevIndex = shuffle ? 
      Math.floor(Math.random() * currentQueue.length) : 
      currentQueueIndex - 1;
    
    if (prevIndex < 0) {
      if (currentQueueType === 'auto' && userQueue.length > 0) {
        // Switch back to user queue
        setCurrentQueueType('user');
        prevIndex = userQueue.length - 1;
        setCurrentQueueIndex(prevIndex);
        await playTrack(userQueue[prevIndex], userQueue, 'user');
        return;
      } else {
        prevIndex = repeat === 'queue' ? currentQueue.length - 1 : 0;
      }
    }
    
    setCurrentQueueIndex(prevIndex);
    await playTrack(currentQueue[prevIndex], currentQueue, currentQueueType);
  };

  const handleTrackSkip = async () => {
    if (currentTrack) {
      try {
        await axios.post(`${API}/tracks/${currentTrack.id}/skip`);
      } catch (error) {
        console.error('Error recording skip:', error);
      }
    }
    await handleNextTrack();
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

  const getFilteredTracks = () => {
    let filtered = tracks.filter(track =>
      track.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      track.artist?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      track.album?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      track.ai_genre?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (selectedGenre) {
      filtered = filtered.filter(track => 
        track.ai_genre === selectedGenre || track.genre === selectedGenre
      );
    }

    if (selectedMood) {
      filtered = filtered.filter(track => track.mood === selectedMood);
    }

    return filtered;
  };

  const addToUserQueue = (track) => {
    setUserQueue([...userQueue, track]);
  };

  const playSmartMix = async (mix) => {
    try {
      const mixTracks = await Promise.all(
        mix.track_ids.map(async (trackId) => {
          try {
            const response = await axios.get(`${API}/tracks/${trackId}`);
            return response.data;
          } catch {
            return null;
          }
        })
      );
      
      const validTracks = mixTracks.filter(track => track !== null);
      if (validTracks.length > 0) {
        await playTrack(validTracks[0], validTracks, 'user');
      }
    } catch (error) {
      console.error('Error playing smart mix:', error);
    }
  };

  const generateAiPlaylist = async () => {
    if (!aiPrompt.trim() || isGeneratingPlaylist) return;
    
    setIsGeneratingPlaylist(true);
    try {
      const response = await axios.post(`${API}/ai-playlists/generate`, {
        prompt: aiPrompt.trim(),
        max_tracks: 25,
        duration_minutes: 60
      });
      
      const aiPlaylist = response.data;
      
      // Play the generated playlist immediately
      await axios.post(`${API}/ai-playlists/${aiPlaylist.id}/play`);
      
      // Get the tracks for the playlist
      const playlistTracks = await Promise.all(
        aiPlaylist.track_ids.map(async (trackId) => {
          try {
            const trackResponse = await axios.get(`${API}/tracks/${trackId}`);
            return trackResponse.data;
          } catch {
            return null;
          }
        })
      );
      
      const validTracks = playlistTracks.filter(track => track !== null);
      if (validTracks.length > 0) {
        await playTrack(validTracks[0], validTracks, 'user');
      }
      
      // Refresh AI playlists list
      loadAiPlaylists();
      
      // Clear the prompt and close the modal
      setAiPrompt('');
      setShowAiPlaylist(false);
      
      alert(`Generated "${aiPlaylist.name}" with ${aiPlaylist.track_count} tracks!`);
    } catch (error) {
      console.error('Error generating AI playlist:', error);
      alert('Failed to generate playlist. Please try a different prompt.');
    } finally {
      setIsGeneratingPlaylist(false);
    }
  };

  const playAiPlaylist = async (aiPlaylist) => {
    try {
      // Convert AI playlist to playable queue
      await axios.post(`${API}/ai-playlists/${aiPlaylist.id}/play`);
      
      // Get the tracks for the playlist
      const playlistTracks = await Promise.all(
        aiPlaylist.track_ids.map(async (trackId) => {
          try {
            const response = await axios.get(`${API}/tracks/${trackId}`);
            return response.data;
          } catch {
            return null;
          }
        })
      );
      
      const validTracks = playlistTracks.filter(track => track !== null);
      if (validTracks.length > 0) {
        await playTrack(validTracks[0], validTracks, 'user');
      }
    } catch (error) {
      console.error('Error playing AI playlist:', error);
    }
  };

  const filteredTracks = getFilteredTracks();

  return (
    <div className={`app ${theme}`}>
      <div className="app-layout">
        {/* Sidebar */}
        <div className="sidebar">
          <div className="sidebar-header">
            <div className="logo">
              <MusicIcon />
              <h1>Smart Music</h1>
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
              className={`nav-item ${currentView === 'smart' ? 'active' : ''}`}
              onClick={() => setCurrentView('smart')}
            >
              <SmartIcon />
              Smart Mixes
            </button>
            
            <button 
              className={`nav-item ${currentView === 'ai-playlists' ? 'active' : ''}`}
              onClick={() => setCurrentView('ai-playlists')}
            >
              <SmartIcon />
              AI Playlists
            </button>
            
            <button 
              className={`nav-item ${currentView === 'folders' ? 'active' : ''}`}
              onClick={() => setCurrentView('folders')}
            >
              <FolderIcon />
              Music Folders
            </button>
            
            <button 
              className={`nav-item ${currentView === 'analytics' ? 'active' : ''}`}
              onClick={() => setCurrentView('analytics')}
            >
              <QueueIcon />
              Analytics
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

          <div className="smart-mixes-section">
            <h3>Smart Mixes</h3>
            {smartMixes.slice(0, 5).map(mix => (
              <button 
                key={mix.id} 
                className="playlist-item"
                onClick={() => playSmartMix(mix)}
              >
                <SmartIcon />
                {mix.name}
              </button>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="main-content">
          <div className="content-header">
            <div className="search-controls">
              <div className="search-bar">
                <SearchIcon />
                <input
                  type="text"
                  placeholder="Search songs, artists, albums, genres..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              
              <div className="filter-controls">
                <select 
                  value={selectedGenre} 
                  onChange={(e) => setSelectedGenre(e.target.value)}
                >
                  <option value="">All Genres</option>
                  {genres.map(genre => (
                    <option key={genre.genre} value={genre.genre}>
                      {genre.genre} ({genre.count})
                    </option>
                  ))}
                </select>
                
                <select 
                  value={selectedMood} 
                  onChange={(e) => setSelectedMood(e.target.value)}
                >
                  <option value="">All Moods</option>
                  {moods.map(mood => (
                    <option key={mood.mood} value={mood.mood}>
                      {mood.mood} ({mood.count})
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="header-controls">
              <button 
                className={`control-btn ${unlimitedMode ? 'active' : ''}`}
                onClick={() => setUnlimitedMode(!unlimitedMode)}
                title="Unlimited Playback"
              >
                <InfiniteIcon />
              </button>
              
              <button 
                className={`control-btn ${showQueue ? 'active' : ''}`}
                onClick={() => setShowQueue(!showQueue)}
                title="Show Queue"
              >
                <QueueIcon />
              </button>
              
              <button 
                className="theme-toggle"
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              >
                {theme === 'dark' ? '☀️' : '🌙'}
              </button>
            </div>
          </div>

          {/* Content Area */}
          <div className="content-area">
            {currentView === 'library' && (
              <div className="library-view">
                <div className="section-header">
                  <h2>Your Music Library</h2>
                  <p>{filteredTracks.length} songs {selectedGenre && `in ${selectedGenre}`} {selectedMood && `• ${selectedMood} mood`}</p>
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
                
                {scanStatus?.ai_processing && (
                  <div className="scan-status ai-processing">
                    <div className="scan-progress">
                      <div className="progress-bar">
                        <div 
                          className="progress-fill smart"
                          style={{ width: `${(scanStatus.ai_processed / scanStatus.processed_files) * 100}%` }}
                        />
                      </div>
                      <p>AI Processing: {scanStatus.ai_processed}/{scanStatus.processed_files} tracks</p>
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
                          {track.ai_genre && <span className="ai-genre">{track.ai_genre}</span>}
                          {track.mood && <span className="mood">{track.mood}</span>}
                          {track.bitrate && track.bitrate > 0 && <span>{track.bitrate} kbps</span>}
                          <span>{formatTime(track.duration)}</span>
                        </div>
                        
                        <button 
                          className="add-to-queue-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            addToUserQueue(track);
                          }}
                        >
                          + Queue
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                
                {filteredTracks.length === 0 && tracks.length > 0 && (searchQuery || selectedGenre || selectedMood) && (
                  <div className="no-results">
                    <p>No tracks found matching your filters</p>
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

            {currentView === 'smart' && (
              <div className="smart-view">
                <div className="section-header">
                  <h2>Smart Mixes</h2>
                  <p>AI-generated playlists based on your music</p>
                </div>
                
                <div className="smart-mixes-grid">
                  {smartMixes.map(mix => (
                    <div key={mix.id} className="mix-card">
                      <div className="mix-artwork" onClick={() => playSmartMix(mix)}>
                        <SmartIcon />
                        <div className="play-overlay">
                          <PlayIcon />
                        </div>
                      </div>
                      <div className="mix-info">
                        <h4>{mix.name}</h4>
                        <p>{mix.description}</p>
                        <span className="mix-type">{mix.mix_type}</span>
                      </div>
                    </div>
                  ))}
                </div>
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

            {currentView === 'analytics' && (
              <div className="analytics-view">
                <div className="section-header">
                  <h2>Listening Analytics</h2>
                  <p>Your music listening insights</p>
                </div>
                
                {stats && (
                  <div className="stats-grid">
                    <div className="stat-card">
                      <h3>{stats.total_tracks}</h3>
                      <p>Total Tracks</p>
                    </div>
                    <div className="stat-card">
                      <h3>{stats.total_plays}</h3>
                      <p>Total Plays</p>
                    </div>
                    <div className="stat-card">
                      <h3>{genres.length}</h3>
                      <p>Genres Detected</p>
                    </div>
                    <div className="stat-card">
                      <h3>{moods.length}</h3>
                      <p>Mood Categories</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Queue Sidebar */}
        {showQueue && (
          <div className="queue-sidebar">
            <div className="queue-header">
              <h3>Queue</h3>
              <button onClick={() => setShowQueue(false)}>×</button>
            </div>
            
            <div className="queue-tabs">
              <button 
                className={currentQueueType === 'user' ? 'active' : ''}
                onClick={() => setCurrentQueueType('user')}
              >
                Your Queue ({userQueue.length})
              </button>
              <button 
                className={currentQueueType === 'auto' ? 'active' : ''}
                onClick={() => setCurrentQueueType('auto')}
              >
                Auto Queue ({autoQueue.length})
              </button>
            </div>
            
            <div className="queue-list">
              {(currentQueueType === 'user' ? userQueue : autoQueue).map((track, index) => (
                <div 
                  key={`${track.id}-${index}`}
                  className={`queue-item ${index === currentQueueIndex && currentQueueType === (currentQueueType) ? 'current' : ''}`}
                  onClick={() => playTrack(track, currentQueueType === 'user' ? userQueue : autoQueue, currentQueueType)}
                >
                  <div className="queue-track-info">
                    <h5>{track.title || track.filename}</h5>
                    <p>{track.artist}</p>
                  </div>
                  {track.ai_genre && <span className="queue-genre">{track.ai_genre}</span>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Enhanced Player Bar */}
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
              <h4>{currentTrack.title || currentTrack.filename}</h4>
              <p>{currentTrack.artist}</p>
              <div className="track-tags">
                {currentTrack.ai_genre && <span className="genre-tag">{currentTrack.ai_genre}</span>}
                {currentTrack.mood && <span className="mood-tag">{currentTrack.mood}</span>}
              </div>
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
              
              <button className="control-btn" onClick={handleTrackSkip}>
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

            <div className="queue-indicator">
              <span className="queue-type">{currentQueueType === 'user' ? 'Your Queue' : 'Auto Queue'}</span>
              {unlimitedMode && <InfiniteIcon />}
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
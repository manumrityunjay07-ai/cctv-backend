import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import Login from './Login'
import './App.css'

const COLORS = ['#00C851', '#ffbb33', '#ff4444'];

function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('search');
  const [zoneData, setZoneData] = useState([]);
  const [riskData, setRiskData] = useState([]);
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [videoUrl, setVideoUrl] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchAnswer, setSearchAnswer] = useState(null);
  const [personCount, setPersonCount] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [timelineModalOpen, setTimelineModalOpen] = useState(false);
  const [timelineItems, setTimelineItems] = useState([]);
  const [timelineIndex, setTimelineIndex] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [exportUrl, setExportUrl] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [jobStatusInfo, setJobStatusInfo] = useState(null);
  const [currentPersonId, setCurrentPersonId] = useState(null);
  
  // Zone Builder State
  const [customZones, setCustomZones] = useState([]);

  useEffect(() => {
    if (activeTab === 'analytics' && user) {
      fetch('/api/analytics')
        .then(res => res.json())
        .then(data => {
          setZoneData(data.zoneData || []);
          setRiskData(data.riskData || []);
        })
        .catch(err => console.error("Failed to load analytics", err));
    }
  }, [activeTab, user]);

  useEffect(() => {
    // fetch current person count on load
    if (user) {
      fetch('/api/person_count')
        .then(r => r.json())
        .then(d => { if (d.ok) setPersonCount(d.count); })
        .catch(()=>{});
    }
  }, [user]);

  const handlePersonSearch = async (personId) => {
    setIsSearching(true);
    setSearchQuery(`Tracking Person ${personId}`);
    try {
      const response = await fetch(`/api/search_by_person?person_id=${personId}`);
      const data = await response.json();
        if (data.results) {
        setSearchResults(data.results.map(r => ({
          ...r,
          clipUrl: (r.metadata && r.metadata.video_clip) ? `${r.metadata.video_clip}` : (videoUrl || "https://www.w3schools.com/html/mov_bbb.mp4")
        })));
      } else {
        setSearchResults([]);
      }
    } catch (err) {
      console.error("Person search failed", err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setVideoUrl(URL.createObjectURL(selectedFile));
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploadStatus('Uploading and processing... This may take a few minutes!');
    
    const formData = new FormData();
    formData.append('file', file);
    if (customZones.length > 0) {
      formData.append('zones', JSON.stringify(customZones));
    }
    
    try {
      const response = await fetch('/api/upload_and_process', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setUploadStatus(`Upload and Processing Complete! Found ${data.events_found || 0} events.`);
      } else {
        setUploadStatus('Error processing video: ' + (data.detail || 'Unknown error'));
      }
    } catch (err) {
      setUploadStatus('Error connecting to backend. Make sure it is running!');
      console.error(err);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    setSearchAnswer(null);
    try {
      const response = await fetch(`/api/search?query=${encodeURIComponent(searchQuery)}`);
      const data = await response.json();
      
      if (data.results) {
        setSearchResults(data.results.map(r => ({
          ...r,
          clipUrl: r.clipUrl || videoUrl || "https://www.w3schools.com/html/mov_bbb.mp4"
        })));
        if (data.answer) {
          setSearchAnswer(data.answer);
        }
      } else {
        setSearchResults([]);
      }
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setIsSearching(false);
    }
  };

  async function viewTimeline(personId) {
    try {
      const r = await fetch(`/api/person_timeline?person_id=${encodeURIComponent(personId)}`)
      const data = await r.json()
      if (data.ok) {
        const items = data.items.map(it => ({...it, snapshot: it.snapshot ? (`${it.snapshot}`) : null}))
        setTimelineItems(items)
        setTimelineIndex(0)
        setExportUrl(null)
        setCurrentPersonId(personId)
        setTimelineModalOpen(true)
      }
    } catch (e) {
      console.error(e)
    }
  }

  async function stitchPersonFromTimeline(personId) {
    if (!personId) return alert('No person id')
    try {
      const r = await fetch(`/api/stitch_person_clip_async?person_id=${encodeURIComponent(personId)}`, {
        method: 'POST'
      })
      const data = await r.json()
      if (data.ok) {
        setJobId(data.job_id)
        pollJob(data.job_id)
      } else {
        alert('Failed to start stitch job')
      }
    } catch (e) {
      console.error(e)
      alert('Error starting stitch')
    }
  }

  async function fetchBestPhoto(personId) {
    try {
      const r = await fetch(`/api/best_photo?person_id=${encodeURIComponent(personId)}`)
      const d = await r.json()
      if (d.ok) {
        window.open(`${d.photo}`, '_blank')
      } else {
        alert('No best photo: ' + (d.reason || 'none'))
      }
    } catch (e) {
      console.error(e)
      alert('Error fetching best photo')
    }
  }

  async function exportCrops(personId) {
    setExporting(true)
    setExportUrl(null)
    try {
      const r = await fetch(`/api/export_person_crops_async?person_id=${encodeURIComponent(personId)}`, {
        method: 'POST'
      })
      const data = await r.json()
      if (data.ok && data.job_id) {
        setJobId(data.job_id)
        pollJob(data.job_id)
      } else {
        alert('Failed to start export job')
        setExporting(false)
      }
    } catch (e) {
      console.error(e)
      alert('Export error')
      setExporting(false)
    }
  }

  async function pollJob(jid) {
    setJobStatusInfo(null)
    const start = Date.now()
    const interval = setInterval(async () => {
      try {
        const r = await fetch(`/api/job_status?job_id=${jid}`)
        const data = await r.json()
        if (data.ok) {
          setJobStatusInfo(data.job)
          if (data.job.status === 'done') {
            const res = data.job.result
            let zipUrl = null;
            if (res && res.zip_url) {
              zipUrl = res.zip_url;
            } else if (res && res.result && res.result.zip_url) {
              zipUrl = res.result.zip_url;
            } else if (res && res.stitched_url) {
              zipUrl = res.stitched_url;
            }
            if (zipUrl) {
              setExportUrl(zipUrl)
              window.location.href = zipUrl;
            }
            clearInterval(interval)
            setExporting(false)
            setJobId(null)
          } else if (data.job.status === 'failed') {
            clearInterval(interval)
            setExporting(false)
            setJobId(null)
            alert('Job failed')
          }
        }
      } catch (e) {
        console.error(e)
      }
      if (Date.now() - start > 20 * 60 * 1000) {
        clearInterval(interval)
        setExporting(false)
        setJobId(null)
      }
    }, 2000)
  }

  if (!user) {
    return <Login onLogin={setUser} />
  }

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-logo">
            <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="20" cy="20" r="18" stroke="url(#grad)" strokeWidth="2"/>
              <circle cx="20" cy="20" r="8" fill="url(#grad)" opacity="0.8"/>
              <circle cx="20" cy="20" r="3" fill="white"/>
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#06b6d4"/>
                  <stop offset="1" stopColor="#3b82f6"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h2>VisionAI</h2>
        </div>

        <nav className="sidebar-nav">
          <button className={`nav-item ${activeTab === 'search' ? 'active' : ''}`} onClick={() => setActiveTab('search')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            Smart Search
          </button>
          <button className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`} onClick={() => setActiveTab('analytics')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 20V10M12 20V4M6 20v-6"/>
            </svg>
            Analytics
          </button>
        </nav>

        <div className="sidebar-upload">
          <h3>Ingest Footage</h3>
          <div className="upload-box">
            <input type="file" accept="video/*" onChange={handleFileChange} id="file-upload" />
            <label htmlFor="file-upload" className="upload-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
              </svg>
              <span>{file ? file.name : 'Select Video File'}</span>
            </label>
            <button onClick={handleUpload} disabled={!file} className="btn-process">
              Process Video
            </button>
            {uploadStatus && <div className="upload-status">{uploadStatus}</div>}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Top Header */}
        <header className="top-header">
          <div className="header-stats">
            <div className="stat-pill">
              <span className="stat-dot"></span>
              {personCount !== null ? `${personCount} People Detected` : 'Monitoring Active'}
            </div>
          </div>
          <div className="user-profile">
            <span className="user-name">{user.username}</span>
            <div className="user-avatar">{user.avatar}</div>
            <button className="btn-logout" onClick={() => setUser(null)} title="Sign out">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
              </svg>
            </button>
          </div>
        </header>

        {/* View Routing */}
        <div className="content-area">
          {activeTab === 'search' && (
            <div className="search-view">
              <div className="hero-search">
                <h1>What are you looking for?</h1>
                <p>Use natural language to search through hours of CCTV footage instantly.</p>
                
                <form onSubmit={handleSearch} className="hero-search-form">
                  <div className="search-input-wrapper">
                    <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                    <input 
                      type="text" 
                      placeholder="e.g. Find customers who looked at a product but didn't purchase..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <button type="submit" disabled={isSearching || !searchQuery} className="btn-search">
                      {isSearching ? <span className="spinner"></span> : 'Search'}
                    </button>
                  </div>
                </form>
              </div>

              {searchAnswer && (
                <div className="ai-insight-card">
                  <div className="ai-icon">✨</div>
                  <div className="ai-content">
                    <h4>AI Summary</h4>
                    <p>{searchAnswer}</p>
                  </div>
                </div>
              )}

              {searchResults.length > 0 && (
                <div className="results-grid">
                  <h3 className="section-title">Match Results ({searchResults.length})</h3>
                  <div className="events-list">
                    {searchResults.map((result) => (
                      <div key={result.id} className={`event-card ${result.riskScore >= 80 ? 'risk-high' : ''}`}>
                        <div className="event-media">
                          <video src={result.clipUrl} controls muted className="event-video"></video>
                          {result.snapshot && (
                            <div className="event-snapshot-wrapper">
                              <img src={result.snapshot} alt="snapshot" className="event-snapshot" />
                            </div>
                          )}
                        </div>
                        <div className="event-details">
                          <div className="event-header-row">
                            <span className={`risk-badge ${result.riskScore >= 80 ? 'high' : result.riskScore >= 50 ? 'med' : 'low'}`}>
                              Risk: {result.riskScore} {result.riskScore >= 80 ? '⚠️' : ''}
                            </span>
                            <div className="event-actions">
                              {/* Cloud mode: Snapshot renders automatically */}
                            </div>
                          </div>
                          <p className="event-summary-text">{result.summary}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="analytics-view">
              <h2 className="section-title">Intelligence Dashboard</h2>
              <div className="charts-grid">
                
                <div className="chart-card">
                  <h3>Zone Traffic</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={zoneData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="name" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" />
                      <RechartsTooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }} />
                      <Bar dataKey="visits" fill="url(#colorVisits)" radius={[4, 4, 0, 0]} />
                      <defs>
                        <linearGradient id="colorVisits" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#38bdf8" stopOpacity={1}/>
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.8}/>
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="chart-card">
                  <h3>Risk Assessment</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={riskData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {riskData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <RechartsTooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }} />
                      <Legend verticalAlign="bottom" height={36}/>
                    </PieChart>
                  </ResponsiveContainer>
                </div>

              </div>
            </div>
          )}
        </div>
      </main>

      {/* Timeline Modal */}
      {timelineModalOpen && (
        <div className="modal-backdrop" onClick={() => setTimelineModalOpen(false)}>
          <div className="modal-window" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Entity Timeline Tracking</h3>
              <div className="modal-actions">
                {exportUrl && <a href={exportUrl} target="_blank" rel="noreferrer" className="btn-process small">Download ZIP</a>}
                <button className="btn-close" onClick={() => setTimelineModalOpen(false)}>✕</button>
              </div>
            </div>
            
            <div className="modal-body">
              {timelineItems.length === 0 ? (
                <div className="empty-state">No timeline events recorded.</div>
              ) : (
                <div className="timeline-viewer">
                  <div className="timeline-media">
                    {timelineItems[timelineIndex].snapshot ? (
                      <img src={timelineItems[timelineIndex].snapshot} alt="Entity Crop" />
                    ) : (
                      <div className="no-media">No Snapshot</div>
                    )}
                  </div>
                  <div className="timeline-info">
                    <span className="timeline-time">{new Date(timelineItems[timelineIndex].start_time).toLocaleString()}</span>
                    <p className="timeline-desc">{timelineItems[timelineIndex].summary}</p>
                  </div>
                  <div className="timeline-controls">
                    <button className="btn-secondary" onClick={() => setTimelineIndex(Math.max(0, timelineIndex-1))} disabled={timelineIndex === 0}>Previous</button>
                    <span className="timeline-counter">{timelineIndex + 1} / {timelineItems.length}</span>
                    <button className="btn-secondary" onClick={() => setTimelineIndex(Math.min(timelineItems.length-1, timelineIndex+1))} disabled={timelineIndex === timelineItems.length-1}>Next</button>
                  </div>
                  <div className="timeline-tools">
                    <button className="btn-process full" onClick={() => stitchPersonFromTimeline(currentPersonId)}>
                      {jobId ? 'Processing Clip...' : 'Stitch Full Video Clip'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App

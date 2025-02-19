---
theme: dashboard
title: Whaleforecast – TikTok
toc: false
head: <link rel="icon"
  href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22 fill=%22black%22>🐳</text></svg>">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
---

<div class="header">
  <h1>Whaleforecast 🐳 – TikTok</h1>
  <p class="description">Most relevant TikTok videos for each German political party</p>
</div>

```js
const data = FileAttachment('data/tiktok_details.json').json()
```

```js
data
```

<style>
.party-list {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding: 1rem;
}

.party-row {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  overflow: hidden;
}

.party-header {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.party-header h2 {
  margin: 0;
  color: #1e293b;
  font-size: 1.5rem;
}

.video-list {
  padding: 1rem;
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 #f1f5f9;
}

.video-list::-webkit-scrollbar {
  height: 8px;
}

.video-list::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.video-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.video-list::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.video-card {
  flex: 0 0 300px;
  min-width: 300px;
  height: 500px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  transition: transform 0.2s;
  text-decoration: none;
  display: block;
}

.video-card:hover {
  transform: translateY(-2px);
}

.video-thumbnail {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #f1f5f9;
}

.video-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 1.5rem;
  color: white;
  z-index: 1;
  background: linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.7) 20%, rgba(0,0,0,0.9) 100%);
}

.video-header {
  position: absolute;
  top: 1rem;
  left: 1rem;
  right: 1rem;
  display: flex;
  align-items: center;
  z-index: 2;
  background: rgba(0,0,0,0.5);
  padding: 0.5rem;
  border-radius: 8px;
  backdrop-filter: blur(4px);
}

.author-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  margin-right: 0.75rem;
  border: 2px solid rgba(255, 255, 255, 0.8);
}

.author-name {
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.video-content {
  margin-top: 1rem;
}

.video-title-wrapper {
  max-height: 2.5rem;
  overflow: hidden;
  margin-bottom: 1rem;
  cursor: pointer;
  position: relative;
  padding-right: 1.5rem;
}

.video-title-wrapper::after {
  content: '▼';
  position: absolute;
  right: 0;
  top: 0;
  color: white;
  font-size: 0.75rem;
  transform: rotate(0deg);
  transition: transform 0.2s ease;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.video-title-wrapper.expanded {
  max-height: none;
}

.video-title-wrapper.expanded::after {
  transform: rotate(180deg);
}

.video-title {
  font-size: 0.875rem;
  line-height: 1.25rem;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.video-stats {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.video-stats-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.video-stat {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.video-link {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.5rem 1rem;
  background: #f1f5f9;
  border-radius: 6px;
  color: #0284c7;
  text-decoration: none;
  font-size: 0.875rem;
}

.video-link:hover {
  background: #e2e8f0;
}

.hashtags-section {
  padding: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.hashtag-pill {
  background: #f1f5f9;
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.875rem;
  color: #0284c7;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
}

.hashtag-pill[data-importance="high"] {
  background: #dbeafe;
  color: #1d4ed8;
  font-weight: 600;
  transform: scale(1.05);
}

.hashtag-pill[data-importance="medium"] {
  background: #f1f5f9;
  color: #0284c7;
}

.hashtag-pill[data-importance="low"] {
  background: #f8fafc;
  color: #64748b;
  font-size: 0.8rem;
}

.hashtag-count {
  background: #e2e8f0;
  padding: 0.125rem 0.375rem;
  border-radius: 999px;
  font-size: 0.75rem;
  color: #475569;
}

.video-card:hover .video-info {
  max-height: 80%;
}
</style>

```js
function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

function formatDate(timestamp) {
  return new Date(timestamp * 1000).toLocaleDateString('de-DE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const partyColors = {
  SPD: '#E3000F',
  CDU: '#000000',
  CSU: '#0066CC',
  'Grüne': '#46962B',
  FDP: '#FFED00',
  Linke: '#BE3075',
  AfD: '#009EE0',
  BSW: '#E64415'
}

const partyRows = Object.entries(data).map(([party, partyData]) => {
  // Calculate score thresholds for this party's hashtags
  const scores = partyData.top_hashtags.map(h => h.score);
  const maxScore = Math.max(...scores);
  const highThreshold = maxScore * 0.7;
  const mediumThreshold = maxScore * 0.3;

  return html`
    <div class="party-row">
      <div class="party-header" style="border-left: 4px solid ${partyColors[party] || '#ccc'}">
        <h2>${party}</h2>
      </div>
      <div class="hashtags-section">
        ${partyData.top_hashtags.map(hashtag => {
          let importance = "low";
          if (hashtag.score >= highThreshold) importance = "high";
          else if (hashtag.score >= mediumThreshold) importance = "medium";
          
          return html`
            <div class="hashtag-pill" data-importance="${importance}">
              #${hashtag.tag}
              <span class="hashtag-count">${formatNumber(hashtag.count)}</span>
            </div>
          `;
        })}
      </div>
      <div class="video-list">
        ${partyData.videos.map(video => html`
          <a class="video-card" href="${video.url}" target="_blank" rel="noopener">
            <div class="video-thumbnail">
              <img src="${video.origin_cover}" alt="Video thumbnail">
            </div>
            <div class="video-header">
              <img class="author-avatar" src="${video.author.avatar}" alt="${video.author.unique_id}">
              <span class="author-name">@${video.author.unique_id}</span>
            </div>
            <div class="video-info">
              <div class="video-content">
                <div class="video-title-wrapper" onclick="event.preventDefault(); this.classList.toggle('expanded')">
                  <div class="video-title">${video.title}</div>
                </div>
                <div class="video-stats">
                  <div class="video-stats-row">
                    <span class="video-stat">👁️ ${formatNumber(video.play_count)}</span>
                    <span class="video-stat">❤️ ${formatNumber(video.digg_count)}</span>
                    <span class="video-stat">💬 ${formatNumber(video.comment_count)}</span>
                  </div>
                  <div class="video-stats-row">
                    <span class="video-stat">📅 ${formatDate(video.create_time)}</span>
                  </div>
                </div>
              </div>
            </div>
          </a>
        `)}
      </div>
    </div>
  `
})

display(html`<div class="party-list">${partyRows}</div>`)

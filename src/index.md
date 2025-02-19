---
theme: dashboard
title: Whaleforecast
toc: false
head: <link rel="icon"
  href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22 fill=%22black%22>🐳</text></svg>">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
---

<div class="header">
  <h1>Whaleforecast 🐳</h1>
  <p class="description">A real-time dashboard tracking German political parties' campaign activities, media presence, and polling data.</p>
</div>

<div class="time-range">
  <div id="slider-container">
    <div class="slider-track-bg"></div>
    <div class="slider-track"></div>
    <input type="range" id="start-date">
    <input type="range" id="end-date">
  </div>
  <div class="date-labels">
    <div class="date-label">From: <span id="start-label"></span></div>
    <div class="date-label">To: <span id="end-label"></span></div>
  </div>
</div>

```js
const endDate = new Date()
const startDate = new Date('2020-01-01')

const value = Generators.observe(notify => {
  const startInput = document.getElementById('start-date')
  const endInput = document.getElementById('end-date')
  const startLabel = document.getElementById('start-label')
  const endLabel = document.getElementById('end-label')
  const sliderTrack = document.querySelector('.slider-track')
  
  // Set min/max values from JavaScript variables
  startInput.min = startDate.getTime()
  startInput.max = endDate.getTime()
  startInput.step = 86400000 // one day in milliseconds
  
  endInput.min = startDate.getTime()
  endInput.max = endDate.getTime()
  endInput.step = 86400000
  
  // Initialize values
  startInput.value = new Date('2024-01-01').getTime()
  endInput.value = endDate.getTime()
  
  function updateTrack() {
    const start = Number(startInput.value)
    const end = Number(endInput.value)
    const range = endDate.getTime() - startDate.getTime()
    const startPercent = ((start - startDate.getTime()) / range) * 100
    const endPercent = ((end - startDate.getTime()) / range) * 100
    
    sliderTrack.style.left = `${startPercent}%`
    sliderTrack.style.width = `${endPercent - startPercent}%`
  }
  
  function updateLabels() {
    startLabel.textContent = formatDate(new Date(Number(startInput.value)))
    endLabel.textContent = formatDate(new Date(Number(endInput.value)))
  }
  
  function notifyChange() {
    notify([
      new Date(Number(startInput.value)),
      new Date(Number(endInput.value))
    ])
  }
  
  startInput.addEventListener('input', () => {
    if (Number(startInput.value) > Number(endInput.value)) {
      startInput.value = endInput.value
    }
    updateTrack()
    updateLabels()
    notifyChange()
  })
  
  endInput.addEventListener('input', () => {
    if (Number(endInput.value) < Number(startInput.value)) {
      endInput.value = startInput.value
    }
    updateTrack()
    updateLabels()
    notifyChange()
  })
  
  // Initial setup
  updateTrack()
  updateLabels()
  notifyChange()
})

const formatDate = d3.timeFormat('%B %d, %Y')
```

```js
const [start, end] = value
```

<div id="slider"></div>

<div class="grid">
  <div class="card">
    <div class="chart">
      ${resize((width) => rallyTimeline(rallies, {width, start, end}))}
    </div>
    <div class="source">
      Data: <a href="https://acleddata.com" target="_blank" rel="noopener">ACLED</a>
    </div>
  </div>
  
  <div class="card">
    <div class="chart">
      ${resize((width) => mediaTimeline(media, {width, start, end}))}
    </div>
    <div class="source">
      Data: <a href="https://mediacloud.org" target="_blank" rel="noopener">Media Cloud</a>
    </div>
  </div>

  <div class="card">
    <div class="chart">
      ${resize((width) => tiktokTimeline(tiktok, {width, start, end}))}
    </div>
    <div class="source">
      Data: <a href="https://github.com/davidteather/TikTok-Api" target="_blank" rel="noopener">TikTok API</a>
    </div>
  </div>

  <div class="card">
    <div class="chart">
      ${resize((width) => pollsTimeline(polls, {width, start, end}))}
    </div>
    <div class="source">
      Data: <a href="https://www.wahlrecht.de/umfragen/" target="_blank" rel="noopener">Wahlrecht.de</a>, 
      <a href="https://www.zeit.de/politik/deutschland/umfragen-bundestagswahl-neuwahl-wahltrend" target="_blank" rel="noopener">ZEIT Online</a>
    </div>
  </div>
</div>

<!-- Load and transform the data -->

```js
const rallies = FileAttachment('data/rallies.json').json()
const media = FileAttachment('data/media.json').json()
const tiktok = FileAttachment('data/tiktok.json').json()
const polls = FileAttachment('data/polls.json').json()
```

<!-- Define party colors -->

```js
const partyColors = {
  SPD: '#E3000F', // Traditional SPD red
  CDU: '#000000', // CDU black
  CSU: '#0066CC', // CSU blue
  Grüne: '#46962B', // Green party green
  FDP: '#FFED00', // FDP yellow
  Linke: '#BE3075', // Left party purple/pink
  AfD: '#009EE0', // AfD blue
  BSW: '#E64415' // BSW orange
}
```

<!-- A shared color scale using party colors -->

```js
const color = Plot.scale({
  color: {
    type: 'categorical',
    domain: Object.keys(partyColors),
    range: Object.values(partyColors),
    unknown: '#CCCCCC' // Default gray for unlisted parties
  }
})
```

<!-- Timeline plots -->

```js
function getTimeInterval(start, end) {
  const daysDiff = (end - start) / (1000 * 60 * 60 * 24)

  if (daysDiff <= 180) {
    return 'day'
  } else if (daysDiff <= 730) {
    return 'week'
  } else {
    return 'month'
  }
}

// Shared plot style configuration
const plotStyle = {
  background: 'transparent',
  fontSize: 13,
  fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
  color: '#1e293b',
  overflow: 'visible'
}

const axisStyle = {
  tickColor: '#94a3b8',
  labelColor: '#64748b',
  labelFontSize: 12,
  tickFontSize: 11
}

function rallyTimeline(data, { width, start, end } = {}) {
  const filteredData = data.filter(d => {
    const date = new Date(d.date)
    return date >= start && date <= end
  })

  const interval = getTimeInterval(start, end)

  return Plot.plot({
    title: '🎯 Campaign Rally Attendance',
    subtitle: `${
      interval.charAt(0).toUpperCase() + interval.slice(1)
    }ly total attendees at political party rallies`,
    width,
    height: 300,
    style: plotStyle,
    y: {
      ...axisStyle,
      label: 'Number of Attendees',
      labelOffset: 45,
      tickFormat: d => `${d / 1000}k`
    },
    x: {
      ...axisStyle,
      label: null,
      labelOffset: 35
    },
    color: { ...color, legend: true },
    marks: [
      Plot.rectY(
        filteredData,
        Plot.binX(
          { y: 'sum' },
          {
            x: 'date',
            y: 'size',
            fill: d => d.organizers_canonical[0],
            interval: interval,
            tip: {
              format: {
                y: d => `${d.toLocaleString()} attendees`
              }
            },
            opacity: 0.9
          }
        )
      ),
      Plot.ruleY([0])
    ]
  })
}

function mediaTimeline(data, { width, start, end } = {}) {
  const filteredData = data
    .filter(d => {
      const date = new Date(d.date)
      return date >= start && date <= end
    })
    .map(d => {
      return Object.entries(d)
        .filter(([key]) => key !== 'date')
        .map(([party, count]) => ({
          date: new Date(d.date),
          party,
          count
        }))
    })
    .flat()

  const interval = getTimeInterval(start, end)

  return Plot.plot({
    title: '📰 Media Coverage',
    subtitle: `${
      interval.charAt(0).toUpperCase() + interval.slice(1)
    }ly average mentions of political parties in German online news`,
    width,
    height: 300,
    style: plotStyle,
    y: {
      ...axisStyle,
      label: 'Number of Articles',
      labelOffset: 45
    },
    x: {
      ...axisStyle,
      label: null,
      labelOffset: 35
    },
    color: { ...color, legend: true },
    marks: [
      Plot.lineY(
        filteredData,
        Plot.binX(
          { y: 'mean' },
          {
            x: 'date',
            y: 'count',
            stroke: 'party',
            interval: interval,
            tip: {
              format: {
                y: d => d.toLocaleString()
              }
            },
            curve: 'basis',
            strokeWidth: 2
          }
        )
      ),
      Plot.ruleY([0]),
      Plot.crosshairX(filteredData, {
        x: "date",
        y: "count"
      })
    ]
  })
}

function tiktokTimeline(data, { width, start, end } = {}) {
  const filteredData = data
    .filter(d => {
      const date = new Date(d.date)
      return date >= start && date <= end
    })
    .map(d => {
      return Object.entries(d)
        .filter(([key]) => key !== 'date')
        .map(([party, count]) => ({
          date: new Date(d.date),
          party,
          count
        }))
    })
    .flat()

  const interval = getTimeInterval(start, end)

  return Plot.plot({
    title: '📱 TikTok Activity',
    subtitle: `${
      interval.charAt(0).toUpperCase() + interval.slice(1)
    }ly total views of videos posted by or mentioning political parties on TikTok`,
    width,
    height: 300,
    style: plotStyle,
    y: {
      ...axisStyle,
      label: 'Number of Views',
      labelOffset: 45,
      tickFormat: d => `${d / 1000000}M`
    },
    x: {
      ...axisStyle,
      label: null,
      labelOffset: 35
    },
    color: { ...color, legend: true },
    marks: [
      Plot.lineY(
        filteredData,
        Plot.binX(
          { y: 'sum' },
          {
            x: 'date',
            y: 'count',
            stroke: 'party',
            interval: interval,
            tip: {
              format: {
                y: d => `${(d / 1000000).toFixed(1)}M views`
              }
            },
            curve: 'basis',
            strokeWidth: 2
          }
        )
      ),
      Plot.ruleY([0]),
      Plot.crosshairX(filteredData, {
        x: "date",
        y: "count"
      })
    ]
  })
}

function pollsTimeline(data, { width, start, end } = {}) {
  const filteredData = data
    .filter(d => {
      const date = new Date(d.date)
      return date >= start && date <= end
    })
    .map(row => ({ ...row, date: new Date(row.date) }))

  const interval = getTimeInterval(start, end)
  const ma = Plot.windowY(
    { k: 14, anchor: 'end', reduce: 'mean' },
    { x: 'date', y: 'value', stroke: 'party', tip: true }
  )

  return Plot.plot({
    title: '🗳️ Polling',
    subtitle: '14-day moving average of German federal election polls, with individual poll results shown as dots',
    width,
    height: 300,
    style: plotStyle,
    y: {
      ...axisStyle,
      label: '%',
      labelOffset: 45
    },
    x: {
      ...axisStyle,
      label: null,
      labelOffset: 35
    },
    color: { ...color, legend: true },
    marks: [
      Plot.dot(filteredData, {
        x: 'date',
        y: 'value',
        stroke: 'party',
        fill: 'party',
        r: 2,
        fillOpacity: 0.5
      }),
      Plot.lineY(filteredData, {
        ...ma,
        strokeWidth: 2,
        tip: {
          format: {
            y: d => `${d.toFixed(1)}%`
          }
        }
      }),
      Plot.ruleY([5], {
        strokeWidth: 5,
        stroke: 'grey',
        strokeOpacity: 0.5
      }),
      Plot.ruleY([0]),
      Plot.crosshairX(filteredData, ma)
    ]
  })
}
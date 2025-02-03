---
theme: dashboard
title: Wahlkampfmonitor
toc: false
head: <link rel="icon"
  href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22 fill=%22black%22>🐳</text></svg>">
---

# Walkampfmonitor 🐳💥

<!-- Load and transform the data -->

```js
const rallies = FileAttachment('data/rallies.json').json()
const media = FileAttachment('data/media.json').json()
const tiktok = FileAttachment('data/tiktok.json').json()
const polls = FileAttachment('data/polls.json').json()
```

<link rel="stylesheet" href="npm:jquery-ui/dist/themes/base/jquery-ui.css">

```js
const $ = (self.jQuery = (
  await import('npm:jquery/dist/jquery.js/+esm')
).default)
await import('npm:jquery-ui/dist/jquery-ui.js/+esm')
```

```js
const endDate = new Date()

const value = Generators.observe(notify => {
  const slider = $('#slider')
  slider.slider({
    range: true,
    min: new Date('2020-01-01').getTime(),
    max: endDate.getTime(),
    values: [new Date('2024-01-01').getTime(), endDate.getTime()],
    slide: (event, ui) => {
      notify(ui.values.map(timestamp => new Date(timestamp)))
    }
  })
  notify(slider.slider('values').map(timestamp => new Date(timestamp))) // report initial dates
})
const formatDate = d3.timeFormat('%B %d, %Y')
```

```js
const [start, end] = value
display(html`Date range: ${formatDate(start)} → ${formatDate(end)}`)
```

<div style="max-width: 100%;" id="slider"></div>

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
    style: {
      background: 'transparent',
      fontSize: 12,
      color: '#2c3e50'
    },
    y: {
      grid: true,
      label: 'Number of Attendees',
      labelOffset: 45,
      tickFormat: d => `${d / 1000}k`
    },
    x: {
      label: '→ Time',
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
            tip: true
          }
        )
      ),
      Plot.ruleY([0]),
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
    style: {
      background: 'transparent',
      fontSize: 12,
      color: '#2c3e50'
    },
    y: {
      grid: true,
      label: 'Number of Articles',
      labelOffset: 45
    },
    x: {
      label: '→ Time',
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
            tip: true,
            curve: 'basis'
          }
        )
      ),
      Plot.ruleY([0]),
      Plot.crosshairX(filteredData, {x: "date"})
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
    style: {
      background: 'transparent',
      fontSize: 12,
      color: '#2c3e50'
    },
    y: {
      grid: true,
      label: 'Number of Views',
      labelOffset: 45,
      tickFormat: d => `${d / 1000000}M`
    },
    x: {
      label: '→ Time',
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
            tip: true,
            curve: 'basis'
          },
        ),
      ),
      Plot.ruleY([0]),
      Plot.crosshairX(filteredData, {x: "date"})
    ]
  })
}

function pollsTimeline(data, { width, start, end } = {}) {
  const filteredData = data.filter(d => {
      const date = new Date(d.date)
      return date >= start && date <= end
    }).map(row => ({...row, date: new Date(row.date)}))
  console.log(filteredData)
  
  const interval = getTimeInterval(start, end)

  const ma = Plot.windowY({k: 14, anchor: "end", reduce: "mean"}, {x: "date", y: "value", stroke: "party", tip: true})

  return Plot.plot({
    title: '🗳️ Polling',
    subtitle: "14-day moving average of German federal election polls, with individual poll results shown as dots",
    width,
    height: 300,
    style: {
      background: 'transparent',
      fontSize: 12,
      color: '#2c3e50'
    },
    y: {
      grid: true,
      label: '%',
      labelOffset: 45
    },
    x: {
      label: '→ Time',
      labelOffset: 35
    },
    color: { ...color, legend: true },
    marks: [
      Plot.dot(filteredData, {x: "date", y: "value", stroke: "party", fill: "party", r: 1}),
      Plot.lineY(filteredData, ma),
      Plot.ruleY([5], { strokeWidth: 5, stroke: "grey", strokeOpacity: 0.5}),
      Plot.ruleY([0]),
      Plot.crosshairX(filteredData, ma)
    ]
  })
}
```

<div class="grid">
  <div class="card">
    ${resize((width) => rallyTimeline(rallies, {width, start, end}))}
    <p>Data source: <a href="https://acleddata.com">Armed Conflict Location & Event Data Project (ACLED)</a></p>
  </div>
  
  <div class="card">
    ${resize((width) => mediaTimeline(media, {width, start, end}))}
    <p>Data source: <a href="https://mediacloud.org">Media Cloud</a></p>
  </div>

  <div class="card">
    ${resize((width) => tiktokTimeline(tiktok, {width, start, end}))}
    <p>Data source: <a href="https://github.com/davidteather/TikTok-Api">TikTok</a></p>
  </div>

  <div class="card">
    ${resize((width) => pollsTimeline(polls, {width, start, end}))}
    <p>Data source: <a href="https://www.wahlrecht.de/umfragen/">Wahlrecht.de</a>, <a href="https://www.zeit.de/politik/deutschland/umfragen-bundestagswahl-neuwahl-wahltrend">ZEIT Online</a></p>
  </div>
</div>

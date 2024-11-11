---
theme: dashboard
title: Wahlkampfmonitor
toc: false
head: <link rel="icon"
  href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22 fill=%22black%22>🐳</text></svg>">
---

# 🐳💥 Wahlkampfmonitor

<!-- Load and transform the data -->

```js
const rallies = FileAttachment('data/rallies.json').json()
const media = FileAttachment('data/media.json').json()
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
    min: new Date('2023-01-01').getTime(),
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
    title: '🎯 Campaign Rally Activity',
    subtitle: `${
      interval.charAt(0).toUpperCase() + interval.slice(1)
    }ly distribution of political party rallies`,
    width,
    height: 300,
    style: {
      background: 'transparent',
      fontSize: 12,
      color: '#2c3e50'
    },
    y: {
      grid: true,
      label: 'Number of Campaign Rallies',
      labelOffset: 45
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
          { y: 'count' },
          {
            x: 'date',
            fill: d => d.organizers_canonical[0],
            interval: interval,
            tip: true
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
      Plot.ruleY([0])
    ]
  })
}
```

<div class="grid grid-cols-1 gap-4">
  <div class="card">
    ${resize((width) => rallyTimeline(rallies, {width, start, end}))}
    <p class="text-sm text-gray-500 mt-2">Data source: <a href="https://acleddata.com" class="underline">Armed Conflict Location & Event Data Project (ACLED)</a></p>
  </div>
  
  <div class="card">
    ${resize((width) => mediaTimeline(media, {width, start, end}))}
    <p class="text-sm text-gray-500 mt-2">Data source: <a href="https://mediacloud.org" class="underline">Media Cloud</a></p>
  </div>
</div>

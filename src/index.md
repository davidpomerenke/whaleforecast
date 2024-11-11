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
function rallyTimeline(data, { width } = {}) {
  return Plot.plot({
    title: '🎯 Campaign Rally Activity',
    subtitle: 'Weekly distribution of political party rallies',
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
        data,
        Plot.binX(
          { y: 'count' },
          {
            x: 'date',
            fill: d => d.organizers_canonical[0],
            interval: 'week',
            tip: true
          }
        )
      ),
      Plot.ruleY([0])
    ]
  })
}

function mediaTimeline(data, { width } = {}) {
  // Process the data into weekly aggregates
  const longData = data
    .map(d => {
      const date = new Date(d.date)
      // Get the start of the week (Sunday)
      const weekStart = new Date(date)
      weekStart.setDate(date.getDate() - date.getDay())

      return Object.entries(d)
        .filter(([key]) => key !== 'date')
        .map(([party, count]) => ({
          date: weekStart, // Use week start date
          party,
          count
        }))
    })
    .flat()

  // Aggregate by week
  const weeklyData = d3.rollup(
    longData,
    v => d3.sum(v, d => d.count),
    d => d.date.getTime(),
    d => d.party
  )

  // Convert back to array format
  const aggregatedData = Array.from(weeklyData, ([time, parties]) =>
    Array.from(parties, ([party, count]) => ({
      date: new Date(time),
      party,
      count
    }))
  ).flat()

  return Plot.plot({
    title: '📰 Media Coverage',
    subtitle: 'Daily mentions of political parties in German online news',
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
      Plot.lineY(aggregatedData, {
        x: 'date',
        y: 'count',
        stroke: 'party',
        tip: true
      }),
      Plot.ruleY([0])
    ]
  })
}
```

<div class="grid grid-cols-1 gap-4">
  <div class="card">
    ${resize((width) => rallyTimeline(rallies, {width}))}
    <p class="text-sm text-gray-500 mt-2">Data source: <a href="https://acleddata.com" class="underline">Armed Conflict Location & Event Data Project (ACLED)</a></p>
  </div>
  
  <div class="card">
    ${resize((width) => mediaTimeline(media, {width}))}
    <p class="text-sm text-gray-500 mt-2">Data source: <a href="https://mediacloud.org" class="underline">Media Cloud</a></p>
  </div>
</div>

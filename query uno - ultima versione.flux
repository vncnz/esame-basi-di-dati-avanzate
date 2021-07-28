import "strings"

from(bucket:"veronacard")
|> range(start: 2019-01-01T00:00:00Z, stop: 2020-12-31T23:59:59Z)
|> filter(fn:(r) => r._measurement == "swipes")
|> keep(columns: ["_time", "_value", "poi"])
|> aggregateWindow(
    every: 1d,
    fn: count,
    column: "_value",
    timeDst: "_time",
    createEmpty: true
)
// |> group(columns:["poi"])
|> map(fn: (r) => ({r with
    dayofyear: strings.substring(v: string(v:r._time), start: 5, end: 10),
    year: strings.substring(v: string(v:r._time), start: 0, end: 4)
  })
)
|> pivot(
  rowKey:["dayofyear", "poi"],
  columnKey: ["year"],
  valueColumn: "_value"
)
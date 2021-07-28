import "strings"

manageData = (tables=<-) =>
  tables
    |> filter(fn:(r) => r._measurement == "swipes")
    |> keep(columns: ["_time", "_value", "poi"])
    |> aggregateWindow(
        every: 1d,
        fn: count,
        column: "_value",
        timeSrc: "_start",
        timeDst: "_time",
        createEmpty: true
    )
    // |> duplicate(column: "_time", as: "otm") solo per debug
    |> map(fn: (r) => ({r with
            dayofyear: strings.substring(v: string(v:r._time), start: 5, end: 10)
        })
    )

from2019 = from(bucket:"veronacard")
|> range(start: 2019-01-01T00:00:00Z, stop: 2019-12-31T23:59:59Z) //-3y)
|> manageData()

from2020 = from(bucket:"veronacard")
|> range(start: 2020-01-01T00:00:00Z, stop: 2020-12-31T23:59:59Z) //-3y)
|> manageData()

join(
  tables: { fr19: from2019, fr20: from2020 },
  on: ["dayofyear", "poi"]
)
|> keep(columns: ["_time", "_value_fr19", "_value_fr20", "dayofyear", "poi"]) // "otm_fr19", "otm_fr20" solo per debug
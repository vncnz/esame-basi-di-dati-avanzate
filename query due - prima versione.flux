import "strings"
filterData = (tables=<-) =>
  tables
    |> range(start: 2019-01-01T00:00:00Z, stop: 2019-01-31T23:59:59Z)
    |> filter(fn:(r) => r._measurement == "swipes")
    |> keep(columns: ["_value", "_time", "poi"])
    |> group(columns:["_value"])
    |> sort(columns:["_time"])
    |> map(fn: (r) => ({r with
            enum: 1,
            year: strings.substring(v: string(v:r._time), start: 0, end: 4)
        })
    )
    |> cumulativeSum(columns: ["enum"])

datafrom2019 = from(bucket:"veronacard")
|> filterData()

datafrom2019_again = from(bucket:"veronacard")
|> filterData()
|> map(fn: (r) => ({r with
        enum: r.enum-1
    })
)

join(
    tables: { tab1: datafrom2019, tab2: datafrom2019_again },
    on: ["_value", "enum", "year"]
)
|> map(fn: (r) => ({r with
        diff: uint(v:r._time_tab2) - uint(v:r._time_tab1)
    })
)
|> group(columns:["poi_tab1", "poi_tab2", "year"])
|> mean(column: "diff")
|> map(fn: (r) => ({r with
        diff_human: string(v: duration(v: uint(v: r.diff)))
    })
)
from(bucket:"veronacard_intpoi")
|> range(start: 2019-01-01T00:00:00Z, stop: 2019-12-31T23:59:59Z)
|> filter(fn:(r) => r._measurement == "swipes")
|> keep(columns: ["_value", "_time", "intpoi"])
|> group(columns:["_value"])
|> sort(columns:["_time"])
|> map(fn: (r) => ({r with
        intpoi: uint(v: r.intpoi)
    })
)
|> difference(
    nonNegative: false,
    columns: ["intpoi"],
    keepFirst: false
)
|> elapsed(
  unit: 1m,
  timeColumn: "_time",
  columnName: "elapsed"
)
|> keep(columns: ["elapsed", "intpoi"])
|> group(columns:["intpoi"])
|> mean(column: "elapsed")
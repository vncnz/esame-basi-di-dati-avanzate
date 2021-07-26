# from influxdb import InfluxDBClient
# client = InfluxDBClient(host='localhost', port=8086)

# from datetime import datetime

from influxdb_client import InfluxDBClient #, Point, WritePrecision
# from influxdb_client.client.write_api import SYNCHRONOUS

org = 'vncnz'
bucket = 'veronacard'

client = InfluxDBClient(
    url="http://localhost:8086",
    # token='XW-1vwymovFSHkMPAa7lO0z7jN5EMylDJIo13Jtk8JPpO_hq832bY8SVmVzxTIoxxzs8y5v9xwYJbJf9SPZI6Q=='
    token='fUqlD-BmuQf4xczeIAWEIZDkYh2C16vZWLG1W8SxjqIl8WZyZUQlp5d--t0iL0SWExq4G53q4hlzzcCUppGOIw==' # windows
    # token='Hki0rGb_R5pbCEkquPmetbu2tgQHFrJ-iYHsJUwep-7UNQ8b_zanqkOjhucWCGCRFRLWnDEsC_aiS8MNQi0Qow==' # win_uff
)

# write_api = client.write_api()
query_api = client.query_api()

def progressBar(current, total, barLength = 20):
    percent = float(current) * 100 / total
    arrow   = '-' * int(percent/100 * barLength - 1) + '>'
    spaces  = ' ' * (barLength - len(arrow))

    print(percent >= 100 and '  ✅' or '  ⏳', 'Progress: [%s%s] %d %%' % (arrow, spaces, percent), end='\r')


query = '''
import "strings"

from2019 = from(bucket:"veronacard")
|> range(start: 2019-01-01T00:00:00Z, stop: 2019-12-31T23:59:59Z) //-3y)
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

from2020 = from(bucket:"veronacard")
|> range(start: 2020-01-01T00:00:00Z, stop: 2020-12-31T23:59:59Z) //-3y)
|> filter(fn:(r) => r._measurement == "swipes")
//|> keep(columns: ["_time", "_value", "poi"])

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
        // otm_time: string(v: duration(v: uint(v:r.otm) - uint(v: 2019-01-01T00:00:00Z)))
        dayofyear: strings.substring(v: string(v:r._time), start: 5, end: 10)
    })
)
// |> timeShift(duration: -1y)

join(
  tables: { fr19: from2019, fr20: from2020 },
  on: ["dayofyear", "poi"]
)
|> keep(columns: ["_time", "_value_fr19", "_value_fr20", "dayofyear", "poi"]) // "otm_fr19", "otm_fr20" solo per debug
'''

query = '''
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
'''








query = '''
import "strings"

from(bucket:"veronacard")
|> range(start: 2019-01-01T00:00:00Z, stop: 2020-12-31T23:59:59Z)
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
|> group(columns:["poi"])
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
'''





















results = query_api.query(query=query, org=org)
lst = []

cols = []

def fltr(lst):
    return [x for x in lst if x.label not in ['result', '_start', '_stop', '_field', '_measurement']]

# for table in results:
#     tablecols = fltr(table.get_group_key())
#     print('\nTable ', ', '.join(map(lambda c: '%s=%s' % (c.label, table.records[0][c.label]), tablecols)))
#     cols = fltr(table.columns)
#     for col in cols:
#         print(col.label.rjust(18), end='  ')
#     print('')
#     for record in table.records:
#         for col in cols:
#             dt = record.values.get(col.label)
#             if col.data_type == 'dateTime:RFC3339':
#                 dt = dt.strftime('%Y%m%d@%H:%M:%S')
#             print('%18s' % dt, end='  ')
#         print('')
#         # lst.append((record.get_time().isoformat(), str(record.values.get('elapsed')).rjust(8), record.values.get('card'), record.values.get('poi'), record.values.get('dispositivo')))

# # ocio, comportamento particolare: se ci sono più valori vengono restituiti più record (tm e card nel mio db di test)

# # for el in lst:
# #    print(el)

# diz = {}
# for el in lst:
#     if not el[2] in diz:
#         diz[el[2]] = []
#     diz[el[2]].append(el)

# for cardlst in diz.values():
#     for el in cardlst:
#         print(el)
#     print('')



print('Query done. Starting plot...')

import matplotlib.pyplot as plt
import math


cols = 4
figure, axis = plt.subplots(math.ceil(len(results)/cols), cols)
xx = 0
yy = 0

xdata = list(range(0, 366))

for table in results:

    dayofyear = [x.values['dayofyear'] for x in table.records]
    for idx, dt in enumerate(dayofyear):
        if dt[3:5] == '01' or dt[3:5] == '15':
            xdata[idx] = dt
    axis[yy, xx].plot(xdata, [x.values['2019'] for x in table.records], label = "2019")
    axis[yy, xx].plot(xdata, [x.values['2020'] for x in table.records], label = "2020")
    tablecols = fltr(table.get_group_key())
    axis[yy, xx].set_title(', '.join(map(lambda c: '%s=%s' % (c.label, table.records[0][c.label]), tablecols)))
    axis[yy, xx].legend()

    xx += 1
    if xx >= cols:
        xx = 0
        yy += 1

# naming the x axis
plt.xlabel('Giorno')

# naming the y axis
plt.ylabel('Visite')

# giving a title to my graph
#tablecols = fltr(table.get_group_key())
#plt.title(', '.join(map(lambda c: '%s=%s' % (c.label, table.records[0][c.label]), tablecols)))

# show a legend on the plot
plt.legend()

# function to show the plot
plt.show()
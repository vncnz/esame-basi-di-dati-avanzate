from datetime import datetime
from influxdb_client import InfluxDBClient

org = 'vncnz'
bucket = 'veronacard_test'

client = InfluxDBClient(
    url="http://localhost:8086",
    # token='XW-1vwymovFSHkMPAa7lO0z7jN5EMylDJIo13Jtk8JPpO_hq832bY8SVmVzxTIoxxzs8y5v9xwYJbJf9SPZI6Q=='
    token='fUqlD-BmuQf4xczeIAWEIZDkYh2C16vZWLG1W8SxjqIl8WZyZUQlp5d--t0iL0SWExq4G53q4hlzzcCUppGOIw==' # windows
    # token='Hki0rGb_R5pbCEkquPmetbu2tgQHFrJ-iYHsJUwep-7UNQ8b_zanqkOjhucWCGCRFRLWnDEsC_aiS8MNQi0Qow==' # win_uff
)
client.api_client.configuration.timeout = 30000

# write_api = client.write_api()
query_api = client.query_api()

def progressBar(current, total, barLength = 20):
    percent = float(current) * 100 / total
    arrow   = '-' * int(percent/100 * barLength - 1) + '>'
    spaces  = ' ' * (barLength - len(arrow))

    print(percent >= 100 and '  ✅' or '  ⏳', 'Progress: [%s%s] %d %%' % (arrow, spaces, percent), end='\r')


query_INEFFICIENT = '''
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
'''

query = '''

from(bucket:"veronacard_intpoi")
|> range(start: 2019-01-01T00:00:00Z, stop: 2019-12-31T23:59:59Z)
|> filter(fn:(r) => r._measurement == "swipes")
|> keep(columns: ["_value", "_time", "intpoi"]) // "poi" è solo per debug
|> group(columns:["_value"])
|> sort(columns:["_time"])
|> duplicate(column: "intpoi", as: "destpoi")
|> map(fn: (r) => ({r with
        intpoi: uint(v: r.intpoi)
    })
)
|> difference(
    nonNegative: false,
    columns: ["intpoi"],
    keepFirst: true
)
|> elapsed(
  unit: 1m,
  timeColumn: "_time",
  columnName: "elapsed"
)

|> keep(columns: ["elapsed", "intpoi"])
|> group(columns:["intpoi"])
|> mean(column: "elapsed")
'''

intpoi_legend = [
    (1, None), (2, 'Tomba Giulietta'), (4, 'Casa Giulietta'), (8, 'Castelvecchio'), (16, 'Teatro Romano'), (32, 'Arena'), 
    (64, 'Centro Fotografia'), (128, 'Santa Anastasia'), (256, 'Duomo'), (512, 'Palazzo della Ragione'), (1024, 'San Zeno'), 
    (2048, 'Torre Lamberti'), (4096, 'San Fermo'), (8192, 'Museo Radio'), (16384, 'Museo Storia'), (32768, 'Giardino Giusti'), 
    (65536, 'Museo Lapidario'), (131072, 'AMO'), (262144, 'Museo Miniscalchi'), (524288, 'Verona Tour'), 
    (1048576, 'Museo Africano'), (2097152, 'Sighseeing'), (4194304, 'Museo Conte')
]

timestamp_1 = datetime.now().replace(microsecond=0)
results = query_api.query(query=query, org=org)
timestamp_2 = datetime.now().replace(microsecond=0)

lst = []

cols = []

def fltr(lst):
    return [x for x in lst if x.label not in ['result', '_start', '_stop', '_field', '_measurement']]


int_to_pois = {}
for a in intpoi_legend:
    for b in intpoi_legend:
        int_to_pois[a[0] - b[0]] = {
            'from': a[1],
            'to': b[1],
            'from_int': a[0],
            'to_int': b[0]
        }
int_to_pois[0] = { 'from': 'POI', 'to': 'stesso POI', 'from_int': None, 'to_int': None }


# ad-hoc pretty print

for table in results:
    if not len(table.records): continue
    if len(table.records) > 1:
        print('\n\nWhat?')
    record = table.records[0]
    intpoi = record.values.get('intpoi')
    elapsed = record.values.get('elapsed')
    path = int_to_pois[intpoi]
    print('%s ===> %s   in %s minuti' % (path['from'].rjust(21), path['to'].ljust(21), round(elapsed)))
    # print("{ from: '%s', to: '%s', from_int: %s, to_int: %s, count: %s }," % (path['from'], path['to'], path['from_int'] or 'null', path['to_int'] or 'null', round(elapsed)))

# end
exit(0)


for table in results:
    tablecols = fltr(table.get_group_key())
    if not len(table.records): continue
    print('\nTable ', ', '.join(map(lambda c: '%s=%s' % (c.label, table.records[0][c.label]), tablecols)))
    cols = fltr(table.columns)
    for col in cols:
        print(col.label.rjust(18), end='  ')
    print('')
    for record in table.records:
        for col in cols:
            dt = record.values.get(col.label)
            if col.data_type == 'dateTime:RFC3339':
                dt = dt.strftime('%Y%m%d@%H:%M:%S')
            print('%18s' % dt, end='  ')
        print('')


print('Query eseguita in %s' % (timestamp_2-timestamp_1))
print('Risultati in %s tabelle' % len(results))

exit(0)








matrix = {}
pois = []

for table in results:
    if len(table.records):

        poi1 = table.records[0]["poi_tab1"]
        poi2 = table.records[0]["poi_tab2"]

        if not poi1 in matrix:
            matrix[poi1] = {}
        
        if not poi1 in pois:
            pois.append(poi1)
        if not poi2 in pois:
            pois.append(poi2)
        
        tablecols = fltr(table.get_group_key())
        print('\nTable ', ', '.join(map(lambda c: '%s=%s' % (c.label, table.records[0][c.label]), tablecols)))
    cols = fltr(table.columns)
    for col in cols:
        print(col.label.rjust(18), end='  ')
    print('')
    for record in table.records:

        matrix[poi1][poi2] = record.values.get('diff_human')

        for col in cols:
            dt = record.values.get(col.label)
            if col.data_type == 'dateTime:RFC3339':
                dt = dt.strftime('%Y%m%d@%H:%M:%S')
            print('%18s' % dt, end='  ')
        print('')
        # lst.append((record.get_time().isoformat(), str(record.values.get('elapsed')).rjust(8), record.values.get('card'), record.values.get('poi'), record.values.get('dispositivo')))

# ocio, comportamento particolare: se ci sono più valori vengono restituiti più record (tm e card nel mio db di test)

# for el in lst:
#    print(el)

import re
from datetime import timedelta


regex = re.compile(r'((?P<hours>\d*)h)?((?P<minutes>\d*)m)?((?P<seconds>\d*)s)?((?P<ms>\d*)ms)?((?P<us>\d*)us)?((?P<ns>\d*)ns)?')

def truncate(time_str):
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {
        'hours': 0,
        'minutes': 0,
        'seconds': 0
    }
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return '%2sh%2sm%2ss' % (time_params['hours'], time_params['minutes'], time_params['seconds'])

def parse_time(time_str):
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)

sz = 10
sz2 = 14
print('')
print(''.rjust(sz2, '.'), end=' ')
for poi2 in pois:
    print(str(poi2[:sz]).rjust(sz, '.'), end=' ')
print('')

for poi1 in pois:
    print(str(poi1[:sz2]).rjust(sz2, '.'), end=' ')
    for poi2 in pois:
        if poi1 in matrix and poi2 in matrix[poi1]:
            tdl = truncate(matrix[poi1][poi2])
            print(tdl.rjust(sz, '.'), end=' ')
        else:
            print('.'.rjust(sz, '.'), end=' ')
    print('')



exit(0)

print('Query done. Starting plot...')

import matplotlib.pyplot as plt
import datetime
import math


cols = 4
figure, axis = plt.subplots(math.ceil(len(results)/cols), cols)
xx = 0
yy = 0

xdata = list(range(0, 365))

for table in results:

    dayofyear = [x.values['dayofyear'] for x in table.records]
    for idx, dt in enumerate(dayofyear):
        if dt[3:5] == '01' or dt[3:5] == '15':
            xdata[idx] = dt
    axis[yy, xx].plot(xdata, [x.values['_value_fr19'] for x in table.records], label = "2019")
    axis[yy, xx].plot(xdata, [x.values['_value_fr20'] for x in table.records], label = "2020")
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
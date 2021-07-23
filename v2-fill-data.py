# from influxdb import InfluxDBClient
# client = InfluxDBClient(host='localhost', port=8086)

from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

org = 'vncnz'
bucket = 'veronacard_intpoi'

# client = InfluxDBClient(
#   url="https://europe-west1-1.gcp.cloud2.influxdata.com",
#   token="Taiju5w8TEteVMjU4bt6emM3L0NpgnWAinolzSEYfB4JCVphV9DjebNRvQASWXzKSOqkKO4TvthcB74N1ICCPw=="
# )
client = InfluxDBClient(
    url="http://localhost:8086",
    # token='XW-1vwymovFSHkMPAa7lO0z7jN5EMylDJIo13Jtk8JPpO_hq832bY8SVmVzxTIoxxzs8y5v9xwYJbJf9SPZI6Q=='
    # token='fUqlD-BmuQf4xczeIAWEIZDkYh2C16vZWLG1W8SxjqIl8WZyZUQlp5d--t0iL0SWExq4G53q4hlzzcCUppGOIw==' # windows
    token='Hki0rGb_R5pbCEkquPmetbu2tgQHFrJ-iYHsJUwep-7UNQ8b_zanqkOjhucWCGCRFRLWnDEsC_aiS8MNQi0Qow==' # win_uff
)

write_api = client.write_api()
query_api = client.query_api()


import os
import re
import datetime

count = 0

columns = [
    'Data', # data ingresso
    'Ora', # ora ingresso
    'POI', # punto di interesse
    'Dispositivo', # lettore tessera, rapporto potenzialmente N:1 con i POI
    'Seriale', # numero tessera
    'DataAttivazione', # data attivazione
    'in?',
    'int?',
    'Profilo' # Tipo di carta: 24-ore, 48-ore, ecc...
]

def convertFileToList (fl):
    global count
    count1 = 0
    lst = []
    pois = []
    for line in fl:
        rowdata = line.split(',')
        count += 1
        count1 += 1
        record = { label: value for label, value in zip(columns, rowdata) }
        record['datetime'] = datetime.datetime.strptime(record['Data'] + record['Ora'], '%d-%m-%y%H:%M:%S')
        if not record['POI'] in pois:
            pois.append(record['POI'])
        lst.append(record)
    print('Caricati da csv %6s nuovi record, totale provvisorio %9s' % (count1, count))
    return lst, pois

def progressBar(current, total, barLength = 20):
    percent = float(current) * 100 / total
    arrow   = '-' * int(percent/100 * barLength - 1) + '>'
    spaces  = ' ' * (barLength - len(arrow))

    print(percent >= 100 and '  ✅' or '  ⏳', 'Progress: [%s%s] %d %%' % (arrow, spaces, percent), end='\r')

years = {}

path_linux = '/home/vncnz/Desktop/dataset_veronacard_2014_2020'
path_windows = 'G:\\NNNNNNNNNNNNNNNNNN\\Esame database\\dataset_veronacard_2014_2020'

all_pois = [None]

for root, dirs, files in os.walk(path_windows, topdown=False):
    # files = [f for f in files if not f[0] == '.']
    # files = [f for f in files if '2015' in f]
    for name in files:
        if not '.csv' in name or name.startswith('.'): continue
        # print(root, dirs, name)
        numbers = re.findall(r'\d+', name)
        year = None
        if len(numbers):
            year = numbers[0]
        with open(os.path.join(root, name)) as fl:
            data, pois = convertFileToList(fl)
            if len(data) and not year:
                year = data[0]['datetime'].year
            years[year] = data

            for poi in pois:
                if not poi in all_pois:
                    all_pois.append(poi)


for k, v in years.items():

    i = 0
    for record in v:
        point = Point("swipes") \
            .tag("poi", record['POI']) \
            .tag("intpoi", 2**all_pois.index(record['POI'])) \
            .tag("dispositivo", record['Dispositivo']) \
            .field("card", record['Seriale']) \
            .time(record['datetime'].isoformat(), WritePrecision.S)

        write_api.write(bucket, org, point)
        i += 1
        progressBar(i, len(v), 40)
    print('')

for poi in all_pois:
    print('%10s %s' % (2**all_pois.index(poi), poi))
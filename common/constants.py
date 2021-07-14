import json

SERVER_PORT = 3030
CLIENT_PORT = 4040
BUFFER_SIZE = 1024
ENCODING = 'utf-8'
INITIAL_INTERVAL = 10
BACKOFF_CUTOFF = 120

f = open('config.json')
CONFIG = json.loads(f)

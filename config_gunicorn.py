bind = '0.0.0.0:5183'
backlog = 2048

workers = 1
worker_class = 'gthread'
worker_connections = 1000
timeout = 30
keepalive = 2
spew = False
capture_output = True
threads = 10

daemon = False

errorlog = '-'
accesslog = '-'
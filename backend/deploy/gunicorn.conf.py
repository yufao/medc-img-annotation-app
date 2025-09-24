import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() // 2 or 1
worker_class = "sync"
timeout = 60
graceful_timeout = 30
keepalive = 2
accesslog = "-"  # stdout
errorlog = "-"
loglevel = "info"
preload_app = False

def when_ready(server):
    server.log.info("Gunicorn server is ready. Workers=%s", workers)
# Ejudge listener

Ejudge listener is a service for pyinformatics.

# Deploy


- Add configuration for systemd unit file:

  /etc/conf.d/celery:

```ini
# Names of nodes to start
CELERYD_NODES="worker1 worker2 worker3 worker4"
# Or just
#CELERYD_NODES=4

# Absolute path to the 'celery' command:
CELERY_BIN="???/venv/bin/celery"

# App instance to use
#CELERY_APP="ejudge-listener project app/celery_worker:celery"

# Extra command-line arguments to the worker
CELERYD_OPTS="--time-limit=300 --concurrency=4"

# - %n will be replaced with the first part of the nodename.
# - %I will be replaced with the current child process index
CELERYD_PID_FILE="/var/run/celery/%n.pid"
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
CELERYD_LOG_LEVEL="INFO"
```

- Add systemd unit file:
  
  /etc/systemd/system/celery.service:

```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=celery
Group=celery
EnvironmentFile=/etc/conf.d/celery
WorkingDirectory=/opt/celery
ExecStart=/bin/sh -c '${CELERY_BIN} multi start ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'
ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait ${CELERYD_NODES} \
  --pidfile=${CELERYD_PID_FILE}'
ExecReload=/bin/sh -c '${CELERY_BIN} multi restart ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'

[Install]
WantedBy=multi-user.target
```

# Testing

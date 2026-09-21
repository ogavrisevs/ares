Ubuntu 24.04 setup
------------------

sudo apt install nginx python3.12-venv

Run backend and web page as separate services
----------------------------------------------

These commands assume the project is installed at `/opt/ares` and that its
files are owned by the `ares` service user.

```sh
sudo useradd --system --home /opt/ares --shell /usr/sbin/nologin ares
sudo mkdir -p /opt/ares /var/lib/ares
sudo chown -R ares:ares /opt/ares /var/lib/ares
```

Copy or clone this project into `/opt/ares`, then install its Python
dependencies:

```sh
cd /opt/ares/backend
sudo -u ares python3.12 -m venv .venv
sudo -u ares .venv/bin/pip install -r requirements.txt
```

Install and enable the service:

```sh
sudo cp /opt/ares/deploy/ares.service /etc/systemd/system/ares.service
sudo systemctl daemon-reload
sudo systemctl enable --now ares.service
sudo systemctl status ares.service
```

Configure Nginx to serve the web page on port 80:

```sh
sudo cp /opt/ares/deploy/ares-nginx.conf /etc/nginx/sites-available/ares
sudo ln -sf /etc/nginx/sites-available/ares /etc/nginx/sites-enabled/ares
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

The Python backend listens on port `8000`, and Nginx serves the map on port
`80`. The map is available at `http://<server-ip>/`. Check both services:

```sh
curl http://127.0.0.1:8000/health
curl -I http://127.0.0.1/
sudo journalctl -u ares.service -f
```

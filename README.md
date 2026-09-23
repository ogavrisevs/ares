Deploy (Ubuntu 24.04, Ansible)
------------------------------

Set the server address in `deploy/inventory.ini`, then run from the repo root:

```sh
ansible-playbook -i deploy/inventory.ini deploy/playbook.yml
```

The playbook installs Nginx and Python, creates the `ares` user, copies the
backend to `/opt/ares/backend` and the web page to `/opt/ares/web`, installs
Python dependencies, and enables `ares.service` and Nginx. Re-run it to deploy
updates.

The Python backend listens on port `8000`, and Nginx serves the map on port
`80`. The map is available at `http://<server-ip>/`. Check both services:

```sh
curl http://127.0.0.1:8000/health
curl -I http://127.0.0.1/
sudo journalctl -u ares.service -f
```

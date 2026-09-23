Deploy with Ansible
===================

Deploys the backend and web page to an Ubuntu 24.04 server.

Requirements
------------

On your machine:

```sh
sudo apt install pipx
pipx install --include-deps ansible
pipx ensurepath
```

Don't use `apt install ansible` on Ubuntu 22.04: that installs Ansible 2.10,
which can't manage Ubuntu 24.04 servers (Python 3.12) and fails with
`No module named 'ansible.module_utils.six.moves'`.

The server needs SSH access for a user with `sudo`.

Configure
---------

Edit `inventory.ini` and set the server address and SSH user:

```ini
[ares]
ares-server ansible_host=192.0.2.10 ansible_user=ubuntu
```

Check that Ansible can reach the server:

```sh
ansible -i poc/deploy/inventory.ini ares -m ping
```

Run
---

From the repo root:

```sh
ansible-playbook -i poc/deploy/inventory.ini poc/deploy/playbook.yml
```

Add `--ask-become-pass` (`-K`) if `sudo` asks for a password. Re-run the same
command to deploy updates.

What it does
------------

- Installs `nginx`, `python3.12-venv` and `acl`
- Creates the `ares` system user, `/opt/ares` and `/var/lib/ares`
- Copies `backend/app.py`, `backend/requirements.txt` and `web/index.html`
- Installs Python dependencies into `/opt/ares/backend/.venv`
- Installs `ares.service` and the Nginx site, then starts both services

Check
-----

```sh
curl http://<server-ip>:8000/health
curl -I http://<server-ip>/
```

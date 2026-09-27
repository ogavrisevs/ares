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

The server address is not stored in the repo. `inventory.ini` reads it from
environment variables:

| Variable         | Required | Default  |
| ---------------- | -------- | -------- |
| `ARES_SERVER_IP` | yes      |          |
| `ARES_SSH_USER`  | no       | `ubuntu` |

```sh
export ARES_SERVER_IP=192.0.2.10
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

GitHub Actions
--------------

`.github/workflows/deploy.yml` runs the playbook on every push to `main` that
changes `poc/backend`, `poc/web` or `poc/deploy`, and on manual
**Run workflow**. It uses the `production` environment. Configure in
**Settings → Environments → production** (or at repository level):

- Variable `ARES_SERVER_IP`: server address
- Variable `ARES_SSH_USER` (optional): SSH user, defaults to `ubuntu`
- Secret `SSH_PRIVATE_KEY`: private key whose public key is in the SSH user's
  `~/.ssh/authorized_keys`

The SSH user needs passwordless `sudo` (the default `ubuntu` user on EC2 has it).
The server's security group must allow SSH from GitHub-hosted runners.

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

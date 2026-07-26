# local-frappe-manager

A local, browser-based dashboard for managing a Frappe bench — install
apps, manage sites, backup, restore, migrate — all without touching the
command line after initial setup. Styled after Frappe Cloud's dashboard,
built for a single local bench instead of a fleet of remote servers.

```
local-frappe-installer/   ("how do I get a bench running?")
        |
        v
local_bench/ + frontend/   ("how do I manage it afterward?")
        |
        v
Frappe / ERPNext / any other Frappe app
```

Both live in this one repo: the installer in `local-frappe-installer/`,
the actual Frappe app (what gets installed on your bench) at the repo
root (`local_bench/`, `frontend/`, `setup.py`, etc.) — this is
deliberate, so `bench get-app` on this repo URL finds the app directly.

---

## Install guide

### Requirements

**Windows 11:**
- WSL2 with Ubuntu 22.04 (see step 1 below if you don't have this yet)
- Virtualization enabled in BIOS (on by default on most machines; some
  work-issued laptops have it locked off by IT policy)
- 8 GB RAM minimum, 16 GB recommended
- 20 GB free disk space

**Native Linux (Ubuntu 22.04 recommended):**
- Same RAM/disk as above, a user account with sudo access

### Step 1 — WSL Ubuntu (skip if you already have it)

In **PowerShell as Administrator**:
```
wsl --install -d Ubuntu-22.04
```
Restart if prompted. Open "Ubuntu" from the Start menu and set a
username/password when asked — this is a new Linux user, separate from
your Windows login.

### Step 2 — Run the installer

Inside that Ubuntu terminal:
```
git clone https://github.com/notyetcoder/local-frappe-manager.git
cd local-frappe-manager/local-frappe-installer
chmod +x install.sh
./install.sh
```

**What happens, in order:**
1. Checks the environment (Linux/WSL detected)
2. Installs Docker if it isn't already present (asks for your Ubuntu
   password once) — if Docker was *just* installed, the script
   automatically re-runs itself once permissions catch up; this is
   expected, not an error
3. Builds a Docker image with Frappe + the dashboard app
   (`local_bench`) — **10-20 minutes** the first time, much faster on
   any re-run since Docker caches layers
4. Starts the containers (database, cache, background workers, etc.)
5. Creates your first site and installs the dashboard on it
6. Builds the dashboard's frontend inside the container (~1-2 min)
7. Prints a URL and login details

No app like ERPNext is installed at this stage on purpose — that
happens next, from inside the dashboard itself, not the installer. This
keeps the two products cleanly separated: the installer's only job is
handing you a working dashboard.

### Step 3 — Log in

Open the URL the script prints — by default:
```
http://local-bench.localhost/local-bench
```
on **Windows**, in a regular browser (Chrome/Edge/Firefox), not inside
the Ubuntu terminal — WSL2 forwards the port automatically.

**Default login (unless you changed it — see below):**
- Username: `Administrator`
- Password: `frappeP`

This default is fine for local-only use, since nothing here is exposed
to the internet by default. If you ever expose this bench externally,
change it first — see "Changing the defaults" below.

---

## Usage guide

### Installing your first app (e.g. ERPNext)

1. Open the **Apps** tab
2. Find ERPNext (or CRM, HR, Helpdesk, Learning, Insights, Gameplan,
   Builder, Wiki, Drive, Healthcare, Lending — all one-click) and click
   **Install**
3. Confirm the site name and password (both default sensibly — site
   name is `<app>.localhost`, password is `frappeP`) or change either
4. Watch the live log as it creates the site, fetches the app, and
   installs it — usually a few minutes
5. Once done, visit `http://<app>.localhost` to use it directly, or
   manage it further from the **Sites** tab

### Installing an app not in the gallery

Click **Install from GitHub URL** on the Apps tab, paste any Frappe app
repo URL, give it an app name matching the repo (usually the last part
of the URL) and a site — same live-log flow as above.

Only install apps you trust — this runs that app's code on your
machine, same as running `bench get-app` yourself would.

### Managing sites (Sites tab)

- **Backup** — takes a full backup (database + files) via `bench backup`
- **Migrate** — runs `bench migrate` (needed after updating an app)
- **Drop** — deletes a site; bench takes an automatic backup first

### Changing the default password

Before installing, set your own:
```
LOCAL_BENCH_DB_PASSWORD=yourpassword LOCAL_BENCH_ADMIN_PASSWORD=yourpassword ./install.sh
```
Or just change it after the fact from inside a site once logged in
(Settings → Change Password), same as any Frappe site.

---

## Troubleshooting

**"Cannot connect to the Docker daemon"** — Docker was just installed;
close and reopen the Ubuntu terminal, then re-run `./install.sh`.

**Stuck WSL / very slow after installing Docker** — in PowerShell:
`wsl --shutdown`, then reopen Ubuntu and re-run `./install.sh`.

**Browser can't reach `local-bench.localhost`** — confirm the script
printed "Done"; try `http://localhost/local-bench` instead; check
containers with `docker compose --project-name local-bench ps`.

**Want to force a full rebuild** — `docker rmi` the image shown in the
script's "already built" message, then re-run.

**Re-running after a failure** — safe to do. The script skips Docker
install if already done, skips the image build if nothing changed,
and skips site creation if the site already exists.

---

## Security notes

- No general-purpose "run this shell command" endpoint exists anywhere
  in this app — only fixed, named actions (install app, backup, etc.)
- Every backend command runs via `subprocess` with a list of arguments,
  never `shell=True`, never string concatenation — shell injection
  isn't possible through this app's inputs
- Site names, app names, and GitHub URLs are validated against a strict
  format before use
- Restoring a backup only accepts files already inside that site's own
  `private/backups` folder, not an arbitrary path
- Every endpoint requires the System Manager role

## Status

Backend and frontend are built and compile-verified, and have been
reviewed line-by-line for correctness against real `bench`/Docker
behavior. Real end-to-end runs (by the maintainer, on an actual
Windows/WSL machine) have caught and fixed several real bugs already —
see commit history. If something breaks for you, please open an issue
with the exact terminal output; that's consistently been the fastest
path to a fix so far.

## License

MIT

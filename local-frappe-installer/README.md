# local-frappe-installer

A guided setup script that prepares a local Frappe/ERPNext environment
on Windows (via WSL) or native Linux, using Docker.

This is **Product 1** in a two-part system:

```
local-frappe-installer    ("how do I get a bench running?")  <- you are here
        |
        v
local-frappe-manager       ("how do I manage it afterward?")
        |
        v
Frappe / ERPNext
```

Once this finishes, all day-to-day management (installing more apps,
backups, new sites) happens in the browser via
[local-frappe-manager](https://github.com/notyetcoder/local-frappe-manager),
which this script installs automatically as part of setup.

## What this actually does

One guided setup command prepares a local ERPNext environment: it
installs Docker if it isn't already present, builds a Frappe image with
ERPNext and the manager dashboard included, and creates your first
site. It is not a single infallible one-liner — see "Known limitations"
below for what it can't paper over.

## Requirements

**Windows 11:**
- WSL2 with Ubuntu 22.04 (this script installs the rest, but not WSL
  itself — see setup below)
- Virtualization enabled in BIOS (usually on by default, but some
  laptops — especially work-issued ones — have it disabled)
- 8 GB RAM minimum, 16 GB recommended
- 20 GB free disk space minimum

**Native Linux (Ubuntu 22.04 recommended):**
- Same RAM/disk requirements as above
- A user account with sudo access

## Setup

**1. If you're on Windows and don't have WSL yet**, open PowerShell as
Administrator:
```
wsl --install -d Ubuntu-22.04
```
Restart if prompted, then open "Ubuntu" from the Start menu.

**2. Inside that Ubuntu terminal (or native Ubuntu), run:**
```
wget https://raw.githubusercontent.com/notyetcoder/local-frappe-installer/main/install.sh
chmod +x install.sh
./install.sh
```

This takes 10-20 minutes on first run (mostly the Docker image build).
When it finishes, it prints a URL and an admin password.

## Known limitations

This script handles the common path well, but can't fully paper over:
- **Antivirus/firewall software** blocking Docker's network setup
- **Corporate-managed Windows machines** with virtualization or WSL
  disabled by IT policy
- **Port conflicts** if something else on your machine is already using
  port 80/8000
- **Very low RAM/disk** machines
- **Re-running after a partial failure** — the script tries to be safe
  to re-run, but hasn't been stress-tested against every failure point
  yet

If you hit one of these, the error message from the script is the
right thing to search or ask about — please open an issue with it.

## Troubleshooting

**"Cannot connect to the Docker daemon"**
Docker was just installed and the group permission hasn't taken effect
yet. Close the Ubuntu terminal window fully and reopen it, then run
`./install.sh` again.

**WSL feels frozen / very slow after installing Docker**
Run this in PowerShell (not Ubuntu):
```
wsl --shutdown
```
Then reopen Ubuntu and re-run `./install.sh`. It picks up where it left
off — it doesn't redo steps that already succeeded.

**Browser shows "This site can't be reached" at local-bench.localhost**
- Confirm the script actually finished (check for the final "Done"
  message and printed URL)
- Try `http://localhost/local-bench` instead — some browser/network
  configurations don't resolve `*.localhost` subdomains correctly on
  every setup, even though it's supposed to be automatic
- Check containers are actually running:
  `docker compose --project-name local-bench ps`

**Build fails partway through image build**
Almost always disk space or a network hiccup. Check free space with
`df -h`, and re-run `./install.sh` — Docker caches build layers, so a
retry is much faster than the first attempt.

**"Virtualization not enabled" or WSL2 won't install**
This needs to be fixed in your BIOS/UEFI settings (usually
"Intel VT-x" or "AMD-V"), not something this script can do for you.
Corporate/work laptops often have this locked by IT policy — if that's
your situation, this setup likely won't work without IT involvement.

## Uninstalling / starting over completely

```
docker compose --project-name local-bench down -v
rm -rf ~/.local-bench
docker rmi local-bench-custom:latest
```
This removes the containers, all site data, and the built image. Your
GitHub repos are untouched — re-running `install.sh` afterward starts
completely fresh.

## FAQ

**Does this send any of my data anywhere?**
No. Everything runs in Docker containers on your own machine. The only
network access during setup is downloading Docker itself, cloning the
GitHub repos, and pulling base container images — the same as running
`bench get-app` or `docker pull` yourself.

**Can I use this on an existing bench I already have?**
This script specifically creates a *new* Dockerized bench. If you
already have a working bench, skip this repo entirely and just install
[local-frappe-manager](https://github.com/notyetcoder/local-frappe-manager)
directly on it with `bench get-app`.

**What if I want a different app instead of ERPNext?**
Once setup finishes, use the dashboard itself — the "Install from
GitHub URL" option installs any Frappe-compatible app, not just what
this script starts you with.



Built and reviewed, but **not yet run end-to-end on a real machine**.
The first real run will likely surface something that needs fixing —
please report it via an issue with the exact error output.

## License

MIT

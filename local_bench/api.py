"""
Whitelisted endpoints for the local-bench dashboard.

Every action that changes something (install app, new site, backup...)
follows the same pattern:
  1. check permission
  2. generate a unique realtime channel name
  3. enqueue the actual bench command as a background job (jobs.py)
  4. return the channel name immediately so the frontend can subscribe
     and show live output while the job runs

Nothing here talks to Docker, servers, or billing. It only talks to the
bench it's already running on top of.
"""

import os
import re

import frappe
from frappe import _
from frappe.utils import get_bench_path, get_sites

from local_bench.jobs import run_bench_command


def _require_admin():
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Not permitted."), frappe.PermissionError)


def _new_channel(prefix: str) -> str:
	return f"local_bench:{prefix}:{frappe.generate_hash(length=8)}"


# ---------------------------------------------------------------------------
# Input validation
#
# Every subprocess call in jobs.py passes arguments as a list, never through
# a shell (no shell=True, no string concatenation into a shell command), so
# shell injection isn't possible here regardless of what's typed in. That
# said, unvalidated input can still confuse `bench`'s own argument parser
# (e.g. a site name starting with "--"), so everything user-supplied is
# checked against a strict format before it's used.
# ---------------------------------------------------------------------------

_SITE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9.-]*$")
_APP_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")
_REPO_URL_RE = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/?$")


def _validate_site_name(site: str):
	if not site or not _SITE_NAME_RE.match(site) or site.startswith("-"):
		frappe.throw(_("Invalid site name."))


def _validate_app_name(app: str):
	if not app or not _APP_NAME_RE.match(app):
		frappe.throw(_("Invalid app name. Use letters, numbers and underscores only."))


def _validate_repo_url(repo_url: str):
	if not repo_url or not _REPO_URL_RE.match(repo_url):
		frappe.throw(_("Only https://github.com/<org>/<repo> URLs are supported."))


def _validate_password(password: str):
	if not password or len(password) < 6 or "\n" in password:
		frappe.throw(_("Password must be at least 6 characters."))


# ---------------------------------------------------------------------------
# First-run welcome screen state
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_welcome_seen() -> bool:
	_require_admin()
	return bool(frappe.db.get_default("local_bench_welcome_seen"))


@frappe.whitelist()
def mark_welcome_seen():
	_require_admin()
	frappe.db.set_default("local_bench_welcome_seen", "1")


# ---------------------------------------------------------------------------
# Read-only: list what's currently on this bench
# ---------------------------------------------------------------------------

@frappe.whitelist()
def list_sites():
	"""All sites on this bench, with their installed apps."""
	_require_admin()
	sites = []
	for site in get_sites():
		try:
			site_apps = _get_installed_apps_for_site(site)
			sites.append({"name": site, "apps": site_apps})
		except Exception:
			sites.append({"name": site, "apps": [], "error": True})
	return sites


def _get_installed_apps_for_site(site: str) -> list[str]:
	apps_txt = os.path.join(get_bench_path(), "sites", site, "apps.txt")
	if not os.path.exists(apps_txt):
		return []
	with open(apps_txt) as f:
		return [line.strip() for line in f if line.strip()]


@frappe.whitelist()
def list_installed_apps_on_bench():
	"""All apps available on this bench (installed in the python env),
	regardless of which sites use them."""
	_require_admin()
	apps_txt = os.path.join(get_bench_path(), "sites", "apps.txt")
	if not os.path.exists(apps_txt):
		return []
	with open(apps_txt) as f:
		return [line.strip() for line in f if line.strip()]


@frappe.whitelist()
def list_gallery_apps():
	"""
	The curated 'install with one click' app gallery.

	Deliberately curated rather than pulled from the full marketplace
	(192+ apps at time of writing): most third-party marketplace apps are
	unverified, several are commercial-only, and many are unmaintained.
	This list is every actively-maintained app under the official
	`frappe` GitHub org — same trust tier as ERPNext itself. For anything
	else, users have "install from GitHub URL" (see install_app below).

	TODO (not built yet): if Frappe publishes a stable public API for
	their marketplace, pull from it live instead of this hardcoded list.
	Wasn't available as a documented public API as of this writing.
	"""
	_require_admin()
	return [
		{
			"app_name": "erpnext",
			"title": "ERPNext",
			"description": "Full-featured, free and open source ERP.",
			"repo": "https://github.com/frappe/erpnext",
		},
		{
			"app_name": "crm",
			"title": "Frappe CRM",
			"description": "Modern, open source CRM.",
			"repo": "https://github.com/frappe/crm",
		},
		{
			"app_name": "hrms",
			"title": "Frappe HR",
			"description": "Open source HR and payroll software.",
			"repo": "https://github.com/frappe/hrms",
		},
		{
			"app_name": "helpdesk",
			"title": "Frappe Helpdesk",
			"description": "Modern support ticketing app.",
			"repo": "https://github.com/frappe/helpdesk",
		},
		{
			"app_name": "lms",
			"title": "Frappe Learning",
			"description": "Open source learning management system.",
			"repo": "https://github.com/frappe/lms",
		},
		{
			"app_name": "insights",
			"title": "Frappe Insights",
			"description": "Open source BI/analytics tool with a no-SQL query builder and dashboards.",
			"repo": "https://github.com/frappe/insights",
		},
		{
			"app_name": "gameplan",
			"title": "Gameplan",
			"description": "Open source discussion and project communication tool for teams.",
			"repo": "https://github.com/frappe/gameplan",
		},
		{
			"app_name": "builder",
			"title": "Frappe Builder",
			"description": "Low-code, drag-and-drop website builder with one-click publishing.",
			"repo": "https://github.com/frappe/builder",
		},
		{
			"app_name": "wiki",
			"title": "Frappe Wiki",
			"description": "Free and open source wiki/documentation tool.",
			"repo": "https://github.com/frappe/wiki",
		},
		{
			"app_name": "drive",
			"title": "Frappe Drive",
			"description": "Open source file storage, sharing, and collaboration.",
			"repo": "https://github.com/frappe/drive",
		},
		{
			"app_name": "healthcare",
			"title": "Frappe Healthcare",
			"description": "Open source management system for medical/healthcare providers.",
			"repo": "https://github.com/frappe/healthcare",
		},
		{
			"app_name": "lending",
			"title": "Frappe Lending",
			"description": "Open source lending/loan management software.",
			"repo": "https://github.com/frappe/lending",
		},
	]


# ---------------------------------------------------------------------------
# Actions: each of these enqueues a real bench command
# ---------------------------------------------------------------------------

@frappe.whitelist()
def install_app(app: str, site: str, repo_url: str | None = None):
	"""
	Install an app onto a site. If it's not already available on this
	bench, fetch it first (repo_url required for anything outside the
	gallery — e.g. a community app the user found on GitHub).
	"""
	_require_admin()
	_validate_app_name(app)
	_validate_site_name(site)
	if repo_url:
		_validate_repo_url(repo_url)
	channel = _new_channel("install")
	commands = []
	if repo_url:
		commands.append(["get-app", repo_url])
	commands.append(["--site", site, "install-app", app])

	frappe.enqueue(
		_run_multiple,
		queue="long",
		commands=commands,
		channel=channel,
	)
	return {"channel": channel}


@frappe.whitelist()
def uninstall_app(app: str, site: str):
	_require_admin()
	_validate_app_name(app)
	_validate_site_name(site)
	channel = _new_channel("uninstall")
	frappe.enqueue(
		run_bench_command,
		queue="long",
		command=["uninstall-app", app, "--yes"],
		channel=channel,
		site=site,
	)
	return {"channel": channel}


@frappe.whitelist()
def new_site(site: str, admin_password: str, install_app_name: str | None = None):
	"""
	Create a new site. If install_app_name is given, the app is installed
	as part of the same command (this is what lets the frontend hide the
	concept of 'sites' entirely for a first-time user — clicking 'Install
	ERPNext' calls this with install_app_name='erpnext' and a generated
	site name, no separate 'create a site' step shown to them).
	"""
	_require_admin()
	_validate_site_name(site)
	_validate_password(admin_password)
	if install_app_name:
		_validate_app_name(install_app_name)
	channel = _new_channel("new_site")
	command = ["new-site", site, "--admin-password", admin_password]
	if install_app_name:
		command += ["--install-app", install_app_name]

	frappe.enqueue(
		run_bench_command,
		queue="long",
		command=command,
		channel=channel,
	)
	return {"channel": channel}


@frappe.whitelist()
def backup_site(site: str, with_files: bool = True):
	_require_admin()
	_validate_site_name(site)
	channel = _new_channel("backup")
	command = ["backup"]
	if with_files:
		command.append("--with-files")

	frappe.enqueue(
		run_bench_command,
		queue="long",
		command=command,
		channel=channel,
		site=site,
	)
	return {"channel": channel}


def _validate_backup_path(site: str, backup_path: str):
	"""Restrict restores to files that actually live in this site's own
	backup directory, instead of accepting any path on disk."""
	backups_dir = os.path.realpath(os.path.join(get_bench_path(), "sites", site, "private", "backups"))
	resolved = os.path.realpath(backup_path)
	if not resolved.startswith(backups_dir + os.sep):
		frappe.throw(_("Backup file must be inside this site's own backups folder."))
	if not os.path.isfile(resolved):
		frappe.throw(_("Backup file not found."))


@frappe.whitelist()
def restore_backup(site: str, backup_path: str, admin_password: str | None = None):
	_require_admin()
	_validate_site_name(site)
	_validate_backup_path(site, backup_path)
	channel = _new_channel("restore")
	command = ["restore", backup_path]
	if admin_password:
		_validate_password(admin_password)
		command += ["--admin-password", admin_password]

	frappe.enqueue(
		run_bench_command,
		queue="long",
		command=command,
		channel=channel,
		site=site,
	)
	return {"channel": channel}


@frappe.whitelist()
def migrate_site(site: str):
	_require_admin()
	_validate_site_name(site)
	channel = _new_channel("migrate")
	frappe.enqueue(
		run_bench_command,
		queue="long",
		command=["migrate"],
		channel=channel,
		site=site,
	)
	return {"channel": channel}


@frappe.whitelist()
def drop_site(site: str):
	"""Drops a site. bench takes its own backup automatically before dropping."""
	_require_admin()
	_validate_site_name(site)
	channel = _new_channel("drop_site")
	frappe.enqueue(
		run_bench_command,
		queue="long",
		command=["drop-site", site, "--force"],
		channel=channel,
	)
	return {"channel": channel}


def _run_multiple(commands: list[list[str]], channel: str):
	"""Run several bench commands in sequence on the same channel — used
	when a single user action maps to more than one bench command (e.g.
	get-app then install-app)."""
	for command in commands:
		run_bench_command(command=command, channel=channel)

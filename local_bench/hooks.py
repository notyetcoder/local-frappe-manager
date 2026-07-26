from . import __version__ as app_version

app_name = "local_bench"
app_title = "Local Bench"
app_publisher = "local-bench contributors"
app_description = "A local, browser-based dashboard for managing a Frappe bench — install/uninstall apps, manage sites, backup and restore, without touching the command line."
app_email = "hello@example.com"
app_license = "MIT"

# The dashboard lives at /local-bench, served automatically by Frappe
# from www/local-bench.html (built by `npm run build` in frontend/, via
# frappe-ui's vite plugin). No manual route wiring needed.

# Everything in this app talks to the frontend over Socketio for live
# command output, so make sure realtime is enabled (it is by default in
# Frappe, this is just documenting the dependency).

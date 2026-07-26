from setuptools import find_packages, setup

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in local_bench/__init__.py
from local_bench import __version__ as version

setup(
	name="local_bench",
	version=version,
	description="A local, browser-based dashboard for managing a Frappe bench.",
	author="local-bench contributors",
	author_email="hello@example.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires,
)

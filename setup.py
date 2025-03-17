from setuptools import setup, find_packages

setup(
  name="Eddie42",
  version="0.1.0",
  description="Get Piscine & Student progress data",
  author="Zedr0",
  package_dir={"": "app"},
  packages=find_packages(include=["app.*"]),
  include_package_data=True,
  scripts=[
    "scripts/build.sh",
    "scripts/run.sh",
  ],
  install_requires=[
    "setuptools",
    "slack_bolt",
    "requests",
    "requests-cache",
    # "colorama",
  ],
  extras_require={
    "dev": ["debugpy", "ruff"],
  },
)

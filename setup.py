# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

def get_version():
    return "2.0.1"

def get_requirements():
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_file):
        with open(req_file) as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return ["frappe>=15.0.0", "erpnext>=15.0.0"]

setup(
    name="portugal_compliance",
    version=get_version(),
    description="Portugal Compliance for ERPNext",
    long_description="Portuguese Fiscal Compliance App (SAF-T, ATCUD, QR Code, Signature)",
    long_description_content_type="text/markdown",
    author="NovaDX - Octávio Daio",
    author_email="app@novadx.pt",
    url="https://github.com/sun2dayo/portugal-compliance",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=get_requirements(),
    python_requires=">=3.10",
    license="GPL-3.0-or-later",
    classifiers=[
        "Framework :: Frappe",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
    ],
)

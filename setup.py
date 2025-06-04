# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

def get_version():
    return "0.0.1"

def get_requirements():
    try:
        with open("requirements.txt") as f:
            return f.read().strip().split("\n")
    except:
        return ["frappe>=15.0.0", "erpnext>=15.0.0"]

setup(
    name="portugal_compliance",
    version=get_version(),
    description="Portugal Compliance for ERPNext",
    author="NovaDX - Octávio Daio",
    author_email="app@novadx.pt",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=get_requirements(),
    python_requires=">=3.8"
)

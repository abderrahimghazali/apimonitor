from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="apimonitor",
    version="1.0.0",
    author="AbderrahimGHAZALI",
    author_email="ghazali.abderrahim1@gmail.com",
    description="A fast and flexible API health monitoring tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abderrahimghazali/apimonitor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "pydantic>=2.0.0",
        "click>=8.0.0",
        "pyyaml>=6.0",
        "aiofiles>=22.0.0",
        "colorama>=0.4.6",
        "tabulate>=0.9.0",
        "jinja2>=3.0.0",
    ],
    extras_require={
        "notifications": [
            "aiosmtplib>=2.0.0",
            "slack-sdk>=3.19.0",
        ],
        "dashboard": [
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=5.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "apimonitor=apimonitor.cli:main",
        ],
    },
)
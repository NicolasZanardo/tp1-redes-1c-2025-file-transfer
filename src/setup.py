from setuptools import setup, find_packages

setup(
    name='tp1-redes-1c-2025',
    version='1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'start-server = src.start_server:main',  # Entry point for the server
            'upload = src.upload:main',              # Entry point for upload
            'download = src.download:main',          # Entry point for download
        ],
    },
)
from setuptools import setup, find_packages

setup(
    name="kirka-py",
    version="0.1.0",
    author="Glitchy",
    author_email="glitchytheglitchking@proton.me",
    description="Bot API for kirka.io",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/i-am-called-glitchy/kirka-py",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.13",
    install_requires=[
        "aiohttp",
        "websockets",
        "asyncio",
        "expiringdict",
        "websockets"
    ],
)
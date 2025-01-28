from setuptools import setup, find_packages

setup(
    name="kirka-py",  # Must be unique on PyPI
    version="0.1.0",
    author="Glitchy",
    author_email="glitchytheglitchking@proton.me",
    description="Bot API for kirka.io",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/your-repo",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.13",
    install_requires=[
        # List your dependencies here
    ],
)
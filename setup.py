from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gnce",
    version="0.7.3",
    author="Valentine Nsukuzonke",
    description="Governance Native Compliance Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/valentinensukuzonke-source/gnce-framework",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8+",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0",
        "typing-extensions>=4.0.0",
        "python-dateutil>=2.8.0",
    ],
)

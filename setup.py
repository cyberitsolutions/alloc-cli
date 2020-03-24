import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="alloccli",
    version="1.8.9",
    author="Alex Lance",
    author_email="code@alexlance.com",
    maintainer="Christopher Bayliss",
    maintainer_email="cjb@cyber.com.au",
    description="A CLI tool to interact with allocPSA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cyberitsolutions/alloc-cli",
    packages=setuptools.find_packages(),
    scripts=["alloc", "tools/add_interested_party", "tools/del_interested_party"],
    data_files=[("/usr/share/bash-completion/completions", ["tools/alloc"])],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: AGPL License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)

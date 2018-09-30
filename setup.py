import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setuptools.setup(
    name="graph-runner",
    version='0.0.5',
    author="Troy Larson",
    author_email="troylar@gmail.com",
    description="Run your graphs in code",
    long_description=long_description,
    install_requires=["gremlinpython"],
    long_description_content_type="text/markdown",
    url="https://github.com/troylar/graph-runner",
    packages=["graph_runner", "graph_entity"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)

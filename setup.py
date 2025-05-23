from setuptools import setup, find_packages

setup(
    name="aima-codegen",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "typer",
        "rich",
        "openai",
        "anthropic",
        "google-generativeai",
        "tiktoken",
        "keyring",
        "pydantic",
        "psutil",
        "packaging",
    ],
    entry_points={
        "console_scripts": [
            "aima-codegen=aima_codegen.main:app",
        ],
    },
    python_requires=">=3.10",
) 
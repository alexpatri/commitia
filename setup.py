from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="commitia",
    version="0.1.0",
    author="Alexsandro Júnior",
    author_email="jalexsandro2005@gmail.com",
    description="Ferramenta CLI para gerar mensagens de commit automáticas usando IA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alexpatri/commitia",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.0",
        "GitPython>=3.1.40",
        "crewai>=0.28.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "commitia=commitia:cli",
        ],
    },
)

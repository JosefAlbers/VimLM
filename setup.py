from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = [l.strip() for l in f.readlines()]

setup(
    name="vimlm",
    version="0.0.9",
    author="Josef Albers",
    author_email="albersj66@gmail.com",
    readme='README.md',
    description="VimLM - LLM-powered Vim assistant",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/JosefAlbers/vimlm",
    # packages=find_packages(),
    py_modules=['vimlm'],
    python_requires=">=3.12.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vimlm=vimlm:run",
        ],
    },
)


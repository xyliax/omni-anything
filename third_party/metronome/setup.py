"""Self-contained setup so packaging works on older setuptools too (the system here
is 59.6, which predates PEP 621 [project] metadata). Modern setuptools (>=64) also
reads the equivalent metadata from pyproject.toml."""
from setuptools import setup, find_packages

setup(
    name="metronome-serve",
    version="0.1.0",
    description="Frame-budget scheduling and KV-budget admission control for real-time "
                "serving of interaction models.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.9",
    license="Apache-2.0",
    packages=["metronome", "metronome.backends", "sim", "bench"],
    install_requires=["numpy>=1.23"],
    extras_require={
        "bench": ["scipy>=1.9", "matplotlib>=3.6", "pandas>=1.5"],
        "engine": ["torch>=2.2", "flash-attn>=2.5"],
        "vllm": ["vllm>=0.6"],
        "realtime": ["websockets>=11"],
        "dev": ["pytest>=7", "pytest-asyncio>=0.21"],
    },
    entry_points={"console_scripts": [
        "metronome-realtime = metronome.realtime:main",
    ]},
    keywords=["llm-serving", "real-time", "scheduling", "admission-control", "kv-cache", "vllm"],
)

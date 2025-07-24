from setuptools import setup, find_packages

setup(
    name="booking-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langgraph>=0.3.27",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "slowapi>=0.1.9",
        "httpx>=0.25.0",
        "python-dotenv>=1.0.0",
        "structlog>=23.2.0",
        "pytz>=2025.1",
        "aiohttp>=3.12.0",
    ],
)
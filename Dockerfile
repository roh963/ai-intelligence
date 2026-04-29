FROM python:3.11-slim

RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libboost-python-dev \
    libboost-thread-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /home/user/app

COPY requirements.txt .

RUN uv pip install --system --no-cache -r requirements.txt

COPY --chown=user . .

EXPOSE 7860

USER user

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
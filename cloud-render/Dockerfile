FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    BLENDER_VERSION=4.2.3 \
    RENDER_ROOT=/data \
    RENDER_DEVICE=auto

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip ffmpeg curl ca-certificates xz-utils \
      libxi6 libxrender1 libxkbcommon0 libsm6 libgl1 libxxf86vm1 \
      libxfixes3 libxinerama1 libxcursor1 libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL \
      "https://download.blender.org/release/Blender4.2/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
      -o /tmp/blender.tar.xz \
    && tar -xJf /tmp/blender.tar.xz -C /opt \
    && ln -s "/opt/blender-${BLENDER_VERSION}-linux-x64/blender" /usr/local/bin/blender \
    && rm /tmp/blender.tar.xz

WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY app.py render.py ./

RUN useradd -m -u 1000 render && mkdir -p /data && chown -R render:render /data /app
USER render
ENV HOME=/home/render

EXPOSE 8000
CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

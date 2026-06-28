FROM python:3.11-slim-bookworm
# Debian 패키지의 chromium + chromium-driver 는 버전이 항상 매칭되어 안정적
# apt 가 deb.debian.org(Fastly CDN) 에서 특정 .deb 를 400 Bad Request 로 받는 현상 회피:
#   파이프라이닝 비활성(요청 1건씩)·캐시 무효화·재시도 → 빌드 안정화
RUN printf 'Acquire::Retries "8";\nAcquire::http::Pipeline-Depth "0";\nAcquire::http::No-Cache "true";\n' > /etc/apt/apt.conf.d/99fix-acquire \
    && apt-get update && apt-get install -y --no-install-recommends \
        chromium chromium-driver fonts-nanum ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER=/usr/bin/chromedriver
WORKDIR /app
COPY bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot/ /app/
EXPOSE 9099
CMD ["python", "bot.py"]

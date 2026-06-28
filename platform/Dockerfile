FROM python:3.11-slim
WORKDIR /app
COPY platform/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY platform/ /app/
ENV USERS_PATH=/data/users.json
EXPOSE 9000
CMD ["gunicorn", "-b", "0.0.0.0:9000", "-w", "2", "app:app"]

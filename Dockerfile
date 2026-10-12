FROM python:3.12-alpine

WORKDIR /app

COPY . /app

RUN chmod -R 755 /app

ENV PORT=8087
EXPOSE 8087

CMD ["python", "server.py"]

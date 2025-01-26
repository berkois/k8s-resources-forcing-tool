FROM python:3.9-slim

ENV PYTHONPATH="${PYTHONPATH}:."

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY . /app/

WORKDIR /app

CMD ["python", "/app/k8s-resource-controller.py"]

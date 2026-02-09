#setbase image, new build stage, use this python image(slim), built on d-linix
FROM python:3.13-slim
#save space and time by not writing bytecode and unbuffered output, + logs appear asap 
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
#install system level packs, exec commands during image build, update packs, install packs
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*
#copy depndencies file into continer 
COPY requirements.txt .

#dont save pip cache to save space, install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

#for the shared db
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

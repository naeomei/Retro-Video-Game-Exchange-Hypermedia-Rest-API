# Email Service - Retro Video Game Exchange API

## Overview

This is a separate microservice that handles email notifications for the Retro Video Game Exchange API. It consumes events from Kafka and sends emails asynchronously, preventing the API from being blocked by slow email operations.

## Architecture

```
API → Kafka → Email Service → SMTP Server → User Inbox
```

## Features

- **Asynchronous Processing**: Doesn't block the API
- **Event-Driven**: Consumes Kafka messages
- **Multiple Event Types**:
  - Password changed
  - Trade offer created
  - Trade offer accepted
  - Trade offer rejected

## Setup

### 1. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your SMTP settings:

**For Development (Mailtrap):**
```env
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=your-mailtrap-username
SMTP_PASS=your-mailtrap-password
```

**For Production (Gmail):**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

### 2. Build Docker Image

```bash
docker build -t retro-games-email-service .
```

### 3. Run with Docker Compose

The service is designed to run with docker-compose. See the main `docker-compose.yml` for the full setup.

## Running Locally (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export SMTP_HOST=sandbox.smtp.mailtrap.io
export SMTP_PORT=2525
export SMTP_USER=your-username
export SMTP_PASS=your-password

# Run the service
python main.py
```

## Testing

1. Start the system with docker-compose
2. Make API calls that trigger events (change password, create trade offer)
3. Check logs: `docker logs -f retro-games-email-service`
4. Check email inbox (Mailtrap or real email)

## Event Format

All events follow this format:

```json
{
  "event_type": "event_name",
  "timestamp": "2025-02-09T15:30:00Z",
  "data": {
    // Event-specific fields
  }
}
```

## Troubleshooting

**Service not consuming messages:**
- Check Kafka is running: `docker ps | grep kafka`
- Check Kafka topic exists: `docker exec kafka-kafka kafka-topics.sh --list --bootstrap-server localhost:9092`

**Emails not sending:**
- Check SMTP credentials in `.env`
- Check SMTP server is accessible
- Review logs: `docker logs retro-games-email-service`

**Container restarting:**
- Check health: `docker inspect retro-games-email-service | grep Health`
- Review logs for errors

## Security Notes

- Never commit `.env` file with real credentials
- Use app-specific passwords for SMTP
- Use TLS for production SMTP connections
- Rotate credentials regularly

## License

Educational use - Distributed Systems Lab 3

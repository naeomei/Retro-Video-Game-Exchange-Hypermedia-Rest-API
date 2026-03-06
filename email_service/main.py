"""
Email Service 

This service consumes notification events from Kafka and sends emails to users.
It runs as a separate process to avoid blocking the API with slow email operations.

Events handled:
- password_changed
- trade_offer_created
- trade_offer_accepted
- trade_offer_rejected
"""

import os
import json
import smtplib
import logging
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv
from prometheus_client import Counter, start_http_server

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
MESSAGES_CONSUMED = Counter('email_service_messages_consumed_total', 'Total Kafka messages consumed', ['event_type'])
EMAILS_SENT = Counter('email_service_emails_sent_total', 'Total emails successfully sent')
ERRORS = Counter('email_service_errors_total', 'Total errors encountered', ['error_type'])


class EmailService:
    """
    Email service that consumes Kafka events and sends notification emails.
    """

    def __init__(self):
        """Initialize email service with Kafka consumer and SMTP configuration."""
        # SMTP Configuration
        self.smtp_host = os.getenv('SMTP_HOST', 'sandbox.smtp.mailtrap.io')
        self.smtp_port = int(os.getenv('SMTP_PORT', '2525'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_pass = os.getenv('SMTP_PASS')
        self.email_from = os.getenv('EMAIL_FROM', 'noreply@retrogames.com')

        # Kafka consumer configuration
        self.consumer_conf = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            'group.id': 'email-service-group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True
        }

        self.consumer = Consumer(self.consumer_conf)
        self.consumer.subscribe(['notifications'])

        logger.info("Email service initialized")
        logger.info(f"SMTP: {self.smtp_host}:{self.smtp_port}")
        logger.info(f"Kafka: {self.consumer_conf['bootstrap.servers']}")

    def send_email(self, to: str, subject: str, body: str, is_html: bool = False) -> bool:
        """
        Send an email via SMTP.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether body is HTML (default: False)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_from
            msg['To'] = to
            msg['Subject'] = subject

            # Attach body
            mime_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, mime_type))

            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.smtp_port == 587:  # TLS
                    server.starttls()

                if self.smtp_user and self.smtp_pass:
                    server.login(self.smtp_user, self.smtp_pass)

                server.send_message(msg)

            logger.info(f'Email sent to {to}: {subject}')
            EMAILS_SENT.inc()
            return True

        except Exception as e:
            logger.error(f'Failed to send email to {to}: {e}', exc_info=True)
            ERRORS.labels(error_type='smtp').inc()
            return False

    def handle_password_changed(self, data: dict):
        """Handle password changed event - notify user their password was changed."""
        subject = "Your Password Was Changed"
        body = f"""Hi {data['user_name']},

Your password for Retro Video Game Exchange was recently changed.

If you made this change, you can safely ignore this email.

If you did NOT make this change, please contact support immediately.

---
Retro Video Game Exchange Team
""".strip()

        self.send_email(data['user_email'], subject, body)

    def handle_trade_offer_created(self, data: dict):
        """Handle trade offer created event - notify both offeror and offeree."""
        # Email to offeror
        offeror_subject = "Your Trade Offer Has Been Created"
        offeror_body = f"""Hi {data['offeror_name']},

Your trade offer has been created successfully!

You offered: {data['offered_game_name']}
You requested: {data['requested_game_name']}
From: {data['offeree_name']}

{f"Message: {data['message']}" if data.get('message') else ""}

We'll notify you when {data['offeree_name']} responds.

---
Retro Video Game Exchange Team
""".strip()
        self.send_email(data['offeror_email'], offeror_subject, offeror_body)

        # Email to offeree
        offeree_subject = "You Received a Trade Offer!"
        offeree_body = f"""Hi {data['offeree_name']},

Good news! You received a trade offer from {data['offeror_name']}!

They're offering: {data['offered_game_name']}
They want: {data['requested_game_name']}

{f"Message: {data['message']}" if data.get('message') else ""}

Log in to accept or reject this offer.

---
Retro Video Game Exchange Team
""".strip()
        self.send_email(data['offeree_email'], offeree_subject, offeree_body)

    def handle_trade_offer_accepted(self, data: dict):
        """Handle trade offer accepted event - notify both parties."""
        # Email to offeror
        offeror_subject = "Your Trade Offer Was Accepted!"
        offeror_body = f"""Hi {data['offeror_name']},

Great news! {data['offeree_name']} accepted your trade offer!

Trade details:
- You give: {data['offered_game_name']}
- You receive: {data['requested_game_name']}

Please coordinate with {data['offeree_name']} to exchange the games.

---
Retro Video Game Exchange Team
""".strip()
        self.send_email(data['offeror_email'], offeror_subject, offeror_body)

        # Email to offeree
        offeree_subject = "Trade Offer Accepted!"
        offeree_body = f"""Hi {data['offeree_name']},

You accepted the trade offer from {data['offeror_name']}!

Trade details:
- You give: {data['requested_game_name']}
- You receive: {data['offered_game_name']}

Please coordinate with {data['offeror_name']} to exchange the games.

---
Retro Video Game Exchange Team
""".strip()
        self.send_email(data['offeree_email'], offeree_subject, offeree_body)

    def handle_trade_offer_rejected(self, data: dict):
        """Handle trade offer rejected event - notify both parties."""
        # Email to offeror
        offeror_subject = "Your Trade Offer Was Declined"
        offeror_body = f"""Hi {data['offeror_name']},

{data['offeree_name']} declined your trade offer.

Don't worry, there are plenty of other games to trade!

---
Retro Video Game Exchange Team
""".strip()
        self.send_email(data['offeror_email'], offeror_subject, offeror_body)

        # Email to offeree
        offeree_subject = "Trade Offer Declined"
        offeree_body = f"""Hi {data['offeree_name']},

You declined the trade offer from {data['offeror_name']}.

If you change your mind, you can always send a new offer!

---
Retro Video Game Exchange Team
""".strip()
        self.send_email(data['offeree_email'], offeree_subject, offeree_body)

    def process_message(self, message):
        """
        Process a single Kafka message.

        Args:
            message: Kafka message object
        """
        try:
            # Parse JSON
            event = json.loads(message.value().decode('utf-8'))

            event_type = event.get('event_type')
            data = event.get('data', {})

            logger.info(f'Processing event: {event_type}')
            MESSAGES_CONSUMED.labels(event_type=event_type or 'unknown').inc()

            # Route to appropriate handler
            handlers = {
                'password_changed': self.handle_password_changed,
                'trade_offer_created': self.handle_trade_offer_created,
                'trade_offer_accepted': self.handle_trade_offer_accepted,
                'trade_offer_rejected': self.handle_trade_offer_rejected,
            }

            handler = handlers.get(event_type)
            if handler:
                handler(data)
                logger.info(f'Successfully processed {event_type}')
            else:
                logger.warning(f'Unknown event type: {event_type}')

        except Exception as e:
            logger.error(f'Error processing message: {e}', exc_info=True)
            ERRORS.labels(error_type='processing').inc()

    def run(self):
        """
        Main loop: consume messages from Kafka and send emails.
        """
        logger.info('Email service started, waiting for messages...')

        try:
            while True:
                # Poll for messages (1 second timeout)
                messages = self.consumer.consume(num_messages=1, timeout=1.0)

                if not messages:
                    continue

                for message in messages:
                    if message is None:
                        continue

                    if message.error():
                        if message.error().code() == KafkaError._PARTITION_EOF:
                            continue
                        else:
                            logger.error(f'Kafka error: {message.error()}')
                            continue

                    # Process valid message
                    self.process_message(message)

        except KeyboardInterrupt:
            logger.info('Shutting down email service...')
        finally:
            self.consumer.close()
            logger.info('Email service stopped')


if __name__ == '__main__':
    start_http_server(8001)
    logger.info("Prometheus metrics server started on port 8001")
    service = EmailService()
    service.run()

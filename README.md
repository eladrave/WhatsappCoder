# WhatsApp-AutoCoder Integration

A WhatsApp interface for AutoCoder that allows users to interact with the AI coding assistant through WhatsApp messages using Twilio, LangChain, and the AutoCoder MCP (Model Context Protocol) server.

## Features

- 🤖 **Natural Language Processing**: Interact with AutoCoder using natural language via WhatsApp
- 🔧 **MCP Tool Integration**: Access all AutoCoder tools through WhatsApp commands
- 💬 **Conversation Management**: Maintains conversation context and history with Redis
- 🔒 **Secure Authentication**: Phone number whitelist and Twilio signature verification
- 📊 **Real-time Status Updates**: Check project and task execution status
- 📁 **File Management**: Get links to generated code files
- 🎯 **Command System**: Quick commands for common operations

## Architecture Overview

```
WhatsApp User → Twilio → FastAPI → LangChain → AutoCoder MCP → AutoCoder API
                                       ↓
                                    Redis (State)
```

## Quick Start

### Prerequisites

- Python 3.11+
- Redis server
- Twilio account with WhatsApp sandbox
- AutoCoder running locally or accessible

### Installation

1. Clone the repository:
```bash
git clone https://github.com/eladrave/WhatsappCoder.git
cd WhatsappCoder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Configure environment variables in `.env`:
```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token  
TWILIO_PHONE_NUMBER=whatsapp:+14155238886

# Security - comma-separated list of allowed phone numbers
ALLOWED_PHONE_NUMBERS=+1234567890,+0987654321

# AutoCoder Integration
AUTOCODER_API_URL=http://localhost:5000/api
AUTOCODER_MCP_URL=http://localhost:5000

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Application Settings
LOG_LEVEL=INFO
SESSION_TTL_HOURS=24
MAX_MESSAGE_LENGTH=1600
```

5. Start Redis:
```bash
docker run -d -p 6379:6379 redis:alpine
```

6. Start AutoCoder (in a separate terminal):
```bash
cd /path/to/AutoCoder
python enhanced_main.py web --port 5000
```

7. Run the application:
```bash
uvicorn app.main:app --reload --port 8000
```

### Twilio Setup

1. Log into your Twilio Console
2. Navigate to WhatsApp Sandbox
3. Configure the webhook URL:
   - **When a message comes in**: `https://your-domain.com/webhook/whatsapp`
   - **Status callback URL**: `https://your-domain.com/webhook/status`

For local development, use ngrok:
```bash
ngrok http 8000
# Use the ngrok URL in Twilio webhook configuration
```

## Usage

### WhatsApp Commands

Send these commands to your Twilio WhatsApp number:

- `/help` - Show available commands
- `/new [project_name]` - Create a new project
- `/list` - List all your projects
- `/status` - Check current task status
- `/files` - Get generated files
- `/clear` - Clear conversation history

### Natural Language Examples

You can also use natural language:

- "Create a Python REST API with user authentication"
- "Build a React dashboard with charts"
- "Generate unit tests for my code"
- "Add a database schema for e-commerce"

## Development

### Project Structure

```
WhatsappCoder/
├── app/
│   ├── api/           # FastAPI routes
│   ├── auth/          # Authentication logic
│   ├── mcp/           # MCP client integration
│   ├── models/        # Pydantic models
│   ├── services/      # Business logic
│   ├── state/         # State management
│   ├── utils/         # Utilities
│   └── main.py        # FastAPI application
├── tests/             # Test suite
├── docker/            # Docker configuration
├── docs/              # Documentation
└── .github/workflows/ # CI/CD pipelines
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_message_processor.py
```

### Docker Deployment

Build and run with Docker:

```bash
# Build image
docker build -t whatsapp-coder .

# Run with docker-compose
docker-compose up -d
```

### Development Mode

For development with hot reload:

```bash
docker-compose -f docker-compose.dev.yml up
```

## API Documentation

Once running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Security Considerations

1. **Phone Whitelist**: Only authorized phone numbers can use the service
2. **Twilio Signature**: All webhooks are verified with Twilio signatures
3. **Rate Limiting**: Prevents abuse (10 requests/minute per phone)
4. **Session Expiry**: Conversations expire after 24 hours
5. **No Message Logging**: Production mode doesn't log message content

## Monitoring

The application provides structured JSON logging with:
- Request IDs for tracing
- Performance metrics
- Error tracking
- User activity monitoring

## Troubleshooting

### Common Issues

1. **"Invalid signature" error**:
   - Verify TWILIO_AUTH_TOKEN is correct
   - Ensure webhook URL matches exactly (including https://)

2. **"Unauthorized phone number"**:
   - Add phone number to ALLOWED_PHONE_NUMBERS
   - Format: +countrycode+number (e.g., +1234567890)

3. **Redis connection error**:
   - Ensure Redis is running
   - Check REDIS_URL in .env

4. **AutoCoder connection error**:
   - Verify AutoCoder is running
   - Check AUTOCODER_API_URL and AUTOCODER_MCP_URL

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/eladrave/WhatsappCoder/issues
- Documentation: See `/docs` directory

## Acknowledgments

- AutoCoder team for the MCP server
- Twilio for WhatsApp Business API
- LangChain for the agent framework

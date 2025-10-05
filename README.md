# Delta Menu Assistant

An intelligent chat agent for Delta Airlines flight menu information, powered by OpenAI Agents SDK and Kimi AI. Query flight menus, check preselect availability, and get detailed meal information across all cabin classes.

## Features

- **Flight Menu Queries**: Get detailed menu information by flight number, date, and airports
- **Cabin Class Filtering**: Query menus for specific cabin classes (Delta One, Premium Select, Comfort+, Main Cabin)
- **Flight Lookup**: Find available flights by route and date using Oracle database integration
- **Menu Availability**: Check preselect windows and eligibility for menu preselection
- **Session Management**: Maintains conversation context using SQLite-based session storage
- **Streaming Responses**: Real-time streaming of agent responses for better UX
- **OAuth Authentication**: Secure API access with automatic token management
- **Gradio Interface**: Modern web interface with streaming support and conversation history

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   - `KIMI_API_KEY`: Your Kimi AI API key (required)
   - `ORACLE_USERNAME`, `ORACLE_PASSWORD`: Oracle DB credentials (optional, for flight lookup)
   - Other API configuration (see Configuration section)

3. **Run the application**:
   ```bash
   uv run python -m src.frontend.gradio_app
   ```
   
   Access at `http://localhost:7860`

## Usage Examples

### Web Interface

**Natural language queries**:
- "What's served in delta one class on DL30 from ATL today?"
- "I'm flying from Atlanta to London next Wednesday, what's the menu on delta one class?"
- "I'm flying from Atlanta to Tokyo today, what Japanese menu is served on this flight for delta one?"
- "Why am I not able to preselect my menu for my flight departing on October 10th from Atlanta to London?"
- "Show me the menu for flight 30 from ATL to LHR on 2025-09-13"

### Programmatic Usage

```python
import asyncio
from src.agents.menu_agent import MenuAgent

async def main():
    agent = MenuAgent()
    
    # Single query with session management
    result = await agent.process_message(
        "What's served in delta one on DL30 from ATL on 2025-08-13?",
        session_id="user_123"
    )
    print(result["response"])
    print(f"Tokens used: {result['usage']['total_tokens']}")
    
    # Streaming response
    async for partial in agent.process_message_stream(
        "Show me the menu",
        session_id="user_123"
    ):
        print(partial, end="\r")
    
    # Clear session when done
    await agent.clear_session("user_123")
    await agent.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Project Structure

```
src/
├── agents/           # OpenAI Agents SDK integration
│   └── menu_agent.py # Main agent with session management
├── client/           # Delta API clients
│   ├── delta_client.py    # Menu API client
│   └── oauth_manager.py   # OAuth token management
├── config/           # Configuration
│   └── streaming_config.py
├── data/             # Static data
│   └── ssr_codes.py  # SSR code descriptions
├── database/         # Database layer
│   ├── connection_pool.py  # Oracle connection pooling
│   └── flight_repository.py # Flight lookup queries
├── frontend/         # Web interface
│   └── gradio_app.py # Gradio chat interface
├── models/           # Pydantic models
│   ├── menu.py       # Menu data models
│   ├── requests.py   # Request models
│   └── responses.py  # Response models
├── tools/            # Agent tools
│   ├── menu_tools.py # Menu query tools
│   └── debug_tools.py # Debugging tools
└── utils/            # Utilities
    ├── logging_config.py
    └── utils.py
```

## Agent Tools

### Menu Query Tools
- **get_flight_menu**: Get complete flight menu with optional cabin filtering
  - Supports flight number or route-based lookup
  - Filters by cabin codes (C, F, W, Y)
  - Returns detailed menu items with descriptions and dietary information
  
- **check_menu_availability**: Check menu preselect availability
  - Verifies preselect eligibility
  - Returns preselect window dates (open/close times)
  - Uses OAuth authentication
  
- **lookup_flights**: Find flights by route and date
  - Queries Oracle database for flight schedules
  - Returns available flight numbers with departure times
  - Supports route-based queries when flight number unknown

### Debug Tools (Available but not exposed to agent)
- **validate_api_health**: Check Delta API status
- **trace_api_call**: Detailed request/response tracing
- **diagnose_error**: Error analysis and recommendations

## Configuration

### Environment Variables

**Required:**
- `KIMI_API_KEY`: Your Kimi AI API key from https://platform.moonshot.cn
- `KIMI_BASE_URL`: Kimi API endpoint (default: https://api.moonshot.cn/v1)

**Delta API:**
- `DELTA_API_BASE_URL`: Delta menu API endpoint (default: https://ifsobs-api.delta.com/CatFltMenuSvcRst/v1)
- `CHANNEL_ID`: Channel identifier (default: DGMNPT)
- `DEFAULT_LANG`: Language preference (default: en-US)

**Oracle Database (Optional - for flight lookup):**
- `ORACLE_USERNAME`: Oracle database username
- `ORACLE_PASSWORD`: Oracle database password
- `ORACLE_CONNECTION_STRING`: JDBC connection string
- `ORACLE_PORT`: Database port (default: 1521)
- `ORACLE_SERVICE_NAME`: Service name (default: ORCL)

### Cabin Class Codes
- **C**: Delta One / Business Class
- **F**: Delta Premium Select / First Class
- **W**: Comfort+
- **Y**: Main Cabin / Economy

### API Parameters
- **departure_date**: YYYY-MM-DD format
- **flight_number**: Integer (e.g., 30 for DL30)
- **departure_airport**: 3-letter IATA code (e.g., ATL, LAX, JFK)
- **arrival_airport**: 3-letter IATA code (e.g., LHR, CDG, NRT)
- **operating_carrier**: 2-letter code (default: DL)
- **cabin_codes**: Comma-separated codes (e.g., "C,F" for Delta One and Premium Select)

## Testing

### Test Scripts
- `test_availability.py`: Test menu availability API
- `benchmark_tokens.py`: Benchmark token usage
- `benchmark_stream_tokens.py`: Benchmark streaming performance
- `usage_example.py`: Example usage patterns

### Manual Testing Checklist
- [ ] Flight menu query with flight number
- [ ] Route-based flight lookup (no flight number)
- [ ] Cabin-specific menu filtering
- [ ] Menu preselect availability check
- [ ] Session context persistence
- [ ] Streaming response functionality
- [ ] Invalid date handling (past/future)
- [ ] Missing parameter handling
- [ ] Database connection fallback
- [ ] OAuth token refresh

### Example Test Cases

1. **Complete Flight Query**:
   ```
   Input: "What's served in delta one on DL30 from ATL on 2025-09-13?"
   Expected: Delta One menu for DL30 with meal details
   ```

2. **Route-Based Lookup**:
   ```
   Input: "What's served from ATL to LHR on 2025-09-13?"
   Expected: List of available flights, then menu after selection
   ```

3. **Preselect Availability**:
   ```
   Input: "Why can't I preselect menu for DL30 on September 30th from ATL?"
   Expected: Preselect window dates and current status
   ```

4. **Context Awareness**:
   ```
   Input: "Show me the menu for DL30 from ATL tomorrow"
   Follow-up: "What about first class?"
   Expected: Agent remembers flight context and shows first class menu
   ```

## Troubleshooting

### Common Issues

1. **Kimi API Key Missing**:
   ```
   Error: KIMI_API_KEY not found in environment variables
   Solution: Add KIMI_API_KEY to .env file
   Get key from: https://platform.moonshot.cn
   ```

2. **Import Errors**:
   ```bash
   # Reinstall dependencies
   uv sync
   
   # Verify Python version
   python --version  # Should be ≥ 3.9
   ```

3. **Database Connection Errors**:
   ```
   Error: Database configuration error
   Solution: Flight lookup requires Oracle credentials in .env
   Note: Agent will still work for direct flight number queries
   ```

4. **API Timeouts**:
   - Check internet connection
   - Verify Delta API endpoint is accessible
   - Try again (API may be temporarily slow)

5. **OAuth Token Errors**:
   - OAuth tokens auto-refresh every 30 minutes
   - Check if availability API endpoint is accessible
   - Verify network allows HTTPS connections

### Debug Mode
Enable debug mode in Gradio interface to see:
- Detailed logging output
- API request/response details
- Tool execution traces
- Session management info
- Token usage statistics

### Logging
Logs are written to `gradio_app.log` with detailed information:
- Agent initialization
- Tool calls and responses
- API interactions
- Session management
- Error traces

## Development

### Adding New Tools

1. **Create tool function** in `src/tools/`:
   ```python
   from agents import function_tool
   
   @function_tool
   async def my_new_tool(param: str) -> dict:
       """Tool description for the agent"""
       # Implementation
       return {"result": "data"}
   ```

2. **Register tool** in `src/agents/menu_agent.py`:
   ```python
   self.agent = Agent(
       tools=[
           self.menu_tools.get_menu_by_flight_tool(),
           self.menu_tools.my_new_tool(),  # Add here
       ]
   )
   ```

3. **Update system instructions** if needed to guide tool usage

### Key Dependencies
- **openai-agents** (≥0.1.0): Agent framework and session management
- **gradio** (≥4.44.0): Web interface with streaming support
- **pydantic** (≥2.9.2): Data validation and modeling
- **httpx** (≥0.27.2): Async HTTP client
- **oracledb** (≥3.3.0): Oracle database connectivity
- **python-dotenv** (≥1.0.1): Environment configuration

### Architecture Notes

**Session Management:**
- Uses SQLite-based session storage (`menu_conversations.db`)
- Automatic context management by OpenAI Agents SDK
- Each user gets unique session ID for conversation history

**Streaming:**
- Real-time response streaming via Gradio
- Tool execution indicators during processing
- Efficient token usage with streaming

**Database Integration:**
- Oracle connection pooling for flight lookups
- Graceful fallback if database unavailable
- Async query execution

### Production Considerations

**Performance:**
- [ ] Add Redis caching for frequent queries
- [ ] Implement connection pooling for HTTP clients
- [ ] Add request rate limiting
- [ ] Optimize database queries with indexes

**Reliability:**
- [ ] Add retry logic with exponential backoff
- [ ] Implement circuit breakers for external APIs
- [ ] Add health check endpoints
- [ ] Set up monitoring and alerting

**Security:**
- [ ] Rotate OAuth tokens securely
- [ ] Encrypt database credentials
- [ ] Add input sanitization
- [ ] Implement API key rotation
- [ ] Add audit logging

**Scalability:**
- [ ] Deploy with load balancer
- [ ] Use distributed session storage
- [ ] Add horizontal scaling support
- [ ] Implement queue for long-running queries

**Features:**
- [ ] Multi-language support (i18n)
- [ ] Additional airline APIs
- [ ] User authentication
- [ ] Meal preference learning
- [ ] Email/SMS notifications for preselect windows
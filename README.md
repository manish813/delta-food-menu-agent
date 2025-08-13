# Delta Menu Assistant - POC

A chat agent for Delta Airlines flight menu information, built with OpenAI Agents SDK and Kimi AI.

## Features

- **Flight Menu Queries**: Get detailed menu information by flight number, date, and airport
- **Cabin Class Specific**: Query menus for First (F), Business (C), or Economy (Y) class
- **Menu Comparisons**: Compare offerings across different cabin classes
- **Debugging Tools**: Validate requests, check API health, and troubleshoot issues
- **Gradio Interface**: Easy-to-use web interface with debug mode

## Quick Start

1. **Install dependencies** (already done with uv):
   ```bash
   uv sync  # Installs all dependencies
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Kimi API key
   ```

3. **Run the application**:
   ```bash
   uv run python -m src.frontend.gradio_app
   ```

## Usage Examples

### Web Interface
Access at `http://localhost:7860`

**Example queries**:
- "What's served in business class on DL30 from ATL on 2025-08-13?"
- "Show me first class menu for DL30"
- "Compare business and first class meals"
- "Is the Delta menu API working?"

### Programmatic Usage

```python
import asyncio
from src.agents.menu_agent import MenuAgent

async def main():
    agent = MenuAgent()
    
    # Single query
    result = await agent.process_message(
        "What's served in business class on DL30 from ATL on 2025-08-13?"
    )
    print(result["response"])

if __name__ == "__main__":
    asyncio.run(main())
```

## Project Structure

```
src/
├── models/           # Pydantic models for data validation
├── client/           # Delta API client
├── agents/           # OpenAI Agents SDK integration
├── tools/            # Menu query and debugging tools
└── frontend/         # Gradio interface
```

## API Tools Available

### Menu Query Tools
- `get_menu_by_flight`: Complete menu for all cabin classes
- `get_cabin_menu`: Specific cabin class menu
- `compare_cabins`: Compare menus across multiple cabin classes

### Debug Tools
- `validate_api_health`: Check API accessibility
- `validate_flight_request`: Validate request parameters
- `trace_api_call`: Detailed request tracing
- `diagnose_error`: Error diagnosis and solutions

## Configuration

### Environment Variables
- `KIMI_API_KEY`: Your Kimi API key
- `KIMI_BASE_URL`: Kimi API endpoint (default: https://api.moonshot.cn/v1)
- `DELTA_API_BASE_URL`: Delta menu API endpoint

### API Parameters
- **departure_date**: Format YYYY-MM-DD
- **flight_number**: Integer (e.g., 30 for DL30)
- **departure_airport**: 3-letter code (e.g., ATL, LAX, JFK)
- **operating_carrier**: 2-letter code (e.g., DL, AA, UA)
- **cabin_code**: F (First), C (Business), Y (Economy)

## Testing

### Manual Testing Checklist
- [ ] Basic flight menu query
- [ ] Specific cabin class query
- [ ] Cabin comparison
- [ ] Invalid date format handling
- [ ] Invalid flight number handling
- [ ] API timeout handling
- [ ] Debug mode functionality

### Example Test Cases

1. **Valid Query**:
   ```
   Input: "What's served in business class on DL30 from ATL on 2025-08-13?"
   Expected: Business class menu details for DL30
   ```

2. **Invalid Date**:
   ```
   Input: "DL30 on 2025-08-10"
   Expected: Error message about past date
   ```

3. **API Health Check**:
   ```
   Input: "Is the Delta menu API working?"
   Expected: API status and response time
   ```

## Troubleshooting

### Common Issues

1. **Kimi API Key Missing**:
   - Set `KIMI_API_KEY` in `.env` file
   - Get key from Kimi dashboard

2. **Import Errors**:
   - Ensure uv environment is active: `uv sync`
   - Check Python version ≥ 3.9

3. **API Timeouts**:
   - Check internet connection
   - Try again later (API may be slow)

### Debug Mode
Enable debug mode in Gradio interface to see:
- Raw API responses
- Request parameters
- Tool usage details
- Error traces

## Development

### Adding New Features
1. Add new tools in `src/tools/`
2. Update agent configuration in `src/agents/menu_agent.py`
3. Add UI elements in `src/frontend/gradio_app.py`

### Extending for Production
- Add caching layer (Redis)
- Implement rate limiting
- Add monitoring and logging
- Multi-language support
- Additional airline APIs
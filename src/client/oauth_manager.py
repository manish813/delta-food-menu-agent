import httpx
import asyncio
import time
from typing import Optional, Dict
from dataclasses import dataclass
import os


@dataclass
class OAuthToken:
    """OAuth token with expiration tracking"""
    access_token: str
    token_type: str
    expires_in: int
    expires_at: float


class DeltaOAuthManager:
    """Manages OAuth tokens for Delta APIs"""
    
    TOKEN_URL = "https://ssaa.delta.com/as/token.oauth2"
    
    def __init__(self, 
                 client_id: Optional[str] = None, 
                 client_secret: Optional[str] = None):
        """
        Initialize OAuth manager with credentials
        
        Args:
            client_id: OAuth client ID (defaults to env var DELTA_CLIENT_ID)
            client_secret: OAuth client secret (defaults to env var DELTA_CLIENT_SECRET)
        """
        self.client_id = client_id or os.getenv("DELTA_CLIENT_ID", "CAT_CateringPreSelectSalesforce_CC")
        self.client_secret = client_secret or os.getenv("DELTA_CLIENT_SECRET", "rVaf29B8IyEnaDriYbDzS9hE3wYmnH2fphWBNq2DPqxzyGuZO4d7xtMP9SmsWA4m")
        
        self._token: Optional[OAuthToken] = None
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def get_access_token(self) -> str:
        """Get valid access token, refresh if needed"""
        if self._token and self._token.expires_at > time.time() + 60:  # 1 min buffer
            return self._token.access_token
        
        await self._refresh_token()
        return self._token.access_token
    
    async def _refresh_token(self) -> None:
        """Request new OAuth token from Delta API"""
        try:
            response = await self._client.post(
                self.TOKEN_URL,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'scope': 'read'
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self._token = OAuthToken(
                    access_token=data['access_token'],
                    token_type=data['token_type'],
                    expires_in=data['expires_in'],
                    expires_at=time.time() + data['expires_in']
                )
            else:
                raise Exception(f"OAuth token request failed: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise Exception("OAuth token request timed out")
        except Exception as e:
            raise Exception(f"Failed to get OAuth token: {str(e)}")
    
    async def close(self) -> None:
        """Close the HTTP client"""
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
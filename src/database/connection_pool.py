import os
import asyncio
import oracledb
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize thick mode
oracle_client_path = os.getenv("ORACLE_INSTANT_CLIENT_PATH")
print(f"Oracle client path from env: {oracle_client_path}")

if oracle_client_path and os.path.exists(oracle_client_path):
    # Add Oracle client to PATH so DLLs can be found
    if oracle_client_path not in os.environ.get('PATH', ''):
        os.environ['PATH'] = oracle_client_path + os.pathsep + os.environ.get('PATH', '')
        print(f"Added Oracle client to PATH: {oracle_client_path}")
    
    try:
        oracledb.init_oracle_client(lib_dir=oracle_client_path)
        print(f"Oracle thick client initialized successfully with path: {oracle_client_path}")
    except Exception as e:
        print(f"Failed to initialize Oracle thick client: {e}")
        raise
else:
    print(f"Oracle client path not found or not set: {oracle_client_path}")
    if oracle_client_path:
        print(f"Path exists check: {os.path.exists(oracle_client_path)}")
    raise RuntimeError(f"Oracle Instant Client path not found: {oracle_client_path}")

class OracleConnectionPool:
    def __init__(self):
        self._pool = None
    
    def initialize(self):
        if self._pool is None:
            dsn = oracledb.makedsn(
                "ora-obscfdctdb-01.mig-prd.aws.delta.com",
                1521,
                service_name="orap001"
            )
            
            self._pool = oracledb.create_pool(
                user=os.getenv("ORACLE_USERNAME"),
                password=os.getenv("ORACLE_PASSWORD"),
                dsn=dsn,
                min=2,
                max=10
            )
    
    @contextmanager
    def get_connection(self):
        if self._pool is None:
            self.initialize()
        
        connection = self._pool.acquire()
        try:
            yield connection
        finally:
            self._pool.release(connection)
    
    def close(self):
        if self._pool:
            self._pool.close()
            self._pool = None

_pool = OracleConnectionPool()

async def get_db_connection():
    return await asyncio.to_thread(lambda: _pool.get_connection())

async def initialize_db_pool():
    await asyncio.to_thread(_pool.initialize)

async def close_db_pool():
    await asyncio.to_thread(_pool.close)
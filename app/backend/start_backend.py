#!/usr/bin/env python3
"""
Backend startup script for VoiceRAG application
"""
import asyncio
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the application
from app import create_app
from aiohttp import web

async def start_server():
    """Start the backend server"""
    try:
        app = await create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', 8000)
        await site.start()
        
        print("🚀 Backend server started successfully on http://0.0.0.0:8000")
        print("✅ Ready to serve requests...")
        
        # Keep the server running
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            print("\n🛑 Shutting down backend server...")
            await runner.cleanup()
            
    except Exception as e:
        print(f"❌ Error starting backend server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(start_server())
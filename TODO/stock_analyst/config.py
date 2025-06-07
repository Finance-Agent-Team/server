"""Configuration and environment setup for AI Stock Analyst."""

import asyncio
import os
import sys
import warnings
from typing import Optional

import logfire

# Windows-specific asyncio subprocess cleanup
if sys.platform == "win32":
    warnings.filterwarnings("ignore", category=ResourceWarning, message=".*Event loop is closed.*")
    warnings.filterwarnings("ignore", category=ResourceWarning, message=".*I/O operation on closed pipe.*")
    
    # Set the appropriate event loop policy for Windows
    if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def setup_environment() -> None:
    """Set up environment variables and configuration."""
    # Set Claude API key
    os.environ['ANTHROPIC_API_KEY'] = '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'
    
    # Configure Logfire for observability
    logfire.configure(
        send_to_logfire='if-token-present',
        environment='development',
        service_name='ai-stock-analyst',
    )
    logfire.instrument_pydantic_ai()

def get_mcp_server_path() -> str:
    """Get the path to the MCP server."""
    return 'C:\\Users\\Chumm\\Desktop\\stock-analysis-mcp\\dist\\index.js'

def get_alpha_vantage_api_key() -> str:
    """Get the Alpha Vantage API key."""
    return 'L7SS5AKKMK8UDTFA'  # Replace with your new key

async def cleanup_tasks() -> None:
    """Clean up asyncio tasks and handle Windows subprocess cleanup."""
    try:
        # Get the current event loop
        loop = asyncio.get_running_loop()
        
        # Get pending tasks, excluding the current task
        current_task = asyncio.current_task(loop)
        tasks = [task for task in asyncio.all_tasks(loop) 
                if not task.done() and task is not current_task]
        
        # Cancel tasks in batches to avoid recursion issues
        if tasks:
            # Cancel all tasks first
            for task in tasks:
                if not task.cancelled() and not task.done():
                    task.cancel()
            
            # Wait a short time for cancellation to propagate
            await asyncio.sleep(0.05)
            
            # Gather results, suppressing cancellation exceptions
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                # Some tasks didn't cancel in time, that's OK
                pass
        
        # On Windows, ensure subprocess cleanup
        if sys.platform == "win32":
            # Give subprocess transports time to clean up
            await asyncio.sleep(0.1)
            
    except Exception:
        # Silently handle cleanup errors to avoid noise
        pass

def run_with_proper_cleanup(main_func):
    """Run the main function with proper Windows asyncio cleanup."""
    if sys.platform == "win32":
        # Use ProactorEventLoop on Windows for better subprocess support
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main_func())
    finally:
        try:
            # Proper cleanup sequence
            if not loop.is_closed():
                # Cancel any remaining tasks more safely
                pending_tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
                for task in pending_tasks:
                    if not task.cancelled():
                        task.cancel()
                
                # Wait briefly for cancellations to complete
                if pending_tasks:
                    try:
                        loop.run_until_complete(
                            asyncio.wait_for(
                                asyncio.gather(*pending_tasks, return_exceptions=True),
                                timeout=0.5
                            )
                        )
                    except (asyncio.TimeoutError, RuntimeError):
                        # Some tasks didn't cancel in time or loop issues, continue cleanup
                        pass
                
                # Shutdown async generators
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                except RuntimeError:
                    # Loop might already be closing
                    pass
                
                # Shutdown default executor
                if hasattr(loop, 'shutdown_default_executor'):
                    try:
                        loop.run_until_complete(loop.shutdown_default_executor())
                    except RuntimeError:
                        # Loop might already be closing
                        pass
                
                # Close the loop
                loop.close()
        except Exception:
            # Ignore cleanup errors on exit
            pass 
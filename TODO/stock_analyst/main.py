"""Main entry point for AI Stock Analyst application."""

from .config import setup_environment, run_with_proper_cleanup
from .cli import StockAnalystCLI


async def main():
    """Main application entry point with proper cleanup."""
    print("🎯 AI Stock Analyst - PydanticAI + Claude + Logfire")
    print("🚀 Real-time stock analysis with MCP tool verification")
    print("=" * 60)
    
    # Initialize the CLI
    cli = StockAnalystCLI()
    
    # Demo mode or interactive mode
    demo_mode = input("Run demo (d) or interactive mode (i)? [d/i]: ").strip().lower()
    
    try:
        if demo_mode == "d":
            await cli.demo_mode()
        else:
            # Interactive mode
            profile = cli.get_user_profile()
            await cli.interactive_session(profile)
    
    except KeyboardInterrupt:
        print("\n\n👋 Thank you for using AI Stock Analyst!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def run():
    """Entry point for the application."""
    setup_environment()
    run_with_proper_cleanup(main)


if __name__ == "__main__":
    run() 
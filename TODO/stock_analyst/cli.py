"""Interactive CLI interface for AI Stock Analyst."""

import asyncio
import logfire

from .models import UserProfile
from .agent import AIStockAnalyst
from .config import cleanup_tasks


class StockAnalystCLI:
    """Interactive command line interface for the AI Stock Analyst."""
    
    def __init__(self):
        self.analyst = AIStockAnalyst()
    
    async def interactive_session(self, profile: UserProfile):
        """Run an interactive analysis session."""
        print(f"\n👋 Welcome to AI Stock Analyst!")
        print("🚀 Ready to analyze stocks with smart tool selection")
        
        # Go directly to smart analysis
        await self.smart_analysis_session(profile)

    async def smart_analysis_session(self, profile: UserProfile):
        """Interactive smart analysis that auto-detects request type."""
        print("\n" + "="*60)
        print("🤖 AI Stock Analyst - Ask Any Question!")
        print("="*60)
        print("🎯 I'll automatically choose the best tool for your question:")
        print("📊 For detailed data → CSV export with full historical data")
        print("📝 For quick questions → Fast text summary")
        
        print("\n💡 Example questions you can ask:")
        print("   📈 'Get daily data for AAPL and save it to Excel'")
        print("   📊 'Show me Tesla's performance data for export'")
        print("   💬 'What's your opinion on Apple stock?'")
        print("   🤔 'Should I buy Microsoft?'")
        print("   📋 'Get me 5-minute intraday data for Google'")
        
        while True:
            print("\n" + "-"*50)
            
            # Simplified input - just ask for the question directly
            question = input("\n❓ Ask me anything about a stock (or 'quit' to exit):\n> ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
                
            if not question:
                print("💡 Please ask a question about a stock!")
                continue
            
            # Try to extract symbol from the question
            symbols = []
            common_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX']
            companies = {'apple': 'AAPL', 'google': 'GOOGL', 'microsoft': 'MSFT', 'tesla': 'TSLA', 
                        'amazon': 'AMZN', 'meta': 'META', 'nvidia': 'NVDA', 'netflix': 'NFLX'}
            
            question_upper = question.upper()
            for symbol in common_symbols:
                if symbol in question_upper:
                    symbols.append(symbol)
            
            for company, symbol in companies.items():
                if company.lower() in question.lower():
                    symbols.append(symbol)
            
            # If no symbol found, ask for it
            if not symbols:
                symbol = input("📈 Which stock symbol? (e.g., AAPL, TSLA, GOOGL): ").strip().upper()
                if not symbol:
                    continue
                symbols = [symbol]
            
            symbol = symbols[0]  # Use the first one found
            
            print(f"\n🤖 Analyzing: {symbol}")
            print(f"📝 Question: '{question}'")
            print("\n⏳ Processing...")
            
            try:
                # Use smart analysis
                response, csv_file = await self.analyst.smart_analyze(question, symbol, profile)
                
                print(f"\n{'='*60}")
                print("📊 ANALYSIS")
                print(f"{'='*60}")
                print(response)
                
                if csv_file:
                    print(f"\n📁 **CSV FILE CREATED**: {csv_file}")
                    print("💡 Open this file in Excel or Google Sheets!")
                
                # Ask if they want to continue
                continue_choice = input(f"\n🔄 Ask another question? (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes']:
                    break
                    
            except Exception as e:
                logfire.error(f"Smart analysis failed: {e}")
                print(f"❌ Analysis failed: {e}")
                print("💡 Please try again!")

        print("\n👋 Thanks for using AI Stock Analyst!")

    async def demo_mode(self):
        """Run a simple demo of the stock analyst."""
        profile = UserProfile(name="Demo", risk_tolerance="moderate", investment_horizon="medium-term")
        
        try:
            print("\n🤖 Demo: AI Stock Analyst")
            print("-" * 40)
            
            # Demo specific request (CSV export)
            print("\n📊 Demo 1: 'Get AAPL daily data and save to Excel'")
            response, csv_file = await self.analyst.smart_analyze(
                "Get AAPL daily data and save to Excel", "AAPL", profile
            )
            print(response[:200] + "...")
            if csv_file:
                print(f"📁 CSV file created: {csv_file}")
            
            print("\n" + "-"*40)
            
            # Demo general request (quick summary)
            print("\n💬 Demo 2: 'What's your opinion on Apple stock?'")
            response, csv_file = await self.analyst.smart_analyze(
                "What's your opinion on Apple stock?", "AAPL", profile
            )
            print(response[:200] + "...")
            
            print("\n✅ Demo Complete!")
            print("💡 Try interactive mode to ask your own questions!")
            
        except Exception as e:
            logfire.error(f"Demo failed: {e}")
            print(f"❌ Demo Error: {e}")
            print("💡 Try interactive mode instead")
        finally:
            await cleanup_tasks()

    def get_user_profile(self) -> UserProfile:
        """Get a simple default user profile."""
        return UserProfile(
            name="User", 
            risk_tolerance="moderate", 
            investment_horizon="medium-term"
        ) 
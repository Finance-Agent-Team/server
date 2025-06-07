"""
FastAPI endpoints for the PydanticAI Stock Analyst with Graph workflow
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
import asyncio
from datetime import datetime

from app.agents.pydantic_ai_stock_analyst import (
    PydanticAIStockAnalyst, 
    UserProfile, 
    AnalysisResult,
    StockDataPoint,
    MarketConditions
)

router = APIRouter(prefix="/stock-analysis", tags=["Stock Analysis"])

# Global analyst instance
analyst = PydanticAIStockAnalyst()

# --- Request/Response Models ---

class StockAnalysisRequest(BaseModel):
    """Request model for stock analysis"""
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL, GOOGL)", min_length=1, max_length=10)
    user_profile: Optional[UserProfile] = Field(None, description="User investment profile")


class StockAnalysisResponse(BaseModel):
    """Response model for stock analysis"""
    success: bool
    analysis_result: Optional[AnalysisResult] = None
    error_message: Optional[str] = None
    execution_time_seconds: Optional[float] = None


class AnalysisStepsResponse(BaseModel):
    """Response model for analysis steps"""
    success: bool
    steps: List[str] = []
    mermaid_diagram: Optional[str] = None
    error_message: Optional[str] = None


class WorkflowVisualization(BaseModel):
    """Response model for workflow visualization"""
    mermaid_diagram: str
    description: str


# --- API Endpoints ---

@router.post("/analyze", response_model=StockAnalysisResponse)
async def analyze_stock(request: StockAnalysisRequest):
    """
    Perform comprehensive stock analysis using PydanticAI Graph workflow
    
    This endpoint runs a multi-stage analysis including:
    1. Data Collection (via MCP)
    2. Technical Analysis
    3. Fundamental Analysis  
    4. Sentiment Analysis
    5. Final Recommendation
    """
    
    start_time = datetime.now()
    
    try:
        # Validate symbol
        symbol = request.symbol.upper().strip()
        if not symbol:
            raise HTTPException(status_code=400, detail="Stock symbol cannot be empty")
        
        # Use provided user profile or default
        user_profile = request.user_profile or UserProfile()
        
        # Run the analysis
        result = await analyst.analyze_stock(symbol, user_profile)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        return StockAnalysisResponse(
            success=True,
            analysis_result=result,
            execution_time_seconds=execution_time
        )
        
    except Exception as e:
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        return StockAnalysisResponse(
            success=False,
            error_message=f"Analysis failed: {str(e)}",
            execution_time_seconds=execution_time
        )


@router.get("/workflow-steps/{symbol}", response_model=AnalysisStepsResponse)
async def get_analysis_steps(symbol: str, user_profile: Optional[UserProfile] = None):
    """
    Get a step-by-step breakdown of the analysis workflow for a given stock
    
    This endpoint shows each node execution in the PydanticAI graph without
    running the full analysis. Useful for debugging and understanding the workflow.
    """
    
    try:
        symbol = symbol.upper().strip()
        if not symbol:
            raise HTTPException(status_code=400, detail="Stock symbol cannot be empty")
        
        # Get analysis steps
        steps = await analyst.get_analysis_steps(symbol, user_profile)
        
        # Generate Mermaid diagram
        mermaid_diagram = analyst.generate_mermaid_diagram()
        
        return AnalysisStepsResponse(
            success=True,
            steps=steps,
            mermaid_diagram=mermaid_diagram
        )
        
    except Exception as e:
        return AnalysisStepsResponse(
            success=False,
            error_message=f"Failed to get analysis steps: {str(e)}"
        )


@router.get("/workflow-diagram", response_model=WorkflowVisualization)
async def get_workflow_diagram():
    """
    Get the Mermaid diagram representation of the stock analysis workflow
    
    Returns a visual representation of the PydanticAI graph showing the flow
    from data collection through final recommendation.
    """
    
    try:
        mermaid_diagram = analyst.generate_mermaid_diagram()
        
        description = """
        Stock Analysis Workflow:
        1. DataCollection - Gather stock data via MCP
        2. TechnicalAnalysis - Analyze price patterns and indicators  
        3. FundamentalAnalysis - Evaluate company financials and valuation
        4. SentimentAnalysis - Assess market sentiment and news
        5. FinalRecommendation - Generate investment recommendation
        """
        
        return WorkflowVisualization(
            mermaid_diagram=mermaid_diagram,
            description=description.strip()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate workflow diagram: {str(e)}")


@router.post("/analyze-async")
async def analyze_stock_async(request: StockAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start stock analysis as a background task
    
    This endpoint immediately returns a task ID and runs the analysis in the background.
    Use this for long-running analyses to avoid timeouts.
    """
    
    # Generate a simple task ID
    task_id = f"task_{request.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Add background task
    background_tasks.add_task(run_analysis_background, task_id, request)
    
    return {
        "success": True,
        "task_id": task_id,
        "message": f"Stock analysis for {request.symbol} started in background",
        "status": "running"
    }


# --- Background Task Function ---

async def run_analysis_background(task_id: str, request: StockAnalysisRequest):
    """Run stock analysis in the background"""
    
    try:
        print(f"Starting background analysis {task_id} for {request.symbol}")
        
        user_profile = request.user_profile or UserProfile()
        result = await analyst.analyze_stock(request.symbol, user_profile)
        
        print(f"Background analysis {task_id} completed successfully")
        print(f"Recommendation: {result.recommendation} (confidence: {result.confidence:.2f})")
        
        # In a real application, you'd store this result in a database or cache
        # For now, we just log it
        
    except Exception as e:
        print(f"Background analysis {task_id} failed: {str(e)}")


# --- Health Check ---

@router.get("/health")
async def health_check():
    """Health check endpoint for the stock analysis service"""
    
    try:
        # Simple check to ensure the analyst is working
        diagram = analyst.generate_mermaid_diagram()
        
        return {
            "status": "healthy",
            "service": "PydanticAI Stock Analyst",
            "workflow_nodes": 5,
            "mcp_enabled": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


# --- Example Usage ---

@router.get("/examples")
async def get_examples():
    """Get example usage of the stock analysis API"""
    
    examples = {
        "basic_analysis": {
            "method": "POST",
            "endpoint": "/stock-analysis/analyze",
            "body": {
                "symbol": "AAPL"
            }
        },
        "custom_profile_analysis": {
            "method": "POST", 
            "endpoint": "/stock-analysis/analyze",
            "body": {
                "symbol": "TSLA",
                "user_profile": {
                    "name": "John Investor",
                    "risk_tolerance": "aggressive",
                    "investment_horizon": "short"
                }
            }
        },
        "workflow_visualization": {
            "method": "GET",
            "endpoint": "/stock-analysis/workflow-diagram"
        },
        "analysis_steps": {
            "method": "GET", 
            "endpoint": "/stock-analysis/workflow-steps/GOOGL"
        }
    }
    
    return {
        "description": "PydanticAI Stock Analyst API Examples",
        "examples": examples,
        "note": "This API uses PydanticAI graphs with MCP for comprehensive stock analysis"
    } 
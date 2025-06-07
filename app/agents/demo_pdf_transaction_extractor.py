import os
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AccountInformation(BaseModel):
    """Account information extracted from financial statements."""
    name: str = Field(..., description="Account holder's full name, it is 'Name' in InteractiveBrokers's statements")
    account: str = Field(..., description="Account number, potentially masked, it is 'Account' in InteractiveBrokers's statements")
    account_type: str = Field(..., description="Type of account (e.g., Individual, Joint), it is 'Account Type' in InteractiveBrokers's statements")
    customer_type: str = Field(..., description="Customer classification, it is 'Customer Type' in InteractiveBrokers's statements")
    account_capabilities: str = Field(..., description="Account trading capabilities, it is 'Account Capabilitioes' in InteractiveBrokers's statements")
    trading_permissions: List[str] = Field(..., description="List of permitted trading instruments, it is 'Trading Permissions' in InteractiveBrokers's statements")
    base_currency: str = Field(..., description="Base currency for the account, it is 'Base Currency' in InteractiveBrokers's statements")

class Transaction(BaseModel):
    """Individual transaction record from financial statements."""
    symbol: str = Field(..., description="Trading symbol or ticker")
    date_time: str = Field(..., description="Transaction date and time, it is 'Date/Time' in InteractiveBrokers's statements")
    quantity: float = Field(..., description="Number of shares or units traded, it can be a float number.")
    trade_price: float = Field(..., description="Price per unit at execution, it is 'T.Price' in InteractiveBrokers's statements")
    close_price: float = Field(..., description="Closing price on trade date, it is 'C.Price' in InteractiveBrokers's statements")
    proceeds: float = Field(..., description="Total proceeds from transaction")
    commission_fee: float = Field(..., description="Commission or fee charged, it is 'Comm/Fee' in InteractiveBrokers's statements")
    basis: float = Field(..., description="Cost basis for the position")
    realized_p_l: float = Field(..., description="Realized profit or loss, it is 'Realized P/L' in InteractiveBrokers's statements")
    mtm_p_l: float = Field(..., description="Mark-to-market profit or loss, it is 'MTM P/L' in InteractiveBrokers's statements")
    code: str = Field(..., description="Transaction or position code")

class FinancialStatement(BaseModel):
    """Complete financial statement data structure."""
    account_information: AccountInformation = Field(..., description="Account details and permissions")
    transactions: List[Transaction] = Field(..., description="List of all transactions in the statement")

# Generate JSON Schema for OpenAI API
response_format_schema = FinancialStatement.model_json_schema()


def process_statement_with_attachments(pdf_path: str) -> FinancialStatement:
    # Upload PDF to OpenAI
    with open(pdf_path, "rb") as pdf_file:
        uploaded_file = client.files.create(
            file=pdf_file,
            purpose="assistants"
        )

    # Process using Responses API
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": """Analyze the attached financial document and extract structured data.
                Follow these extraction rules:
                1. Identify account holder information in document headers
                2. Locate transaction tables with trade execution details
                3. Convert all currency values to base currency
                4. Map data fields to JSON schema precisely"""
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all account information and transactions from the attached statement in JSON format."},
                    {
                        "type": "file",
                        "file": {
                            "file_id": uploaded_file.id
                        }
                    }
                ]
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": 'statement_schema',
                "description": 'Monthly statmement of InteractiveBrokers',
                "schema": response_format_schema
            }
        }
    )

    try:
        print(response.choices[0].message)
        return FinancialStatement.model_validate_json(response.choices[0].message.content)
    except Exception as e:
        raise RuntimeError(f"Extraction failed: {str(e)}")


# Example usage
statement_data = process_statement_with_attachments("D:\\my-git-repos\\finance-news-agent\\InteractiveBrokers_Sample_Statement.pdf")
print(statement_data.model_dump_json(indent=2))

with open("InteractiveBrokers_Activity_Statement.json", "w") as f:
    f.write(statement_data.model_dump_json(indent=2))
=======
import os
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AccountInformation(BaseModel):
    """Account information extracted from financial statements."""
    name: str = Field(..., description="Account holder's full name, it is 'Name' in InteractiveBrokers's statements")
    account: str = Field(..., description="Account number, potentially masked, it is 'Account' in InteractiveBrokers's statements")
    account_type: str = Field(..., description="Type of account (e.g., Individual, Joint), it is 'Account Type' in InteractiveBrokers's statements")
    customer_type: str = Field(..., description="Customer classification, it is 'Customer Type' in InteractiveBrokers's statements")
    account_capabilities: str = Field(..., description="Account trading capabilities, it is 'Account Capabilitioes' in InteractiveBrokers's statements")
    trading_permissions: List[str] = Field(..., description="List of permitted trading instruments, it is 'Trading Permissions' in InteractiveBrokers's statements")
    base_currency: str = Field(..., description="Base currency for the account, it is 'Base Currency' in InteractiveBrokers's statements")

class Transaction(BaseModel):
    """Individual transaction record from financial statements."""
    symbol: str = Field(..., description="Trading symbol or ticker")
    date_time: str = Field(..., description="Transaction date and time, it is 'Date/Time' in InteractiveBrokers's statements")
    quantity: float = Field(..., description="Number of shares or units traded, it can be a float number.")
    trade_price: float = Field(..., description="Price per unit at execution, it is 'T.Price' in InteractiveBrokers's statements")
    close_price: float = Field(..., description="Closing price on trade date, it is 'C.Price' in InteractiveBrokers's statements")
    proceeds: float = Field(..., description="Total proceeds from transaction")
    commission_fee: float = Field(..., description="Commission or fee charged, it is 'Comm/Fee' in InteractiveBrokers's statements")
    basis: float = Field(..., description="Cost basis for the position")
    realized_p_l: float = Field(..., description="Realized profit or loss, it is 'Realized P/L' in InteractiveBrokers's statements")
    mtm_p_l: float = Field(..., description="Mark-to-market profit or loss, it is 'MTM P/L' in InteractiveBrokers's statements")
    code: str = Field(..., description="Transaction or position code")

class FinancialStatement(BaseModel):
    """Complete financial statement data structure."""
    account_information: AccountInformation = Field(..., description="Account details and permissions")
    transactions: List[Transaction] = Field(..., description="List of all transactions in the statement")

# Generate JSON Schema for OpenAI API
response_format_schema = FinancialStatement.model_json_schema()


def process_statement_with_attachments(pdf_path: str) -> FinancialStatement:
    # Upload PDF to OpenAI
    with open(pdf_path, "rb") as pdf_file:
        uploaded_file = client.files.create(
            file=pdf_file,
            purpose="assistants"
        )

    # Process using Responses API
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": """Analyze the attached financial document and extract structured data.
                Follow these extraction rules:
                1. Identify account holder information in document headers
                2. Locate transaction tables with trade execution details
                3. Convert all currency values to base currency
                4. Map data fields to JSON schema precisely"""
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all account information and transactions from the attached statement in JSON format."},
                    {
                        "type": "file",
                        "file": {
                            "file_id": uploaded_file.id
                        }
                    }
                ]
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": 'statement_schema',
                "description": 'Monthly statmement of InteractiveBrokers',
                "schema": response_format_schema
            }
        }
    )

    try:
        print(response.choices[0].message)
        return FinancialStatement.model_validate_json(response.choices[0].message.content)
    except Exception as e:
        raise RuntimeError(f"Extraction failed: {str(e)}")


# Example usage
statement_data = process_statement_with_attachments("D:\\my-git-repos\\finance-news-agent\\InteractiveBrokers_Sample_Statement.pdf")
print(statement_data.model_dump_json(indent=2))

with open("InteractiveBrokers_Activity_Statement.json", "w") as f:
    f.write(statement_data.model_dump_json(indent=2))
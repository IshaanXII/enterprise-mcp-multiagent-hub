"""CRM/ERP MCP Server — WHY MCP: brief requires MCP Client-Server. Tools are the ONLY
way agents touch the DB (auditable, policy-safe). Run: python -m src.mcp_server"""
from mcp.server.fastmcp import FastMCP
from src.database import db_get_customer, db_get_orders, db_get_disputes, db_create_refund, db_log_ticket

mcp = FastMCP("crm-erp-server")

@mcp.tool()
def get_customer(customer_id: str) -> dict:
    """Fetch account status, tier, fraud flag."""
    return db_get_customer(customer_id)

@mcp.tool()
def get_orders(customer_id: str) -> list:
    """Fetch purchase history."""
    return db_get_orders(customer_id)

@mcp.tool()
def get_disputes(customer_id: str) -> list:
    """Fetch past dispute logs."""
    return db_get_disputes(customer_id)

@mcp.tool()
def create_refund(order_id: str, amount: float) -> dict:
    """Execute billing/refund action. Policy check happens in Resolution Agent BEFORE calling."""
    return db_create_refund(order_id, amount)

@mcp.tool()
def log_ticket(ticket_id: str, customer_id: str, text: str, category: str, priority: str, status: str, resolution: str) -> dict:
    """Persist ticket + resolution for memory."""
    db_log_ticket(ticket_id, customer_id, text, category, priority, status, resolution)
    return {"ok": True, "ticket_id": ticket_id}

if __name__ == "__main__":
    mcp.run()

import logging
import os
import sys
from pathlib import Path
from typing import Optional, List

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from data.load_data import get_policies_data, get_claims_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicerag")

class PolicyUpdateRequest(BaseModel):
    phone: str
    premium: Optional[float] = None
    status: Optional[str] = None

class ClaimRequest(BaseModel):
    policy_number: str
    claim_type: str
    description: str
    estimated_amount: Optional[float] = None

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    if not os.environ.get("RUNNING_IN_PRODUCTION"):
        logger.info("Running in development mode, loading from .env file")
        load_dotenv()

@app.get("/health")
async def read_root():
    return 'Contoso Insurance Voice Assistant API'

@app.get("/api/policies")
async def get_policies(policy_number: Optional[str] = None, holder_name: Optional[str] = None, 
                      first_name: Optional[str] = None, last_name: Optional[str] = None, 
                      policy_type: Optional[str] = None):
    """
    Retrieve insurance policies with flexible name search.
    
    - **policy_number**: Filter by policy number (optional)
    - **holder_name**: Search by full name (e.g., "Jean Dupont") (optional)
    - **first_name**: Search by first name only (e.g., "Jean") (optional) 
    - **last_name**: Search by last name only (e.g., "Dupont") (optional)
    - **policy_type**: Filter by policy type (Auto, Habitation, Santé, etc.) (optional)
    """
    policies = get_policies_data()
    
    if policy_number:
        policies = [p for p in policies if p["policy"].lower() == policy_number.lower()]
    
    if holder_name:
        # Support partial and full name matching
        holder_name_lower = holder_name.lower()
        policies = [p for p in policies if (
            holder_name_lower in p["name"].lower() or
            holder_name_lower == p["first_name"].lower() or
            holder_name_lower == p["last_name"].lower() or
            holder_name_lower == f"{p['first_name']} {p['last_name']}".lower()
        )]
    
    if first_name:
        first_name_lower = first_name.lower()
        policies = [p for p in policies if first_name_lower in p["first_name"].lower()]
    
    if last_name:
        last_name_lower = last_name.lower()
        policies = [p for p in policies if last_name_lower in p["last_name"].lower()]
    
    if policy_type:
        policies = [p for p in policies if p["type"].lower() == policy_type.lower()]
    
    return {"policies": policies}

@app.get("/api/policies/{policy_id}")
async def get_policy(policy_id: int):
    policies = get_policies_data()
    policy = next((p for p in policies if p["id"] == policy_id), None)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"policy": policy}

@app.get("/api/claims")
async def get_claims(claim_number: Optional[str] = None, policy_number: Optional[str] = None, 
                    holder_name: Optional[str] = None, first_name: Optional[str] = None, 
                    last_name: Optional[str] = None, claim_type: Optional[str] = None):
    """
    Retrieve insurance claims with flexible name search.
    
    - **claim_number**: Filter by claim ID (optional)
    - **policy_number**: Filter by policy number (optional) 
    - **holder_name**: Search by full holder name (e.g., "Jean Dupont") (optional)
    - **first_name**: Search by holder first name only (e.g., "Jean") (optional)
    - **last_name**: Search by holder last name only (e.g., "Dupont") (optional)
    - **claim_type**: Filter by claim type (Auto, Dégât des eaux, Vol, etc.) (optional)
    """
    claims = get_claims_data()
    
    if claim_number:
        claims = [c for c in claims if c["id"].lower() == claim_number.lower()]
    
    if policy_number:
        claims = [c for c in claims if c["policy_number"].lower() == policy_number.lower()]
    
    if holder_name:
        # Support partial and full name matching
        holder_name_lower = holder_name.lower()
        claims = [c for c in claims if holder_name_lower in c["holder"].lower()]
    
    if first_name:
        first_name_lower = first_name.lower()
        claims = [c for c in claims if (
            'holder_first_name' in c and first_name_lower in c["holder_first_name"].lower()
        ) or first_name_lower in c["holder"].lower()]
    
    if last_name:
        last_name_lower = last_name.lower()
        claims = [c for c in claims if (
            'holder_last_name' in c and last_name_lower in c["holder_last_name"].lower()
        ) or last_name_lower in c["holder"].lower()]
    
    if claim_type:
        claims = [c for c in claims if c["type"].lower() == claim_type.lower()]
    
    return {"claims": claims}

@app.get("/api/claims/{claim_id}")
async def get_claim_by_id(claim_id: str):
    """
    Retrieve a specific claim by its ID.
    
    - **claim_id**: The unique identifier of the claim.
    """
    claims = get_claims_data()
    claim = next((c for c in claims if c["id"] == claim_id), None)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"claim": claim}

@app.get("/api/realtime/policies")
async def get_realtime_policies(policy_type: Optional[str] = None, status: Optional[str] = None, 
                               holder_name: Optional[str] = None, first_name: Optional[str] = None, 
                               last_name: Optional[str] = None):
    """
    Retrieve comprehensive real-time policy information from the demo system.
    
    - **policy_type**: Filter by policy type (Auto, Habitation, Santé, etc.) (optional)
    - **status**: Filter by policy status (active, suspended, expired, etc.) (optional)
    - **holder_name**: Search by full or partial policyholder name (optional)
    - **first_name**: Search by first name only (e.g., "Jean") (optional)
    - **last_name**: Search by last name only (e.g., "Dupont") (optional)
    """
    # In a real implementation, this would connect to the actual insurance database
    # For now, return the static data with filtering
    policies = get_policies_data()
    
    if policy_type:
        policies = [p for p in policies if p["type"].lower() == policy_type.lower()]
    
    if status:
        policies = [p for p in policies if p["status"].lower() == status.lower()]
    
    if holder_name:
        # Support partial and full name matching
        holder_name_lower = holder_name.lower()
        policies = [p for p in policies if (
            holder_name_lower in p["name"].lower() or
            holder_name_lower == p["first_name"].lower() or
            holder_name_lower == p["last_name"].lower() or
            holder_name_lower == f"{p['first_name']} {p['last_name']}".lower()
        )]
    
    if first_name:
        first_name_lower = first_name.lower()
        policies = [p for p in policies if first_name_lower in p["first_name"].lower()]
    
    if last_name:
        last_name_lower = last_name.lower()
        policies = [p for p in policies if last_name_lower in p["last_name"].lower()]
        
    return {"policies": policies, "total": len(policies)}

@app.get("/api/agencies")
async def get_agencies(city: Optional[str] = None, agent_name: Optional[str] = None):
    """
    Retrieve Contoso agency information.
    
    - **city**: City to find nearby agencies (optional)
    - **agent_name**: Name of specific insurance agent (optional)
    """
    # Static agency data - in real implementation would come from database
    agencies = [
        {
            "name": "Agence Contoso Lyon Centre",
            "city": "Lyon", 
            "address": "123 rue de la République, 69002 Lyon",
            "phone": "01 23 45 67 89",
            "agents": ["Jean Martin", "Sophie Dubois"],
            "services": ["Auto", "Habitation", "Santé", "Professionnelle"]
        },
        {
            "name": "Agence Contoso Bordeaux",
            "city": "Bordeaux",
            "address": "456 cours de l'Intendance, 33000 Bordeaux", 
            "phone": "01 23 45 67 89",
            "agents": ["Sophie Bernard", "Pierre Moreau"],
            "services": ["Auto", "Habitation", "Vie", "Jeune"]
        },
        {
            "name": "Agence Contoso Paris 5ème",
            "city": "Paris",
            "address": "789 boulevard Saint-Germain, 75005 Paris",
            "phone": "01 23 45 67 89", 
            "agents": ["Michel Rousseau", "Anne Lefebvre"],
            "services": ["Auto", "Habitation", "Santé", "Professionnelle"]
        }
    ]
    
    if city:
        agencies = [a for a in agencies if a["city"].lower() == city.lower()]
    if agent_name:
        agencies = [a for a in agencies if any(agent_name.lower() in agent.lower() for agent in a["agents"])]
    
    return {"agencies": agencies}

@app.get("/api/contact")
async def get_contact_info(service_type: Optional[str] = None, company: Optional[str] = None):
    """
    Retrieve Contoso contact information.
    
    - **service_type**: Type of service (customer_service, claims, emergency, etc.) (optional) 
    - **company**: Insurance company (optional)
    """
    contacts = {
        "CONTOSO": {
            "customer_service": "01 23 45 67 89",
            "claims": "01 23 45 67 89",
            "emergency": "01 23 45 67 89",
            "roadside_assistance": "01 23 45 67 89",
            "website": "https://www.contoso.com"
        }
    }
    
    result = contacts
    if company:
        company_key = company.upper()
        if company_key != "CONTOSO":
            company_key = "CONTOSO"
        result = {company_key: contacts.get(company_key, {})}
    if service_type:
        filtered = {}
        for comp, services in result.items():
            if service_type in services:
                filtered[comp] = {service_type: services[service_type]}
        result = filtered
        
    return {"contact_info": result}

if __name__ == "__main__":
    import uvicorn
    host = "0.0.0.0"
    port = int(os.getenv("PORT", 8765))  # Changed default port to 8765
    uvicorn.run(app, host=host, port=port)
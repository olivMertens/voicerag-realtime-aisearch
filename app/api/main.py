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
    return 'MAAF/MAIF Insurance Voice Assistant API'

@app.get("/api/policies")
async def get_policies(policy_number: Optional[str] = None, name: Optional[str] = None, policy_type: Optional[str] = None):
    policies = get_policies_data()
    if policy_number:
        policies = [p for p in policies if p["policy"] == policy_number]
    if name:
        policies = [p for p in policies if p["name"].lower() == name.lower()]
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
async def get_claims(claim_number: Optional[str] = None, policy_number: Optional[str] = None, holder_name: Optional[str] = None, claim_type: Optional[str] = None):
    claims = get_claims_data()
    if claim_number:
        claims = [c for c in claims if c["id"] == claim_number]
    if policy_number:
        claims = [c for c in claims if c["policy_number"] == policy_number]
    if holder_name:
        claims = [c for c in claims if c["holder"].lower() == holder_name.lower()]
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
async def get_realtime_policies(policy_type: Optional[str] = None, status: Optional[str] = None, holder_name: Optional[str] = None):
    """
    Retrieve comprehensive real-time policy information from MAAF/MAIF system.
    
    - **policy_type**: Filter by policy type (Auto, Habitation, Santé, etc.) (optional)
    - **status**: Filter by policy status (active, suspended, expired, etc.) (optional)
    - **holder_name**: Search by policyholder name (optional)
    """
    # In a real implementation, this would connect to the actual MAAF/MAIF database
    # For now, return the static data with filtering
    policies = get_policies_data()
    if policy_type:
        policies = [p for p in policies if p["type"].lower() == policy_type.lower()]
    if status:
        policies = [p for p in policies if p["status"].lower() == status.lower()]
    if holder_name:
        policies = [p for p in policies if holder_name.lower() in p["name"].lower()]
    return {"policies": policies, "total": len(policies)}

@app.get("/api/agencies")
async def get_agencies(city: Optional[str] = None, agent_name: Optional[str] = None):
    """
    Retrieve MAAF and MAIF agency information.
    
    - **city**: City to find nearby agencies (optional)
    - **agent_name**: Name of specific insurance agent (optional)
    """
    # Static agency data - in real implementation would come from database
    agencies = [
        {
            "name": "Agence MAAF Lyon Centre",
            "city": "Lyon", 
            "address": "123 rue de la République, 69002 Lyon",
            "phone": "09 72 72 15 15",
            "agents": ["Jean Martin", "Sophie Dubois"],
            "services": ["Auto", "Habitation", "Santé", "Professionnelle"]
        },
        {
            "name": "Agence MAIF Bordeaux",
            "city": "Bordeaux",
            "address": "456 cours de l'Intendance, 33000 Bordeaux", 
            "phone": "3015",
            "agents": ["Sophie Bernard", "Pierre Moreau"],
            "services": ["Auto", "Habitation", "Vie", "Jeune"]
        },
        {
            "name": "Agence MAAF Paris 5ème",
            "city": "Paris",
            "address": "789 boulevard Saint-Germain, 75005 Paris",
            "phone": "09 72 72 15 15", 
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
    Retrieve MAAF and MAIF contact information.
    
    - **service_type**: Type of service (customer_service, claims, emergency, etc.) (optional) 
    - **company**: Insurance company (MAAF or MAIF) (optional)
    """
    contacts = {
        "MAAF": {
            "customer_service": "09 72 72 15 15",
            "claims": "09 72 72 15 15", 
            "emergency": "09 72 72 15 16",
            "roadside_assistance": "09 72 72 15 17",
            "website": "https://www.maaf.fr"
        },
        "MAIF": {
            "customer_service": "3015",
            "claims": "3015",
            "emergency": "05 49 73 73 73", 
            "roadside_assistance": "05 49 73 73 74",
            "website": "https://www.maif.fr"
        }
    }
    
    result = contacts
    if company:
        result = {company.upper(): contacts.get(company.upper(), {})}
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
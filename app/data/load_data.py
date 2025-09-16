"""
Insurance data loading functions for MAAF/MAIF policies and claims
"""
import json
import os
from typing import List, Dict, Any
from pathlib import Path

def get_policies_data() -> List[Dict[str, Any]]:
    """
    Get sample MAAF/MAIF policy data for demonstration purposes.
    In production, this would connect to the actual insurance database.
    """
    return [
        {
            "id": 1,
            "policy": "MAIF-AUTO-001",
            "name": "Jean Dupont",
            "type": "Auto",
            "status": "Active",
            "premium": 650.00,
            "coverage": "Tous Risques",
            "vehicle": "Renault Clio 2019",
            "start_date": "2024-01-15",
            "end_date": "2025-01-14"
        },
        {
            "id": 2,
            "policy": "MAAF-HAB-002",
            "name": "Marie Martin",
            "type": "Habitation",
            "status": "Active",
            "premium": 450.00,
            "coverage": "Multirisque Habitation",
            "property": "Appartement 3 pièces Lyon",
            "start_date": "2023-06-01",
            "end_date": "2024-05-31"
        },
        {
            "id": 3,
            "policy": "MAIF-VIE-003",
            "name": "Pierre Bernard",
            "type": "Assurance Vie",
            "status": "Active",
            "premium": 1200.00,
            "coverage": "PER Responsable et Solidaire",
            "capital": 85000.00,
            "start_date": "2020-03-10",
            "end_date": "2050-03-10"
        },
        {
            "id": 4,
            "policy": "MAAF-SANTE-004",
            "name": "Sophie Dubois",
            "type": "Santé",
            "status": "Active",
            "premium": 380.00,
            "coverage": "VIVAZEN Niveau 3",
            "beneficiaries": 2,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        },
        {
            "id": 5,
            "policy": "MAIF-MOTO-005",
            "name": "Julien Moreau",
            "type": "Moto",
            "status": "Active",
            "premium": 320.00,
            "coverage": "Tous Risques Plénitude",
            "vehicle": "Yamaha MT-07 2021",
            "start_date": "2024-04-15",
            "end_date": "2025-04-14"
        }
    ]

def get_claims_data() -> List[Dict[str, Any]]:
    """
    Get sample MAAF/MAIF claims data for demonstration purposes.
    In production, this would connect to the actual insurance database.
    """
    return [
        {
            "id": "CLAIM-001",
            "policy_number": "MAIF-AUTO-001",
            "holder": "Jean Dupont",
            "type": "Auto",
            "description": "Collision avec un autre véhicule",
            "status": "En cours d'expertise",
            "estimated_amount": 2500.00,
            "declaration_date": "2024-08-15",
            "incident_date": "2024-08-12"
        },
        {
            "id": "CLAIM-002",
            "policy_number": "MAAF-HAB-002",
            "holder": "Marie Martin",
            "type": "Dégât des eaux",
            "description": "Fuite de canalisation dans la salle de bain",
            "status": "Indemnisé",
            "estimated_amount": 1800.00,
            "declaration_date": "2024-07-20",
            "incident_date": "2024-07-18"
        },
        {
            "id": "CLAIM-003",
            "policy_number": "MAIF-MOTO-005",
            "holder": "Julien Moreau",
            "type": "Vol",
            "description": "Vol de moto stationnée devant domicile",
            "status": "Déclaré",
            "estimated_amount": 4500.00,
            "declaration_date": "2024-09-10",
            "incident_date": "2024-09-09"
        }
    ]

def get_insurance_products() -> List[Dict[str, Any]]:
    """
    Get MAAF/MAIF insurance product information
    """
    return [
        {
            "company": "MAIF",
            "product": "Auto",
            "formulas": ["Tiers Initiale", "Tiers Essentiel", "Tous Risques Différence", "Tous Risques Plénitude"],
            "features": ["Responsabilité civile", "Assistance", "Protection corporelle", "Défense juridique"]
        },
        {
            "company": "MAAF", 
            "product": "Auto",
            "formulas": ["Tiers Eco", "Tiers Essentiel", "Tiers Essentiel+", "Tous Risques Eco", "Tous Risques Confort", "Tous Risques Confort+"],
            "features": ["Responsabilité civile illimitée", "Assistance 24/7", "Véhicule de remplacement", "Options mobilité"]
        },
        {
            "company": "MAIF",
            "product": "Habitation",
            "formulas": ["Initiale", "Essentiel", "Différence"],
            "features": ["Multirisque", "Protection des enfants scolarisés", "Assistance 24/7", "Renseignements juridiques"]
        },
        {
            "company": "MAAF",
            "product": "Habitation",
            "formulas": ["Tempo Initiale", "Tempo Classique", "Tempo Intégrale"],
            "features": ["Protection étendue", "Assistance dépannage", "Défense juridique", "Services après sinistre"]
        }
    ]

def load_faq_data() -> List[Dict[str, Any]]:
    """
    Load FAQ data from the main data directory
    """
    try:
        # Get the path to the FAQ file in the root data directory
        current_dir = Path(__file__).parent
        faq_path = current_dir.parent.parent / "data" / "faq.json"
        
        if faq_path.exists():
            with open(faq_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Return empty list if file doesn't exist
            return []
    except Exception as e:
        print(f"Error loading FAQ data: {e}")
        return []
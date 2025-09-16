# Insurance policy data for MAAF and MAIF
# Generated on 2025-01-15 11:11:04
# Contains realistic French insurance policy data

def get_policies_data():
    return [
    {'id': 1, 'name': "Marie Dubois", 'policy': "MAA-2025-001234", 'type': "Auto", 'premium': 125.50, 'currency': "EUR", 'phone': "0123456789", 'vehicle': {'make': "Peugeot", 'model': "308", 'year': 2022}, 'agent_phone': "09 72 72 15 15", 'status': "active"},
    {'id': 2, 'name': "Pierre Leroy", 'policy': "MIF-2025-005678", 'type': "Habitation", 'premium': 89.90, 'currency': "EUR", 'phone': "0234567890", 'property': {'type': "Appartement", 'surface': 75, 'rooms': 3}, 'agent_phone': "3015", 'status': "active"},
    {'id': 3, 'name': "Anne Moreau", 'policy': "MAA-2025-009012", 'type': "Santé", 'premium': 156.80, 'currency': "EUR", 'phone': "0345678901", 'health': {'beneficiaries': 3, 'coverage': "Essentielle Plus"}, 'agent_phone': "09 72 72 15 15", 'status': "active"},
    {'id': 4, 'name': "Julien Petit", 'policy': "MIF-2025-003456", 'type': "Auto", 'premium': 95.75, 'currency': "EUR", 'phone': "0456789012", 'vehicle': {'make': "Renault", 'model': "Clio", 'year': 2020}, 'agent_phone': "3015", 'status': "suspended"},
    {'id': 5, 'name': "David Laurent", 'policy': "MAA-2025-007890", 'type': "Professionnelle", 'premium': 89.50, 'currency': "EUR", 'phone': "0567890123", 'business': {'name': "Laurent Consulting SARL", 'employees': 5}, 'agent_phone': "09 72 72 15 15", 'status': "active"},
    {'id': 6, 'name': "Isabelle Garcia", 'policy': "MIF-2025-001122", 'type': "Vie", 'premium': 200.00, 'currency': "EUR", 'phone': "0678901234", 'life_insurance': {'capital': 50000, 'type': "Épargne Retraite"}, 'agent_phone': "3015", 'status': "active"},
    {'id': 7, 'name': "Nicolas Roux", 'policy': "MAA-2025-004567", 'type': "Habitation", 'premium': 145.30, 'currency': "EUR", 'phone': "0789012345", 'property': {'type': "Maison", 'surface': 120, 'rooms': 5}, 'agent_phone': "09 72 72 15 15", 'status': "pending_claim"},
    {'id': 8, 'name': "Emma Lefebvre", 'policy': "MIF-2025-008901", 'type': "Jeune", 'premium': 39.90, 'currency': "EUR", 'phone': "0890123456", 'student': {'age': 22, 'university': "Montpellier"}, 'agent_phone': "3015", 'status': "active"},
    {'id': 9, 'name': "Alexandre Benoit", 'policy': "MAA-2025-005432", 'type': "Moto", 'premium': 165.40, 'currency': "EUR", 'phone': "0901234567", 'vehicle': {'make': "Yamaha", 'model': "MT-07", 'year': 2023}, 'agent_phone': "09 72 72 15 15", 'status': "active"},
    {'id': 10, 'name': "Camille Dubois", 'policy': "MIF-2025-006789", 'type': "Voyage", 'premium': 89.50, 'currency': "EUR", 'phone': "0012345678", 'travel': {'destination': "Japon", 'duration': 15}, 'agent_phone': "3015", 'status': "expired"}
    ]


def get_claims_data():
    return [
        {'id': "CLM-2024-789", 'policy_number': "MAA-2025-001234", 'type': "Collision mineure", 'date': "2024-08-12", 'amount': 1200, 'status': "settled", 'holder': "Marie Dubois", 'description': "Accrochage parking - réparation pare-chocs"},
        {'id': "SNT-2024-456", 'policy_number': "MAA-2025-009012", 'type': "Consultation spécialiste", 'date': "2024-11-05", 'amount': 85, 'reimbursed': 68, 'status': "processed", 'holder': "Anne Moreau", 'description': "Consultation cardiologue + examens"},
        {'id': "HAB-2025-123", 'policy_number': "MAA-2025-004567", 'type': "Dégât des eaux", 'date': "2025-01-08", 'estimated_amount': 3500, 'status': "in_progress", 'holder': "Nicolas Roux", 'description': "Fuite canalisation - dégâts plafond salon"},
        {'id': "AUTO-2024-998", 'policy_number': "MIF-2025-003456", 'type': "Vol véhicule", 'date': "2024-12-20", 'amount': 8500, 'status': "investigating", 'holder': "Julien Petit", 'description': "Vol Renault Clio - parking souterrain Nice"},
        {'id': "SANT-2024-335", 'policy_number': "MAA-2025-009012", 'type': "Hospitalisation", 'date': "2024-09-15", 'amount': 2400, 'reimbursed': 2160, 'status': "settled", 'holder': "Anne Moreau", 'description': "Intervention chirurgie ambulatoire"},
        {'id': "PROF-2024-667", 'policy_number': "MAA-2025-007890", 'type': "Responsabilité civile", 'date': "2024-10-30", 'amount': 15000, 'status': "settled", 'holder': "David Laurent", 'description': "Erreur conseil informatique - dommages client"},
        {'id': "MOTO-2024-445", 'policy_number': "MAA-2025-005432", 'type': "Accident corporel", 'date': "2024-06-18", 'amount': 4200, 'status': "settled", 'holder': "Alexandre Benoit", 'description': "Chute moto - fracture poignet + réparations"},
        {'id': "HAB-2024-889", 'policy_number': "MIF-2025-005678", 'type': "Cambriolage", 'date': "2024-07-22", 'amount': 3800, 'reimbursed': 3400, 'status': "settled", 'holder': "Pierre Leroy", 'description': "Vol objets valeur + dégâts porte entrée"},
        {'id': "VIE-2024-112", 'policy_number': "MIF-2025-001122", 'type': "Rachat partiel", 'date': "2024-11-10", 'amount': 5000, 'status': "processed", 'holder': "Isabelle Garcia", 'description': "Rachat partiel épargne - travaux maison"},
        {'id': "JEUN-2024-223", 'policy_number': "MIF-2025-008901", 'type': "Protection juridique", 'date': "2024-08-05", 'amount': 800, 'status': "settled", 'holder': "Emma Lefebvre", 'description': "Litige propriétaire - aide juridique logement étudiant"}
    ]


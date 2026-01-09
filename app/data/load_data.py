"""Insurance data loading functions for Groupama (demo) policies and claims."""
import json
import os
from typing import List, Dict, Any
from pathlib import Path

def get_policies_data() -> List[Dict[str, Any]]:
    """
    Get sample Groupama (demo) policy data for demonstration purposes.
    In production, this would connect to the actual insurance database.
    """
    return [
        {
            "id": 1,
            "policy": "GROUPAMA-AUTO-001",
            "name": "Jean Dupont",
            "first_name": "Jean",
            "last_name": "Dupont",
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
            "policy": "GROUPAMA-HAB-002",
            "name": "Marie Martin",
            "first_name": "Marie",
            "last_name": "Martin",
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
            "policy": "GROUPAMA-VIE-003",
            "name": "Pierre Leroy",
            "first_name": "Pierre",
            "last_name": "Leroy",
            "type": "Assurance Vie",
            "status": "Active",
            "premium": 1200.00,
            "coverage": "PER Responsable et Solidaire",
            "capital": 77000.00,
            "start_date": "2020-03-10",
            "end_date": "2050-03-10"
        },
        {
            "id": 4,
            "policy": "GROUPAMA-SANTE-004",
            "name": "Sophie Dubois",
            "first_name": "Sophie",
            "last_name": "Dubois",
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
            "policy": "GROUPAMA-MOTO-005",
            "name": "Julien Moreau",
            "first_name": "Julien",
            "last_name": "Moreau",
            "type": "Moto",
            "status": "Active",
            "premium": 320.00,
            "coverage": "Tous Risques Plénitude",
            "vehicle": "Yamaha MT-07 2021",
            "start_date": "2024-04-15",
            "end_date": "2025-04-14"
        },
        {
            "id": 6,
            "policy": "GROUPAMA-AUTO-006",
            "name": "Catherine Leroy",
            "first_name": "Catherine",
            "last_name": "Leroy",
            "type": "Auto",
            "status": "Active",
            "premium": 720.00,
            "coverage": "Tous Risques Confort+",
            "vehicle": "Peugeot 3008 2022",
            "start_date": "2024-02-01",
            "end_date": "2025-01-31"
        },
        {
            "id": 7,
            "policy": "GROUPAMA-HAB-007",
            "name": "Michel Rousseau",
            "first_name": "Michel",
            "last_name": "Rousseau",
            "type": "Habitation",
            "status": "Active",
            "premium": 580.00,
            "coverage": "Multirisque Différence",
            "property": "Maison 4 pièces Bordeaux",
            "start_date": "2023-09-01",
            "end_date": "2024-08-31"
        },
        {
            "id": 8,
            "policy": "GROUPAMA-PROF-008",
            "name": "Anne Lefebvre",
            "first_name": "Anne",
            "last_name": "Lefebvre",
            "type": "Professionnelle",
            "status": "Active",
            "premium": 890.00,
            "coverage": "RC Professionnelle Enseignant",
            "activity": "Professeure des écoles",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        },
        {
            "id": 9,
            "policy": "GROUPAMA-HAB-003",
            "name": "Isabelle Durand",
            "first_name": "Isabelle",
            "last_name": "Durand",
            "type": "Habitation",
            "status": "Active",
            "premium": 395.00,
            "coverage": "Tempo Classique",
            "property": "Appartement 2 pièces Marseille",
            "start_date": "2024-03-01",
            "end_date": "2025-02-28"
        },
        {
            "id": 10,
            "policy": "GROUPAMA-SANTE-010",
            "name": "Jérôme Parel",
            "first_name": "Jérôme",
            "last_name": "Parel",
            "type": "Santé",
            "status": "Active",
            "premium": 510.00,
            "coverage": "Contrat Santé Collectif (Remboursements de groupe)",
            "beneficiaries": 1,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
    ]

def get_claims_data() -> List[Dict[str, Any]]:
    """
    Get sample Groupama (demo) claims data for demonstration purposes.
    In production, this would connect to the actual insurance database.
    """
    return [
        {
            "id": "CLAIM-001",
            "policy_number": "GROUPAMA-AUTO-001",
            "holder": "Jean Dupont",
            "holder_first_name": "Jean",
            "holder_last_name": "Dupont",
            "type": "Auto",
            "description": "Collision avec un autre véhicule",
            "status": "En cours d'expertise",
            "estimated_amount": 2500.00,
            "declaration_date": "2024-08-15",
            "incident_date": "2024-08-12",
            "long_description": "Collision lors d'un dépassement sur la D906",
            "call_history": [
                {
                    "call_id": "CALL-001-001",
                    "date": "2024-08-15",
                    "time": "09:15",
                    "duration": "18 minutes",
                    "agent": "Thomas Durand",
                    "summary": "Déclaration de sinistre auto - collision. M. Dupont déclare une collision lors d'un dépassement sur la D906. Véhicule endommagé à l'avant droit.",
                    "decisions": [
                        "Sinistre accepté - responsabilité partagée présumée",
                        "Expert auto désigné: M. Leblanc",
                        "RDV expertise fixé au 20/08"
                    ],
                    "next_actions": "Envoi constat amiable + photos demandées"
                },
                {
                    "call_id": "CALL-002-001",
                    "date": "2024-08-22",
                    "time": "14:45",
                    "duration": "12 minutes",
                    "agent": "Thomas Durand",
                    "summary": "Suivi expertise. Rapport expert reçu. Estimation dégâts: 2500€. Discussion responsabilités avec autre assureur en cours.",
                    "decisions": [
                        "Devis garage validé: Garage Martin",
                        "Attente accord responsabilité adverse",
                        "Véhicule de remplacement accordé 5 jours"
                    ],
                    "next_actions": "Contact assureur adverse - retour prévu sous 48h"
                }
            ]
        },
        {
            "id": "CLAIM-002",
            "policy_number": "GROUPAMA-HAB-002",
            "holder": "Marie Martin",
            "holder_first_name": "Marie",
            "holder_last_name": "Martin",
            "type": "Dégât des eaux",
            "description": "Fuite de canalisation dans la salle de bain",
            "status": "Indemnisé",
            "estimated_amount": 1800.00,
            "declaration_date": "2024-07-20",
            "incident_date": "2024-07-18",
            "long_description": "Rupture de canalisation encastrée causant infiltration dans l'appartement du dessous",
            "call_history": [
                {
                    "call_id": "CALL-001-002",
                    "date": "2024-07-20",
                    "time": "10:30",
                    "duration": "15 minutes",
                    "agent": "Claire Moreau",
                    "summary": "Déclaration dégât des eaux urgent. Mme Martin signale fuite importante salle de bain avec dégâts voisin du dessous. Plombier déjà intervenu.",
                    "decisions": [
                        "Dossier urgent accepté",
                        "Expert dégât des eaux: Mme Petit",
                        "RDV expertise immédiat - jour même 16h"
                    ],
                    "next_actions": "Coordination avec assurance voisin + photos"
                },
                {
                    "call_id": "CALL-002-002",
                    "date": "2024-07-25",
                    "time": "16:20",
                    "duration": "10 minutes",
                    "agent": "Claire Moreau",
                    "summary": "Rapport expertise reçu. Dégâts: 1800€ chez Mme Martin + 2200€ chez voisin. Responsabilité établie: défaut d'entretien exclu.",
                    "decisions": [
                        "Indemnisation 1800€ validée",
                        "Franchise 150€ déduite",
                        "Versement 1650€ autorisé"
                    ],
                    "next_actions": "Virement sous 72h après réception RIB"
                }
            ]
        },
        {
            "id": "CLAIM-003",
            "policy_number": "GROUPAMA-MOTO-005",
            "holder": "Julien Moreau",
            "holder_first_name": "Julien",
            "holder_last_name": "Moreau",
            "type": "Vol",
            "description": "Vol de moto stationnée devant domicile",
            "status": "En cours d'enquête",
            "estimated_amount": 4500.00,
            "declaration_date": "2024-09-10",
            "incident_date": "2024-09-09",
            "long_description": "Yamaha MT-07 volée dans la nuit, serrure forcée",
            "call_history": [
                {
                    "call_id": "CALL-001-003",
                    "date": "2024-09-10",
                    "time": "08:45",
                    "duration": "20 minutes",
                    "agent": "Pierre Lemoine",
                    "summary": "Déclaration vol moto. M. Moreau découvre vol Yamaha MT-07 au matin. Serrure forcée, pas de trace d'effraction autre. Dépôt plainte effectué.",
                    "decisions": [
                        "Dossier vol accepté sous réserve enquête",
                        "Délai enquête: 30 jours",
                        "Valeur vénale: 4500€ (expertise à confirmer)"
                    ],
                    "next_actions": "Envoi copie plainte + carte grise originale"
                },
                {
                    "call_id": "CALL-002-003",
                    "date": "2024-09-15",
                    "time": "11:30",
                    "duration": "8 minutes",
                    "agent": "Pierre Lemoine",
                    "summary": "Point enquête. Gendarmerie: pas de retrouvailles. M. Moreau demande avancement dossier. Documents complets reçus.",
                    "decisions": [
                        "Enquête en cours - RAS",
                        "Expertise valeur confirmée: 4500€",
                        "Attente fin délai légal (encore 15 jours)"
                    ],
                    "next_actions": "Rappel automatique dans 2 semaines"
                }
            ]
        },
        {
            "id": "CLAIM-004",
            "policy_number": "GROUPAMA-AUTO-006",
            "holder": "Catherine Leroy",
            "holder_first_name": "Catherine",
            "holder_last_name": "Leroy",
            "type": "Bris de glace",
            "description": "Pare-brise fissuré par projection",
            "status": "Réparé",
            "estimated_amount": 350.00,
            "declaration_date": "2024-08-05",
            "incident_date": "2024-08-03",
            "long_description": "Impact de gravillon sur autoroute A6, fissure étoilée de 15cm",
            "call_history": [
                {
                    "call_id": "CALL-001-004",
                    "date": "2024-08-05",
                    "time": "13:20",
                    "duration": "5 minutes",
                    "agent": "Julie Renaud",
                    "summary": "Déclaration bris de glace rapide. Mme Leroy signale impact gravillon A6. Fissure étoilée 15cm côté passager. Conduite possible.",
                    "decisions": [
                        "Bris de glace accepté",
                        "Réparation autorisée: Carglass partenaire",
                        "Pas de franchise bris de glace"
                    ],
                    "next_actions": "RDV Carglass pris: 08/08 à 9h"
                },
                {
                    "call_id": "CALL-002-004",
                    "date": "2024-08-08",
                    "time": "17:10",
                    "duration": "3 minutes",
                    "agent": "Julie Renaud",
                    "summary": "Confirmation réparation. Carglass confirme réparation effectuée. Coût: 350€. Mme Leroy satisfaite du service.",
                    "decisions": [
                        "Réparation validée et payée",
                        "Dossier clos",
                        "Satisfaction client: 5/5"
                    ],
                    "next_actions": "Dossier archivé"
                }
            ]
        },
        {
            "id": "CLAIM-005",
            "policy_number": "GROUPAMA-HAB-007",
            "holder": "Michel Rousseau",
            "holder_first_name": "Michel",
            "holder_last_name": "Rousseau",
            "type": "Tempête",
            "description": "Dégâts suite à la tempête - tuiles arrachées",
            "status": "En cours d'indemnisation",
            "estimated_amount": 3200.00,
            "declaration_date": "2024-09-01",
            "incident_date": "2024-08-30",
            "long_description": "Tempête de grêle avec vents à 120 km/h, toiture endommagée sur 40m²",
            "call_history": [
                {
                    "call_id": "CALL-001-005",
                    "date": "2024-09-01",
                    "time": "07:30",
                    "duration": "14 minutes",
                    "agent": "Antoine Mercier",
                    "summary": "Déclaration dégâts tempête. M. Rousseau signale dégâts importants toiture suite tempête 30/08. Tuiles arrachées, gouttières endommagées. Bâchage effectué.",
                    "decisions": [
                        "Catastrophe naturelle - procédure accélérée",
                        "Expert bâtiment: M. Roux",
                        "RDV expertise: 05/09"
                    ],
                    "next_actions": "Photos + devis provisoire couvreur"
                },
                {
                    "call_id": "CALL-002-005",
                    "date": "2024-09-06",
                    "time": "15:45",
                    "duration": "12 minutes",
                    "agent": "Antoine Mercier",
                    "summary": "Retour expertise. Rapport M. Roux: dégâts 3200€. Toiture à refaire partiellement. Devis entreprise Martineau validé.",
                    "decisions": [
                        "Montant 3200€ accepté",
                        "Franchise tempête: 380€",
                        "Net à payer: 2820€"
                    ],
                    "next_actions": "Autorisation travaux + acompte 50%"
                }
            ]
        },
        {
            "id": "CLAIM-006",
            "policy_number": "GROUPAMA-HAB-003",
            "holder": "Isabelle Durand",
            "holder_first_name": "Isabelle",
            "holder_last_name": "Durand",
            "type": "Dégât par animaux",
            "description": "Dégâts causés par chiens et chats dans logement",
            "status": "En cours d'expertise",
            "estimated_amount": 2800.00,
            "declaration_date": "2024-09-15",
            "incident_date": "2024-09-10",
            "long_description": "Dégâts importants causés par 3 chats et 2 chiens laissés seuls pendant 10 jours suite à hospitalisation d'urgence. Parquet griffé, papier peint déchiré, canapé et fauteuils détériorés, moquette souillée dans 2 chambres.",
            "call_history": [
                {
                    "call_id": "CALL-001-006",
                    "date": "2024-09-15",
                    "time": "14:30",
                    "duration": "12 minutes",
                    "agent": "Sophie Lambert",
                    "summary": "Déclaration initiale du sinistre. Mme Durand explique la situation d'urgence médicale. Ouverture du dossier, attribution numéro CLAIM-006.",
                    "decisions": [
                        "Dossier accepté en garantie dégât par animaux domestiques",
                        "Expert désigné: M. Petit",
                        "RDV expertise fixé au 20/09"
                    ],
                    "next_actions": "Envoi courrier confirmation + questionnaire détaillé"
                },
                {
                    "call_id": "CALL-002-006",
                    "date": "2024-09-18",
                    "time": "16:15",
                    "duration": "8 minutes",
                    "agent": "Marc Dubois",
                    "summary": "Mme Durand demande report RDV expertise pour raisons médicales. Nouvelle date proposée.",
                    "decisions": [
                        "Report expertise au 25/09 à 10h",
                        "Prolongation délai documents à 30 jours"
                    ],
                    "next_actions": "Confirmation nouveau RDV par SMS"
                },
                {
                    "call_id": "CALL-003-006",
                    "date": "2024-09-25",
                    "time": "11:45",
                    "duration": "15 minutes",
                    "agent": "Sophie Lambert",
                    "summary": "Rapport d'expertise reçu. Montant estimé 2800€. Discussion sur franchise et modalités d'indemnisation.",
                    "decisions": [
                        "Franchise 200€ applicable",
                        "Indemnisation 2600€ validée",
                        "Paiement sous 8 jours après envoi justificatifs"
                    ],
                    "next_actions": "Envoi formulaire règlement + RIB à fournir"
                }
            ]
        },
        {
            "id": "CLAIM-007",
            "policy_number": "GROUPAMA-VIE-003",
            "holder": "Pierre Leroy",
            "holder_first_name": "Pierre",
            "holder_last_name": "Leroy",
            "type": "Rachat partiel",
            "description": "Demande de rachat partiel pour financement travaux",
            "status": "Traité",
            "estimated_amount": 8000.00,
            "declaration_date": "2024-08-20",
            "incident_date": "2024-08-20",
            "long_description": "Demande de rachat partiel de 8000€ sur contrat d'assurance vie pour financement travaux d'extension maison",
            "call_history": [
                {
                    "call_id": "CALL-001-007",
                    "date": "2024-08-20",
                    "time": "14:15",
                    "duration": "25 minutes",
                    "agent": "Sandrine Lefebvre",
                    "summary": "M. Leroy demande rachat partiel 8000€ sur son contrat vie GROUPAMA-VIE-003. Capital actuel: 85000€. Demande motivée par travaux extension maison.",
                    "decisions": [
                        "Rachat partiel 8000€ autorisé",
                        "Valeur de rachat confirmée: 8000€",
                        "Fiscalité applicable: 0€ (versements <8 ans)"
                    ],
                    "next_actions": "Formulaire rachat + RIB à retourner"
                },
                {
                    "call_id": "CALL-002-007", 
                    "date": "2024-08-25",
                    "time": "10:30",
                    "duration": "8 minutes",
                    "agent": "Sandrine Lefebvre",
                    "summary": "Documents rachat reçus et validés. Traitement en cours. M. Leroy confirme coordonnées bancaires pour virement.",
                    "decisions": [
                        "Dossier complet validé",
                        "Virement 8000€ programmé",
                        "Nouveau capital restant: 77000€"
                    ],
                    "next_actions": "Virement sous 48h + avenant contrat"
                },
                {
                    "call_id": "CALL-003-007",
                    "date": "2024-09-10",
                    "time": "16:20",
                    "duration": "6 minutes",
                    "agent": "Sandrine Lefebvre",
                    "summary": "Appel de courtoisie. M. Leroy confirme réception virement et avenant. Questions sur optimisation fiscale future des versements.",
                    "decisions": [
                        "Satisfaction client confirmée",
                        "Conseil: versements programmés recommandés",
                        "RDV conseiller prévu si souhaité"
                    ],
                    "next_actions": "Contact conseiller si besoin - dossier clos"
                }
            ]
        },
        {
            "id": "CLAIM-008",
            "policy_number": "GROUPAMA-SANTE-004",
            "holder": "Sophie Dubois",
            "holder_first_name": "Sophie",
            "holder_last_name": "Dubois",
            "type": "Santé",
            "description": "Remboursement optique",
            "status": "En attente de justificatifs",
            "estimated_amount": 210.00,
            "declaration_date": "2024-09-03",
            "incident_date": "2024-09-01",
            "long_description": "Demande de remboursement lunettes (monture + verres). Télétransmission partielle, besoin de facture acquittée.",
            "call_history": [
                {
                    "call_id": "CALL-001-008",
                    "date": "2024-09-03",
                    "time": "10:10",
                    "duration": "9 minutes",
                    "agent": "Claire Moreau",
                    "summary": "Mme Dubois demande un remboursement optique. Vérification des garanties et des pièces manquantes.",
                    "decisions": [
                        "Dossier remboursement ouvert",
                        "Facture acquittée requise",
                        "Contrôle télétransmission en cours"
                    ],
                    "next_actions": "Envoyer facture opticien + décompte Sécurité sociale"
                }
            ]
        },
        {
            "id": "CLAIM-009",
            "policy_number": "GROUPAMA-PROF-008",
            "holder": "Anne Lefebvre",
            "holder_first_name": "Anne",
            "holder_last_name": "Lefebvre",
            "type": "RC Professionnelle",
            "description": "Demande d'assistance juridique (activité)",
            "status": "Conseil fourni",
            "estimated_amount": 0.00,
            "declaration_date": "2024-09-11",
            "incident_date": "2024-09-11",
            "long_description": "Question sur la couverture RC professionnelle suite à un incident mineur dans le cadre de l'activité.",
            "call_history": [
                {
                    "call_id": "CALL-001-009",
                    "date": "2024-09-11",
                    "time": "18:05",
                    "duration": "12 minutes",
                    "agent": "Nadia Pelletier",
                    "summary": "Mme Lefebvre sollicite un avis sur sa couverture RC pro. Recueil des informations et orientation.",
                    "decisions": [
                        "Couverture potentielle confirmée sous réserve d'éléments",
                        "Conseil sur documents à conserver",
                        "Proposition d'ouverture de dossier si nécessaire"
                    ],
                    "next_actions": "Transmettre éléments factuels si ouverture dossier souhaitée"
                }
            ]
        },
        {
            "id": "CLAIM-010",
            "policy_number": "GROUPAMA-SANTE-010",
            "holder": "Jérôme Parel",
            "holder_first_name": "Jérôme",
            "holder_last_name": "Parel",
            "type": "Santé (Collectif)",
            "description": "Remboursement de groupe incomplet",
            "status": "En cours de régularisation",
            "estimated_amount": 135.00,
            "declaration_date": "2024-09-20",
            "incident_date": "2024-09-18",
            "long_description": "Remboursement d'un acte médical sur contrat collectif: montant perçu inférieur à l'attendu. Vérification des flux de télétransmission et du paramétrage du contrat de groupe.",
            "call_history": [
                {
                    "call_id": "CALL-001-010",
                    "date": "2024-09-20",
                    "time": "12:05",
                    "duration": "17 minutes",
                    "agent": "Thomas Durand",
                    "summary": "M. Parel signale un remboursement de groupe incomplet sur son contrat santé collectif. Contrôle des décomptes et des garanties.",
                    "decisions": [
                        "Dossier remboursement ouvert",
                        "Vérification contrat collectif / paramétrage garanties",
                        "Demande du décompte Sécurité sociale + facture"
                    ],
                    "next_actions": "Transmettre décompte + facture; retour sous 5 jours ouvrés"
                },
                {
                    "call_id": "CALL-002-010",
                    "date": "2024-09-24",
                    "time": "09:50",
                    "duration": "9 minutes",
                    "agent": "Nadia Pelletier",
                    "summary": "Suivi dossier remboursement collectif. Une correction de paramétrage est en cours, un complément devrait être versé.",
                    "decisions": [
                        "Anomalie de paramétrage identifiée",
                        "Correction en cours",
                        "Complément de remboursement autorisé"
                    ],
                    "next_actions": "Attendre virement complémentaire; confirmation envoyée"
                }
            ]
        }
    ]

def get_insurance_products() -> List[Dict[str, Any]]:
    """
    Get Groupama (demo) insurance product information
    """
    return [
        {
            "company": "GROUPAMA",
            "product": "Auto",
            "formulas": ["Tiers", "Tous Risques"],
            "features": ["Responsabilité civile", "Assistance", "Protection corporelle", "Défense juridique"]
        },
        {
            "company": "GROUPAMA", 
            "product": "Auto",
            "formulas": ["Tiers", "Tous Risques"],
            "features": ["Responsabilité civile illimitée", "Assistance 24/7", "Véhicule de remplacement", "Options mobilité"]
        },
        {
            "company": "GROUPAMA",
            "product": "Habitation",
            "formulas": ["Essentiel", "Confort"],
            "features": ["Multirisque", "Protection des enfants scolarisés", "Assistance 24/7", "Renseignements juridiques"]
        },
        {
            "company": "GROUPAMA",
            "product": "Habitation",
            "formulas": ["Essentiel", "Confort"],
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
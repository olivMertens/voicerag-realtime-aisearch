import logging
import os
from pathlib import Path
from aiohttp import web
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential, DefaultAzureCredential
from dotenv import load_dotenv
from ragtools import attach_rag_tools

# Import telemetry
try:
    from telemetry import telemetry
except ImportError:
    telemetry = None

from rtmt import RTMiddleTier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicerag")


RUNNING_IN_PRODUCTION = os.getenv("RUNNING_IN_PRODUCTION", "false").lower() == "true"
HOST = "0.0.0.0" if RUNNING_IN_PRODUCTION else "localhost"
PORT = 8000

async def create_app():
    if not os.environ.get("RUNNING_IN_PRODUCTION"):
        logger.info("Running in development mode, loading from .env file")
        load_dotenv()

    llm_key = os.environ.get("AZURE_OPENAI_API_KEY")
    search_key = os.environ.get("AZURE_SEARCH_API_KEY")
    logger.info("Loading environment variables:")
    for key, value in os.environ.items():
        logger.info(f"{key}: {value}")

    credential = None
    if not llm_key or not search_key:
        if tenant_id := os.environ.get("AZURE_TENANT_ID"):
            logger.info("Using AzureDeveloperCliCredential with tenant_id %s", tenant_id)
            credential = AzureDeveloperCliCredential(tenant_id=tenant_id, process_timeout=60)
        else:
            logger.info("Using DefaultAzureCredential")
            credential = DefaultAzureCredential()
    llm_credential = AzureKeyCredential(llm_key) if llm_key else credential
    search_credential = AzureKeyCredential(search_key) if search_key else credential
    
    app = web.Application()
    rtmt = RTMiddleTier(
        credentials=llm_credential,
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment=os.environ["AZURE_OPENAI_REALTIME_DEPLOYMENT"],
        voice_choice=os.environ.get("AZURE_OPENAI_REALTIME_VOICE_CHOICE") or "alloy",
        )
    rtmt.system_message = "Vous êtes un conseiller en assurance bienveillant et professionnel pour MAIF et MAAF. Vous répondez uniquement aux questions basées sur les informations de la base de connaissances, accessible avec l'outil 'search'. " + \
                          "L'utilisateur écoute vos réponses en audio, il est donc *essentiel* que les réponses soient courtes et claires, idéalement une phrase si possible. " + \
                          "Ne jamais mentionner les noms de fichiers, sources ou clés à voix haute. " + \
                          "Règles de fonctionnement à respecter : \n" + \
                          "- Vous pouvez répondre en français et en anglais selon la langue utilisée par l'utilisateur \n" + \
                          "- Vous êtes un conseiller pour les assurances MAIF et MAAF uniquement \n" + \
                          "- Adoptez un ton professionnel, rassurant et empathique, comme un vrai conseiller en assurance \n" + \
                          "- Toujours vouvoyer les clients et utiliser 'Madame' ou 'Monsieur' selon le contexte approprié \n" + \
                          "- Ne jamais tutoyer, maintenir un langage soutenu et respectueux \n" + \
                          "- Toujours utiliser l'outil 'search' pour rechercher dans la base de connaissances avant de répondre \n" + \
                          "- Toujours utiliser l'outil 'report_grounding' pour citer la source des informations de la base de connaissances \n" + \
                          "- Utilisez les outils API disponibles pour récupérer les informations clients : \n" + \
                          "  * Outil 'get_policies' pour consulter les polices d'assurance \n" + \
                          "  * Outil 'get_claims' pour consulter les sinistres déclarés \n" + \
                          "  * Outil 'get_agencies' pour trouver les agences locales \n" + \
                          "  * Outil 'get_contact_info' pour les informations de contact MAIF/MAAF \n" + \
                          "- Couvrez tous les domaines MAIF/MAAF : auto, habitation, moto, assurance vie, retraite, prévoyance, santé \n" + \
                          "- Pour les déclarations de sinistre, orientez vers les canaux officiels (applications mobile, numéros de téléphone) \n" + \
                          "- Soyez précis sur les garanties, franchises et modalités d'indemnisation \n" + \
                          "- Si l'information n'est pas dans la base de connaissances, dites-le clairement et orientez vers un conseiller \n" + \
                          "- Réponses les plus courtes possibles tout en restant informatives et utiles \n" + \
                          "- En fin de conversation, vous pouvez dire 'Merci de votre confiance en MAIF/MAAF, nous sommes là pour vous protéger' \n" + \
                          "- Maintenez toujours un ton professionnel et bienveillant, caractéristique du service client MAIF/MAAF"


    attach_rag_tools(rtmt,
        credentials=search_credential,
        search_endpoint=os.environ.get("AZURE_SEARCH_ENDPOINT"),
        search_index=os.environ.get("AZURE_SEARCH_INDEX"),
        semantic_configuration=os.environ.get("AZURE_SEARCH_SEMANTIC_CONFIGURATION") or "default",
        identifier_field=os.environ.get("AZURE_SEARCH_IDENTIFIER_FIELD") or "chunk_id",
        content_field=os.environ.get("AZURE_SEARCH_CONTENT_FIELD") or "chunk",
        embedding_field=os.environ.get("AZURE_SEARCH_EMBEDDING_FIELD") or "text_vector",
        title_field=os.environ.get("AZURE_SEARCH_TITLE_FIELD") or "title",
        use_vector_query=(os.environ.get("AZURE_SEARCH_USE_VECTOR_QUERY") == "true") or True
        )

    rtmt.attach_to_app(app, "/realtime")
    
    # Add telemetry endpoint
    async def telemetry_handler(request):
        if telemetry:
            data = telemetry.get_telemetry_data()
            return web.json_response(data)
        else:
            return web.json_response({"error": "Telemetry not available"}, status=503)
    
    app.router.add_get('/api/telemetry', telemetry_handler)
    
    current_directory = Path(__file__).parent
    app.add_routes([web.get('/', lambda _: web.FileResponse(current_directory / 'static/index.html'))])
    app.router.add_static('/', path=current_directory / 'static', name='static')
    return app


if __name__ == "__main__":
    host = HOST
    port = 8000
    app = create_app()
    web.run_app(app, host=host, port=port)

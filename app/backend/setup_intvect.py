import json
import logging
import os
import subprocess

import json
import logging
import os
import subprocess
import uuid

from azure.core.exceptions import ResourceExistsError, HttpResponseError
from azure.identity import AzureDeveloperCliCredential, get_bearer_token_provider, DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    AzureOpenAIParameters,
    AzureOpenAIVectorizer,
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from rich.logging import RichHandler
from openai import AzureOpenAI
import uuid
import json


def load_azd_env():
    """Get path to current azd env file and load file using python-dotenv"""
    result = subprocess.run("azd env list -o json", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("Error loading azd env")
    env_json = json.loads(result.stdout)
    env_file_path = None
    for entry in env_json:
        if entry["IsDefault"]:
            env_file_path = entry["DotEnvPath"]
    if not env_file_path:
        raise Exception("No default azd env file found")
    logger.info(f"Loading azd env from {env_file_path}")
    load_dotenv(env_file_path, override=True)


def setup_index(azure_credential, index_name, azure_search_endpoint, azure_storage_connection_string, azure_storage_container, azure_openai_embedding_endpoint, azure_openai_embedding_deployment, azure_openai_embedding_model, azure_openai_embeddings_dimensions):
    index_client = SearchIndexClient(azure_search_endpoint, azure_credential)

    try:
        index_names = [index.name for index in index_client.list_indexes()]
        if index_name in index_names:
            logger.info(f"Index {index_name} already exists, not re-creating")
        else:
            logger.info(f"Creating index: {index_name}")
            logger.info(f"Using embedding model: {azure_openai_embedding_model} with {azure_openai_embeddings_dimensions} dimensions")
            
            # Create the search index with hybrid search support (semantic + vector)
            search_index = SearchIndex(
                name=index_name,
                fields=[
                    SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True),
                    SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
                    SearchableField(name="title", type=SearchFieldDataType.String, searchable=True),
                    SearchableField(name="chunk", type=SearchFieldDataType.String, searchable=True),
                    SearchField(
                        name="text_vector", 
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        vector_search_dimensions=azure_openai_embeddings_dimensions,
                        vector_search_profile_name="my-vector-config",
                        stored=True,
                        retrievable=True,
                        searchable=True,
                        hidden=False
                    )
                ],
                vector_search=VectorSearch(
                    algorithms=[
                        HnswAlgorithmConfiguration(
                            name="my-hnsw-vector-config",
                            parameters=HnswParameters(
                                metric=VectorSearchAlgorithmMetric.COSINE,
                                m=4,  # Reduced for better memory usage
                                ef_construction=400,
                                ef_search=500
                            )
                        )
                    ],
                    profiles=[
                        VectorSearchProfile(
                            name="my-vector-config",
                            algorithm_configuration_name="my-hnsw-vector-config"
                        )
                    ]
                ),
                semantic_search=SemanticSearch(
                    configurations=[
                        SemanticConfiguration(
                            name="default",
                            prioritized_fields=SemanticPrioritizedFields(
                                title_field=SemanticField(field_name="title"),
                                content_fields=[SemanticField(field_name="chunk")]
                            )
                        )
                    ]
                )
            )
            
            # Create the index
            index_client.create_index(search_index)
            logger.info(f"✅ Successfully created index: {index_name}")
            
    except HttpResponseError as e:
        logger.error(f"❌ HTTP Error creating index: {e}")
        logger.error(f"Status code: {e.status_code}")
        if hasattr(e, 'response') and hasattr(e.response, 'json'):
            try:
                error_details = e.response.json()
                logger.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                logger.error(f"Error response: {e.response.text if hasattr(e.response, 'text') else 'No response text'}")
        raise e
    except Exception as e:
        logger.error(f"❌ Unexpected error creating index: {type(e).__name__}: {e}")
        raise e
    
    # Upload documents after index creation
    upload_documents(azure_credential, index_name, azure_search_endpoint, azure_openai_embedding_endpoint, azure_openai_embedding_deployment)

def upload_documents(azure_credential, index_name, azure_search_endpoint, azure_openai_embedding_endpoint, azure_openai_embedding_deployment):
    try:
        search_client = SearchClient(endpoint=azure_search_endpoint, index_name=index_name, credential=azure_credential)
        
        # Use latest API version for embeddings
        openai_client = AzureOpenAI(
            azure_endpoint=azure_openai_embedding_endpoint,
            azure_deployment=azure_openai_embedding_deployment,
            azure_ad_token_provider=get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default"),
            api_version="2024-06-01"  # Updated API version for better model support
        )

        def generate_embeddings(text):
            try:
                response = openai_client.embeddings.create(
                    input=text,
                    model=azure_openai_embedding_deployment,
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Error generating embedding for text: {text[:100]}...")
                logger.error(f"Embedding error: {e}")
                raise e

        # Check if FAQ file exists
        faq_path = "data/faq.json"
        if not os.path.exists(faq_path):
            # Try relative path from script location
            script_dir = os.path.dirname(os.path.abspath(__file__))
            faq_path = os.path.join(script_dir, "..", "..", "data", "faq.json")
            
        if not os.path.exists(faq_path):
            logger.error(f"❌ FAQ file not found at {faq_path}")
            logger.info("Please ensure the data/faq.json file exists in your project root")
            return
            
        logger.info(f"Loading FAQ data from: {faq_path}")
        
        with open(faq_path, "r", encoding="utf-8") as file:
            faq = json.load(file)
            faq_documents = []

            logger.info(f"Processing {len(faq)} FAQ items for embedding...")
            
            for i, item in enumerate(faq):
                try:
                    logger.info(f"Processing item {i+1}/{len(faq)}: {item.get('title', 'Unknown')[:50]}...")
                    
                    embedding_vector = generate_embeddings(item["chunk"])
                    
                    faq_documents.append({
                        "chunk_id": str(uuid.uuid4()),
                        "category": item.get("category", "General"),
                        "title": item.get("title", ""),
                        "chunk": item.get("chunk", ""),
                        "text_vector": embedding_vector
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing FAQ item {i+1}: {e}")
                    continue
            
            if faq_documents:
                logger.info(f"Uploading {len(faq_documents)} documents to Azure AI Search index {index_name}...")
                search_client.upload_documents(faq_documents)
                logger.info(f'✅ Successfully uploaded {len(faq_documents)} documents to Azure AI Search index {index_name}')
            else:
                logger.error("❌ No documents were processed successfully")
                
    except Exception as e:
        logger.error(f"❌ Error uploading documents: {type(e).__name__}: {e}")
        raise e



if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)])
    logger = logging.getLogger("voicerag")
    logger.setLevel(logging.INFO)

    try:
        load_azd_env()
        
        logger.info("🔍 Checking if we need to set up Azure AI Search index...")
        if os.environ.get("AZURE_SEARCH_REUSE_EXISTING") == "true":
            logger.info("Since an existing Azure AI Search index is being used, no changes will be made to the index.")
            exit()
        else:
            logger.info("🚀 Setting up Azure AI Search index and integrated vectorization...")

        # Required environment variables
        required_env_vars = [
            "AZURE_SEARCH_INDEX",
            "AZURE_OPENAI_ENDPOINT", 
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
            "AZURE_OPENAI_EMBEDDING_MODEL",
            "AZURE_SEARCH_ENDPOINT",
            "AZURE_STORAGE_ENDPOINT",
            "AZURE_STORAGE_CONNECTION_STRING", 
            "AZURE_STORAGE_CONTAINER"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please make sure you have run 'azd up' and the deployment is complete.")
            exit(1)

        # Load configuration
        AZURE_SEARCH_INDEX = os.environ["AZURE_SEARCH_INDEX"]
        AZURE_OPENAI_EMBEDDING_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
        AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]
        AZURE_OPENAI_EMBEDDING_MODEL = os.environ["AZURE_OPENAI_EMBEDDING_MODEL"]
        EMBEDDINGS_DIMENSIONS = 3072  # text-embedding-3-large dimensions
        AZURE_SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
        AZURE_STORAGE_ENDPOINT = os.environ["AZURE_STORAGE_ENDPOINT"]
        AZURE_STORAGE_CONNECTION_STRING = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        AZURE_STORAGE_CONTAINER = os.environ["AZURE_STORAGE_CONTAINER"]

        logger.info(f"📋 Configuration:")
        logger.info(f"  - Search Index: {AZURE_SEARCH_INDEX}")
        logger.info(f"  - Embedding Model: {AZURE_OPENAI_EMBEDDING_MODEL}")
        logger.info(f"  - Embedding Deployment: {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
        logger.info(f"  - Embedding Dimensions: {EMBEDDINGS_DIMENSIONS}")
        logger.info(f"  - Search Endpoint: {AZURE_SEARCH_ENDPOINT}")

        # Try AzureDeveloperCliCredential first, then DefaultAzureCredential
        azure_credential = None
        try:
            logger.info("🔐 Attempting authentication with Azure Developer CLI...")
            azure_credential = AzureDeveloperCliCredential(
                tenant_id=os.environ.get("AZURE_TENANT_ID"),
                process_timeout=60
            )
            # Test the credential
            from azure.search.documents.indexes import SearchIndexClient
            test_client = SearchIndexClient(AZURE_SEARCH_ENDPOINT, azure_credential)
            list(test_client.list_indexes())  # This will fail if credential doesn't work
            logger.info("✅ Azure Developer CLI authentication successful")
        except Exception as e:
            logger.warning(f"⚠️ Azure Developer CLI authentication failed: {e}")
            logger.info("🔐 Trying DefaultAzureCredential...")
            try:
                azure_credential = DefaultAzureCredential()
                # Test the credential
                test_client = SearchIndexClient(AZURE_SEARCH_ENDPOINT, azure_credential)
                list(test_client.list_indexes())  # This will fail if credential doesn't work
                logger.info("✅ DefaultAzureCredential authentication successful")
            except Exception as e2:
                logger.error(f"❌ DefaultAzureCredential also failed: {e2}")
                logger.error("Please ensure you're authenticated with 'az login' or 'azd auth login'")
                exit(1)

        # Setup the index and upload documents
        setup_index(azure_credential,
            index_name=AZURE_SEARCH_INDEX, 
            azure_search_endpoint=AZURE_SEARCH_ENDPOINT,
            azure_storage_connection_string=AZURE_STORAGE_CONNECTION_STRING,
            azure_storage_container=AZURE_STORAGE_CONTAINER,
            azure_openai_embedding_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT,
            azure_openai_embedding_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            azure_openai_embedding_model=AZURE_OPENAI_EMBEDDING_MODEL,
            azure_openai_embeddings_dimensions=EMBEDDINGS_DIMENSIONS)

        logger.info("🎉 Index setup and document upload completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("⚠️ Operation cancelled by user")
        exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {type(e).__name__}: {e}")
        logger.error("Please check the logs above for more details")
        exit(1)
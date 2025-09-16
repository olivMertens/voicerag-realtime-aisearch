import re, httpx, os
from typing import Any
import logging
import time
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
from rtmt import RTMiddleTier, Tool, ToolResult, ToolResultDirection
from openai import AzureOpenAI

# Import telemetry
try:
    from telemetry import telemetry
except ImportError:
    # Fallback if OpenTelemetry is not available
    class DummyTelemetry:
        def trace_tool_call(self, *args, **kwargs): pass
        def trace_model_call(self, *args, **kwargs): pass
        def trace_search_operation(self, *args, **kwargs): pass
        def get_telemetry_data(self): return {"tool_calls": [], "model_calls": [], "stats": {}}
    
    telemetry = DummyTelemetry()
from dotenv import load_dotenv
from rtmt import RTMiddleTier, Tool, ToolResult, ToolResultDirection
from openai import AzureOpenAI
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("toolingCall")

if not os.environ.get("RUNNING_IN_PRODUCTION"):
    logger.info("Running in development mode, loading from .env file")
    load_dotenv()
else:
    logger.info("Running in production mode")


AZURE_API_ENDPOINT = os.environ.get("AZURE_API_ENDPOINT")

_search_tool_schema = {
    "type": "function",
    "name": "search",
    "description": "Search the knowledge base. The knowledge base is in English, translate to and from English if " + \
                   "needed. Results are formatted as a source name first in square brackets, followed by the text " + \
                   "content, and a line with '-----' at the end of each result.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            }
        },
        "required": ["query"],
        "additionalProperties": False
    }
}

_grounding_tool_schema = {
    "type": "function",
    "name": "report_grounding",
    "description": "Report use of a source from the knowledge base as part of an answer (effectively, cite the source). Sources " + \
                   "appear in square brackets before each knowledge base passage. Always use this tool to cite sources when responding " + \
                   "with information from the knowledge base.",
    "parameters": {
        "type": "object",
        "properties": {
            "sources": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of source names from last statement actually used, do not include the ones not used to formulate a response"
            }
        },
        "required": ["sources"],
        "additionalProperties": False
    }
}

_policy_tool_schema = {
    "type": "function",
    "name": "get_policies",
    "description": "Retrieve insurance policy information for MAAF and MAIF customers. Each policy includes holder details, coverage type, premiums, vehicle/property information, and status.",
    "parameters": {
        "type": "object",
        "properties": {
            "policy_number": {
                "type": "string",
                "description": "Policy number (e.g., MAA-2025-001234, MIF-2025-005678)"
            },
            "name": {
                "type": "string",
                "description": "Name of the policyholder"
            },
            "policy_type": {
                "type": "string",
                "description": "Type of policy (Auto, Habitation, Santé, Professionnelle, Vie, Moto, Jeune, Voyage)"
            }
        },
        "required": [],
        "additionalProperties": False
    }
}

_claims_tool_schema = {
    "type": "function",
    "name": "get_claims",
    "description": "Retrieve insurance claim information for MAAF and MAIF policies. Each claim includes claim number, policy details, type, amounts, status, and processing information.",
    "parameters": {
        "type": "object",
        "properties": {
            "claim_number": {
                "type": "string",
                "description": "Claim ID (e.g., CLM-2024-789, SNT-2024-456)"
            },
            "policy_number": {
                "type": "string",
                "description": "Associated policy number"
            },
            "holder_name": {
                "type": "string",
                "description": "Name of the policyholder"
            },
            "claim_type": {
                "type": "string",
                "description": "Type of claim (Collision, Dégât des eaux, Vol, etc.)"
            }
        },
        "required": [],
        "additionalProperties": False
    }
}

_real_policy_tool_schema = {
    "type": "function",
    "name": "get_real_policies",
    "description": "Retrieve comprehensive real-time policy information from the MAAF/MAIF system database, including detailed coverage limits, payment history, and current status.",
    "parameters": {
        "type": "object",
        "properties": {
            "policy_type": {
                "type": "string",
                "description": "Filter by policy type (Auto, Habitation, Santé, Professionnelle, Vie, Moto, Jeune, Voyage)"
            },
            "status": {
                "type": "string",
                "description": "Filter by policy status (active, suspended, expired, pending_claim)"
            },
            "holder_name": {
                "type": "string",
                "description": "Policyholder name to search for"
            }
        },
        "required": [],
        "additionalProperties": False
    }
}

_agency_tool_schema = {
    "type": "function",
    "name": "get_agencies",
    "description": "Retrieve MAAF and MAIF agency information including contact details, locations, and agent information for customer service.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City to find nearby agencies (e.g., Lyon, Paris, Bordeaux)"
            },
            "agent_name": {
                "type": "string",
                "description": "Name of specific insurance agent"
            }
        },
        "required": [],
        "additionalProperties": False
    }
}

_contact_tool_schema = {
    "type": "function",
    "name": "get_contact_info",
    "description": "Retrieve MAAF and MAIF contact information including phone numbers for customer service, claims, emergencies, and specific departments.",
    "parameters": {
        "type": "object",
        "properties": {
            "service_type": {
                "type": "string",
                "description": "Type of service needed (customer_service, claims, emergency, roadside_assistance)"
            },
            "company": {
                "type": "string",
                "description": "Insurance company (MAAF or MAIF)"
            }
        },
        "required": [],
        "additionalProperties": False
    }
}

async def _search_tool(
    search_client: SearchClient, 
    semantic_configuration: str,
    identifier_field: str,
    content_field: str,
    embedding_field: str,
    use_vector_query: bool,
    args: Any) -> ToolResult:
    start_time = time.time()
    print(f"Searching for '{args['query']}' in the knowledge base.")
    
    # Trace the search operation
    with telemetry.trace_search_operation(args['query'], 0, "hybrid") as search_span:
        # Hybrid search: semantic + vector queries for best results
        vector_queries = []
        embedding_time = 0
        
        if use_vector_query:
            # Generate embedding for the query using Azure OpenAI
            try:
                embedding_start = time.time()
                
                # Get Azure OpenAI credentials from environment
                embedding_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
                embedding_deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
                
                # Create Azure OpenAI client for embeddings
                openai_client = AzureOpenAI(
                    azure_endpoint=embedding_endpoint,
                    azure_deployment=embedding_deployment,
                    azure_ad_token_provider=get_bearer_token_provider(
                        search_client._credential, 
                        "https://cognitiveservices.azure.com/.default"
                    ),
                    api_version="2024-06-01"
                )
                
                # Generate embedding for the search query
                response = openai_client.embeddings.create(
                    input=args['query'],
                    model=embedding_deployment,
                )
                query_vector = response.data[0].embedding
                embedding_time = time.time() - embedding_start
                
                # Trace the model call
                telemetry.trace_model_call(
                    model_name=embedding_deployment,
                    operation="embedding_generation",
                    tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None,
                    latency=embedding_time
                )
                
                # Use VectorizedQuery with pre-computed embeddings (no vectorizer needed)
                vector_queries.append(VectorizedQuery(
                    vector=query_vector, 
                    k_nearest_neighbors=50, 
                    fields=embedding_field
                ))
                print(f"✅ Generated vector query with {len(query_vector)} dimensions in {embedding_time:.3f}s")
                
            except Exception as e:
                print(f"⚠️ Warning: Failed to generate vector query: {e}. Using semantic search only.")

        # Execute hybrid search (semantic + vector)
        search_results = await search_client.search(
            search_text=args['query'], 
            query_type="semantic",
            semantic_configuration_name=semantic_configuration,
            top=5,
            vector_queries=vector_queries,
            select=", ".join([identifier_field, content_field])
        )
        
        result = ""
        result_count = 0
        async for r in search_results:
            result += f"[{r[identifier_field]}]: {r[content_field]}\n-----\n"
            result_count += 1
        
        # Update search span with results
        search_span.set_attribute("search.results_count", result_count)
        
        # Trace the complete search tool call
        search_duration = time.time() - start_time
        telemetry.trace_tool_call("search", args, search_duration)
        
        print(f"🔍 Search completed: {result_count} results in {search_duration:.3f}s")
        
        return ToolResult(result, ToolResultDirection.TO_SERVER)

KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_=\-]+$')

# TODO: move from sending all chunks used for grounding eagerly to only sending links to 
# the original content in storage, it'll be more efficient overall
async def _report_grounding_tool(search_client: SearchClient, identifier_field: str, title_field: str, content_field: str, args: Any) -> None:
    sources = [s for s in args["sources"] if KEY_PATTERN.match(s)]
    list = " OR ".join(sources)
    print(f"Grounding source: {list}")
    # Use search instead of filter to align with how detailt integrated vectorization indexes
    # are generated, where chunk_id is searchable with a keyword tokenizer, not filterable 
    search_results = await search_client.search(search_text=list, 
                                                search_fields=[identifier_field], 
                                                select=[identifier_field, title_field, content_field], 
                                                top=len(sources), 
                                                query_type="full")
    
    # If your index has a key field that's filterable but not searchable and with the keyword analyzer, you can 
    # use a filter instead (and you can remove the regex check above, just ensure you escape single quotes)
    # search_results = await search_client.search(filter=f"search.in(chunk_id, '{list}')", select=["chunk_id", "title", "chunk"])

    docs = []
    async for r in search_results:
        docs.append({"chunk_id": r[identifier_field], "title": r[title_field], "chunk": r[content_field]})
    return ToolResult({"sources": docs}, ToolResultDirection.TO_CLIENT)

async def _policy_tool(args: Any) -> ToolResult:
    start_time = time.time()
    print(f"Retrieving policies for policy '{args.get('policy_number')}', name '{args.get('name')}', and type '{args.get('policy_type')}'.")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_API_ENDPOINT+"/api/policies", params=args)
            response.raise_for_status()
            policies = response.json()
        
        # Trace the tool call
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_policies", args, duration)
        
        return ToolResult({"policies": policies}, ToolResultDirection.TO_SERVER)
    except Exception as e:
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_policies", args, duration)
        raise e

async def _claims_tool(args: Any) -> ToolResult:
    start_time = time.time()
    print(f"Retrieving claims for claim '{args.get('claim_number')}', policy '{args.get('policy_number')}', and holder '{args.get('holder_name')}'.")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_API_ENDPOINT+"/api/claims", params=args)
            response.raise_for_status()
            claims = response.json()
        
        # Trace the tool call
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_claims", args, duration)
        
        return ToolResult({"claims": claims}, ToolResultDirection.TO_SERVER)
    except Exception as e:
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_claims", args, duration)
        raise e

async def _real_policy_tool(args: Any) -> ToolResult:
    start_time = time.time()
    print(f"Retrieving real-time policies with params: {args}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_API_ENDPOINT+"/api/realtime/policies", params=args)
            response.raise_for_status()
            policies = response.json()
        
        # Trace the tool call
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_real_policies", args, duration)
        
        return ToolResult({"real_policies": policies}, ToolResultDirection.TO_SERVER)
    except Exception as e:
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_real_policies", args, duration)
        raise e

async def _agency_tool(args: Any) -> ToolResult:
    start_time = time.time()
    print(f"Retrieving agency information for city: {args.get('city')}, agent: {args.get('agent_name')}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_API_ENDPOINT+"/api/agencies", params=args)
            response.raise_for_status()
            agencies = response.json()
        
        # Trace the tool call
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_agencies", args, duration)
        
        return ToolResult({"agencies": agencies}, ToolResultDirection.TO_SERVER)
    except Exception as e:
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_agencies", args, duration)
        raise e

async def _contact_tool(args: Any) -> ToolResult:
    start_time = time.time()
    print(f"Retrieving contact information for service: {args.get('service_type')}, company: {args.get('company')}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_API_ENDPOINT+"/api/contact", params=args)
            response.raise_for_status()
            contacts = response.json()
        
        # Trace the tool call
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_contact_info", args, duration)
        
        return ToolResult({"contact_info": contacts}, ToolResultDirection.TO_SERVER)
    except Exception as e:
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_contact_info", args, duration)
        raise e

def attach_rag_tools(rtmt: RTMiddleTier,
    credentials: AzureKeyCredential | DefaultAzureCredential,
    search_endpoint: str, search_index: str,
    semantic_configuration: str,
    identifier_field: str,
    content_field: str,
    embedding_field: str,
    title_field: str,
    use_vector_query: bool
    ) -> None:
    if not isinstance(credentials, AzureKeyCredential):
        credentials.get_token("https://search.azure.com/.default") # warm this up before we start getting requests
    search_client = SearchClient(search_endpoint, search_index, credentials, user_agent="RTMiddleTier")
    logger.info("Attaching Rag tool")
    rtmt.tools["search"] = Tool(schema=_search_tool_schema, target=lambda args: _search_tool(search_client, semantic_configuration, identifier_field, content_field, embedding_field, use_vector_query, args))
    rtmt.tools["report_grounding"] = Tool(schema=_grounding_tool_schema, target=lambda args: _report_grounding_tool(search_client, identifier_field, title_field, content_field, args))
    
    logger.info("Attaching policy tool")
    rtmt.tools["get_policies"] = Tool(schema=_policy_tool_schema, target=lambda args: _policy_tool(args))

    logger.info("Attaching claims tool")
    rtmt.tools["get_claims"] = Tool(schema=_claims_tool_schema, target=lambda args: _claims_tool(args))
    
    logger.info("Attaching real-time insurance API tools")
    rtmt.tools["get_real_policies"] = Tool(schema=_real_policy_tool_schema, target=lambda args: _real_policy_tool(args))
    rtmt.tools["get_agencies"] = Tool(schema=_agency_tool_schema, target=lambda args: _agency_tool(args))
    rtmt.tools["get_contact_info"] = Tool(schema=_contact_tool_schema, target=lambda args: _contact_tool(args))
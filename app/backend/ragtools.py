import re, httpx, os
from typing import Any
import asyncio
import json
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
from openai import AzureOpenAI
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("toolingCall")

if not os.environ.get("RUNNING_IN_PRODUCTION"):
    logger.info("Running in development mode, loading from .env file")
    load_dotenv()
else:
    logger.info("Running in production mode")


AZURE_API_ENDPOINT = os.environ.get("AZURE_API_ENDPOINT")

# Validate API endpoint configuration
if not AZURE_API_ENDPOINT:
    logger.warning("AZURE_API_ENDPOINT environment variable is not set. Insurance API tools will be unavailable.")
else:
    logger.info(f"Insurance API endpoint configured: {AZURE_API_ENDPOINT}")

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
                   "with information from the knowledge base. This will display the referenced FAQ entries to the user for transparency.",
    "parameters": {
        "type": "object",
        "properties": {
            "sources": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of source chunk IDs from the last search results that were actually used to formulate the response. Do not include sources that were not used."
            },
            "confidence_level": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "Confidence level in the information provided based on source quality and relevance"
            },
            "summary": {
                "type": "string",
                "description": "Brief summary of what information was extracted from these sources (optional but recommended for UI display)"
            }
        },
        "required": ["sources"],
        "additionalProperties": False
    }
}

_policy_tool_schema = {
    "type": "function",
    "name": "get_policies",
    "description": "Retrieve insurance policy information for Contoso demo customers. Each policy includes holder details, coverage type, premiums, vehicle/property information, and status. Supports flexible name search by full name, first name, or last name.",
    "parameters": {
        "type": "object",
        "properties": {
            "policy_number": {
                "type": "string",
                "description": "Policy number (e.g., CONTOSO-AUTO-001, CONTOSO-HAB-002)"
            },
            "name": {
                "type": "string",
                "description": "Full name or partial name of the policyholder (e.g., 'Jean Dupont', 'Jean', 'Dupont')"
            },
            "first_name": {
                "type": "string",
                "description": "First name of the policyholder (e.g., 'Jean', 'Marie')"
            },
            "last_name": {
                "type": "string",
                "description": "Last name of the policyholder (e.g., 'Dupont', 'Martin')"
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
    "description": "Retrieve insurance claim information for Contoso demo policies. Each claim includes claim number, policy details, type, amounts, status, and processing information. Supports flexible name search by full name, first name, or last name.",
    "parameters": {
        "type": "object",
        "properties": {
            "claim_number": {
                "type": "string",
                "description": "Claim ID (e.g., CLAIM-001, CLAIM-002)"
            },
            "policy_number": {
                "type": "string",
                "description": "Associated policy number (e.g., CONTOSO-AUTO-001)"
            },
            "holder_name": {
                "type": "string",
                "description": "Full name or partial name of the policyholder (e.g., 'Jean Dupont', 'Jean', 'Dupont')"
            },
            "first_name": {
                "type": "string",
                "description": "First name of the claim holder (e.g., 'Jean', 'Marie')"
            },
            "last_name": {
                "type": "string",
                "description": "Last name of the claim holder (e.g., 'Dupont', 'Martin')"
            },
            "claim_type": {
                "type": "string",
                "description": "Type of claim (Auto, Collision, Dégât des eaux, Vol, Bris de glace, Tempête, etc.)"
            }
        },
        "required": [],
        "additionalProperties": False
    }
}

_real_policy_tool_schema = {
    "type": "function",
    "name": "get_real_policies",
    "description": "Retrieve comprehensive real-time policy information from the Contoso demo system database, including detailed coverage limits, payment history, and current status. Supports flexible name search.",
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
                "description": "Full name or partial name of the policyholder (e.g., 'Jean Dupont', 'Jean', 'Dupont')"
            },
            "first_name": {
                "type": "string",
                "description": "First name of the policyholder (e.g., 'Jean', 'Marie')"
            },
            "last_name": {
                "type": "string",
                "description": "Last name of the policyholder (e.g., 'Dupont', 'Martin')"
            }
        },
        "required": [],
        "additionalProperties": False
    }
}

_agency_tool_schema = {
    "type": "function",
    "name": "get_agencies",
    "description": "Retrieve Contoso agency information including contact details, locations, and agent information for customer service.",
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
    "description": "Retrieve Contoso contact information including phone numbers for customer service, claims, emergencies, and specific departments.",
    "parameters": {
        "type": "object",
        "properties": {
            "service_type": {
                "type": "string",
                "description": "Type of service needed (customer_service, claims, emergency, roadside_assistance)"
            },
            "company": {
                "type": "string",
                "description": "Insurance company (e.g., Contoso)"
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
    
    logger.info(f"🔍 SEARCH TOOL CALLED - Query: '{args['query']}'")
    logger.info(f"📊 Search Config: semantic_config={semantic_configuration}, use_vector={use_vector_query}")
    logger.info(f"📋 Fields: id={identifier_field}, content={content_field}, embedding={embedding_field}")
    print(f"🔍 Searching for '{args['query']}' in the knowledge base.")
    
    # Trace the search operation
    with telemetry.trace_search_operation(args['query'], 0, "hybrid") as search_span:
        # Enhanced hybrid search: semantic + vector queries with optimized parameters
        vector_queries = []
        embedding_time = 0
        
        if use_vector_query:
            # Generate embedding for the query using Azure OpenAI with enhanced error handling
            try:
                embedding_start = time.time()
                
                # Get Azure OpenAI credentials from environment
                embedding_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
                embedding_deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
                
                if not embedding_endpoint or not embedding_deployment:
                    logger.warning("⚠️ Missing embedding configuration, skipping vector search")
                else:
                    # Create Azure OpenAI client for embeddings with retry logic
                    openai_client = AzureOpenAI(
                        azure_endpoint=embedding_endpoint,
                        azure_deployment=embedding_deployment,
                        azure_ad_token_provider=get_bearer_token_provider(
                            search_client._credential, 
                            "https://cognitiveservices.azure.com/.default"
                        ),
                        api_version="2024-06-01",
                        max_retries=3,
                        timeout=30.0
                    )
                    
                    # Generate embedding for the search query with enhanced input processing
                    # Truncate query if too long for embedding model (max 8191 tokens for text-embedding-3-large)
                    query_text = args['query'][:4000]  # Conservative token limit
                    
                    response = openai_client.embeddings.create(
                        input=query_text,
                        model=embedding_deployment,
                        dimensions=None  # Use model's native dimensions for best quality
                    )
                    query_vector = response.data[0].embedding
                    embedding_time = time.time() - embedding_start
                    
                    # Trace the model call with enhanced details
                    telemetry.trace_model_call(
                        model_name=embedding_deployment,
                        operation="embedding_generation",
                        tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None,
                        latency=embedding_time,
                        prompt=query_text,
                        response=f"Generated {len(query_vector)} dimensional vector"
                    )
                    
                    # Enhanced VectorizedQuery with optimized parameters for better relevance
                    vector_queries.append(VectorizedQuery(
                        vector=query_vector, 
                        k_nearest_neighbors=25,  # Optimized for quality vs performance
                        fields=embedding_field,
                        weight=0.5  # Balance between vector and text search
                    ))
                    logger.info(f"✅ Generated optimized vector query: {len(query_vector)}D in {embedding_time:.3f}s")
                
            except Exception as e:
                logger.warning(f"⚠️ Vector embedding failed: {str(e)[:100]}... Continuing with semantic search only")
                # Don't raise - continue with semantic search

        # Execute enhanced hybrid search with semantic ranking and answer generation
        try:
            logger.info(f"🔎 Executing enhanced hybrid search with {len(vector_queries)} vector queries")
            
            # Primary search with full semantic capabilities
            search_results = await search_client.search(
                search_text=args['query'],
                query_type="semantic",
                semantic_configuration_name=semantic_configuration,
                search_fields=[content_field, "title"],  # Only search in searchable fields
                query_answer="extractive|count-3",  # Generate semantic answers
                query_answer_highlight=True,  # Highlight answer passages
                query_caption="extractive|highlight-true",  # Generate captions with highlights
                top=10,  # Get more results for better ranking
                vector_queries=vector_queries,
                select=", ".join([identifier_field, content_field, "title", "category"]),
                scoring_statistics=True,  # Include scoring statistics
                session_id=f"search_{int(time.time())}"  # Session for semantic ranking consistency
            )
            
            # Process results with enhanced metadata and semantic information
            result = ""
            sources_metadata = []
            result_count = 0
            semantic_answers = []
            
            # Process semantic answers first (if available)
            if hasattr(search_results, 'get_answers') and callable(search_results.get_answers):
                try:
                    answers = await search_results.get_answers()
                    for answer in answers:
                        semantic_answers.append({
                            "text": answer.text,
                            "score": getattr(answer, 'score', 0.0),
                            "highlights": getattr(answer, 'highlights', [])
                        })
                        logger.info(f"🎯 Semantic answer found: {answer.text[:100]}... (score: {getattr(answer, 'score', 'N/A')})")
                except Exception as e:
                    logger.debug(f"Could not retrieve semantic answers: {e}")
            
            # Process search results with enhanced scoring
            async for r in search_results:
                # Enhanced result processing with semantic information
                search_score = getattr(r, '@search.score', 0.0)
                reranker_score = getattr(r, '@search.reranker_score', None)
                captions = getattr(r, '@search.captions', [])
                
                # Build result content with semantic enhancements
                result_text = r[content_field]
                if captions:
                    # Use caption if available for better relevance
                    caption_text = captions[0].text if captions else result_text
                    result_text = caption_text
                
                result += f"[{r[identifier_field]}]: {result_text}\n-----\n"
                
                # Enhanced metadata with scoring and semantic information
                source_metadata = {
                    "id": r[identifier_field],
                    "content": r[content_field],
                    "title": r.get("title", ""),
                    "category": r.get("category", ""),
                    "search_score": search_score,
                    "reranker_score": reranker_score,
                    "excerpt": result_text[:300] + "..." if len(result_text) > 300 else result_text,
                    "captions": [{"text": cap.text, "highlights": getattr(cap, 'highlights', [])} for cap in captions] if captions else []
                }
                sources_metadata.append(source_metadata)
                
                result_count += 1
                score_info = f"score: {search_score:.3f}" + (f", reranker: {reranker_score:.3f}" if reranker_score else "")
                logger.info(f"📄 Result {result_count}: {r[identifier_field]} - {r.get('title', 'No title')[:50]}... ({score_info})")
            
            # Add enhanced metadata including semantic answers
            enhanced_metadata = {
                "sources": sources_metadata,
                "semantic_answers": semantic_answers,
                "search_stats": {
                    "total_results": result_count,
                    "has_vector_search": len(vector_queries) > 0,
                    "embedding_time": embedding_time
                }
            }
            
            if enhanced_metadata:
                result += f"\n__METADATA__: {json.dumps(enhanced_metadata, ensure_ascii=False)}"
            
            logger.info(f"✅ Enhanced hybrid search completed: {result_count} results with {len(semantic_answers)} semantic answers")
            
        except Exception as e:
            logger.error(f"❌ Enhanced search failed: {e}")
            # Enhanced fallback with multiple strategies
            result, result_count = await _fallback_search_strategies(
                search_client, args['query'], identifier_field, content_field, embedding_field, vector_queries
            )
        
        # Update search span with enhanced metrics
        search_span.set_attribute("search.results_count", result_count)
        search_span.set_attribute("search.has_vector", len(vector_queries) > 0)
        search_span.set_attribute("search.embedding_time", embedding_time)
        
        # Trace the complete search tool call with enhanced details
        search_duration = time.time() - start_time
        
        # Create comprehensive response for telemetry
        search_response = {
            "results_count": result_count,
            "search_type": "hybrid" if vector_queries else "semantic",
            "embedding_time": embedding_time
        }
        
        telemetry.trace_tool_call("search", args, search_duration, search_response, len(result.encode('utf-8')) if result else 0)
        
        logger.info(f"🔍 Enhanced search completed: {result_count} results in {search_duration:.3f}s")
        
        return ToolResult(result, ToolResultDirection.TO_SERVER)

KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_=\-]+$')

async def _fallback_search_strategies(
    search_client: SearchClient,
    query: str,
    identifier_field: str,
    content_field: str,
    embedding_field: str,
    vector_queries: list
) -> tuple[str, int]:
    """
    Enhanced fallback search strategies with multiple approaches
    Returns (result_text, result_count)
    """
    result = ""
    result_count = 0
    
    # Strategy 1: Simple text search without semantic configuration
    try:
        logger.info("🔄 Fallback Strategy 1: Simple text search...")
        search_results = await search_client.search(
            search_text=query,
            search_fields=[content_field, "title"],
            top=8,
            select=", ".join([identifier_field, content_field, "title"]),
            search_mode="any",  # More permissive matching
            query_type="simple"
        )
        
        async for r in search_results:
            result += f"[{r[identifier_field]}]: {r[content_field]}\n-----\n"
            result_count += 1
            logger.info(f"📄 Fallback result {result_count}: {r[identifier_field]}")
        
        if result_count > 0:
            logger.info(f"✅ Fallback Strategy 1 successful: {result_count} results")
            return result, result_count
            
    except Exception as e:
        logger.warning(f"⚠️ Fallback Strategy 1 failed: {e}")
    
    # Strategy 2: Vector search only (if available)
    if vector_queries:
        try:
            logger.info("🔄 Fallback Strategy 2: Vector search only...")
            search_results = await search_client.search(
                search_text="*",  # Wildcard for vector-only search
                vector_queries=vector_queries,
                top=6,
                select=", ".join([identifier_field, content_field, "title"])
            )
            
            async for r in search_results:
                result += f"[{r[identifier_field]}]: {r[content_field]}\n-----\n"
                result_count += 1
                logger.info(f"📄 Vector fallback result {result_count}: {r[identifier_field]}")
            
            if result_count > 0:
                logger.info(f"✅ Fallback Strategy 2 successful: {result_count} vector results")
                return result, result_count
                
        except Exception as e:
            logger.warning(f"⚠️ Fallback Strategy 2 failed: {e}")
    
    # Strategy 3: Keyword-based search with OR logic
    try:
        logger.info("🔄 Fallback Strategy 3: Keyword-based search...")
        # Extract keywords from query
        keywords = [word.strip() for word in query.split() if len(word.strip()) > 2][:5]
        if keywords:
            keyword_query = " OR ".join(keywords)
            search_results = await search_client.search(
                search_text=keyword_query,
                search_fields=[content_field, "title"],
                top=5,
                select=", ".join([identifier_field, content_field])
            )
            
            async for r in search_results:
                result += f"[{r[identifier_field]}]: {r[content_field]}\n-----\n"
                result_count += 1
                logger.info(f"📄 Keyword fallback result {result_count}: {r[identifier_field]}")
            
            if result_count > 0:
                logger.info(f"✅ Fallback Strategy 3 successful: {result_count} keyword results")
                return result, result_count
        
    except Exception as e:
        logger.warning(f"⚠️ Fallback Strategy 3 failed: {e}")
    
    # Final fallback: Return helpful error message
    logger.error("❌ All fallback strategies failed")
    result = "Je n'ai pas pu trouver d'informations pertinentes dans la base de connaissances. Veuillez reformuler votre question ou contacter un conseiller pour une assistance personnalisée."
    return result, 0

# TODO: move from sending all chunks used for grounding eagerly to only sending links to 
# the original content in storage, it'll be more efficient overall
async def _report_grounding_tool(search_client: SearchClient, identifier_field: str, title_field: str, content_field: str, args: Any) -> None:
    sources = [s for s in args["sources"] if KEY_PATTERN.match(s)]
    confidence_level = args.get("confidence_level", "medium")
    summary = args.get("summary", "")
    
    print(f"📋 Grounding sources: {sources} (confidence: {confidence_level})")
    
    if not sources:
        logger.warning("No valid sources provided for grounding")
        return ToolResult({
            "sources": [],
            "grounding_info": {
                "total_sources": 0,
                "confidence_level": confidence_level,
                "summary": "No sources were referenced",
                "status": "no_sources"
            }
        }, ToolResultDirection.TO_CLIENT)
    
    try:
        # Since chunk_id is not searchable but is filterable (as a key field), use filter instead of search
        # Escape single quotes in chunk IDs and create a filter expression
        escaped_sources = [s.replace("'", "''") for s in sources]
        filter_expression = f"search.in({identifier_field}, '{','.join(escaped_sources)}')"
        
        search_results = await search_client.search(
            search_text="*",  # Use wildcard to match all, since we're filtering
            filter=filter_expression,
            select=[identifier_field, title_field, content_field, "category"], 
            top=len(sources)
        )

        # Enhanced document collection with UI-friendly information
        docs = []
        found_sources = set()
        
        async for r in search_results:
            found_sources.add(r[identifier_field])
            
            # Create enhanced document info for UI display
            doc_info = {
                "chunk_id": r[identifier_field],
                "title": r.get(title_field, ""),
                "chunk": r[content_field],
                "category": r.get("category", "General"),
                "excerpt": r[content_field][:200] + "..." if len(r[content_field]) > 200 else r[content_field],
                "word_count": len(r[content_field].split()),
                "relevance": "high" if r[identifier_field] in sources[:2] else "medium"  # First 2 sources considered high relevance
            }
            docs.append(doc_info)
            
        # Check for missing sources
        missing_sources = set(sources) - found_sources
        if missing_sources:
            logger.warning(f"⚠️ Could not find sources: {missing_sources}")
        
        # Enhanced grounding information for UI
        grounding_info = {
            "total_sources": len(docs),
            "requested_sources": len(sources),
            "found_sources": len(found_sources),
            "missing_sources": list(missing_sources),
            "confidence_level": confidence_level,
            "summary": summary,
            "status": "success" if docs else "not_found",
            "categories": list(set(doc.get("category", "General") for doc in docs)),
            "total_words": sum(doc.get("word_count", 0) for doc in docs),
            "timestamp": time.time()
        }
        
        # Log grounding activity for telemetry
        logger.info(f"✅ Grounding completed: {len(docs)} sources found ({confidence_level} confidence)")
        if summary:
            logger.info(f"📝 Summary: {summary}")
        
        # Trace the grounding operation with enhanced details
        grounding_response = {
            "sources": docs,
            "grounding_info": grounding_info
        }
        
        telemetry.trace_tool_call("report_grounding", {
            "sources_count": len(sources),
            "found_count": len(docs),
            "confidence": confidence_level
        }, 0.0, grounding_response)
        
        return ToolResult({
            "sources": docs,
            "grounding_info": grounding_info
        }, ToolResultDirection.TO_CLIENT)
        
    except Exception as e:
        logger.error(f"❌ Grounding tool error: {e}")
        return ToolResult({
            "sources": [],
            "grounding_info": {
                "total_sources": 0,
                "confidence_level": confidence_level,
                "summary": f"Error retrieving sources: {str(e)}",
                "status": "error",
                "error_details": str(e)
            }
        }, ToolResultDirection.TO_CLIENT)

def _extract_call_history_metadata(data_items):
    """Extract call history information from policies or claims data for UI popup"""
    call_history_metadata = []
    
    for item in data_items:
        if 'call_history' in item and item['call_history']:
            customer_info = {
                'name': item.get('holder', item.get('name', '')),
                'first_name': item.get('holder_first_name', item.get('first_name', '')),
                'last_name': item.get('holder_last_name', item.get('last_name', '')),
                'policy_number': item.get('policy_number', item.get('policy', '')),
                'customer_id': item.get('id', '')
            }
            
            call_history_metadata.append({
                'customer': customer_info,
                'call_history': item['call_history']
            })
    
    return call_history_metadata

def _extract_call_history_metadata(data_items):
    """Extract call history information from policies or claims data for UI popup"""
    call_history_metadata = []
    
    for item in data_items:
        if 'call_history' in item and item['call_history']:
            customer_info = {
                'name': item.get('holder', item.get('name', '')),
                'first_name': item.get('holder_first_name', item.get('first_name', '')),
                'last_name': item.get('holder_last_name', item.get('last_name', '')),
                'policy_number': item.get('policy_number', item.get('policy', '')),
                'customer_id': item.get('id', '')
            }
            
            call_history_metadata.append({
                'customer': customer_info,
                'call_history': item['call_history']
            })
    
    return call_history_metadata

async def _policy_tool(args: Any) -> ToolResult:
    """Retrieve insurance policy information"""
    if not AZURE_API_ENDPOINT:
        error_msg = "Insurance API is not available. AZURE_API_ENDPOINT environment variable is not configured."
        logger.error(error_msg)
        return ToolResult({"error": error_msg, "policies": []}, ToolResultDirection.TO_SERVER)
        
    start_time = time.time()
    # Build search description for logging
    search_parts = []
    if args.get('policy_number'): search_parts.append(f"policy '{args.get('policy_number')}'")
    if args.get('name'): search_parts.append(f"name '{args.get('name')}'")
    if args.get('first_name'): search_parts.append(f"first_name '{args.get('first_name')}'")
    if args.get('last_name'): search_parts.append(f"last_name '{args.get('last_name')}'")
    if args.get('policy_type'): search_parts.append(f"type '{args.get('policy_type')}'")
    
    search_desc = ", ".join(search_parts) if search_parts else "all policies"
    print(f"Retrieving policies for {search_desc}.")
    
    try:
        # Build API parameters including new name search fields
        api_params = {}
        if args.get('policy_number'): api_params['policy_number'] = args['policy_number']
        if args.get('name'): api_params['name'] = args['name']
        if args.get('first_name'): api_params['first_name'] = args['first_name']
        if args.get('last_name'): api_params['last_name'] = args['last_name']
        if args.get('policy_type'): api_params['policy_type'] = args['policy_type']
        
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_API_ENDPOINT+"/api/policies", params=api_params)
            response.raise_for_status()
            policies = response.json()
        
        # Trace the tool call with enhanced details
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_policies", args, duration, {"policies": policies}, len(str(policies)))
        
        # Extract call history metadata for UI
        call_history_data = _extract_call_history_metadata(policies.get('policies', []))
        
        # Include call history metadata in the response if available
        result_data = {"policies": policies}
        if call_history_data:
            result_data["__CALL_HISTORY_METADATA__"] = call_history_data
        
        return ToolResult(result_data, ToolResultDirection.TO_SERVER)
    except Exception as e:
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_policies", args, duration, {"error": str(e)}, len(str(e)))
        raise e

async def _claims_tool(args: Any) -> ToolResult:
    """Retrieve insurance claim information"""
    if not AZURE_API_ENDPOINT:
        error_msg = "Insurance API is not available. AZURE_API_ENDPOINT environment variable is not configured."
        logger.error(error_msg)
        return ToolResult({"error": error_msg, "claims": []}, ToolResultDirection.TO_SERVER)
        
    start_time = time.time()
    # Build search description for logging
    search_parts = []
    if args.get('claim_number'): search_parts.append(f"claim '{args.get('claim_number')}'")
    if args.get('policy_number'): search_parts.append(f"policy '{args.get('policy_number')}'")
    if args.get('holder_name'): search_parts.append(f"holder '{args.get('holder_name')}'")
    if args.get('first_name'): search_parts.append(f"first_name '{args.get('first_name')}'")
    if args.get('last_name'): search_parts.append(f"last_name '{args.get('last_name')}'")
    if args.get('claim_type'): search_parts.append(f"type '{args.get('claim_type')}'")
    
    search_desc = ", ".join(search_parts) if search_parts else "all claims"
    print(f"Retrieving claims for {search_desc}.")
    
    try:
        # Build API parameters including new name search fields
        api_params = {}
        if args.get('claim_number'): api_params['claim_number'] = args['claim_number']
        if args.get('policy_number'): api_params['policy_number'] = args['policy_number']
        if args.get('holder_name'): api_params['holder_name'] = args['holder_name']
        if args.get('first_name'): api_params['first_name'] = args['first_name']
        if args.get('last_name'): api_params['last_name'] = args['last_name']
        if args.get('claim_type'): api_params['claim_type'] = args['claim_type']
        
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_API_ENDPOINT+"/api/claims", params=api_params)
            response.raise_for_status()
            claims = response.json()
        
        # Trace the tool call with enhanced details
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_claims", args, duration, {"claims": claims}, len(str(claims)))
        
        # Extract call history metadata for UI
        call_history_data = _extract_call_history_metadata(claims.get('claims', []))
        
        # Include call history metadata in the response if available
        result_data = {"claims": claims}
        if call_history_data:
            result_data["__CALL_HISTORY_METADATA__"] = call_history_data
        
        return ToolResult(result_data, ToolResultDirection.TO_SERVER)
    except Exception as e:
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_claims", args, duration, {"error": str(e)}, len(str(e)))
        raise e

async def _real_policy_tool(args: Any) -> ToolResult:
    """Retrieve comprehensive real-time policy information"""
    if not AZURE_API_ENDPOINT:
        error_msg = "Insurance API is not available. AZURE_API_ENDPOINT environment variable is not configured."
        logger.error(error_msg)
        return ToolResult({"error": error_msg, "policies": []}, ToolResultDirection.TO_SERVER)
        
    start_time = time.time()
    # Build search description for logging
    search_parts = []
    if args.get('policy_type'): search_parts.append(f"type '{args.get('policy_type')}'")
    if args.get('status'): search_parts.append(f"status '{args.get('status')}'")
    if args.get('holder_name'): search_parts.append(f"holder '{args.get('holder_name')}'")
    if args.get('first_name'): search_parts.append(f"first_name '{args.get('first_name')}'")
    if args.get('last_name'): search_parts.append(f"last_name '{args.get('last_name')}'")
    
    search_desc = ", ".join(search_parts) if search_parts else "all real-time policies"
    print(f"Retrieving real-time policies with {search_desc}")
    
    try:
        # Build API parameters including new name search fields
        api_params = {}
        if args.get('policy_type'): api_params['policy_type'] = args['policy_type']
        if args.get('status'): api_params['status'] = args['status']
        if args.get('holder_name'): api_params['holder_name'] = args['holder_name']
        if args.get('first_name'): api_params['first_name'] = args['first_name']
        if args.get('last_name'): api_params['last_name'] = args['last_name']
        
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_API_ENDPOINT+"/api/realtime/policies", params=api_params)
            response.raise_for_status()
            policies = response.json()
        
        # Trace the tool call with enhanced details
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_real_policies", args, duration, {"real_policies": policies}, len(str(policies)))
        
        return ToolResult({"real_policies": policies}, ToolResultDirection.TO_SERVER)
    except Exception as e:
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_real_policies", args, duration, {"error": str(e)}, len(str(e)))
        raise e

async def _agency_tool(args: Any) -> ToolResult:
    """Retrieve Contoso agency information"""
    if not AZURE_API_ENDPOINT:
        error_msg = "Insurance API is not available. AZURE_API_ENDPOINT environment variable is not configured."
        logger.error(error_msg)
        return ToolResult({"error": error_msg, "agencies": []}, ToolResultDirection.TO_SERVER)
        
    start_time = time.time()
    # Build search description for logging
    search_parts = []
    if args.get('city'): search_parts.append(f"city '{args.get('city')}'")
    if args.get('agent_name'): search_parts.append(f"agent '{args.get('agent_name')}'")
    
    search_desc = ", ".join(search_parts) if search_parts else "all agencies"
    print(f"Retrieving agencies with {search_desc}")
    
    try:
        # Build API parameters
        api_params = {}
        if args.get('city'): api_params['city'] = args['city']
        if args.get('agent_name'): api_params['agent_name'] = args['agent_name']
        
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_API_ENDPOINT+"/api/agencies", params=api_params)
            response.raise_for_status()
            agencies = response.json()
        
        # Trace the tool call with enhanced details
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_agencies", args, duration, {"agencies": agencies}, len(str(agencies)))
        
        return ToolResult({"agencies": agencies}, ToolResultDirection.TO_SERVER)
    except Exception as e:
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_agencies", args, duration, {"error": str(e)}, len(str(e)))
        raise e

async def _contact_tool(args: Any) -> ToolResult:
    """Retrieve Contoso contact information"""
    if not AZURE_API_ENDPOINT:
        error_msg = "Insurance API is not available. AZURE_API_ENDPOINT environment variable is not configured."
        logger.error(error_msg)
        return ToolResult({"error": error_msg, "contact_info": {}}, ToolResultDirection.TO_SERVER)
        
    start_time = time.time()
    # Build search description for logging
    search_parts = []
    if args.get('service_type'): search_parts.append(f"service '{args.get('service_type')}'")
    if args.get('company'): search_parts.append(f"company '{args.get('company')}'")
    
    search_desc = ", ".join(search_parts) if search_parts else "all contact information"
    print(f"Retrieving contact information for {search_desc}")
    
    try:
        # Build API parameters
        api_params = {}
        if args.get('service_type'): api_params['service_type'] = args['service_type']
        if args.get('company'): api_params['company'] = args['company']
        
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_API_ENDPOINT+"/api/contact", params=api_params)
            response.raise_for_status()
            contacts = response.json()
        
        # Trace the tool call with enhanced details
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_contact_info", args, duration, {"contact_info": contacts}, len(str(contacts)))
        
        return ToolResult({"contact_info": contacts}, ToolResultDirection.TO_SERVER)
    except Exception as e:
        duration = time.time() - start_time
        telemetry.trace_tool_call("get_contact_info", args, duration, {"error": str(e)}, len(str(e)))
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

def attach_rag_tools_to_client(chat_handler,
    credentials: AzureKeyCredential | DefaultAzureCredential = None,
    search_endpoint: str = None, search_index: str = None,
    semantic_configuration: str = None,
    identifier_field: str = None,
    content_field: str = None,
    embedding_field: str = None,
    title_field: str = None,
    use_vector_query: bool = None
    ) -> None:
    """Attach RAG tools to chat handler for GPT-4o Audio API"""
    
    # Use environment variables if parameters not provided
    search_endpoint = search_endpoint or os.environ.get("AZURE_SEARCH_ENDPOINT")
    search_index = search_index or os.environ.get("AZURE_SEARCH_INDEX")
    semantic_configuration = semantic_configuration or os.environ.get("AZURE_SEARCH_SEMANTIC_CONFIGURATION", "default")
    identifier_field = identifier_field or os.environ.get("AZURE_SEARCH_IDENTIFIER_FIELD", "chunk_id")
    content_field = content_field or os.environ.get("AZURE_SEARCH_CONTENT_FIELD", "chunk")
    embedding_field = embedding_field or os.environ.get("AZURE_SEARCH_EMBEDDING_FIELD", "text_vector")
    title_field = title_field or os.environ.get("AZURE_SEARCH_TITLE_FIELD", "title")
    use_vector_query = use_vector_query if use_vector_query is not None else os.environ.get("AZURE_SEARCH_USE_VECTOR_QUERY", "true").lower() == "true"
    
    if not credentials:
        if "AZURE_SEARCH_API_KEY" in os.environ:
            credentials = AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"])
        else:
            credentials = DefaultAzureCredential()
    
    if not isinstance(credentials, AzureKeyCredential):
        credentials.get_token("https://search.azure.com/.default") # warm this up
    
    logger.info("Attaching RAG tools to chat handler")
    
    # Create search client
    search_client = SearchClient(search_endpoint, search_index, credentials, user_agent="ChatHandler")
    
    # Add search tool
    chat_handler.add_tool({
        "type": "function",
        "function": _search_tool_schema
    })
    
    # Add grounding tool
    chat_handler.add_tool({
        "type": "function", 
        "function": _grounding_tool_schema
    })
    
    # Add insurance tools
    chat_handler.add_tool({
        "type": "function",
        "function": _policy_tool_schema
    })
    
    chat_handler.add_tool({
        "type": "function",
        "function": _claims_tool_schema
    })
    
    chat_handler.add_tool({
        "type": "function",
        "function": _real_policy_tool_schema
    })
    
    chat_handler.add_tool({
        "type": "function",
        "function": _agency_tool_schema
    })
    
    chat_handler.add_tool({
        "type": "function",
        "function": _contact_tool_schema
    })
    
    # Store search client reference for tool execution
    chat_handler._search_client = search_client
    chat_handler._search_config = {
        "semantic_configuration": semantic_configuration,
        "identifier_field": identifier_field,
        "content_field": content_field,
        "embedding_field": embedding_field,
        "title_field": title_field,
        "use_vector_query": use_vector_query
    }
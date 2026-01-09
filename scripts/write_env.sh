#!/bin/bash

# Define the .env file path
ENV_FILE_PATH="app/backend/.env"

# Clear the contents of the .env file
> $ENV_FILE_PATH

get_azd_value() {
	name="$1"
	value="$(azd env get-value "$name" 2>/dev/null)"
	if [ -z "$value" ] || echo "$value" | grep -q '^ERROR:'; then
		echo "Missing azd env value: $name" >&2
		exit 1
	fi
	printf '%s' "$value"
}

# Append new values to the .env file
echo "AZURE_OPENAI_ENDPOINT=$(get_azd_value AZURE_OPENAI_ENDPOINT)" >> $ENV_FILE_PATH
echo "AZURE_OPENAI_REALTIME_DEPLOYMENT=$(get_azd_value AZURE_OPENAI_REALTIME_DEPLOYMENT)" >> $ENV_FILE_PATH
echo "AZURE_OPENAI_REALTIME_VOICE_CHOICE=$(get_azd_value AZURE_OPENAI_REALTIME_VOICE_CHOICE)" >> $ENV_FILE_PATH
echo "AZURE_OPENAI_REALTIME_VOICE_NAME=$(get_azd_value AZURE_OPENAI_REALTIME_VOICE_NAME)" >> $ENV_FILE_PATH
echo "AZURE_OPENAI_REALTIME_VOICE_MODEL_VERSION=$(get_azd_value AZURE_OPENAI_REALTIME_VOICE_MODEL_VERSION)" >> $ENV_FILE_PATH
echo "AZURE_OPENAI_REALTIME_API_VERSION=2025-04-01-preview" >> $ENV_FILE_PATH
echo "AZURE_SEARCH_ENDPOINT=$(get_azd_value AZURE_SEARCH_ENDPOINT)" >> $ENV_FILE_PATH
echo "AZURE_SEARCH_INDEX=$(get_azd_value AZURE_SEARCH_INDEX)" >> $ENV_FILE_PATH
echo "AZURE_TENANT_ID=$(get_azd_value AZURE_TENANT_ID)" >> $ENV_FILE_PATH
echo "AZURE_SEARCH_SEMANTIC_CONFIGURATION=$(get_azd_value AZURE_SEARCH_SEMANTIC_CONFIGURATION)" >> $ENV_FILE_PATH
echo "AZURE_SEARCH_IDENTIFIER_FIELD=$(get_azd_value AZURE_SEARCH_IDENTIFIER_FIELD)" >> $ENV_FILE_PATH
echo "AZURE_SEARCH_CONTENT_FIELD=$(get_azd_value AZURE_SEARCH_CONTENT_FIELD)" >> $ENV_FILE_PATH
echo "AZURE_SEARCH_TITLE_FIELD=$(get_azd_value AZURE_SEARCH_TITLE_FIELD)" >> $ENV_FILE_PATH
echo "AZURE_SEARCH_EMBEDDING_FIELD=$(get_azd_value AZURE_SEARCH_EMBEDDING_FIELD)" >> $ENV_FILE_PATH
echo "AZURE_SEARCH_USE_VECTOR_QUERY=$(get_azd_value AZURE_SEARCH_USE_VECTOR_QUERY)" >> $ENV_FILE_PATH
echo "AZURE_API_ENDPOINT=$(get_azd_value AZURE_API_ENDPOINT)" >> $ENV_FILE_PATH

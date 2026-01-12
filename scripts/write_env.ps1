# Define the .env file path
$envFilePath = "app\backend\.env"

# Clear the contents of the .env file
Set-Content -Path $envFilePath -Value ""

# Append new values to the .env file
function Get-AzdEnvValue([string]$name) {
	$value = azd env get-value $name 2>$null
	if (-not $value) {
		throw "Missing azd env value: $name"
	}
	$value = $value.Trim()
	if ($value.StartsWith("ERROR:")) {
		throw "azd env value not found: $name ($value)"
	}
	return $value
}

function Try-GetAzdEnvValue([string]$name) {
       try {
	       return Get-AzdEnvValue $name
       } catch {
	       return $null
       }
}

$azureOpenAiEndpoint = Get-AzdEnvValue "AZURE_OPENAI_ENDPOINT"
$azureOpenAiRealtimeDeployment = Get-AzdEnvValue "AZURE_OPENAI_REALTIME_DEPLOYMENT"
$azureOpenAiRealtimeVoiceChoice = Get-AzdEnvValue "AZURE_OPENAI_REALTIME_VOICE_CHOICE"
$azureSearchEndpoint = Get-AzdEnvValue "AZURE_SEARCH_ENDPOINT"
$azureSearchIndex = Get-AzdEnvValue "AZURE_SEARCH_INDEX"
$azureTenantId = Get-AzdEnvValue "AZURE_TENANT_ID"
$azureSearchSemanticConfiguration = Get-AzdEnvValue "AZURE_SEARCH_SEMANTIC_CONFIGURATION"
$azureSearchIdentifierField = Get-AzdEnvValue "AZURE_SEARCH_IDENTIFIER_FIELD"
$azureSearchTitleField = Get-AzdEnvValue "AZURE_SEARCH_TITLE_FIELD"
$azureSearchContentField = Get-AzdEnvValue "AZURE_SEARCH_CONTENT_FIELD"
$azureSearchEmbeddingField = Get-AzdEnvValue "AZURE_SEARCH_EMBEDDING_FIELD"
$azureSearchUseVectorQuery = Get-AzdEnvValue "AZURE_SEARCH_USE_VECTOR_QUERY"
$azureClientId = Try-GetAzdEnvValue "AZURE_CLIENT_ID"
$azureAiFoundryHubName = Try-GetAzdEnvValue "AZURE_AI_FOUNDRY_HUB_NAME"
$azureAiFoundryProjectName = Try-GetAzdEnvValue "AZURE_AI_FOUNDRY_PROJECT_NAME"
$azureApiEndpoint = Try-GetAzdEnvValue "AZURE_API_ENDPOINT"
if (-not $azureApiEndpoint) {
	# Backward compatible with current IaC output naming
	$azureApiEndpoint = Get-AzdEnvValue "API_URI"
}

Add-Content -Path $envFilePath -Value "AZURE_OPENAI_ENDPOINT=$azureOpenAiEndpoint"
Add-Content -Path $envFilePath -Value "AZURE_OPENAI_REALTIME_DEPLOYMENT=$azureOpenAiRealtimeDeployment"
Add-Content -Path $envFilePath -Value "AZURE_OPENAI_REALTIME_VOICE_CHOICE=$azureOpenAiRealtimeVoiceChoice"
Add-Content -Path $envFilePath -Value "AZURE_OPENAI_REALTIME_API_VERSION=2025-04-01-preview"
Add-Content -Path $envFilePath -Value "AZURE_SEARCH_ENDPOINT=$azureSearchEndpoint"
Add-Content -Path $envFilePath -Value "AZURE_SEARCH_INDEX=$azureSearchIndex"
Add-Content -Path $envFilePath -Value "AZURE_SEARCH_SEMANTIC_CONFIGURATION=$azureSearchSemanticConfiguration"
Add-Content -Path $envFilePath -Value "AZURE_SEARCH_IDENTIFIER_FIELD=$azureSearchIdentifierField"
Add-Content -Path $envFilePath -Value "AZURE_SEARCH_TITLE_FIELD=$azureSearchTitleField"
Add-Content -Path $envFilePath -Value "AZURE_SEARCH_CONTENT_FIELD=$azureSearchContentField"
Add-Content -Path $envFilePath -Value "AZURE_SEARCH_EMBEDDING_FIELD=$azureSearchEmbeddingField"
Add-Content -Path $envFilePath -Value "AZURE_SEARCH_USE_VECTOR_QUERY=$azureSearchUseVectorQuery"
Add-Content -Path $envFilePath -Value "AZURE_TENANT_ID=$azureTenantId"
Add-Content -Path $envFilePath -Value "AZURE_API_ENDPOINT=$azureApiEndpoint"

if ($azureClientId) {
	Add-Content -Path $envFilePath -Value "AZURE_CLIENT_ID=$azureClientId"
}

if ($azureAiFoundryHubName) {
	Add-Content -Path $envFilePath -Value "AZURE_AI_FOUNDRY_HUB_NAME=$azureAiFoundryHubName"
}

if ($azureAiFoundryProjectName) {
	Add-Content -Path $envFilePath -Value "AZURE_AI_FOUNDRY_PROJECT_NAME=$azureAiFoundryProjectName"
}

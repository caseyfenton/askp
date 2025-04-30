# Perplexity API for Google Sheets

This Google Apps Script enables you to query the Perplexity API directly from Google Sheets. Simply type `=AskPerplexity("your question")` in any cell, and get AI-powered answers right in your spreadsheet.

## Features

- Simple one-function interface with optional parameter overrides
- Uses Perplexity's Sonar Pro model by default (customizable)
- All processing happens server-side
- Returns clean answers without source citations
- Automatic response caching for faster results and reduced API costs
- Customizable temperature and max tokens parameters
- Global configuration for easy management

## Setup Instructions

1. **Open your Google Sheet**
2. **Access the Script Editor**:
   - Click on **Extensions > Apps Script** in the top menu
3. **Copy the Code**:
   - Delete any existing code in the editor
   - Paste the entire contents of the `perplexity.gs` file
4. **Configure Global Settings**:
   - Edit the `PERPLEXITY_CONFIG` object at the top of the script:
     ```javascript
     const PERPLEXITY_CONFIG = {
       API_KEY: "YOUR_PERPLEXITY_API_KEY", // Required
       DEFAULT_MODEL: "sonar-pro",         // Default model
       DEFAULT_TEMPERATURE: 0.7,           // Default creativity level
       DEFAULT_MAX_TOKENS: 4096,           // Default max tokens
       CACHE_ENABLED: true,                // Enable/disable caching
       CACHE_SHEET_NAME: "PerplexityCache" // Sheet name for cache
     };
     ```
   - Replace `YOUR_PERPLEXITY_API_KEY` with your actual Perplexity API key
   - You can get an API key from [Perplexity's website](https://www.perplexity.ai/settings/api)
5. **Save and Deploy**:
   - Click the disk icon to save
   - Click **Deploy > New deployment**
   - Select **Web app** as the deployment type
   - Set "Who has access" to "Anyone"
   - Click **Deploy**
   - Authorize the script when prompted

## Usage

### Basic Usage

In any cell of your Google Sheet, you can use the function with just the query:

```
=AskPerplexity("What is machine learning?")
```

### Advanced Usage

You can override any of the default parameters by specifying them in the function call:

```
=AskPerplexity("What is machine learning?", 2048, 0.3, "sonar-pro")
```

Parameter order:
1. `query` (required): Your question
2. `maxTokens` (optional): Maximum tokens in the response
3. `temperature` (optional): Controls randomness (0.0-1.0)
4. `model` (optional): Model to use (e.g., "sonar-pro", "sonar-small", "sonar-reasoning-pro")

For example, to just change the max tokens:
```
=AskPerplexity("What is machine learning?", 2048)
```

To use default max tokens but specify a different temperature:
```
=AskPerplexity("What is machine learning?", , 0.3)
```

To use default max tokens and temperature but specify a model:
```
=AskPerplexity("What is machine learning?", , , "sonar-reasoning-pro")
```

## Caching System

The script automatically caches responses to avoid unnecessary API calls for repeated queries. This:
- Reduces API costs
- Improves response times for repeated queries
- Stores responses in a separate worksheet named "PerplexityCache" (configurable)

You can clear the cache at any time by clicking **Perplexity API > Clear Cache** from the menu.

## Available Models

You can use any of the Perplexity models, including:
- `sonar-pro` (default): General-purpose model (1¢ per million tokens)
- `sonar-small`: Smaller, faster model (0.1¢ per million tokens)
- `sonar-medium`: Medium-sized model (0.2¢ per million tokens)
- `sonar-reasoning`: Advanced reasoning (5¢ per million tokens)
- `sonar-reasoning-pro`: Best reasoning capabilities (8¢ per million tokens)

## Notes

- Each query will count against your Perplexity API usage and may incur costs
- There is a slight delay when executing the function as it waits for the API response
- If you see "#ERROR!" in a cell, check the function parameters and API key
- The caching system uses MD5 hashing to create unique keys based on query + parameters

## Created By

This integration was created for the ASKP (Ask Perplexity) project by Casey Fenton.

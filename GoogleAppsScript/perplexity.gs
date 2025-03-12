/**
 * Perplexity API Configuration
 * Replace with your own API key from Perplexity
 * 
 * Available Perplexity Models:
 * ------------------------------
 * - sonar-pro          : General-purpose model (1¢ per million tokens)
 * - sonar-small        : Smaller, faster model (0.1¢ per million tokens)
 * - sonar-medium       : Medium-sized model (0.2¢ per million tokens)
 * - sonar-large        : Large model with strong capabilities (0.5¢ per million tokens)
 * - sonar-reasoning    : Advanced reasoning capabilities (5¢ per million tokens)
 * - sonar-reasoning-pro: Best reasoning capabilities (8¢ per million tokens)
 */
const PERPLEXITY_CONFIG = {
  API_KEY: "YOUR_PERPLEXITY_API_KEY",
  DEFAULT_MODEL: "sonar-pro",
  DEFAULT_TEMPERATURE: 0.7,
  DEFAULT_MAX_TOKENS: 4096,
  CACHE_ENABLED: true,
  CACHE_SHEET_NAME: "PerplexityCache"
};

/**
 * AskPerplexity - Query the Perplexity API from Google Sheets
 * 
 * @param {string} query - The question or query to send to Perplexity
 * @param {number} maxTokens - Optional: Maximum tokens in response (default from global config)
 * @param {number} temperature - Optional: Controls randomness (0.0-1.0, default from global config)
 * @param {string} model - Optional: Model to use (default from global config)
 * @return {string} The response from Perplexity AI
 * @customfunction
 */
function AskPerplexity(query, maxTokens, temperature, model) {
  // Validate inputs
  if (!query) {
    return "ERROR: Please provide a query";
  }
  
  // Use provided parameters or defaults from config
  maxTokens = maxTokens || PERPLEXITY_CONFIG.DEFAULT_MAX_TOKENS;
  temperature = temperature !== undefined ? temperature : PERPLEXITY_CONFIG.DEFAULT_TEMPERATURE;
  model = model || PERPLEXITY_CONFIG.DEFAULT_MODEL;
  
  // Check if caching is enabled and if we have a cached response
  if (PERPLEXITY_CONFIG.CACHE_ENABLED) {
    const cachedResponse = getCachedResponse(query, model, temperature, maxTokens);
    if (cachedResponse) {
      return cachedResponse;
    }
  }
  
  // Prepare the request
  const url = "https://api.perplexity.ai/chat/completions";
  const payload = {
    model: model,
    messages: [{ role: "user", content: query }],
    temperature: temperature,
    max_tokens: maxTokens
  };
  
  const options = {
    method: "post",
    contentType: "application/json",
    headers: {
      "Authorization": "Bearer " + PERPLEXITY_CONFIG.API_KEY
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
  
  try {
    // Make the API request
    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    
    // Handle response
    if (responseCode === 200) {
      const responseData = JSON.parse(response.getContentText());
      
      // Extract the content from the response
      const content = responseData.choices[0].message.content;
      
      // Store in cache if enabled
      if (PERPLEXITY_CONFIG.CACHE_ENABLED) {
        cacheResponse(query, content, model, temperature, maxTokens);
      }
      
      return content;
    } else {
      // Handle error responses
      const errorData = JSON.parse(response.getContentText());
      return "ERROR: " + (errorData.error?.message || "API returned status code " + responseCode);
    }
  } catch (error) {
    // Handle any exceptions
    return "ERROR: " + error.toString();
  }
}

/**
 * Retrieves a cached response if available
 * 
 * @param {string} query - The original query
 * @param {string} model - The model used
 * @param {number} temperature - The temperature setting used
 * @param {number} maxTokens - The max tokens setting used
 * @return {string|null} The cached response or null if not found
 */
function getCachedResponse(query, model, temperature, maxTokens) {
  try {
    const cacheKey = generateCacheKey(query, model, temperature, maxTokens);
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    
    // Check if cache sheet exists, if not return null (no cache)
    let cacheSheet;
    try {
      cacheSheet = ss.getSheetByName(PERPLEXITY_CONFIG.CACHE_SHEET_NAME);
    } catch (e) {
      return null;
    }
    
    if (!cacheSheet) return null;
    
    // Look for the cache entry
    const data = cacheSheet.getDataRange().getValues();
    for (let i = 1; i < data.length; i++) {  // Start at 1 to skip header row
      if (data[i][0] === cacheKey) {
        return data[i][4]; // Column E contains the cached response
      }
    }
    return null;
  } catch (error) {
    Logger.log("Cache retrieval error: " + error);
    return null; // On any error, just return null and proceed with the API call
  }
}

/**
 * Stores a response in the cache sheet
 * 
 * @param {string} query - The original query
 * @param {string} response - The API response to cache
 * @param {string} model - The model used
 * @param {number} temperature - The temperature setting used
 * @param {number} maxTokens - The max tokens setting used
 */
function cacheResponse(query, response, model, temperature, maxTokens) {
  try {
    const cacheKey = generateCacheKey(query, model, temperature, maxTokens);
    const timestamp = new Date();
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    
    // Create cache sheet if it doesn't exist
    let cacheSheet = ss.getSheetByName(PERPLEXITY_CONFIG.CACHE_SHEET_NAME);
    if (!cacheSheet) {
      cacheSheet = ss.insertSheet(PERPLEXITY_CONFIG.CACHE_SHEET_NAME);
      cacheSheet.appendRow([
        "CacheKey", 
        "Query", 
        "Timestamp", 
        "Parameters", 
        "Response"
      ]);
      cacheSheet.getRange("A1:E1").setFontWeight("bold");
    }
    
    // Check if entry already exists
    const data = cacheSheet.getDataRange().getValues();
    for (let i = 1; i < data.length; i++) {
      if (data[i][0] === cacheKey) {
        // Update existing entry
        cacheSheet.getRange(i+1, 3).setValue(timestamp); // Update timestamp
        cacheSheet.getRange(i+1, 5).setValue(response);  // Update response
        return;
      }
    }
    
    // Add new entry
    cacheSheet.appendRow([
      cacheKey,
      query,
      timestamp,
      JSON.stringify({model: model, temperature: temperature, maxTokens: maxTokens}),
      response
    ]);
  } catch (error) {
    Logger.log("Cache storage error: " + error);
    // Continue even if caching fails
  }
}

/**
 * Generates a unique cache key for a query and its parameters
 */
function generateCacheKey(query, model, temperature, maxTokens) {
  return Utilities.base64Encode(
    Utilities.computeDigest(
      Utilities.DigestAlgorithm.MD5, 
      query + "|" + model + "|" + temperature + "|" + maxTokens
    )
  );
}

/**
 * Test function to make sure the API connection works
 */
function testPerplexityAPI() {
  const result = AskPerplexity("What is the capital of France?", 4096, 0.7, "sonar-pro");
  Logger.log(result);
}

/**
 * Clears the cache sheet
 */
function clearPerplexityCache() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const cacheSheet = ss.getSheetByName(PERPLEXITY_CONFIG.CACHE_SHEET_NAME);
    
    if (cacheSheet) {
      // Keep the header row and delete all other rows
      const dataRange = cacheSheet.getDataRange();
      if (dataRange.getNumRows() > 1) {
        cacheSheet.deleteRows(2, dataRange.getNumRows() - 1);
      }
      SpreadsheetApp.getUi().alert("Perplexity cache cleared successfully!");
    } else {
      SpreadsheetApp.getUi().alert("No cache sheet found!");
    }
  } catch (error) {
    SpreadsheetApp.getUi().alert("Error clearing cache: " + error);
  }
}

/**
 * Add a custom menu when the spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Perplexity API')
    .addItem('Test Connection', 'testPerplexityAPI')
    .addItem('Clear Cache', 'clearPerplexityCache')
    .addToUi();
}

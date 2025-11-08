/**
 * Netlify Function to proxy API requests to external Flask backend
 * This is a workaround since Netlify's Python functions have limitations
 * For better performance, consider using Railway or deploying Flask separately
 */

exports.handler = async (event, context) => {
  const { path, httpMethod, headers, body, queryStringParameters } = event;
  
  // Extract the API path (remove /api/ prefix)
  const apiPath = path.replace('/api/', '');
  
  // Get the Flask backend URL from environment variable
  const flaskBackendUrl = process.env.FLASK_BACKEND_URL;
  
  if (!flaskBackendUrl) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Flask backend URL not configured' }),
      headers: {
        'Content-Type': 'application/json',
      },
    };
  }

  try {
    // Forward the request to Flask backend
    const response = await fetch(`${flaskBackendUrl}/api/${apiPath}`, {
      method: httpMethod,
      headers: {
        'Content-Type': headers['content-type'] || 'application/json',
        ...(headers.authorization && { Authorization: headers.authorization }),
      },
      body: body || undefined,
    });

    const data = await response.text();
    
    return {
      statusCode: response.status,
      body: data,
      headers: {
        'Content-Type': response.headers.get('content-type') || 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
      },
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message }),
      headers: {
        'Content-Type': 'application/json',
      },
    };
  }
};


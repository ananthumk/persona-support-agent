# API Troubleshooting Guide

## Common API Errors

### 400 Bad Request
**Cause:** Invalid request format or missing required parameters.
**Solution:**
- Verify all required fields are included in the request body
- Check that JSON is properly formatted (no trailing commas)
- Ensure request headers include `Content-Type: application/json`
- Validate parameter types (strings, numbers, booleans)

Example of correct request:
```json
{
  "email": "user@example.com",
  "action": "verify",
  "timestamp": 1718832000
}
```

### 401 Unauthorized
**Cause:** Missing or invalid authentication token.
**Solution:**
- Include valid API key in request header: `Authorization: Bearer YOUR_API_KEY`
- Check that token hasn't expired (tokens expire after 24 hours)
- Regenerate token if necessary from dashboard
- Verify API key has correct permissions for the endpoint

### 403 Forbidden
**Cause:** Authenticated but insufficient permissions.
**Solution:**
- Verify your account tier allows access to this endpoint
- Contact support to upgrade permissions
- Check if IP whitelist restrictions apply

### 404 Not Found
**Cause:** Requested resource doesn't exist.
**Solution:**
- Verify the resource ID is correct
- Check if the resource has been deleted
- Ensure endpoint URL spelling is correct

### 429 Rate Limited
**Cause:** Too many requests exceeding rate limits.
**Solution:**
- Standard tier: 100 requests/minute
- Pro tier: 1,000 requests/minute
- Enterprise: Custom limits
- Implement exponential backoff in retry logic
- Wait before retrying (check `Retry-After` header)

### 500 Internal Server Error
**Cause:** Server-side issue.
**Solution:**
- Retry after 30 seconds
- Contact support with request ID from response header
- Check system status at status.example.com

## Connection Issues

**Timeout after 30 seconds:**
- Check network connectivity
- Verify firewall isn't blocking API endpoint
- Reduce payload size if uploading large files

**SSL Certificate Error:**
- Update CA certificates
- Ensure TLS 1.2 or higher is supported
- Contact support if issue persists


## Authentication Setup

### Generating a New API Key

1. Log into the Developer Dashboard.
2. Navigate to Settings > API Keys.
3. Click "Generate New Key."
4. Copy the key immediately — for security reasons, the full key is only displayed once and cannot be retrieved again later.
5. Store the key in an environment variable or secrets manager. Never hard-code API keys directly into source code or commit them to version control.

### Revoking an Old API Key

Old or compromised keys can be revoked from Settings > API Keys by clicking "Revoke" next to the key. Revoking a key takes effect immediately and cannot be undone. Any application still using a revoked key will begin receiving 401 Unauthorized errors right away.

## Testing API Connection

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.example.com/v1/status
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0",
  "timestamp": 1718832000
}
```
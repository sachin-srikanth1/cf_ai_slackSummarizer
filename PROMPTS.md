# PROMPTS.md

This file contains prompts used in the Slack AI Summarizer project.

## FastAPI Backend Setup

**Date**: 2025-09-28
**Type**: User Request
**Source**: Project architecture

**Prompt**:
```
Set up a Python FastAPI backend with Cloudflare Workers AI integration. Implement async message processing with MongoDB using Motor and Beanie ODM for persistence. Use Pydantic for schema validation and implement proper error handling for AI service calls.
```

---

## MongoDB Integration

**Date**: 2025-09-28
**Type**: User Request
**Source**: Data modeling

**Prompt**:
```
Implement MongoDB collections for storing Slack messages and summaries. Create proper indexes on channel_id and timestamp fields for efficient querying of message history.
```

---

## Cloudflare AI Service

**Date**: 2025-09-28
**Type**: User Request
**Source**: AI integration

**Prompt**:
```
Implement Cloudflare Workers AI service integration using the Llama 3.3 model. Add proper error handling and retry logic for AI API calls. Include custom prompt engineering for EOD/EOW summaries with conversation context.
```

---

## Slack Bot Integration

**Date**: 2025-09-29
**Type**: User Request
**Source**: Slack integration

**Prompt**:
```
Build Slack webhook handling using slack-sdk with proper signature verification. Implement mention detection and slash commands for triggering summaries. Add message fetching from Slack channels with proper OAuth token handling. Explain NGROK
```

---

## PDF Report Generation

**Date**: 2025-09-29
**Type**: User Request
**Source**: Report generation

**Prompt**:
```
Implement PDF generation using ReportLab for creating summary reports. Add custom styling and formatting for professional-looking EOD/EOW summary documents with proper text wrapping and layout.
```

---

## Error Handling Implementation

**Date**: 2025-09-29
**Type**: User Request
**Source**: Error handling

**Prompt**:
```
The webhook signature verification needs proper error handling. Implement structured exception handling with appropriate HTTP status codes and error responses for different failure scenarios.
```

---

## Event Deduplication

**Date**: 2025-09-29
**Type**: User Request
**Source**: Event processing

**Prompt**:
```
Slack is sending duplicate webhook events causing multiple responses. Implement in-memory event deduplication using Python sets to track processed events and commands with unique identifiers.
```

---

## Repository Cleanup

**Date**: 2025-09-29
**Type**: User Request
**Source**: Code organization

**Prompt**:
```
Remove unnecessary test files and unused components while maintaining 100% bot functionality. Clean up the codebase to only include essential files for the Slack AI summarizer bot operation.
```

---
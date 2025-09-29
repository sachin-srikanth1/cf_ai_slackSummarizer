# PROMPTS.md

This file contains prompts used in the Slack AI Summarizer project.

## Initial Architecture Design

**Date**: 2025-09-28
**Type**: User Request
**Source**: Project architecture

**Prompt**:
```
Set up a multi-agent architecture using Python FastAPI with Cloudflare Workers AI integration. I need async message processing with MongoDB for persistence, implementing the repository pattern with proper dependency injection. Use Pydantic for schema validation and implement proper error handling with circuit breakers for the AI service calls.
```

---

## Database Schema Design

**Date**: 2025-09-28
**Type**: User Request
**Source**: Data modeling

**Prompt**:
```
Design the MongoDB collections with proper indexing strategy for time-series message data. Implement compound indexes on (channel_id, timestamp) and (user_id, timestamp) for optimal query performance. Add TTL indexes for message cleanup and ensure proper sharding keys for horizontal scaling.
```

---

## AI Service Implementation

**Date**: 2025-09-28
**Type**: User Request
**Source**: AI integration

**Prompt**:
```
Implement the Cloudflare Workers AI service with proper retry logic, exponential backoff, and rate limiting. Use the Llama 3.3 model with custom prompt engineering for different summary styles. Add streaming support for large payloads and implement context window management for token optimization.
```

---

## Slack API Integration

**Date**: 2025-09-29
**Type**: User Request
**Source**: Slack integration

**Prompt**:
```
Build robust Slack webhook handling with proper signature verification. Add support for interactive components, slash commands, and file attachments with proper error handling and retry mechanisms.
```

---

## WebSocket Implementation

**Date**: 2025-09-29
**Type**: User Request
**Source**: Real-time features

**Prompt**:
```
Add WebSocket support for real-time dashboard updates using FastAPI's WebSocket capabilities. Implement connection pooling, heartbeat monitoring, and graceful disconnection handling. Use Redis pub/sub for multi-instance deployments with proper message broadcasting.
```

---



## Security Implementation

**Date**: 2025-09-29
**Type**: User Request
**Source**: Security hardening

**Prompt**:
```
Implement OAuth 2.0 with JWT tokens for API authentication. Add request rate limiting using token bucket algorithm, CORS configuration for cross-origin requests. Include audit logging.
```

---

## Frontend Architecture

**Date**: 2025-09-29
**Type**: User Request
**Source**: Frontend development

**Prompt**:
```
Create a responsive React TypeScript frontend with Material-UI components. Implement proper state management using React Query for server state and Zustand for client state. Add proper error boundaries, loading states, and optimistic updates for better UX.
```

---

## PDF Generation Service

**Date**: 2025-09-29
**Type**: User Request
**Source**: Report generation

**Prompt**:
```
Build PDF generation using ReportLab with custom templates. Implement async rendering for large reports, add watermarking and digital signatures. Include chart generation using matplotlib and proper memory management for concurrent PDF creation.
```

---

## Monitoring and Observability

**Date**: 2025-09-29
**Type**: User Request
**Source**: DevOps implementation

**Prompt**:
```
Add comprehensive logging using structlog with correlation IDs. Implement metrics collection using Prometheus, distributed tracing with OpenTelemetry, and health checks with circuit breaker patterns. Include custom dashboards for business metrics.
```

---

## Deployment Configuration

**Date**: 2025-09-29
**Type**: User Request
**Source**: Infrastructure

**Prompt**:
```
Set up Docker multi-stage builds with distroless base images. Implement Kubernetes deployments with proper resource limits, horizontal pod autoscaling, and rolling updates. Add Helm charts for environment management and secrets handling with External Secrets Operator.
```

---

## Testing Strategy

**Date**: 2025-09-29
**Type**: User Request
**Source**: Quality assurance

**Prompt**:
```
Implement comprehensive testing with pytest for unit tests, integration tests using testcontainers for MongoDB, and end-to-end tests with Playwright. Add property-based testing with Hypothesis and mutation testing for coverage quality verification.
```

---

## Error Handling Refinement

**Date**: 2025-09-29
**Type**: User Request
**Source**: Error handling

**Prompt**:
```
The webhook signature verification is failing intermittently. Need to implement proper error classification with custom exception hierarchies, add structured error responses with error codes, and implement dead letter queues for failed message processing.
```

---

## Performance Bottleneck Analysis

**Date**: 2025-09-29
**Type**: User Request
**Source**: Performance debugging

**Prompt**:
```
The AI summarization is causing timeout issues under load. Implement request queuing with priority levels, add async batch processing for multiple summaries, and optimize the prompt engineering to reduce token usage while maintaining quality.
```

---

## Duplicate Event Handling

**Date**: 2025-09-29
**Type**: User Request
**Source**: Event processing

**Prompt**:
```
Slack is sending duplicate webhook events causing multiple responses. Implement idempotency keys using Redis with TTL, add event fingerprinting for deduplication, and create proper atomic operations to prevent race conditions in concurrent processing.
```

---

## Repository Cleanup

**Date**: 2025-09-29
**Type**: User Request
**Source**: Code organization

**Prompt**:
```
get rid of all unnessecary files (files that don't contribute to the bot ex. test files). Make sure the bot still has 100% functionality. Add this prompt to prompts.md
```

---
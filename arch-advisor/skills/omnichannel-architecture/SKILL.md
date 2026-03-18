---
name: omnichannel-architecture
description: "Use this skill when designing customer-facing systems across multiple channels, when discussing chatbots, omnichannel, WhatsApp integration, web chat, email automation, or when someone says 'we need to serve customers on multiple channels', 'WhatsApp + web + email support', 'agent must adapt to each channel', 'we need session continuity across channels', 'intent classification for customer messages', 'escalation to human agent'. Also trigger for: channel adapters, intent routing, session management, response formatting by channel, human handoff."
---

# Omnichannel Architecture for Agent Systems

## Core Principle: Channel-Agnostic Processing

Process all requests in a unified internal format, regardless of channel. Translate to/from channel formats at the boundary.

```
[WhatsApp] → [Adapter] ┐
[Web Chat] → [Adapter] ├─→ [UnifiedMessage] → [Agent System] → [Response]
[Email]    → [Adapter] ┘                                           ↓
                                                    [Adapter: format for each channel]
```

This means: one agent pipeline, N channel adapters. The agent never needs to know which channel the request came from.

## Intent Classification Hierarchy

1. **Rules/keywords** (zero LLM cost): catch high-confidence cases — "cancelar pedido", "segunda via de boleto"
2. **LLM classifier** (structured output): handles ambiguous, contextual, informal language
3. **Confidence threshold**: if confidence < 0.7 → escalate to human or ask clarifying question

Intent taxonomy must be finite and documented. Common categories: FAQ, Transactional, Complaint, Technical Support, Escalation Request, Out-of-scope.

## Channel Capabilities and Response Formatting

Different channels support different formats:

| Channel | Max length | Markdown | Rich media | Buttons |
|---|---|---|---|---|
| WhatsApp | ~4096 chars | No (plain text) | Images, audio | Quick-reply buttons |
| Web Chat | Unlimited | Yes | Full HTML | Any |
| Email | Unlimited | No (HTML/text) | Inline images | Links only |
| SMS | 160 chars | No | No | No |

The Response Formatter is a dedicated component that:
- Truncates responses for channels with length limits
- Strips markdown for channels that render it as literal characters
- Adapts tone (email = formal, chat = conversational)
- Never modifies the semantic content — only the presentation

## Session Management

Multi-turn conversations require stateful sessions:

```
SessionState {
  sessionId: string
  userId: string
  channel: Channel
  turns: Message[]
  context: AgentContext   // current intent, entities extracted
  status: active | awaiting_input | escalated | closed
  ttl: Date               // auto-close after inactivity
}
```

State is stored in Redis (fast access, TTL-based expiry).

For omnichannel continuity: sessions persist across channels. If a user starts on web chat and follows up via WhatsApp, the session context must be available on both channels.

## Escalation Policy

Trigger escalation when:
- Confidence score consistently < 0.7 after 2 turns
- User explicitly requests human agent
- Intent category = complaint (above a severity threshold)
- Unauthorized action attempt detected
- Session duration > maximum (e.g., 20 turns without resolution)

Escalation agent responsibilities:
- Summarize the conversation for the human agent
- Create a support ticket with full context
- Notify the human agent via their queue
- Inform the user of wait time and ticket number
- Transfer the session to human-controlled mode

## Graceful Degradation

Never fail completely. Fallback cascade:
1. Primary agent handles request
2. If primary fails → secondary agent (simpler, rule-based)
3. If secondary fails → menu-driven options
4. If all automation fails → direct escalation to human

## Perguntas diagnósticas
1. Which channels must be supported at launch, and which are on the roadmap?
2. Does each channel have different capabilities that the response must adapt to?
3. Is session continuity required across channels, or can each channel be independent?
4. What is the escalation policy — when should the agent hand off to a human?
5. What is the intent taxonomy? How many distinct intents are in scope?
6. What is the SLA per channel (WhatsApp: 2 min, email: 4 hours)?

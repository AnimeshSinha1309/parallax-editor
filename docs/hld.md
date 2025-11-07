# **Parallax - Product Requirements Document**

## **1. Executive Summary**

**Product Name:** Parallax  
**Tagline:** An AI that thinks alongside you while you work, surfacing insights and connections in real-time as inline suggestions.

**Problem:** Current AI tools operate transactionally with a request-response loop that interrupts flow. Planning sessions stretch from 10 minutes to an hour because of constant context-switching.

**Solution:** Parallax continuously processes context in the background and surfaces insights, questions, and connections as you type—without ever blocking your work.

**Target Launch:** K2 Think AI Hackathon Demo  
**Platform:** Terminal-based (Linux/macOS)

---

## **2. Target Users**

### **Primary:**
- **Developers** planning refactors, writing specs for coding agents (Cursor, Aider, Claude Code), architecting systems

### **Secondary:**
- Product Managers synthesizing research into PRDs
- Technical writers creating documentation

### **User Pain Points:**
1. Context-switching disrupts flow state
2. Manual search for similar code patterns
3. Missing edge cases and ambiguities in plans
4. Waiting for AI responses blocks progress

---

## **3. Core Value Proposition**

### **The Paradigm Shift:**
**Traditional AI:** You type → Press Enter → Wait → AI responds → Repeat  
**Parallax:** You type → AI thinks in parallel → Suggestions appear → You keep typing

### **Key Benefits:**
1. **Uninterrupted Flow:** AI never blocks your typing
2. **Proactive Intelligence:** Surfaces issues before you ask
3. **Contextual Awareness:** Understands your entire codebase
4. **10x Latency Advantage:** K2 Think's 2000 tok/s enables real-time UX

---

## **4. High-Level Architecture**

```
┌─────────────────────────────────────────────────┐
│         PARALLAX MAIN APPLICATION               │
│                                                 │
│  ┌──────────────────┐    ┌──────────────────┐ │
│  │  Text Editor     │    │   Right Sidebar  │ │
│  │  (Markdown)      │    │                  │ │
│  │                  │    │  [Agent Cards]   │ │
│  │  [Grey inline    │    │  - Questions     │ │
│  │   completion]    │    │  - Context       │ │
│  └──────────────────┘    └──────────────────┘ │
└────────────┬────────────────────────────────────┘
             │
             │ User types → 300ms debounce
             │
        ┌────▼─────────────────────────┐
        │   Spawn 3 Parallel Agents    │
        │   (all get same context)     │
        └────┬─────────────────────────┘
             │
    ┌────────┼────────┬─────────────┐
    │        │        │             │
┌───▼───┐ ┌─▼──────┐ ┌──▼────────┐
│Context│ │Complete│ │ Questions │
│ Agent │ │  Agent │ │   Agent   │
└───┬───┘ └─┬──────┘ └──┬────────┘
    │       │           │
    │ {type, title, string}
    │       │           │
    └───────┴───────────┴────────────▶ Update UI
```

---

## **5. System Components**

### **5.1 Main Application**

**Responsibilities:**
- Render terminal UI (Textual framework)
- Track user input and cursor position
- Debounce typing events (300ms)
- Manage agent lifecycle
- Display agent outputs

**Key State:**
```python
current_file: str           # Markdown plan content
cursor_position: (int, int) # (line, column)
pwd: str                    # Working directory
agent_outputs: {
    "completion": AgentResponse,
    "questions": AgentResponse,
    "context": AgentResponse
}
```

---

### **5.2 Sub-Agent Interface**

**Contract:**
```python
class AgentContext:
    """Input provided to each agent"""
    file_content: str       # Full markdown file
    cursor_position: tuple  # (line, col)
    pwd: str               # Current directory

class AgentResponse:
    """Output returned by each agent"""
    type: str      # "completion" | "questions" | "context"
    title: str     # Display title (e.g., "Similar Code")
    content: str   # Main content to display
```

**Agent Responsibilities:**
- Receive context
- Perform independent work (API calls, searches, etc.)
- Return formatted response
- Handle own errors (fallback + logging)

---

### **5.3 The Three Core Agents**

#### **A. Completion Agent**

**Purpose:** Provide inline code/text completions

**Input:**
- Current file content
- Cursor position

**Process:**
1. Extract context around cursor (e.g., last 100 lines)
2. Call K2 Think completion endpoint
3. Format response

**Output:**
```python
{
    "type": "completion",
    "title": "",  # No title needed
    "content": "    return result.json()\n    logger.info('Success')"
}
```

**Display:** Grey inline text at cursor

---

#### **B. Questions Agent**

**Purpose:** Surface clarifying questions about ambiguities

**Input:**
- Current file content
- Cursor position

**Process:**
1. Identify current section/context
2. Call K2 Think with prompt:
   ```
   Analyze this plan and identify 2-3 critical ambiguities or edge cases.
   Ask short, specific questions.
   ```
3. Parse response into list

**Output:**
```python
{
    "type": "questions",
    "title": "Clarifying Questions",
    "content": "• Should retry be per-user or per-transaction?\n• How to handle timeout in payment flow?\n• What's the max file size limit?"
}
```

**Display:** Card in right sidebar

---

#### **C. Context Agent**

**Purpose:** Find similar code patterns and relevant files

**Input:**
- Current file content
- Cursor position
- Working directory (pwd)

**Process:**
1. Extract key terms from current context
2. Search codebase using Hound
3. Optionally: Call K2 Think to summarize findings
4. Format as file:line references

**Output:**
```python
{
    "type": "context",
    "title": "Similar Code",
    "content": "payments/stripe_handler.py:142\nauth/retry_logic.py:89\nutils/error_handler.py:233"
}
```

**Display:** Card in right sidebar

---

## **6. Execution Model**

### **6.1 Trigger Flow**

```
User types
    ↓
Wait 300ms (debounce)
    ↓
User still typing? → Reset timer
    ↓
No more typing? → Spawn agents
    ↓
All 3 agents execute in parallel
    ↓
Each agent returns when done
    ↓
Update UI with results
    ↓
User types again? → Cancel & restart
```

### **6.2 Cancellation Policy**

**If user types while agents are working:**
- Don't cancel HTTP requests (complexity)
- Simply ignore responses when they arrive
- Immediately start new agent cycle

**Rationale:** K2 Think is fast enough that responses arrive quickly anyway

---

### **6.3 Error Handling**

**Agent-Level Errors:**
- Each agent catches its own errors
- Fallback to basic completion
- Log error to file (non-blocking)

**Example:**
```python
try:
    result = await hound.search(query)
    return format_response(result)
except HoundConnectionError:
    log_error("Hound unavailable")
    return basic_completion_fallback()
```

**Never:** Show error messages to user (breaks flow)

---

## **7. Technical Specifications**

### **7.1 Technology Stack**

| Component | Technology | Justification |
|-----------|-----------|---------------|
| TUI Framework | Textual | Async-native, modern, Python |
| Concurrency | asyncio | Native to Textual, I/O bound tasks |
| LLM Backend | K2 Think (Cerebras) | 2000 tok/s = real-time UX |
| Code Search | Hound | Fast, already indexed, minimal setup |
| HTTP Client | aiohttp/httpx | Async requests |

### **7.2 LLM Configuration**

```python
K2_THINK_ENDPOINT = "https://api.cerebras.ai/v1/chat/completions"

# Shared configuration
MODEL = "k2-think"
TEMPERATURE = 0.7
MAX_TOKENS = 1000

# Note: Endpoint is variable, can swap to:
# - OpenRouter
# - Claude API
# - Local model
```

### **7.3 Performance Targets**

| Metric | Target | Rationale |
|--------|--------|-----------|
| Debounce delay | 300ms | Balance responsiveness vs API calls |
| Agent timeout | 5s | K2 Think should respond in ~1-2s |
| UI refresh | <50ms | Maintain 60fps feel |
| Memory usage | <500MB | Lightweight terminal app |

---

## **8. User Experience**

### **8.1 User Journey**

1. **Launch:** `parallax plan.md`
2. **Start typing:** User writes agent plan
3. **300ms pause:** Parallax detects thinking opportunity
4. **Suggestions appear:**
   - Grey inline completion at cursor
   - Questions card in sidebar
   - Context card in sidebar
5. **User continues typing:** Suggestions update continuously
6. **Accept suggestion:** Tab key accepts inline completion

### **8.2 UI Layout**

```
┌─────────────────────────────────┬──────────────────────┐
│ plan.md                         │  SUGGESTIONS         │
│─────────────────────────────────│──────────────────────│
│                                 │                      │
│ # Payment System Refactor      │  ❓ Questions:       │
│                                 │  • Should retry be   │
│ ## Objectives                   │    per-user or       │
│ - Implement retry logic         │    per-transaction?  │
│ - Add error handling            │  • How to handle     │
│ - [grey: Log all attempts]      │    timeout?          │
│                                 │                      │
│                                 │  🔗 Similar Code:    │
│                                 │  stripe_handler:142  │
│                                 │  retry_logic.py:89   │
│                                 │                      │
└─────────────────────────────────┴──────────────────────┘
```

### **8.3 Key Interactions**

| Action | Result |
|--------|--------|
| Type continuously | Suggestions don't appear (waiting for pause) |
| Pause 300ms | All suggestions update |
| Press Tab | Accept inline completion |
| Click context link | Jump to file:line |
| Press Esc | Clear suggestions |

---

## **9. Success Metrics**

### **9.1 Demo Success Criteria**

**Must Have:**
✅ All 3 agent types working  
✅ Real-time updates (< 2s latency)  
✅ No typing interruption  
✅ Side-by-side comparison showing 10x speed vs traditional AI  

**Nice to Have:**
- File navigation from context links
- Multiple suggestion refinement as user edits
- Suggestion history

### **9.2 Technical Metrics**

- **Latency:** Agent responses in < 2 seconds
- **Accuracy:** Suggestions relevant 80%+ of time
- **Stability:** No crashes during 10-min demo
- **Resource:** < 200MB RAM, < 5% CPU when idle

---

## **10. Development Phases**

### **Phase 1: Foundation (4 hours)**
- Textual TUI skeleton
- Text editor with cursor tracking
- K2 Think API integration
- Basic debouncing

**Deliverable:** Can type, see cursor, call K2 Think

---

### **Phase 2: Agent Framework (4 hours)**
- AgentContext & AgentResponse interfaces
- Parallel agent execution
- UI update mechanism

**Deliverable:** Framework ready for agents

---

### **Phase 3: Implement Agents (6 hours)**
- Completion Agent (2h)
- Questions Agent (2h)
- Context Agent with Hound (2h)

**Deliverable:** All 3 agents working

---

### **Phase 4: Polish & Demo (4 hours)**
- Ghost text rendering
- Sidebar cards
- Error handling
- Demo script
- Latency comparison

**Deliverable:** Demo-ready product

---

## **11. Out of Scope (v1)**

**Explicitly NOT included:**
- Tree-sitter integration (agents can add later if needed)
- Multi-file editing
- Git integration
- Persistent history
- User authentication
- Plugin system
- Configuration UI

**Rationale:** Focus on core "thinking in parallel" UX

---

## **12. Risk Mitigation**

| Risk | Impact | Mitigation |
|------|--------|-----------|
| K2 Think API unstable | High | Use OpenRouter as backup endpoint |
| Hound indexing slow | Medium | Pre-index demo repository |
| Textual performance issues | Medium | Profile early, optimize rendering |
| Agent responses irrelevant | Medium | Iterate on prompts, add examples |

---

## **13. Future Enhancements**

**Post-Demo v2 Features:**
- Multi-model support (use different models per agent)
- Custom agent plugins
- Semantic code search (embeddings)
- Tree-sitter for syntax-aware parsing
- Integration with coding agents (Cursor, Aider)
- Persistent context across sessions

---

## **14. Open Questions**

1. **Prompt Engineering:** What exact prompts for each agent?
2. **Context Limits:** How much file content to send to K2?
3. **Hound Query Strategy:** What search terms to extract?
4. **UI Polish:** Colors, styling, animations?

**Decision:** Address during implementation

---

## **Appendix: Key Design Decisions**

**Q: Why all K2 Think?**  
A: Simplicity for v1. Unified endpoint. Speed advantage.

**Q: Why wait for complete response?**  
A: K2 Think is fast enough. Avoids partial gibberish.

**Q: Why 300ms debounce?**  
A: Balance between responsiveness and API cost.

**Q: Why string output from agents?**  
A: Simplicity. Can always add structure later.

**Q: Why ignore errors instead of showing them?**  
A: Never break user's flow state.

---

**Document Version:** 1.0  
**Last Updated:** Nov 6, 2025  
**Status:** Ready for Implementation

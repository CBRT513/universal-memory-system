# 🎯 WHEN TO USE WHAT - Your Personal AI Assistant Decision Guide

## Quick Decision Tree

### "I need to..."

#### 📝 **Remember something for later**
→ **Use:** `mem store "your note"`
→ **Example:** `mem store "Use Firebase for SwiftNotes authentication"`
→ **When:** You made a decision, learned something, or need to remember it

#### 🔍 **Find something I stored before**
→ **Use:** `mem search "topic"`
→ **Example:** `mem search "firebase auth"`
→ **When:** You know you saved something but can't remember details

#### 💻 **Write new code**
→ **Use:** SubAgent for that language/framework
→ **Example:** `python3 subagents/cli/subagent_cli.py execute frontend-developer "Create a React dashboard"`
→ **When:** Starting a new feature, component, or module

#### 🐛 **Fix broken code**
→ **Use:** Just ask Claude directly (you don't need a special tool)
→ **Example:** "This function is throwing an error: [paste error]"
→ **When:** Something isn't working

#### 📚 **Review articles I saved**
→ **Use:** `~/g` then press `2`
→ **Example:** Shows all your saved articles with priorities
→ **When:** Looking for something to learn/implement

#### 🤔 **Not sure what I need**
→ **Use:** `~/g` (Galactica interface)
→ **Example:** Natural language interface that understands context
→ **When:** You want to explore or aren't sure what tool to use

---

## Real-World Scenarios

### Scenario 1: "I'm starting a new project"
```bash
# 1. Store your project decision
mem store "Starting new project: Task tracker app using React + Firebase"

# 2. Create the frontend structure
python3 subagents/cli/subagent_cli.py execute frontend-developer "Create React app structure for task tracker"

# 3. Create the backend
python3 subagents/cli/subagent_cli.py execute backend-developer "Create Firebase backend for task tracker"

# 4. Review what you built
python3 subagents/cli/subagent_cli.py execute code-reviewer "Review task tracker code"
```

### Scenario 2: "I read an article and want to implement it"
```bash
# 1. Check your actionable articles
~/g
# Press 1 (What needs action?)

# 2. Pick an article to implement
# The article will show action items

# 3. Use the appropriate SubAgent
python3 subagents/cli/subagent_cli.py execute javascript-developer "Implement [action item from article]"
```

### Scenario 3: "I'm debugging and need to track what I tried"
```bash
# 1. Store what's broken
mem store "Bug: Login button not working - returns 401 error"

# 2. Store each solution you try
mem store "Tried: Checking Firebase auth rules - didn't fix it"
mem store "Tried: Updating auth token refresh - didn't fix it"
mem store "FIXED: CORS settings were blocking auth headers"

# 3. Later, search for similar issues
mem search "401 error auth"
```

### Scenario 4: "I need to document my code"
```bash
# Use the documentation writer
python3 subagents/cli/subagent_cli.py execute documentation-writer "Document the TaskTracker API"
```

### Scenario 5: "I want to optimize performance"
```bash
# Use the performance engineer
python3 subagents/cli/subagent_cli.py execute performance-engineer "Optimize React rendering in TaskList component"
```

---

## Which SubAgent for What?

| If you need to... | Use this SubAgent | Command |
|-------------------|-------------------|---------|
| Build UI/frontend | `frontend-developer` | For React, Vue, CSS, components |
| Create backend/API | `backend-developer` | For servers, databases, APIs |
| Write Python code | `python-developer` | For Python-specific tasks |
| Write JavaScript | `javascript-developer` | For JS/Node.js tasks |
| Add TypeScript types | `typescript-developer` | For TS type safety |
| Setup CI/CD | `devops-engineer` | For deployment, Docker, K8s |
| Design database | `database-architect` | For schema, queries, optimization |
| Add tests | `test-automation-engineer` | For unit/integration tests |
| Review code | `code-reviewer` | After writing significant code |
| Write docs | `documentation-writer` | For README, API docs, guides |
| Fix performance | `performance-engineer` | For speed optimization |
| Add security | `security-engineer` | For auth, encryption, safety |
| Build mobile app | `mobile-developer` | For React Native, Flutter |
| Create cloud infra | `cloud-architect` | For AWS, Azure, GCP |
| Build ML features | `ml-engineer` | For AI/ML integration |
| Process data | `data-engineer` | For ETL, pipelines |

---

## The Golden Rules

### 1. **Memory First, Action Second**
Always store decisions/learnings BEFORE you implement them:
```bash
mem store "Decision: Use Tailwind CSS for styling"
# THEN implement it
```

### 2. **Use SubAgents for NEW Code**
SubAgents are for CREATING new code, not fixing existing code:
- ✅ "Create a new login component" → Use SubAgent
- ❌ "Fix this error in my code" → Just ask Claude directly

### 3. **Natural Language is Fine**
Galactica (`~/g`) understands natural language:
- "What did I decide about authentication?"
- "Show me articles about React"
- "What needs to be done?"

### 4. **Switch Workspaces for Context**
```bash
work      # Switch to work data/memories
personal  # Switch to personal data/memories
```

---

## Quick Reference Card

```bash
# Memory Operations
mem store "note"          # Save something
mem search "topic"        # Find something
mem list                  # See recent memories

# Galactica (Natural Language)
~/g                       # Interactive interface
  1 → Actionable items
  2 → Recent articles
  3 → Search memories

# SubAgents (Code Generation)
python3 subagents/cli/subagent_cli.py list     # See all agents
python3 subagents/cli/subagent_cli.py execute [agent] "[task]"

# Workspace Switching
work                      # Use work data
personal                  # Use personal data
```

---

## Still Not Sure?

Just use `~/g` - it's the smart assistant that helps you figure out what you need!

Or ask yourself:
1. **"Am I trying to remember something?"** → `mem store`
2. **"Am I looking for something I saved?"** → `mem search`
3. **"Am I creating NEW code?"** → Use SubAgent
4. **"Am I fixing EXISTING code?"** → Just ask Claude
5. **"I have no idea"** → Use `~/g`
# 🔄 UMS MIGRATION PREPARATION

## This Universal Memory System is about to be migrated!

### What's Happening:
The UMS is being moved from a user-specific location to a **shared system location** so multiple users can access the same memory system.

### Migration Details:

**FROM (Current):**
```
~/Projects/AgentWorkspace/agentforge/backend/universal-memory-system/
```

**TO (New Shared Location):**
```
System Files: /usr/local/share/universal-memory-system/
Database:     /usr/local/var/universal-memory-system/databases/
Logs:         /usr/local/var/universal-memory-system/logs/
```

### What This Means:

1. **For AI Agents (Claude Code, Cursor, etc.):**
   - After migration, use the new shared paths
   - A symlink will maintain compatibility with old paths
   - Migration notices will be added to AGENT.md and CLAUDE.md

2. **For Your Current User (cerion):**
   - Your environment will be updated automatically
   - New aliases and commands will use shared location
   - Existing work remains unaffected

3. **For the New User (equillabs):**
   - Will have full access to the same UMS
   - Shares the same memory database
   - Can collaborate on the same memories

### Database Sharing:
- Both users will share the SAME database
- Changes by either user are immediately visible to both
- This enables true collaborative memory management

### Backup Safety:
- Your current UMS will be backed up before migration
- Backup location: `universal-memory-system.backup.YYYYMMDD_HHMMSS`
- Original functionality preserved through symlinks

### To Execute Migration:
```bash
bash /tmp/RUN_SETUP.sh
```

This will:
1. Back up current UMS
2. Move to shared location
3. Create equillabs user
4. Update all configurations
5. Notify all AI agents

### Post-Migration:
After migration, all AI agents will see notices in:
- `/usr/local/share/universal-memory-system/AGENT.md`
- `/usr/local/share/universal-memory-system/CLAUDE.md`
- `~/UMS_MIGRATION_NOTICE.md`
- `~/UMS_QUICK_REFERENCE.md`

---
*Migration Script Created: $(date)*
*This ensures all AI agents and tools know about the new shared location*
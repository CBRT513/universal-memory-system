# Claude Code SubAgents Makefile

.PHONY: help list create-all test-frontend test-backend review clean

help:
	@echo "Claude Code SubAgents - Available commands:"
	@echo "  make list          - List all available subagents"
	@echo "  make create-all    - Create all subagent files"
	@echo "  make test-frontend - Test frontend developer subagent"
	@echo "  make test-backend  - Test backend developer subagent"
	@echo "  make review        - Run code review subagent"
	@echo "  make clean         - Clean generated files"

list:
	python3 cli/subagent_cli.py list

create-all:
	python3 cli/subagent_cli.py create-all

test-frontend:
	python3 cli/subagent_cli.py execute frontend-developer "Create a simple React component"

test-backend:
	python3 cli/subagent_cli.py execute backend-developer "Create a REST API endpoint"

review:
	python3 cli/subagent_cli.py execute code-reviewer "Review recent changes"

clean:
	rm -rf output/*.md
	@echo "Cleaned generated files"

# Workflow targets
workflow-fullstack:
	@echo "Running full-stack development workflow..."
	python3 cli/subagent_cli.py execute frontend-developer "Create frontend components"
	python3 cli/subagent_cli.py execute backend-developer "Create API endpoints"
	python3 cli/subagent_cli.py execute api-developer "Document API"
	python3 cli/subagent_cli.py execute test-automation-engineer "Create tests"

workflow-deploy:
	@echo "Running deployment workflow..."
	python3 cli/subagent_cli.py execute security-engineer "Security audit"
	python3 cli/subagent_cli.py execute performance-engineer "Performance optimization"
	python3 cli/subagent_cli.py execute devops-engineer "Deploy to production"

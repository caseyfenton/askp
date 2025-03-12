
ASKP Quickstart

First-time Setup

git clone https://github.com/caseyfenton/askp
cd askp
./install.sh --wizard

Common Workflows

Basic Query

askp "What is the capital of France?"

Multi-Query Processing

askp -m "Python best practices" "Python security" "Python performance"

Deep Research Mode

# Generate a comprehensive research plan
askp -d "Impact of quantum computing on cryptography"

Run Tests

pytest tests/ -v

Build Documentation

mkdocs build

Submit PR
	1.	Create feature branch
	2.	Add tests
	3.	Run checks:

make validate

	4.	Push and create PR

Update Installation

askp --update

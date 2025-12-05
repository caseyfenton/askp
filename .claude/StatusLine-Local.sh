#!/bin/bash
# StatusLine-Local.sh Template - Project-Specific Status Line Additions
#
# This template provides examples of status line enhancements you can add to your project.
# Uncomment and customize the sections you want to use.
#
# 📚 Complete Guide: ~/.claude/StatusLine-Development-Guide.md (COMPREHENSIVE EXAMPLES)
# 📋 Quick Reference: ~/.claude/status_lines/CLAUDE.md
# 🎮 Management: ~/.claude/agents/statusline-manager/statusline-manager.sh
# ⏱️  Performance: Keep total execution under 100ms for best results

# Get JSON input from Claude Code
input=$(cat)

# Extract common information
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')
project_dir=$(echo "$input" | jq -r '.workspace.project_dir')

# Initialize status components array
project_parts=()

# ═══════════════════════════════════════════════════════════════════════════
# 📁 FILE SYSTEM STATUS
# ═══════════════════════════════════════════════════════════════════════════

# Example: Track recently modified files (last 10 minutes)
# recent_files=$(find . -type f -mmin -10 2>/dev/null | wc -l | tr -d ' ')
# if [ "$recent_files" -gt 0 ]; then
#     project_parts+=("📝 Recent:$recent_files")
# fi

# Example: Count total project files
# total_files=$(find . -type f 2>/dev/null | wc -l | tr -d ' ')
# project_parts+=("📂 Files:$total_files")

# Example: Check for large files (>10MB)
# large_files=$(find . -type f -size +10M 2>/dev/null | wc -l | tr -d ' ')
# if [ "$large_files" -gt 0 ]; then
#     project_parts+=("🐘 Large:$large_files")
# fi

# ═══════════════════════════════════════════════════════════════════════════
# 🌐 WEB DEVELOPMENT STATUS
# ═══════════════════════════════════════════════════════════════════════════

# Example: Check for running web servers
# for port in 3000 8000 8080 5000 4200 3001 8888; do
#     if command -v lsof >/dev/null 2>&1 && lsof -i ":$port" >/dev/null 2>&1; then
#         project_parts+=("🌐 :$port")
#         break
#     fi
# done

# Example: Check npm/package.json status
# if [ -f "package.json" ]; then
#     if [ -d "node_modules" ]; then
#         package_version=$(node -p "require('./package.json').version" 2>/dev/null)
#         project_parts+=("📦 npm:v$package_version")
#     else
#         project_parts+=("📦 npm:deps-needed")
#     fi
# fi

# Example: Check build status
# if [ -f "dist/index.html" ] || [ -f "build/index.html" ] || [ -f "public/index.html" ]; then
#     project_parts+=("🏗️ built")
# elif [ -f "package.json" ] || [ -f "webpack.config.js" ] || [ -f "vite.config.js" ]; then
#     project_parts+=("🏗️ unbuild")
# fi

# ═══════════════════════════════════════════════════════════════════════════
# 🐍 PYTHON DEVELOPMENT STATUS
# ═══════════════════════════════════════════════════════════════════════════

# Example: Virtual environment status
# if [ -n "$VIRTUAL_ENV" ]; then
#     venv_name=$(basename "$VIRTUAL_ENV")
#     python_version=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
#     project_parts+=("🐍 $venv_name:py$python_version")
# elif [ -d "venv" ] || [ -d ".venv" ] || [ -d "env" ]; then
#     project_parts+=("🐍 venv:inactive")
# fi

# Example: Python package status
# if [ -f "requirements.txt" ]; then
#     req_count=$(wc -l < requirements.txt 2>/dev/null)
#     project_parts+=("📋 reqs:$req_count")
# elif [ -f "pyproject.toml" ]; then
#     project_parts+=("📋 pyproject")
# elif [ -f "Pipfile" ]; then
#     project_parts+=("📋 pipfile")
# fi

# ═══════════════════════════════════════════════════════════════════════════
# 🧪 TESTING & CI/CD STATUS
# ═══════════════════════════════════════════════════════════════════════════

# Example: Test file detection
# test_files=0
# for pattern in "test_*.py" "*_test.py" "*.test.js" "*.spec.js" "*Test.java"; do
#     count=$(ls $pattern 2>/dev/null | wc -l | tr -d ' ')
#     test_files=$((test_files + count))
# done
# if [ -d "tests" ]; then
#     test_dir_files=$(find tests -name "*.py" -o -name "*.js" -o -name "*.java" 2>/dev/null | wc -l | tr -d ' ')
#     test_files=$((test_files + test_dir_files))
# fi
# if [ "$test_files" -gt 0 ]; then
#     project_parts+=("🧪 tests:$test_files")
# fi

# Example: CI/CD pipeline status
# if [ -f ".github/workflows/ci.yml" ] || [ -f ".github/workflows/main.yml" ]; then
#     project_parts+=("🔄 GHA")
# elif [ -f ".gitlab-ci.yml" ]; then
#     project_parts+=("🔄 GitLab")
# elif [ -f "Jenkinsfile" ]; then
#     project_parts+=("🔄 Jenkins")
# fi

# ═══════════════════════════════════════════════════════════════════════════
# 🗄️ DATABASE & SERVICES STATUS
# ═══════════════════════════════════════════════════════════════════════════

# Example: Database connection check
# for port in 5432 3306 27017 6379; do
#     if command -v lsof >/dev/null 2>&1 && lsof -i ":$port" >/dev/null 2>&1; then
#         case $port in
#             5432) project_parts+=("🐘 postgres") ;;
#             3306) project_parts+=("🐬 mysql") ;;
#             27017) project_parts+=("🍃 mongo") ;;
#             6379) project_parts+=("🔴 redis") ;;
#         esac
#     fi
# done

# Example: Docker container status
# if command -v docker >/dev/null 2>&1; then
#     running_containers=$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')
#     if [ "$running_containers" -gt 0 ]; then
#         project_parts+=("🐳 docker:$running_containers")
#     fi
# fi

# ═══════════════════════════════════════════════════════════════════════════
# 🎤 SPECIALIZED PROJECT STATUS (Examples)
# ═══════════════════════════════════════════════════════════════════════════

# Example: OpenVoiceOS/Mycroft status (like EgoHackersBook)
# if command -v pgrep >/dev/null 2>&1; then
#     ovos_count=$(timeout 2s pgrep -f "ovos\|mycroft" 2>/dev/null | wc -l | tr -d ' ')
#     if [ "$ovos_count" -gt 0 ]; then
#         project_parts+=("🎤 OVOS:$ovos_count")
#     fi
# fi

# Example: Book/Content management
# if [ -d "book/chapters" ]; then
#     chapter_count=$(ls book/chapters/chapter_*.md 2>/dev/null | wc -l | tr -d ' ')
#     if [ "$chapter_count" -gt 0 ]; then
#         project_parts+=("📖 chapters:$chapter_count")
#     fi
# fi

# Example: Skill development status
# if [ -f "*/__init__.py" ] && [ -f "test_*.py" ]; then
#     project_parts+=("✅ skill+tests")
# elif [ -f "*/__init__.py" ]; then
#     project_parts+=("🔧 skill-dev")
# fi

# ═══════════════════════════════════════════════════════════════════════════
# 🔧 DEVELOPMENT ENVIRONMENT STATUS
# ═══════════════════════════════════════════════════════════════════════════

# Example: Git status (lightweight version)
# if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then
#     # Use timeout to prevent hanging
#     branch=$(timeout 2s git branch --show-current 2>/dev/null || echo "unknown")
#     if [ "$branch" != "main" ] && [ "$branch" != "master" ] && [ "$branch" != "unknown" ]; then
#         project_parts+=("🌿 $branch")
#     fi
# fi

# Example: IDE/Editor detection
# if [ -d ".vscode" ]; then
#     project_parts+=("💻 vscode")
# elif [ -d ".idea" ]; then
#     project_parts+=("💻 idea")
# fi

# Example: Environment variables check
# if [ -f ".env" ]; then
#     env_vars=$(grep -c "=" .env 2>/dev/null)
#     project_parts+=("🔐 env:$env_vars")
# fi

# ═══════════════════════════════════════════════════════════════════════════
# 📊 PERFORMANCE & MONITORING
# ═══════════════════════════════════════════════════════════════════════════

# Example: Log file monitoring
# if [ -d "logs" ]; then
#     recent_logs=$(find logs -name "*.log" -mmin -5 2>/dev/null | wc -l | tr -d ' ')
#     if [ "$recent_logs" -gt 0 ]; then
#         project_parts+=("📋 logs:$recent_logs")
#     fi
# fi

# Example: Process monitoring (project-specific)
# project_name=$(basename "$current_dir")
# if command -v pgrep >/dev/null 2>&1; then
#     project_processes=$(pgrep -f "$project_name" 2>/dev/null | wc -l | tr -d ' ')
#     if [ "$project_processes" -gt 0 ]; then
#         project_parts+=("⚙️ proc:$project_processes")
#     fi
# fi

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 OUTPUT FORMATTING
# ═══════════════════════════════════════════════════════════════════════════

# Combine all status parts and output
if [ ${#project_parts[@]} -gt 0 ]; then
    # Join array elements with " | " separator
    project_status=$(IFS=' | '; echo "${project_parts[*]}")
    printf "\033[2m\033[95m📚 LOCAL:\033[0m %s" "$project_status"
fi

# NO fallback - LOCAL only shows when there's actual project-specific content
# This prevents generic "development environment" messages

# ═══════════════════════════════════════════════════════════════════════════
# 💡 CUSTOMIZATION TIPS
# ═══════════════════════════════════════════════════════════════════════════
#
# 1. Keep execution time under 100ms for best performance
# 2. Use timeouts for external commands: timeout 2s command
# 3. Cache expensive operations in /tmp/ files
# 4. Test your changes with: statusline-manager.sh test-project
# 5. Check performance with: statusline-manager.sh timing
#
# Color codes:
# - \033[2m\033[95m = dim magenta (for prefixes)
# - \033[0m = reset colors
# - \033[32m = green, \033[33m = yellow, \033[31m = red
#
# Emojis for common status types:
# - 🌐 web servers    - 📦 packages      - 🧪 tests
# - 🐍 python        - 📁 files         - 🔧 development
# - 🗄️ databases      - 🎤 voice/audio   - 📖 content
# - 🐳 docker        - 🌿 git branches  - ⚙️ processes
#
# Documentation links:
# - 📚 COMPLETE GUIDE: ~/.claude/StatusLine-Development-Guide.md (ALL EXAMPLES & CACHING)
# - 📋 Quick reference: ~/.claude/status_lines/CLAUDE.md
# - 🎮 Agent help: ~/.claude/agents/statusline-manager/statusline-manager.sh help
# - ⏱️  Performance analysis: ~/.claude/agents/statusline-manager/statusline-manager.sh timing
# - 🌐 External inspiration: Starship, Powerline, Shox (see development guide)
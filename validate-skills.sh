#!/bin/bash

# Validates skills against the Agent Skills specification.
# Reference: https://agentskills.io/specification.md
#
# Spec-defined frontmatter (only these top-level fields are allowed):
#   name          (required) 1-64 chars, [a-z0-9-], no leading/trailing/consecutive hyphens, must match dir name
#   description   (required) 1-1024 chars, non-empty
#   license       (optional) any license name or reference
#   compatibility (optional) 1-500 chars
#   metadata      (optional) map of string -> string
#   allowed-tools (optional) space-separated STRING (not a YAML list)
#
# Also enforced, from the same spec:
#   - SKILL.md must start with YAML frontmatter
#   - no duplicate top-level keys (YAML forbids them; a parser may take either one)
#   - body under 500 lines, and under ~5000 tokens (the spec's recommended
#     instruction budget: line count alone misses a short file with long lines)
#   - relative file references resolve, and stay one level deep
#
# Usage: validate-skills.sh [DIR]   (default: the current directory)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SKILLS_DIR="${1:-.}"
ISSUES=0
WARNINGS=0
PASSED=0

# Fields the spec allows at the top level of the frontmatter.
ALLOWED_FIELDS="name description license compatibility metadata allowed-tools"

echo "🔍 Auditing Skills Against Agent Skills Specification"
echo "======================================================"
echo ""
echo "Reference: https://agentskills.io/specification.md"
echo ""

for skill_dir in "$SKILLS_DIR"/*/; do
    skill_name=$(basename "$skill_dir")
    skill_file="${skill_dir}SKILL.md"
    skill_errors=()
    skill_warnings=()

    # Skip directories that aren't skills (no SKILL.md), e.g. assets/
    [[ -f "$skill_file" ]] || continue

    # ===== FRONTMATTER EXTRACTION =====
    # Frontmatter MUST be the first thing in the file, delimited by --- ... ---
    first_line=$(head -1 "$skill_file")
    if [[ "$first_line" != "---" ]]; then
        echo -e "${RED}❌ $skill_name${NC}"
        echo -e "   ${RED}Error:${NC} File must start with YAML frontmatter ('---' on line 1)"
        ((ISSUES++))
        continue
    fi

    # Everything between the first '---' and the next '---'
    frontmatter=$(awk 'NR==1 && /^---[[:space:]]*$/{f=1; next} f && /^---[[:space:]]*$/{done=1; exit} f{print} END{if(!done) exit 3}' "$skill_file")
    if [[ $? -eq 3 ]]; then
        echo -e "${RED}❌ $skill_name${NC}"
        echo -e "   ${RED}Error:${NC} Frontmatter is not closed with a second '---'"
        ((ISSUES++))
        continue
    fi

    # Top-level keys = frontmatter lines that start at column 0 with "key:"
    top_keys=$(echo "$frontmatter" | grep -oE '^[A-Za-z][A-Za-z0-9_-]*:' | sed 's/:$//')

    # ===== DUPLICATE TOP-LEVEL FIELDS =====
    # YAML forbids duplicate keys in a mapping, and every check below reads the
    # first one - so a second 'description:' is validated by nobody and may be
    # the one a different parser keeps.
    dupes=$(echo "$top_keys" | sort | uniq -d)
    while IFS= read -r key; do
        [[ -z "$key" ]] && continue
        skill_errors+=("Duplicate top-level field '$key' (YAML mappings must have unique keys)")
    done <<< "$dupes"

    # ===== UNKNOWN TOP-LEVEL FIELDS =====
    # Anything outside the spec's field set risks breaking strict parsers on other agents.
    while IFS= read -r key; do
        [[ -z "$key" ]] && continue
        if ! echo " $ALLOWED_FIELDS " | grep -q " $key "; then
            skill_errors+=("Unknown top-level field '$key' (not in spec; move custom data under 'metadata:')")
        fi
    done <<< "$top_keys"

    # ===== NAME VALIDATION =====
    name_in_file=$(echo "$frontmatter" | grep -E '^name:' | head -1 | sed -E 's/^name:[[:space:]]*//' | sed -E 's/[[:space:]]*$//' | sed -E 's/^"(.*)"$/\1/;s/^'"'"'(.*)'"'"'$/\1/')

    if ! echo "$top_keys" | grep -qx "name"; then
        skill_errors+=("Missing required 'name' field")
    elif [[ -z "$name_in_file" ]]; then
        skill_errors+=("'name' is empty")
    else
        if [[ "$name_in_file" != "$skill_name" ]]; then
            skill_errors+=("Name mismatch: directory='$skill_name' but frontmatter='$name_in_file'")
        fi
        if [[ ${#name_in_file} -gt 64 ]]; then
            skill_errors+=("Name too long: ${#name_in_file} chars (max 64)")
        fi
        # a-z0-9, hyphen-separated, no leading/trailing/consecutive hyphens
        if ! [[ "$name_in_file" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
            skill_errors+=("Invalid name '$name_in_file' (lowercase a-z/0-9/hyphens only; no leading, trailing, or consecutive hyphens)")
        fi
    fi

    # ===== DESCRIPTION VALIDATION =====
    description=$(echo "$frontmatter" | grep -E '^description:' | head -1 | sed -E 's/^description:[[:space:]]*//' | sed -E 's/[[:space:]]*$//' | sed -E 's/^"(.*)"$/\1/;s/^'"'"'(.*)'"'"'$/\1/')

    if ! echo "$top_keys" | grep -qx "description"; then
        skill_errors+=("Missing required 'description' field")
    elif [[ "$description" =~ ^[\|\>][0-9+-]*$ ]]; then
        # A block scalar ('description: >-' and the text indented below) leaves
        # only the indicator on this line, so the length check below would
        # measure 2 characters and wave a 3000-character description through.
        # Measure the folded block instead.
        desc_block=$(echo "$frontmatter" | awk '/^description:/{d=1; next} d && /^[A-Za-z]/{d=0} d{print}')
        desc_len=$(echo "$desc_block" | tr -d '\n' | sed -E 's/^[[:space:]]+//' | wc -c | tr -d ' ')
        if [[ $desc_len -le 1 ]]; then
            skill_errors+=("'description' block scalar is empty (must be 1-1024 chars)")
        elif [[ $desc_len -gt 1024 ]]; then
            skill_errors+=("Description too long: ~$desc_len chars (max 1024)")
        fi
    elif [[ -z "$description" ]]; then
        skill_errors+=("'description' is empty (must be 1-1024 chars)")
    else
        desc_len=${#description}
        if [[ $desc_len -gt 1024 ]]; then
            skill_errors+=("Description too long: $desc_len chars (max 1024)")
        fi
    fi

    # ===== COMPATIBILITY VALIDATION =====
    if echo "$top_keys" | grep -qx "compatibility"; then
        compatibility=$(echo "$frontmatter" | grep -E '^compatibility:' | head -1 | sed -E 's/^compatibility:[[:space:]]*//' | sed -E 's/[[:space:]]*$//' | sed -E 's/^"(.*)"$/\1/;s/^'"'"'(.*)'"'"'$/\1/')
        if [[ -z "$compatibility" ]]; then
            skill_errors+=("'compatibility' is present but empty (must be 1-500 chars)")
        elif [[ ${#compatibility} -gt 500 ]]; then
            skill_errors+=("Compatibility too long: ${#compatibility} chars (max 500)")
        fi
    fi

    # ===== LICENSE VALIDATION =====
    # Spec allows ANY license name or reference; only flag an empty value.
    if echo "$top_keys" | grep -qx "license"; then
        license=$(echo "$frontmatter" | grep -E '^license:' | head -1 | sed -E 's/^license:[[:space:]]*//' | sed -E 's/[[:space:]]*$//')
        if [[ -z "$license" ]]; then
            skill_warnings+=("'license' is present but empty")
        fi
    fi

    # ===== ALLOWED-TOOLS VALIDATION =====
    # Must be a space-separated STRING on the same line, not a YAML block/list.
    if echo "$top_keys" | grep -qx "allowed-tools"; then
        at_value=$(echo "$frontmatter" | grep -E '^allowed-tools:' | head -1 | sed -E 's/^allowed-tools:[[:space:]]*//' | sed -E 's/[[:space:]]*$//')
        if [[ -z "$at_value" ]]; then
            skill_errors+=("'allowed-tools' must be an inline space-separated string, not a YAML list/block")
        fi
    fi

    # ===== METADATA VALIDATION =====
    # metadata is a map of string -> string. Flag unquoted numeric values (they parse as numbers, not strings).
    if echo "$top_keys" | grep -qx "metadata"; then
        # Lines indented under metadata, until the next top-level key
        meta_block=$(echo "$frontmatter" | awk '/^metadata:/{m=1; next} m && /^[A-Za-z]/{m=0} m{print}')
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            val=$(echo "$line" | sed -E 's/^[[:space:]]*[^:]+:[[:space:]]*//')
            if [[ "$val" =~ ^-?[0-9]+(\.[0-9]+)?$ ]]; then
                mkey=$(echo "$line" | sed -E 's/^[[:space:]]*([^:]+):.*/\1/')
                skill_warnings+=("metadata.$mkey='$val' is unquoted numeric (metadata values should be strings, e.g. \"$val\")")
            fi
        done <<< "$meta_block"
    fi

    # ===== FILE STRUCTURE VALIDATION =====
    line_count=$(wc -l < "$skill_file")
    if [[ $line_count -gt 500 ]]; then
        skill_warnings+=("SKILL.md is $line_count lines (spec recommends <500; move detail into references/)")
    fi

    # The whole body is loaded once the skill activates, and the spec puts that
    # budget at ~5000 tokens. Line count misses a short file with long lines,
    # which is the usual shape of a dense SKILL.md. ~4 chars per token.
    char_count=$(wc -c < "$skill_file" | tr -d ' ')
    approx_tokens=$((char_count / 4))
    if [[ $approx_tokens -gt 5000 ]]; then
        skill_warnings+=("SKILL.md is ~$approx_tokens tokens (spec recommends <5000 for the body; move reference material behind a pointer)")
    fi

    # ===== FILE REFERENCES =====
    # A link to a file that is not there sends the agent looking for material
    # that does not exist, and nothing else in this script would notice.
    while IFS= read -r ref; do
        [[ -z "$ref" ]] && continue
        target="${ref%%#*}"
        [[ -z "$target" ]] && continue                      # pure anchor
        [[ "$target" =~ ^(https?:|mailto:) ]] && continue   # external
        if [[ ! -e "$skill_dir$target" ]]; then
            skill_errors+=("Broken reference in SKILL.md: '$target' does not exist")
        fi
        # "Keep file references one level deep from SKILL.md."
        depth=$(echo "${target%/*}" | awk -F/ '{print NF}')
        if [[ "$target" == */* && $depth -gt 1 ]]; then
            skill_warnings+=("Reference '$target' is more than one level deep (spec: avoid deeply nested reference chains)")
        fi
    done < <(grep -oE '\]\([^)]+\)' "$skill_file" | sed -E 's/^\]\(//; s/\)$//')

    # ===== REPORT RESULTS =====
    if [[ ${#skill_errors[@]} -gt 0 ]]; then
        echo -e "${RED}❌ $skill_name${NC}"
        for error in "${skill_errors[@]}"; do
            echo -e "   ${RED}Error:${NC} $error"
        done
        for warning in "${skill_warnings[@]}"; do
            echo -e "   ${YELLOW}Warning:${NC} $warning"
        done
        ((ISSUES++))
    elif [[ ${#skill_warnings[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  $skill_name${NC}"
        for warning in "${skill_warnings[@]}"; do
            echo -e "   ${YELLOW}Warning:${NC} $warning"
        done
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓ $skill_name${NC}"
        ((PASSED++))
    fi
done

echo ""
echo "======================================================"
echo "Summary:"
echo -e "  ${GREEN}✓ Passed: $PASSED${NC}"
if [[ $WARNINGS -gt 0 ]]; then
    echo -e "  ${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
fi
if [[ $ISSUES -gt 0 ]]; then
    echo -e "  ${RED}❌ Issues: $ISSUES${NC}"
fi
echo ""

if [[ $ISSUES -eq 0 ]]; then
    echo -e "${GREEN}All skills are spec-compliant! ✓${NC}"
    exit 0
else
    echo -e "${RED}Found $ISSUES skill(s) with spec violations.${NC}"
    exit 1
fi

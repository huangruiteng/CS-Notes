#!/bin/bash

# OpenClaw Workspace Symlink Restorer
# Usage: Run this script inside ~/.openclaw/workspace/ on the remote machine
# or ensure CS-Notes is in the current directory.

WORKSPACE_DIR="$HOME/.openclaw/workspace"
CS_NOTES_DIR="CS-Notes"

# Mappings of LinkName -> SourcePath (relative to CS-Notes)
# Use space as separator, format: "LinkName:SourcePath"
MAPPINGS=(
    "AGENTS.md:.openclaw-memory/AGENTS.md"
    "HEARTBEAT.md:.openclaw-memory/HEARTBEAT.md"
    "IDENTITY.md:.openclaw-memory/IDENTITY.md"
    "MEMORY.md:.openclaw-memory/MEMORY.md"
    "SOUL.md:.openclaw-memory/SOUL.md"
    "TOOLS.md:.openclaw-memory/TOOLS.md"
    "USER.md:.openclaw-memory/USER.md"
    "memory:.openclaw-memory/memory"
    "skills:.trae/openclaw-skills"
)

echo "Starting OpenClaw symlink restoration..."
echo "Workspace: $WORKSPACE_DIR"

cd "$WORKSPACE_DIR" || { echo "Error: Cannot change to workspace directory $WORKSPACE_DIR"; exit 1; }

if [ ! -d "$CS_NOTES_DIR" ]; then
    echo "Error: $CS_NOTES_DIR directory not found in $WORKSPACE_DIR."
    echo "Please ensure you have cloned the repo or are in the right directory."
    exit 1
fi

for mapping in "${MAPPINGS[@]}"; do
    link_name="${mapping%%:*}"
    source_path="${mapping#*:}"
    target="$CS_NOTES_DIR/$source_path"
    
    # Check if the source file actually exists in CS-Notes
    if [ ! -e "$target" ]; then
        echo "Warning: Source file $target does not exist. Skipping..."
        continue
    fi

    # Check if the destination exists
    if [ -e "$link_name" ]; then
        # Check if it is already a symlink
        if [ -L "$link_name" ]; then
            current_link=$(readlink "$link_name")
            if [ "$current_link" == "$target" ]; then
                echo "[OK] $link_name is already correctly linked."
                continue
            else
                echo "[FIX] $link_name is a symlink but points to '$current_link'. Relinking..."
                rm "$link_name"
            fi
        else
            echo "[FIX] $link_name is a regular file/directory. Deleting and linking..."
            rm -rf "$link_name"
        fi
    else
        echo "[NEW] $link_name does not exist. Creating link..."
    fi

    # Create the symlink
    ln -s "$target" "$link_name"
    echo "     -> Linked $link_name to $target"
done

echo "Restoration complete."
ls -laH

#!/bin/bash
# Filter bee output to show clean progress
# Suppresses verbose streaming logs and adds task completion counter

task_count=0
total_tasks=0

while IFS= read -r line; do
    # Extract total tasks from initial output (if available)
    if [[ "$line" =~ num_truncate.*=.*([0-9]+) ]]; then
        total_tasks="${BASH_REMATCH[1]}"
    fi
    
    # Count completed tasks
    if [[ "$line" =~ Task.*succeeded ]]; then
        ((task_count++))
        if [[ $total_tasks -gt 0 ]]; then
            echo "✓ Task completed [$task_count/$total_tasks]"
        else
            echo "✓ Task $task_count completed"
        fi
    fi
    
    # Filter out streaming noise
    if [[ "$line" =~ \[focused\]\ (Processing\ new\ streaming\ response|Processed\ [0-9]+\ stream\ events|Finished\ processing\ a\ streaming\ response) ]]; then
        continue  # Skip this line
    fi
    
    # Skip empty lines
    if [[ -z "${line// }" ]]; then
        continue
    fi
    
    # Print everything else
    echo "$line"
done


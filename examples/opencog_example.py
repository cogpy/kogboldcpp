#!/usr/bin/env python3
"""
OpenCog Orchestrator Example for KoboldCPP

This example demonstrates how to use the OpenCog autonomous orchestrator
to submit goals, manage tasks, and query the knowledge base.

Prerequisites:
- KoboldCPP running with --opencog flag enabled
- Model loaded in KoboldCPP
- Default port 5001 (or adjust BASE_URL below)

Usage:
    python opencog_example.py
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:5001"
TIMEOUT = 5  # seconds

def check_orchestrator_available():
    """Check if the OpenCog orchestrator is available"""
    try:
        response = requests.get(f"{BASE_URL}/api/extra/opencog/status", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            return data.get('enabled', False)
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to KoboldCPP: {e}")
        return False

def get_status():
    """Get the current status of the orchestrator"""
    try:
        response = requests.get(f"{BASE_URL}/api/extra/opencog/status", timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting status: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def submit_goal(goal_text, priority=0.5):
    """Submit a high-level goal to the orchestrator"""
    try:
        payload = {
            "goal": goal_text,
            "priority": priority
        }
        response = requests.post(
            f"{BASE_URL}/api/extra/opencog/submit_goal",
            json=payload,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error submitting goal: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def submit_task(agent_name, task_name, description, priority=0.5):
    """Submit a specific task to an agent"""
    try:
        payload = {
            "agent": agent_name,
            "name": task_name,
            "description": description,
            "priority": priority
        }
        response = requests.post(
            f"{BASE_URL}/api/extra/opencog/submit_task",
            json=payload,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error submitting task: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def query_knowledge(pattern):
    """Query the knowledge base"""
    try:
        payload = {"pattern": pattern}
        response = requests.post(
            f"{BASE_URL}/api/extra/opencog/query",
            json=payload,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error querying knowledge: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def get_atomspace_snapshot():
    """Get a snapshot of the entire knowledge base"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/extra/opencog/atomspace",
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting atomspace: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def main():
    """Main example workflow"""
    print("="*60)
    print("OpenCog Orchestrator Example for KoboldCPP")
    print("="*60)
    print()
    
    # Check if orchestrator is available
    print("1. Checking if OpenCog orchestrator is available...")
    if not check_orchestrator_available():
        print("\nERROR: OpenCog orchestrator is not available!")
        print("\nMake sure KoboldCPP is running with the --opencog flag:")
        print("  python koboldcpp.py --model your_model.gguf --opencog")
        sys.exit(1)
    print("   ✓ OpenCog orchestrator is available!\n")
    
    # Get initial status
    print("2. Getting orchestrator status...")
    status = get_status()
    if status:
        print(f"   Running: {status.get('running', False)}")
        print(f"   Agents: {len(status.get('agents', []))}")
        for agent in status.get('agents', []):
            print(f"     - {agent['name']}: {agent['pending_tasks']} pending tasks")
        print(f"   Total atoms in knowledge base: {status.get('atomspace', {}).get('total_atoms', 0)}")
    print()
    
    # Submit some goals
    print("3. Submitting goals...")
    
    goal1 = submit_goal(
        "Generate creative story ideas about artificial intelligence",
        priority=0.9
    )
    if goal1 and goal1.get('success'):
        print(f"   ✓ Goal 1 submitted: {goal1.get('task_id', 'N/A')}")
    
    goal2 = submit_goal(
        "Analyze trends in technology adoption",
        priority=0.7
    )
    if goal2 and goal2.get('success'):
        print(f"   ✓ Goal 2 submitted: {goal2.get('task_id', 'N/A')}")
    
    goal3 = submit_goal(
        "Summarize recent developments in AI safety",
        priority=0.8
    )
    if goal3 and goal3.get('success'):
        print(f"   ✓ Goal 3 submitted: {goal3.get('task_id', 'N/A')}")
    print()
    
    # Submit specific tasks
    print("4. Submitting specific tasks...")
    
    task1 = submit_task(
        "reasoner",
        "analyze_patterns",
        "Identify common patterns in user behavior",
        priority=0.6
    )
    if task1 and task1.get('success'):
        print(f"   ✓ Task 1 submitted to reasoner: {task1.get('task_id', 'N/A')}")
    
    task2 = submit_task(
        "executor",
        "format_output",
        "Format analysis results in readable format",
        priority=0.5
    )
    if task2 and task2.get('success'):
        print(f"   ✓ Task 2 submitted to executor: {task2.get('task_id', 'N/A')}")
    print()
    
    # Wait a moment for processing
    print("5. Waiting for agents to process tasks...")
    time.sleep(2)
    print("   (Processing...)")
    print()
    
    # Query the knowledge base
    print("6. Querying knowledge base for goals...")
    goals_query = query_knowledge({"type": "goal"})
    if goals_query and goals_query.get('success'):
        results = goals_query.get('results', [])
        print(f"   Found {len(results)} goals in knowledge base:")
        for i, goal in enumerate(results, 1):
            tv = goal.get('truth_value', {})
            print(f"     {i}. {goal.get('name', 'Unknown')}")
            print(f"        Strength: {tv.get('strength', 0):.2f}, "
                  f"Confidence: {tv.get('confidence', 0):.2f}")
    print()
    
    # Get updated status
    print("7. Getting updated orchestrator status...")
    status = get_status()
    if status:
        print(f"   Running: {status.get('running', False)}")
        print(f"   Agents: {len(status.get('agents', []))}")
        for agent in status.get('agents', []):
            print(f"     - {agent['name']}: "
                  f"{agent['total_tasks']} total tasks, "
                  f"{agent['pending_tasks']} pending")
        print(f"   Total atoms in knowledge base: "
              f"{status.get('atomspace', {}).get('total_atoms', 0)}")
    print()
    
    # Get atomspace snapshot
    print("8. Getting knowledge base snapshot...")
    snapshot = get_atomspace_snapshot()
    if snapshot and snapshot.get('success'):
        atomspace = snapshot.get('atomspace', {})
        total_atoms = atomspace.get('total_atoms', 0)
        print(f"   Total atoms: {total_atoms}")
        
        # Show atom type distribution
        atoms = atomspace.get('atoms', [])
        if atoms:
            types = {}
            for atom in atoms:
                atom_type = atom.get('type', 'unknown')
                types[atom_type] = types.get(atom_type, 0) + 1
            print("   Atom types:")
            for atom_type, count in sorted(types.items()):
                print(f"     - {atom_type}: {count}")
    print()
    
    print("="*60)
    print("Example completed successfully!")
    print("="*60)
    print()
    print("You can now:")
    print("- Submit more goals or tasks")
    print("- Query the knowledge base")
    print("- Monitor agent status")
    print("- Build more complex workflows")
    print()
    print("See docs/OPENCOG_ORCHESTRATOR.md for full API documentation")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

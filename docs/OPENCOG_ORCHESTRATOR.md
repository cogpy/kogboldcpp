# OpenCog Autonomous Orchestrator for KoboldCPP

This module implements an OpenCog-inspired autonomous orchestrator agent system for KoboldCPP, enabling advanced task coordination, reasoning, and autonomous goal achievement.

## Overview

The OpenCog orchestrator provides:

- **AtomSpace**: Knowledge representation system for storing concepts, goals, beliefs, and relationships
- **CogServer**: Agent coordination system that schedules and manages multiple cognitive agents
- **Cognitive Agents**: Specialized agents for planning, reasoning, and execution
- **LLM Integration**: Direct integration with KoboldCPP's language model backend

## Features

1. **Autonomous Goal Processing**: Submit high-level goals that are automatically broken down and executed
2. **Multi-Agent Coordination**: Multiple specialized agents work together to accomplish complex tasks
3. **Knowledge Base**: Persistent knowledge representation using an AtomSpace-inspired graph database
4. **Task Scheduling**: Intelligent task prioritization and scheduling across agents
5. **LLM-Powered Reasoning**: Agents can leverage the loaded language model for decision-making

## Enabling the Orchestrator

To enable the OpenCog orchestrator, add the `--opencog` flag when starting KoboldCPP:

```bash
python koboldcpp.py --model your_model.gguf --opencog
```

Or in the GUI, enable the "OpenCog Orchestrator" checkbox (if available).

## API Endpoints

Once enabled, the following API endpoints are available:

### 1. Get Status

**Endpoint**: `/api/extra/opencog/status`  
**Method**: GET  
**Description**: Get the current status of the orchestrator and all agents

**Response**:
```json
{
  "enabled": true,
  "running": true,
  "agents": [
    {
      "name": "planner",
      "active": true,
      "pending_tasks": 2,
      "total_tasks": 5
    },
    {
      "name": "reasoner",
      "active": true,
      "pending_tasks": 0,
      "total_tasks": 3
    }
  ],
  "atomspace": {
    "total_atoms": 42
  }
}
```

### 2. Submit Goal

**Endpoint**: `/api/extra/opencog/submit_goal`  
**Method**: POST  
**Description**: Submit a high-level goal for the orchestrator to achieve

**Request Body**:
```json
{
  "goal": "Analyze the sentiment of user feedback",
  "priority": 0.8
}
```

**Response**:
```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 3. Submit Task

**Endpoint**: `/api/extra/opencog/submit_task`  
**Method**: POST  
**Description**: Submit a specific task to a particular agent

**Request Body**:
```json
{
  "agent": "executor",
  "name": "process_data",
  "description": "Process and clean input data",
  "priority": 0.6
}
```

**Response**:
```json
{
  "success": true,
  "task_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

### 4. Query Knowledge Base

**Endpoint**: `/api/extra/opencog/query`  
**Method**: POST  
**Description**: Query the knowledge base (AtomSpace) for specific information

**Request Body**:
```json
{
  "pattern": {
    "type": "goal",
    "name": "sentiment"
  }
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "id": "atom-123",
      "type": "goal",
      "name": "Analyze the sentiment of user feedback",
      "truth_value": {
        "strength": 0.8,
        "confidence": 0.7
      },
      "metadata": {
        "priority": 0.8,
        "timestamp": 1234567890.0
      }
    }
  ]
}
```

### 5. Get AtomSpace Snapshot

**Endpoint**: `/api/extra/opencog/atomspace`  
**Method**: GET  
**Description**: Get a complete snapshot of the knowledge base

**Response**:
```json
{
  "success": true,
  "atomspace": {
    "atoms": [...],
    "total_atoms": 42
  }
}
```

## Agent Types

The orchestrator includes three default agents:

1. **Planner**: Breaks down high-level goals into actionable tasks
2. **Reasoner**: Analyzes context and makes logical inferences
3. **Executor**: Executes specific tasks and actions

Additional agents can be created dynamically through the API.

## Python Usage Example

```python
import requests
import json

BASE_URL = "http://localhost:5001"

# Submit a goal
goal_response = requests.post(
    f"{BASE_URL}/api/extra/opencog/submit_goal",
    json={
        "goal": "Generate creative story ideas about space exploration",
        "priority": 0.9
    }
)
print("Goal submitted:", goal_response.json())

# Check orchestrator status
status_response = requests.get(f"{BASE_URL}/api/extra/opencog/status")
print("Status:", status_response.json())

# Query for goals
query_response = requests.post(
    f"{BASE_URL}/api/extra/opencog/query",
    json={
        "pattern": {"type": "goal"}
    }
)
print("Active goals:", query_response.json())

# Submit a specific task
task_response = requests.post(
    f"{BASE_URL}/api/extra/opencog/submit_task",
    json={
        "agent": "reasoner",
        "name": "analyze_themes",
        "description": "Analyze common themes in generated stories",
        "priority": 0.7
    }
)
print("Task submitted:", task_response.json())
```

## Architecture

The orchestrator follows OpenCog principles:

```
┌─────────────────────────────────────┐
│      OpenCog Orchestrator           │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐  │
│  │       AtomSpace              │  │
│  │  (Knowledge Representation)  │  │
│  └──────────────────────────────┘  │
│              ▲                      │
│              │                      │
│  ┌──────────┴───────────────────┐  │
│  │       CogServer              │  │
│  │  (Agent Coordination)        │  │
│  └──────────────────────────────┘  │
│       ▲         ▲         ▲        │
│       │         │         │        │
│  ┌────┴───┐ ┌──┴────┐ ┌──┴─────┐  │
│  │Planner │ │Reasoner│ │Executor│  │
│  │ Agent  │ │ Agent  │ │ Agent  │  │
│  └────────┘ └────────┘ └────────┘  │
│                                     │
└─────────────────────────────────────┘
             ▲
             │ LLM Callback
             ▼
┌─────────────────────────────────────┐
│        KoboldCPP Backend            │
│     (Language Model Inference)      │
└─────────────────────────────────────┘
```

## Use Cases

1. **Autonomous Task Execution**: Let the orchestrator break down and execute complex multi-step tasks
2. **Knowledge Management**: Build and maintain a knowledge base that persists across interactions
3. **Multi-Agent Workflows**: Coordinate multiple specialized agents for complex reasoning tasks
4. **Goal-Oriented Behavior**: Define high-level goals and let the system figure out how to achieve them
5. **Context-Aware Decision Making**: Leverage the knowledge base for informed decision making

## Technical Details

### AtomSpace

The AtomSpace is a hypergraph-based knowledge representation system where:
- **Atoms** are the basic units of knowledge
- **Links** connect atoms to form relationships
- **Truth Values** represent probabilistic confidence in beliefs
- **Metadata** stores additional contextual information

### CogServer

The CogServer manages:
- Agent registration and lifecycle
- Task scheduling and prioritization
- Resource allocation
- Inter-agent communication

### Cognitive Agents

Each agent has:
- A task queue with priority sorting
- Access to the shared AtomSpace
- Optional LLM callback for reasoning
- Independent execution threads

## Performance Considerations

- The orchestrator runs in separate threads to avoid blocking the main LLM inference
- Task execution is asynchronous to allow concurrent processing
- The AtomSpace uses efficient indexing for fast queries
- Memory usage scales with the number of atoms in the knowledge base

## Limitations

- The orchestrator is currently in an early implementation stage
- LLM integration is simplified and may need refinement for production use
- The system is designed for experimentation and research
- For production deployments, additional testing and hardening is recommended

## Future Enhancements

Potential future improvements:
- More sophisticated reasoning algorithms
- Pattern matching and inference engines
- Persistent storage backend for the AtomSpace
- Advanced agent communication protocols
- Integration with external knowledge sources
- Visual knowledge graph explorer

## Contributing

Contributions to improve the orchestrator are welcome! Areas of interest:
- Enhanced cognitive algorithms
- Additional agent types
- Better LLM integration strategies
- Performance optimizations
- Documentation improvements

## References

- OpenCog Project: https://opencog.org/
- OpenCog Hyperon: https://wiki.opencog.org/w/Hyperon
- AtomSpace Documentation: https://wiki.opencog.org/w/AtomSpace
- CogServer Architecture: https://wiki.opencog.org/w/CogServer

## Support

For issues or questions:
1. Check the KoboldCPP documentation
2. Review this README
3. Open an issue on the repository
4. Join the community discussions

## License

This implementation follows the KoboldCPP license terms. The OpenCog-inspired architecture is based on concepts from the OpenCog project.

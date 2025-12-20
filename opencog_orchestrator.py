#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenCog-inspired Autonomous Orchestrator Agent for KoboldCPP

This module implements an autonomous agent orchestration system inspired by
OpenCog's cognitive architecture principles, including:
- AtomSpace-like knowledge representation
- CogServer-like agent coordination
- Autonomous task planning and execution
- Integration with KoboldCPP's LLM backend
"""

import json
import time
import threading
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AtomType(Enum):
    """Types of atoms in the knowledge space"""
    CONCEPT = "concept"
    PREDICATE = "predicate"
    GOAL = "goal"
    ACTION = "action"
    BELIEF = "belief"
    PLAN = "plan"


class TruthValue:
    """Probabilistic truth value for atoms"""
    def __init__(self, strength: float = 0.5, confidence: float = 0.5):
        self.strength = max(0.0, min(1.0, strength))
        self.confidence = max(0.0, min(1.0, confidence))
    
    def to_dict(self) -> Dict[str, float]:
        return {"strength": self.strength, "confidence": self.confidence}


@dataclass
class Atom:
    """Basic unit of knowledge representation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    atom_type: AtomType = AtomType.CONCEPT
    name: str = ""
    truth_value: TruthValue = field(default_factory=TruthValue)
    outgoing: List[str] = field(default_factory=list)  # Links to other atoms
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.atom_type.value,
            "name": self.name,
            "truth_value": self.truth_value.to_dict(),
            "outgoing": self.outgoing,
            "metadata": self.metadata,
            "created_at": self.created_at
        }


class AtomSpace:
    """
    Knowledge representation system inspired by OpenCog's AtomSpace.
    Stores and manages atoms and their relationships.
    """
    def __init__(self):
        self.atoms: Dict[str, Atom] = {}
        self.lock = threading.RLock()
        self.index_by_type: Dict[AtomType, List[str]] = {t: [] for t in AtomType}
        logger.info("AtomSpace initialized")
    
    def add_atom(self, atom: Atom) -> Atom:
        """Add an atom to the space"""
        with self.lock:
            self.atoms[atom.id] = atom
            self.index_by_type[atom.atom_type].append(atom.id)
            logger.debug(f"Added atom: {atom.name} ({atom.atom_type.value})")
            return atom
    
    def get_atom(self, atom_id: str) -> Optional[Atom]:
        """Retrieve an atom by ID"""
        with self.lock:
            return self.atoms.get(atom_id)
    
    def get_atoms_by_type(self, atom_type: AtomType) -> List[Atom]:
        """Get all atoms of a specific type"""
        with self.lock:
            atom_ids = self.index_by_type.get(atom_type, [])
            return [self.atoms[aid] for aid in atom_ids if aid in self.atoms]
    
    def update_truth_value(self, atom_id: str, strength: float, confidence: float):
        """Update an atom's truth value"""
        with self.lock:
            if atom_id in self.atoms:
                self.atoms[atom_id].truth_value = TruthValue(strength, confidence)
    
    def query(self, pattern: Dict[str, Any]) -> List[Atom]:
        """Query atoms matching a pattern"""
        with self.lock:
            results = []
            for atom in self.atoms.values():
                if self._matches_pattern(atom, pattern):
                    results.append(atom)
            return results
    
    def _matches_pattern(self, atom: Atom, pattern: Dict[str, Any]) -> bool:
        """Check if an atom matches a query pattern"""
        if "type" in pattern and atom.atom_type.value != pattern["type"]:
            return False
        if "name" in pattern and pattern["name"] not in atom.name:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Export atomspace to dictionary"""
        with self.lock:
            return {
                "atoms": [atom.to_dict() for atom in self.atoms.values()],
                "total_atoms": len(self.atoms)
            }


@dataclass
class AgentTask:
    """Represents a task for the agent to execute"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    priority: float = 0.5
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Any] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }


class CognitiveAgent:
    """
    Base cognitive agent that can process tasks and interact with the LLM
    """
    def __init__(self, name: str, atomspace: AtomSpace, llm_callback: Optional[Callable] = None):
        self.name = name
        self.atomspace = atomspace
        self.llm_callback = llm_callback
        self.tasks: Dict[str, AgentTask] = {}
        self.active = True
        self.lock = threading.RLock()
        logger.info(f"CognitiveAgent '{name}' initialized")
    
    def add_task(self, task: AgentTask) -> str:
        """Add a task to the agent's queue"""
        with self.lock:
            self.tasks[task.id] = task
            logger.info(f"Agent '{self.name}' received task: {task.name}")
            return task.id
    
    def execute_task(self, task_id: str) -> Optional[Any]:
        """Execute a specific task"""
        with self.lock:
            if task_id not in self.tasks:
                logger.error(f"Task {task_id} not found")
                return None
            
            task = self.tasks[task_id]
            task.status = "running"
        
        try:
            logger.info(f"Executing task: {task.name}")
            
            # Use LLM to help execute the task if callback is available
            if self.llm_callback:
                result = self.llm_callback({
                    "prompt": f"Task: {task.name}\nDescription: {task.description}\nProvide a solution:",
                    "max_length": 256
                })
                task.result = result
            else:
                task.result = {"message": "Task processed without LLM"}
            
            # Update knowledge base
            task_atom = Atom(
                atom_type=AtomType.ACTION,
                name=f"completed_task_{task.name}",
                truth_value=TruthValue(0.9, 0.8),
                metadata={"task_id": task.id, "result": task.result}
            )
            self.atomspace.add_atom(task_atom)
            
            task.status = "completed"
            task.completed_at = time.time()
            logger.info(f"Task completed: {task.name}")
            
            return task.result
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.status = "failed"
            task.result = {"error": str(e)}
            return None
    
    def get_pending_tasks(self) -> List[AgentTask]:
        """Get all pending tasks sorted by priority"""
        with self.lock:
            pending = [t for t in self.tasks.values() if t.status == "pending"]
            return sorted(pending, key=lambda x: x.priority, reverse=True)


class CogServer:
    """
    Agent orchestration and coordination system inspired by OpenCog's CogServer.
    Manages multiple agents and schedules their tasks.
    """
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        self.agents: Dict[str, CognitiveAgent] = {}
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()
        logger.info("CogServer initialized")
    
    def register_agent(self, agent: CognitiveAgent):
        """Register an agent with the orchestrator"""
        with self.lock:
            self.agents[agent.name] = agent
            logger.info(f"Registered agent: {agent.name}")
    
    def unregister_agent(self, agent_name: str):
        """Remove an agent from the orchestrator"""
        with self.lock:
            if agent_name in self.agents:
                del self.agents[agent_name]
                logger.info(f"Unregistered agent: {agent_name}")
    
    def submit_task(self, agent_name: str, task: AgentTask) -> Optional[str]:
        """Submit a task to a specific agent"""
        with self.lock:
            if agent_name not in self.agents:
                logger.error(f"Agent {agent_name} not found")
                return None
            
            return self.agents[agent_name].add_task(task)
    
    def start(self):
        """Start the orchestrator's scheduling loop"""
        if self.running:
            logger.warning("CogServer already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._scheduling_loop, daemon=True)
        self.worker_thread.start()
        logger.info("CogServer started")
    
    def stop(self):
        """Stop the orchestrator"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        logger.info("CogServer stopped")
    
    def _scheduling_loop(self):
        """Main scheduling loop that processes agent tasks"""
        while self.running:
            try:
                with self.lock:
                    for agent in self.agents.values():
                        if not agent.active:
                            continue
                        
                        # Get highest priority pending task
                        pending_tasks = agent.get_pending_tasks()
                        if pending_tasks:
                            task = pending_tasks[0]
                            # Execute task in separate thread to avoid blocking
                            threading.Thread(
                                target=agent.execute_task,
                                args=(task.id,),
                                daemon=True
                            ).start()
                
                time.sleep(0.1)  # Brief sleep to avoid CPU spinning
                
            except Exception as e:
                logger.error(f"Error in scheduling loop: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the orchestrator"""
        with self.lock:
            return {
                "running": self.running,
                "agents": [
                    {
                        "name": agent.name,
                        "active": agent.active,
                        "pending_tasks": len(agent.get_pending_tasks()),
                        "total_tasks": len(agent.tasks)
                    }
                    for agent in self.agents.values()
                ],
                "atomspace": {
                    "total_atoms": len(self.atomspace.atoms)
                }
            }


class OpenCogOrchestrator:
    """
    Main orchestrator interface that integrates with KoboldCPP.
    Provides high-level API for autonomous agent coordination.
    """
    def __init__(self, llm_callback: Optional[Callable] = None):
        self.atomspace = AtomSpace()
        self.cogserver = CogServer(self.atomspace)
        self.llm_callback = llm_callback
        
        # Create default agents
        self._initialize_default_agents()
        
        logger.info("OpenCogOrchestrator initialized")
    
    def _initialize_default_agents(self):
        """Initialize default cognitive agents"""
        # Planning agent
        planner = CognitiveAgent("planner", self.atomspace, self.llm_callback)
        self.cogserver.register_agent(planner)
        
        # Reasoning agent
        reasoner = CognitiveAgent("reasoner", self.atomspace, self.llm_callback)
        self.cogserver.register_agent(reasoner)
        
        # Execution agent
        executor = CognitiveAgent("executor", self.atomspace, self.llm_callback)
        self.cogserver.register_agent(executor)
    
    def start(self):
        """Start the orchestrator"""
        self.cogserver.start()
        logger.info("OpenCogOrchestrator started")
    
    def stop(self):
        """Stop the orchestrator"""
        self.cogserver.stop()
        logger.info("OpenCogOrchestrator stopped")
    
    def create_agent(self, name: str) -> str:
        """Create a new cognitive agent"""
        agent = CognitiveAgent(name, self.atomspace, self.llm_callback)
        self.cogserver.register_agent(agent)
        return name
    
    def submit_goal(self, goal: str, priority: float = 0.5) -> str:
        """Submit a high-level goal to be accomplished"""
        # Create goal atom
        goal_atom = Atom(
            atom_type=AtomType.GOAL,
            name=goal,
            truth_value=TruthValue(0.8, 0.7),
            metadata={"priority": priority, "timestamp": time.time()}
        )
        self.atomspace.add_atom(goal_atom)
        
        # Break down into task for planner
        task = AgentTask(
            name=f"plan_goal",
            description=f"Create a plan to achieve: {goal}",
            priority=priority
        )
        task_id = self.cogserver.submit_task("planner", task)
        
        logger.info(f"Goal submitted: {goal}")
        return task_id or ""
    
    def submit_task(self, agent_name: str, task_name: str, description: str, priority: float = 0.5) -> Optional[str]:
        """Submit a task to a specific agent"""
        task = AgentTask(
            name=task_name,
            description=description,
            priority=priority
        )
        return self.cogserver.submit_task(agent_name, task)
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return self.cogserver.get_status()
    
    def query_knowledge(self, pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query the knowledge base"""
        atoms = self.atomspace.query(pattern)
        return [atom.to_dict() for atom in atoms]
    
    def get_atomspace_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of the entire atomspace"""
        return self.atomspace.to_dict()


# Global orchestrator instance
_orchestrator_instance: Optional[OpenCogOrchestrator] = None


def get_orchestrator(llm_callback: Optional[Callable] = None) -> OpenCogOrchestrator:
    """Get or create the global orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OpenCogOrchestrator(llm_callback)
    return _orchestrator_instance


def reset_orchestrator():
    """Reset the global orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance:
        _orchestrator_instance.stop()
    _orchestrator_instance = None


if __name__ == "__main__":
    # Example usage
    print("OpenCog Orchestrator - Example Usage")
    print("=" * 50)
    
    # Create orchestrator
    orchestrator = OpenCogOrchestrator()
    orchestrator.start()
    
    # Submit some goals
    orchestrator.submit_goal("Analyze user preferences", priority=0.8)
    orchestrator.submit_goal("Generate creative content", priority=0.6)
    
    # Submit specific tasks
    orchestrator.submit_task(
        "reasoner",
        "analyze_context",
        "Analyze the current conversation context",
        priority=0.7
    )
    
    # Wait a bit for processing
    time.sleep(2)
    
    # Check status
    status = orchestrator.get_status()
    print("\nOrchestrator Status:")
    print(json.dumps(status, indent=2))
    
    # Query knowledge
    goals = orchestrator.query_knowledge({"type": "goal"})
    print(f"\nActive Goals: {len(goals)}")
    
    # Get atomspace snapshot
    snapshot = orchestrator.get_atomspace_snapshot()
    print(f"\nTotal Atoms in Knowledge Base: {snapshot['total_atoms']}")
    
    # Cleanup
    orchestrator.stop()
    print("\nOrchestrator stopped.")

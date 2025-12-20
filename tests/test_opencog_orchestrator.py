#!/usr/bin/env python3
"""
Unit tests for the OpenCog Orchestrator

Run with: python -m pytest tests/test_opencog_orchestrator.py -v
Or: python tests/test_opencog_orchestrator.py
"""

import unittest
import sys
import os
import time

# Add parent directory to path to import the orchestrator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opencog_orchestrator import (
    AtomSpace, Atom, AtomType, TruthValue,
    CognitiveAgent, CogServer, AgentTask,
    OpenCogOrchestrator, get_orchestrator, reset_orchestrator
)


class TestTruthValue(unittest.TestCase):
    """Test TruthValue class"""
    
    def test_creation(self):
        """Test creating truth values"""
        tv = TruthValue(0.8, 0.9)
        self.assertEqual(tv.strength, 0.8)
        self.assertEqual(tv.confidence, 0.9)
    
    def test_bounds(self):
        """Test that truth values are bounded [0, 1]"""
        tv = TruthValue(1.5, -0.5)
        self.assertEqual(tv.strength, 1.0)
        self.assertEqual(tv.confidence, 0.0)
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        tv = TruthValue(0.7, 0.6)
        d = tv.to_dict()
        self.assertEqual(d['strength'], 0.7)
        self.assertEqual(d['confidence'], 0.6)


class TestAtom(unittest.TestCase):
    """Test Atom class"""
    
    def test_creation(self):
        """Test creating atoms"""
        atom = Atom(
            atom_type=AtomType.CONCEPT,
            name="test_concept",
            truth_value=TruthValue(0.9, 0.8)
        )
        self.assertEqual(atom.atom_type, AtomType.CONCEPT)
        self.assertEqual(atom.name, "test_concept")
        self.assertIsNotNone(atom.id)
    
    def test_to_dict(self):
        """Test atom serialization"""
        atom = Atom(
            atom_type=AtomType.GOAL,
            name="test_goal",
            metadata={"priority": 0.8}
        )
        d = atom.to_dict()
        self.assertEqual(d['type'], 'goal')
        self.assertEqual(d['name'], 'test_goal')
        self.assertEqual(d['metadata']['priority'], 0.8)


class TestAtomSpace(unittest.TestCase):
    """Test AtomSpace class"""
    
    def setUp(self):
        """Create a fresh atomspace for each test"""
        self.atomspace = AtomSpace()
    
    def test_add_atom(self):
        """Test adding atoms"""
        atom = Atom(atom_type=AtomType.CONCEPT, name="test")
        self.atomspace.add_atom(atom)
        self.assertEqual(len(self.atomspace.atoms), 1)
        self.assertIn(atom.id, self.atomspace.atoms)
    
    def test_get_atom(self):
        """Test retrieving atoms"""
        atom = Atom(atom_type=AtomType.CONCEPT, name="test")
        self.atomspace.add_atom(atom)
        retrieved = self.atomspace.get_atom(atom.id)
        self.assertEqual(retrieved.id, atom.id)
        self.assertEqual(retrieved.name, atom.name)
    
    def test_get_atoms_by_type(self):
        """Test filtering atoms by type"""
        concept1 = Atom(atom_type=AtomType.CONCEPT, name="concept1")
        concept2 = Atom(atom_type=AtomType.CONCEPT, name="concept2")
        goal1 = Atom(atom_type=AtomType.GOAL, name="goal1")
        
        self.atomspace.add_atom(concept1)
        self.atomspace.add_atom(concept2)
        self.atomspace.add_atom(goal1)
        
        concepts = self.atomspace.get_atoms_by_type(AtomType.CONCEPT)
        goals = self.atomspace.get_atoms_by_type(AtomType.GOAL)
        
        self.assertEqual(len(concepts), 2)
        self.assertEqual(len(goals), 1)
    
    def test_update_truth_value(self):
        """Test updating atom truth values"""
        atom = Atom(atom_type=AtomType.BELIEF, name="belief")
        self.atomspace.add_atom(atom)
        
        self.atomspace.update_truth_value(atom.id, 0.95, 0.85)
        updated = self.atomspace.get_atom(atom.id)
        
        self.assertEqual(updated.truth_value.strength, 0.95)
        self.assertEqual(updated.truth_value.confidence, 0.85)
    
    def test_query(self):
        """Test querying atoms"""
        self.atomspace.add_atom(Atom(atom_type=AtomType.GOAL, name="goal_test"))
        self.atomspace.add_atom(Atom(atom_type=AtomType.CONCEPT, name="concept_test"))
        self.atomspace.add_atom(Atom(atom_type=AtomType.GOAL, name="another_goal"))
        
        # Query by type
        results = self.atomspace.query({"type": "goal"})
        self.assertEqual(len(results), 2)
        
        # Query by name pattern
        results = self.atomspace.query({"name": "test"})
        self.assertEqual(len(results), 2)
    
    def test_to_dict(self):
        """Test atomspace serialization"""
        self.atomspace.add_atom(Atom(atom_type=AtomType.CONCEPT, name="test"))
        d = self.atomspace.to_dict()
        self.assertEqual(d['total_atoms'], 1)
        self.assertIn('atoms', d)


class TestAgentTask(unittest.TestCase):
    """Test AgentTask class"""
    
    def test_creation(self):
        """Test creating tasks"""
        task = AgentTask(
            name="test_task",
            description="Test description",
            priority=0.8
        )
        self.assertEqual(task.name, "test_task")
        self.assertEqual(task.status, "pending")
        self.assertEqual(task.priority, 0.8)
    
    def test_to_dict(self):
        """Test task serialization"""
        task = AgentTask(name="test", description="desc")
        d = task.to_dict()
        self.assertEqual(d['name'], 'test')
        self.assertEqual(d['description'], 'desc')
        self.assertEqual(d['status'], 'pending')


class TestCognitiveAgent(unittest.TestCase):
    """Test CognitiveAgent class"""
    
    def setUp(self):
        """Create agent for testing"""
        self.atomspace = AtomSpace()
        self.agent = CognitiveAgent("test_agent", self.atomspace)
    
    def test_creation(self):
        """Test agent creation"""
        self.assertEqual(self.agent.name, "test_agent")
        self.assertTrue(self.agent.active)
        self.assertEqual(len(self.agent.tasks), 0)
    
    def test_add_task(self):
        """Test adding tasks to agent"""
        task = AgentTask(name="task1", description="Test task")
        task_id = self.agent.add_task(task)
        self.assertIsNotNone(task_id)
        self.assertEqual(len(self.agent.tasks), 1)
    
    def test_execute_task(self):
        """Test task execution"""
        task = AgentTask(name="task1", description="Test task")
        task_id = self.agent.add_task(task)
        
        result = self.agent.execute_task(task_id)
        self.assertIsNotNone(result)
        
        executed_task = self.agent.tasks[task_id]
        self.assertEqual(executed_task.status, "completed")
        self.assertIsNotNone(executed_task.completed_at)
    
    def test_get_pending_tasks(self):
        """Test retrieving pending tasks"""
        task1 = AgentTask(name="task1", priority=0.5)
        task2 = AgentTask(name="task2", priority=0.9)
        task3 = AgentTask(name="task3", priority=0.3)
        
        self.agent.add_task(task1)
        self.agent.add_task(task2)
        self.agent.add_task(task3)
        
        pending = self.agent.get_pending_tasks()
        self.assertEqual(len(pending), 3)
        # Should be sorted by priority (highest first)
        self.assertEqual(pending[0].name, "task2")
        self.assertEqual(pending[2].name, "task3")


class TestCogServer(unittest.TestCase):
    """Test CogServer class"""
    
    def setUp(self):
        """Create cogserver for testing"""
        self.atomspace = AtomSpace()
        self.cogserver = CogServer(self.atomspace)
    
    def test_creation(self):
        """Test cogserver creation"""
        self.assertFalse(self.cogserver.running)
        self.assertEqual(len(self.cogserver.agents), 0)
    
    def test_register_agent(self):
        """Test registering agents"""
        agent = CognitiveAgent("agent1", self.atomspace)
        self.cogserver.register_agent(agent)
        self.assertEqual(len(self.cogserver.agents), 1)
        self.assertIn("agent1", self.cogserver.agents)
    
    def test_unregister_agent(self):
        """Test unregistering agents"""
        agent = CognitiveAgent("agent1", self.atomspace)
        self.cogserver.register_agent(agent)
        self.cogserver.unregister_agent("agent1")
        self.assertEqual(len(self.cogserver.agents), 0)
    
    def test_submit_task(self):
        """Test submitting tasks"""
        agent = CognitiveAgent("agent1", self.atomspace)
        self.cogserver.register_agent(agent)
        
        task = AgentTask(name="task1", description="Test")
        task_id = self.cogserver.submit_task("agent1", task)
        
        self.assertIsNotNone(task_id)
        self.assertEqual(len(agent.tasks), 1)
    
    def test_get_status(self):
        """Test getting cogserver status"""
        agent1 = CognitiveAgent("agent1", self.atomspace)
        agent2 = CognitiveAgent("agent2", self.atomspace)
        
        self.cogserver.register_agent(agent1)
        self.cogserver.register_agent(agent2)
        
        status = self.cogserver.get_status()
        self.assertIn('running', status)
        self.assertIn('agents', status)
        self.assertEqual(len(status['agents']), 2)


class TestOpenCogOrchestrator(unittest.TestCase):
    """Test OpenCogOrchestrator class"""
    
    def setUp(self):
        """Create orchestrator for testing"""
        reset_orchestrator()
        self.orchestrator = OpenCogOrchestrator()
    
    def tearDown(self):
        """Clean up after tests"""
        if self.orchestrator:
            self.orchestrator.stop()
        reset_orchestrator()
    
    def test_creation(self):
        """Test orchestrator creation"""
        self.assertIsNotNone(self.orchestrator.atomspace)
        self.assertIsNotNone(self.orchestrator.cogserver)
        # Should have default agents
        status = self.orchestrator.get_status()
        self.assertGreater(len(status['agents']), 0)
    
    def test_start_stop(self):
        """Test starting and stopping orchestrator"""
        self.orchestrator.start()
        status = self.orchestrator.get_status()
        self.assertTrue(status['running'])
        
        self.orchestrator.stop()
        status = self.orchestrator.get_status()
        self.assertFalse(status['running'])
    
    def test_submit_goal(self):
        """Test submitting goals"""
        task_id = self.orchestrator.submit_goal("Test goal", priority=0.8)
        self.assertIsNotNone(task_id)
        
        # Goal should be in knowledge base
        goals = self.orchestrator.query_knowledge({"type": "goal"})
        self.assertGreater(len(goals), 0)
    
    def test_submit_task(self):
        """Test submitting tasks"""
        task_id = self.orchestrator.submit_task(
            "planner",
            "test_task",
            "Test description",
            priority=0.7
        )
        self.assertIsNotNone(task_id)
    
    def test_query_knowledge(self):
        """Test querying knowledge base"""
        self.orchestrator.submit_goal("Test goal 1")
        self.orchestrator.submit_goal("Test goal 2")
        
        results = self.orchestrator.query_knowledge({"type": "goal"})
        self.assertGreaterEqual(len(results), 2)
    
    def test_get_atomspace_snapshot(self):
        """Test getting atomspace snapshot"""
        self.orchestrator.submit_goal("Test goal")
        snapshot = self.orchestrator.get_atomspace_snapshot()
        
        self.assertIn('atoms', snapshot)
        self.assertIn('total_atoms', snapshot)
        self.assertGreater(snapshot['total_atoms'], 0)
    
    def test_create_agent(self):
        """Test creating new agents"""
        agent_name = self.orchestrator.create_agent("custom_agent")
        self.assertEqual(agent_name, "custom_agent")
        
        status = self.orchestrator.get_status()
        agent_names = [a['name'] for a in status['agents']]
        self.assertIn("custom_agent", agent_names)
    
    def test_singleton_orchestrator(self):
        """Test singleton orchestrator access"""
        orch1 = get_orchestrator()
        orch2 = get_orchestrator()
        self.assertIs(orch1, orch2)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=True)


if __name__ == '__main__':
    run_tests()

import os
import unittest
import networkx as nx
from src.graph.builder import GraphBuilder

class TestGraphBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = GraphBuilder()
        self.test_graph_path = "data/graphs/test_graph.gpickle"

    def tearDown(self):
        """Cleanup test graph file."""
        if os.path.exists(self.test_graph_path):
            os.remove(self.test_graph_path)

    def test_node_addition(self):
        # Valid URL node
        self.builder.add_node('URL', 'url_1', url="http://google.com", label="safe")
        self.assertEqual(self.builder.get_node_count(), 1)
        
        # Valid Domain node
        self.builder.add_node('DOMAIN', 'google.com', domain="google.com", trust_score=1.0)
        self.assertEqual(self.builder.get_node_count(), 2)

        # Invalid node type
        result = self.builder.add_node('INVALID_TYPE', 'bad_node')
        self.assertFalse(result)
        self.assertEqual(self.builder.get_node_count(), 2)

    def test_edge_addition(self):
        self.builder.add_node('URL', 'url_1', url="http://google.com")
        self.builder.add_node('DOMAIN', 'google.com', domain="google.com")
        
        # Valid URL_TO_DOMAIN edge
        self.builder.add_edge('url_1', 'google.com', 'URL_TO_DOMAIN')
        self.assertEqual(self.builder.get_edge_count(), 1)
        
        edge_data = self.builder.graph.edges['url_1', 'google.com']
        self.assertEqual(edge_data['weight'], 1.0)
        self.assertEqual(edge_data['edge_type'], 'URL_TO_DOMAIN')

        # Invalid edge type
        result = self.builder.add_edge('url_1', 'google.com', 'INVALID_EDGE')
        self.assertFalse(result)
        self.assertEqual(self.builder.get_edge_count(), 1)

    def test_serialization(self):
        self.builder.add_node('URL', 'url_1', url="http://google.com")
        self.builder.add_node('DOMAIN', 'google.com', domain="google.com")
        self.builder.add_edge('url_1', 'google.com', 'URL_TO_DOMAIN')
        
        # Save graph
        self.builder.save_graph(self.test_graph_path)
        self.assertTrue(os.path.exists(self.test_graph_path))
        
        # Load into new builder
        new_builder = GraphBuilder()
        new_builder.load_graph(self.test_graph_path)
        
        self.assertEqual(new_builder.get_node_count(), 2)
        self.assertEqual(new_builder.get_edge_count(), 1)
        self.assertTrue(new_builder.graph.has_edge('url_1', 'google.com'))

if __name__ == "__main__":
    unittest.main()

"""ROBDD (Reduced Ordered Binary Decision Diagram) Engine
"""

from __future__ import annotations
import re
from typing import List, Dict, Tuple, Optional
import argparse
import webbrowser     
import urllib.parse
from graphviz import Digraph
from parser import parse_pysmt
from pysmt.shortcuts import Symbol, And, Or, Not, Xor, Implies, Iff , TRUE, FALSE
from pysmt.typing import BOOL


# Example formula demonstrating syntax
FORUMULA = "(a & !c) | (b ^ d)"
# Default output filename for ROBDD visualization
FILE_NAME = "robdd_output"


class ROBDDEngine:
    """Core ROBDD construction and management engine.
    """
    
    def __init__(self):
            """Initialize the ROBDD engine with terminal nodes.
            """
            # Table mapping ID -> (Variable Name, Low Child ID, High Child ID)
            # ID 0 = False Terminal, ID 1 = True Terminal
            self.nodes: Dict[int, Tuple[Optional[str], Optional[int], Optional[int]]] = {
                0: (None, None, None), 
                1: (None, None, None)
            }
            # Unique table for reduction: (var_name, low_id, high_id) -> node_id
            # This dictionary implements Shannon factorization sharing
            self.unique_table: Dict[Tuple[str, int, int], int] = {}
            self.next_id = 2

    def _get_node(self, var_name: str, low: int, high: int) -> int:
        """Creates a new ROBDD node or retrieves an existing one (implements reduction & sharing).
        """
        # Rule 1: Eliminate Redundant Nodes
        # If both branches point to same node, this node is redundant
        if low == high:
            return low

        # Rule 2: Share Equivalent Sub-graphs
        # Check if we've already built this exact node configuration
        key = (var_name, low, high)
        if key in self.unique_table:
            # Reuse existing node - maximizes sharing
            return self.unique_table[key]

        # Create new node (no duplicate found)
        node_id = self.next_id
        self.next_id += 1
        # Store node in nodes dictionary: id -> (var, low_child, high_child)
        self.nodes[node_id] = (var_name, low, high)
        # Register in unique_table to enable future sharing
        self.unique_table[key] = node_id
        return node_id

    def build_robdd(self, formula, ordering: List[str]) -> int:
        """
        Builds the ROBDD for a given PySMT formula using Shannon expansion.
        This is the main recursive algorithm that constructs the ROBDD. It uses
        Shannon expansion to decompose the formula at each variable level.
        """
        # Simplify first to handle trivial cases
        # This performs Boolean constant folding (e.g., TRUE & a -> a)
        simplified = formula.simplify()
        if simplified.is_true():
            # Formula is always true regardless of variable assignments
            return 1
        if simplified.is_false():
            # Formula is always false regardless of variable assignments
            return 0
        
        # Determine variable ordering if not strictly followed by recursion (safety)
        if not ordering:
            # Should be constant if we reached here with no vars, handled above.
            # This is a safety check - if no more variables, formula should be constant
            return 1 if simplified.is_true() else 0

        # Get the next variable from ordering (top-down traversal)
        var_name = ordering[0]
        # Create pysmt Symbol for substitution (needed by pysmt library)
        var_sym = Symbol(var_name, BOOL)

        # SHANNON EXPANSION - Part 1: Low Branch (when variable = False)
        # Substitute variable with FALSE and recursively build ROBDD for simplified formula
        low_expr = formula.substitute({var_sym: FALSE()})
        low_node_id = self.build_robdd(low_expr, ordering[1:])

        # SHANNON EXPANSION - Part 2: High Branch (when variable = True)
        # Substitute variable with TRUE and recursively build ROBDD for simplified formula
        high_expr = formula.substitute({var_sym: TRUE()})
        high_node_id = self.build_robdd(high_expr, ordering[1:])

        # Create or retrieve the node for this (variable, low, high) combination
        # This applies the reduction rules and enables maximal sharing
        return self._get_node(var_name, low_node_id, high_node_id)

    def save_image(self, root_id: int, filename: str = "robdd_output"):
            """
            Generates and saves a visualization of the ROBDD as PNG.
            This method creates a DOT graph representation and attempts to render it locally.
            If Graphviz is not installed, it automatically falls back to GraphvizOnline
            (a web-based visualization service).
            """
            # Create a Graphviz Digraph object for building the DOT representation
            dot = Digraph(comment='ROBDD')
            # Set ranking direction: TB = Top to Bottom (standard for decision trees)
            dot.attr(rankdir='TB') 
            
            # Add terminal nodes with distinct colors for clarity
            # Node 0 (False): Light red background
            dot.node('0', '0', shape='box', style='filled', fillcolor='#ffcccc') 
            # Node 1 (True): Light green background
            dot.node('1', '1', shape='box', style='filled', fillcolor='#ccffcc') 

            # Depth-first traversal to add all reachable nodes and edges
            visited = set()
            def traverse(u_id):
                """Recursively traverse ROBDD and add nodes/edges to graph.
                """
                # Skip if already visited (avoid infinite loops)
                if u_id in visited or u_id in (0, 1):
                    return
                visited.add(u_id)
                
                # Get node information (variable, low_child, high_child)
                var, low, high = self.nodes[u_id]
                # Add decision node (circle shape, variable name as label)
                dot.node(str(u_id), var, shape='circle')
                
                # Add edge to low branch (red, dashed line for variable=0)
                dot.edge(str(u_id), str(low), label='0', style='dashed', color='red')
                # Add edge to high branch (blue, solid line for variable=1)
                dot.edge(str(u_id), str(high), label='1', style='solid', color='blue')
                
                # Recursively add descendants
                traverse(low)
                traverse(high)

            # Start traversal from root node
            traverse(root_id)
            
            try:
                # Attempt local rendering using Graphviz
                # dot.render() calls graphviz command-line tool to generate PNG
                # view=True automatically opens the image after rendering
                output_path = dot.render(filename, format='png', view=True)
                print(f" ROBDD Image saved locally to: {output_path}")
                
            except Exception as e:
                # Graphviz executable not found - fall back to web-based visualization
                print(f"Could not render locally (Graphviz executable not found).")
                print("Opening GraphvizOnline in your browser instead...")
                
                # 1. Get the raw DOT code from the Digraph object
                # This is the complete graph description in DOT language
                dot_source = dot.source
                
                # 2. URL-encode the DOT source to be safely included in a URL
                # urllib.parse.quote() handles special characters properly
                encoded_source = urllib.parse.quote(dot_source)
                
                # 3. Construct the full URL for GraphvizOnline
                # The hash (#) indicates client-side rendering (no server upload)
                base_url = "https://dreampuf.github.io/GraphvizOnline/#"
                full_url = base_url + encoded_source
                
                # 4. Open the generated URL in the default web browser
                # User can then save/download the visualization from GraphvizOnline
                webbrowser.open(full_url)



if __name__ == "__main__":
    """
    Main entry point: Command-line interface for ROBDD builder.
    """

    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Build and visualize a Reduced Ordered Binary Decision Diagram (ROBDD)")
    # Positional argument: the Boolean formula string
    parser.add_argument("formula", help="Boolean formula string (e.g., '(a & !c) | (b ^ d)')")
    # Optional argument: custom output filename (default: 'robdd_output')
    parser.add_argument("-o", "--output", default=FILE_NAME, help="Output filename (without extension, default: 'robdd_output')")
    # Optional argument: custom variable ordering (default: alphabetical)
    parser.add_argument("--ordering", type=str, default=None, help="Comma-separated variable ordering (default: alphabetical)")
    
    # Parse the command-line arguments
    args = parser.parse_args()

    # Extract the formula string from arguments
    formula_str = args.formula
    print(f"Formula String: {formula_str}")

    # Parse the formula string into a PySMT expression tree
    try:
        pysmt_expr = parse_pysmt(formula_str)
        print(f"Parsed PySMT: {pysmt_expr}")
    except Exception as e:
        print(f"Parsing Error: {e}")
        exit(1)

    # Determine variable ordering
    if args.ordering:
        # User provided explicit ordering via command line
        ordering = [v.strip() for v in args.ordering.split(",")]
        print(f"Variable Ordering (user-defined): {ordering}")
    else:
        # Extract variables from formula and sort them alphabetically
        # get_free_variables() returns all variables that appear in the formula
        free_vars = pysmt_expr.get_free_variables()
        # Sort variable names alphabetically for default ordering
        ordering = sorted([v.symbol_name() for v in free_vars])
        print(f"Variable Ordering (alphabetical): {ordering}")

    # Build ROBDD
    # Initialize the ROBDD engine with empty nodes (only terminals)
    engine = ROBDDEngine()
    # Construct ROBDD using Shannon expansion recursively
    root_node = engine.build_robdd(pysmt_expr, ordering)
    print(f"ROBDD Root ID: {root_node}")

    # Export the ROBDD as a visualization
    # save_image() generates PNG locally or falls back to GraphvizOnline
    engine.save_image(root_node, filename=args.output)
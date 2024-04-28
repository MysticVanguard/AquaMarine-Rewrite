from typing import Dict, List

class Node():
    
    def __init__(
            self,
            type: str,
            completed: bool
    ):
        self.type = type
        self.completed = completed

        

class Graph():
        
    graph_dict: Dict[Node, List[Node]]
    def __init__(
            self,
            graph_string: str = None,
            curr_node: Node = None):
        self.curr_node = curr_node
        if graph_string:
            self.graph_dict = compile_graph(graph_string)
        else:
            start = Node()
            self.graph_dict[start] = []

    def get_curr(self) -> Node:
        return self.curr_node
    
    def get_node(self, index) -> Node:
        return self.graph_dict.keys()[index]
    
    def add_node(self, node: Node) -> bool:
        if node in self.graph_dict.keys():
            return False
        self.graph_dict[node] = []
        return True
    
    def add_path(self, node1: Node, node2: Node) -> bool:
        if node2 in self.graph_dict[node1]:
            return False
        self.graph_dict[node1].append(node2)
        return True
    
    def get_graph_string(self) -> str:
        returned = ""
        for node, node_list in self.graph_dict.items():
            returned += node.type + "." + str(node.completed) + ":"
            for connected_node in node_list:
                returned += connected_node.type + "." + str(connected_node.completed) + ","
        return returned
    


def compile_graph(graph_string: str) -> Dict[Node, List[Node]]:
    graph_dict: Dict[Node, List[Node]] = {}
    curr_node: Node = None
    for count, node in enumerate(graph_string.split(":")):
        if count % 2:
            node_obj = Node(node.split(".")[0],node.split(".")[1])
            graph_dict[node_obj] = []
            curr_node = node_obj
        else:
            for connected_node in node.split(","):
                node_obj = Node(connected_node.split(".")[0],connected_node.split(".")[1])
                graph_dict[curr_node].append(node_obj)
    return graph_dict
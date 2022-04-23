import csv
class Input:
    def __init__(self):
        self.node_file="nodes_Anaheim.txt"
        self.link_file="links_Anaheim.txt"

    def read_node(self):
        self.node_list=[]
        with open(self.node_file,"r") as fl:
            lines=fl.readlines()
            self.number_of_nodes=len(lines)-1

        for node_id in range(self.number_of_nodes):
            node=Node()
            node.node_id=node_id
            self.node_list.append(node)

    def read_links(self):
        self.link_list=[]
        self.read_node()
        with open(self.link_file,"r") as fl:
            lines=fl.readlines()
            self.g_number_of_links=0
            for line in lines[1:]:
                link_str_list=line.strip().split("\t")
                link = Link()
                link.link_id = self.g_number_of_links
                link.from_node_id =int(link_str_list[1])-1
                link.to_node_id = int(link_str_list[2])-1
                link.travel_time_mean = int(link_str_list[3])
                link.travel_time_variance = (int(link_str_list[4]))**2
                self.link_list.append(link)

                self.node_list[link.from_node_id].outbound_nodes_list.append(link.to_node_id)
                self.node_list[link.from_node_id].outbound_links_list.append(link)
                self.node_list[link.from_node_id].outbound_nodes_number = len(self.node_list[link.from_node_id].outbound_nodes_list)

                self.node_list[link.to_node_id].inbound_nodes_list.append(link.from_node_id)
                self.node_list[link.to_node_id].inbound_links_list.append(link)
                self.node_list[link.to_node_id].inbound_nodes_number = len(self.node_list[link.to_node_id].inbound_nodes_list)

                self.g_number_of_links+=1
        print("nodes:{}".format(self.number_of_nodes))
        print("Links:{}".format(self.g_number_of_links))
        return self.node_list,self.link_list,self.number_of_nodes,self.g_number_of_links



class Node:
    def __init__(self):
        self.node_id=None
        self.outbound_nodes_list=[]
        self.outbound_links_list=[]
        self.outbound_nodes_number=[]
        self.inbound_nodes_list = []
        self.inbound_links_list = []
        self.inbound_nodes_number = []


class Link:
    def __init__(self):
        self.link_id=None
        self.from_node_id=None
        self.to_node_id=None
        self.travel_time_mean=None
        self.travel_time_variance=None

# A=Excel_read()
# A.read_links()
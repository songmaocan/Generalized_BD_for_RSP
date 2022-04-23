import csv
class Input:
    def __init__(self):
        self.node_file="nodes_Anaheim.txt"
        self.link_file="links_Anaheim.txt"

    def read_node(self):
        self.node_list=[]
        with open(self.node_file,"r") as fl:
            self.number_of_nodes=0
            self.dict_id_to_index={}
            lines=fl.readlines()
            for line in lines[1:]:
                str_list=line.strip().split("\t")
                node = Node()
                node.node_id = int(str_list[0])
                node.node_index=self.number_of_nodes
                self.node_list.append(node)
                self.dict_id_to_index[node.node_id]=node.node_index
                self.number_of_nodes+=1

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
                link.from_node_id =int(link_str_list[1])
                link.to_node_id = int(link_str_list[2])
                link.travel_time_mean = int(link_str_list[3])
                link.travel_time_variance = (int(link_str_list[4]))**2
                self.link_list.append(link)

                from_node_index=self.dict_id_to_index[link.from_node_id]
                to_node_index=self.dict_id_to_index[link.to_node_id]

                self.node_list[from_node_index].outbound_nodes_list.append(link.to_node_id)
                self.node_list[from_node_index].outbound_links_list.append(link)
                self.node_list[from_node_index].outbound_nodes_number = len(self.node_list[from_node_index].outbound_nodes_list)

                self.node_list[to_node_index].inbound_nodes_list.append(link.from_node_id)
                self.node_list[to_node_index].inbound_links_list.append(link)
                self.node_list[to_node_index].inbound_nodes_number = len(self.node_list[to_node_index].inbound_nodes_list)

                self.g_number_of_links+=1
        print("nodes:{}".format(self.number_of_nodes))
        print("Links:{}".format(self.g_number_of_links))
        return self.node_list,self.link_list,self.number_of_nodes,self.g_number_of_links



class Node:
    def __init__(self):
        self.node_id=None
        self.node_index=None #from 0
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
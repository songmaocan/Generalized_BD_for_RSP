import xlrd
class Excel_read:
    def __init__(self):
        self.file="Input.xlsx"

    def read_node(self):
        self.node_list=[]
        self.workbooks=xlrd.open_workbook(self.file)
        sheet_0=self.workbooks.sheet_by_index(0)
        self.number_of_nodes=int(sheet_0.cell_value(1,0))
        self.origin=int(sheet_0.cell_value(1,1))-1
        self.destination=int(sheet_0.cell_value(1,2))-1
        for node_id in range(self.number_of_nodes):
            node=Node()
            node.node_id=node_id
            self.node_list.append(node)

    def read_links(self):
        self.link_list=[]
        self.read_node()
        sheet_1 = self.workbooks.sheet_by_index(1)
        self.number_of_links=sheet_1.nrows-1
        for row in range(1,sheet_1.nrows):
            link=Link()
            link.link_id=row-1
            link.from_node_id=int(sheet_1.cell_value(row,1))-1
            link.to_node_id=int(sheet_1.cell_value(row,2))-1
            link.travel_time_mean=int(sheet_1.cell_value(row,3))
            link.travel_time_variance=int(sheet_1.cell_value(row,4))
            self.link_list.append(link)

            self.node_list[link.from_node_id].outbound_nodes_list.append(link.to_node_id)
            self.node_list[link.from_node_id].outbound_links_list.append(link)
            self.node_list[link.from_node_id].outbound_nodes_number=len(self.node_list[link.from_node_id].outbound_nodes_list)

            self.node_list[link.to_node_id].inbound_nodes_list.append(link.from_node_id)
            self.node_list[link.to_node_id].inbound_links_list.append(link)
            self.node_list[link.to_node_id].inbound_nodes_number = len(self.node_list[link.to_node_id].inbound_nodes_list)

        return self.node_list,self.link_list,self.number_of_nodes,self.number_of_links,self.origin,self.destination




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
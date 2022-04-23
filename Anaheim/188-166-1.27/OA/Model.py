from gurobipy import *
from Read_data import Input
class OA:
    def __init__(self):
        data=Input()
        self.node_list, self.link_list, self.number_of_nodes, self.number_of_links=data.read_links()
        self.reliability_coefficient=1.27
        self.origin=188
        self.destination=166
        self.global_lower_bound=[]
        self.global_upper_bound=[]
        self.local_lower_bound = []
        self.local_upper_bound = []
        # self.SP_solution=[]
        # self.RMP_solution=[]
        # self.dual_price=[]
        self.maximum_iterations=50
        self.acceptable_gap=0.00
        # self.variance_limit=1000
        # self.g_solve_the_primal_problem()

    def g_solve_RSP_OA(self):
        #step 1: Initilize :the range of t and add two cuts
        min_mean, max_mean, min_variance, max_variance = self.g_reduce_the_searching_region_of_RMP()
        self.g_construct_master_problem(min_variance, max_variance)
        #iterations
        for i in range(self.maximum_iterations):
            print("iteration:{}".format(i+1))
            #Master problem:MIP, lower bound,and solutions
            self.SP.optimize()
            local_LB=self.SP.objval
            self.local_lower_bound.append(local_LB)
            if i == 0 and self.global_lower_bound == []:
                self.global_lower_bound.append(local_LB)
            if i != 0 and local_LB >= self.global_lower_bound[-1]:
                self.global_lower_bound.append(local_LB)
            if i != 0 and local_LB < self.global_lower_bound[-1]:
                self.global_lower_bound.append(self.global_lower_bound[-1])

            values = self.SP.getVars()
            mean_obj = 0
            variance_obj = 0
            for link in self.link_list:
                index = link.link_id
                # if round(values[index].x) != 0:
                if round(values[index].x) == 1:
                    variance_obj += link.travel_time_variance
                    mean_obj += link.travel_time_mean

            #Subproblem:upper bound, and a cut
            t_value=(variance_obj)**0.5
            local_UB=mean_obj+self.reliability_coefficient*t_value
            self.local_upper_bound.append(local_UB)
            if i == 0 and self.global_upper_bound == []:
                self.global_upper_bound.append(local_UB)
            if i != 0 and local_UB <= self.global_upper_bound[-1]:
                self.global_upper_bound.append(local_UB)
            if i != 0 and local_UB > self.global_upper_bound[-1]:
                self.global_upper_bound.append(self.global_upper_bound[-1])

            expr=LinExpr()
            for link in self.link_list:
                index=link.link_id
                variance=link.travel_time_variance
                name=self.SP.getVarByName("x_{}_{}".format(link.from_node_id,link.to_node_id))
                if round(values[index].x) == 1:
                    expr.addTerms(variance,name)
            name = self.SP.getVarByName("t")
            expr.addTerms(-1*t_value,name)

            rhs=variance_obj-t_value**2
            self.SP.addConstr(expr,GRB.LESS_EQUAL,rhs)

            gap=(self.global_upper_bound[-1]-self.global_lower_bound[-1])/self.global_upper_bound[-1]
            print(gap)
            if gap<=self.acceptable_gap:
                break
        print(self.global_upper_bound)
        print(self.global_lower_bound)




    def g_construct_master_problem(self,min_variance, max_variance):
        self.SP=Model("MP")
        self.SP.setParam('OutputFlag', 0)
        self.SP.setParam('MIPGap', 0)
        expr=LinExpr()
        for link in self.link_list:
            name="x_{}_{}".format(link.from_node_id,link.to_node_id)
            name=self.SP.addVar(vtype=GRB.BINARY,name=name,lb=0,ub=1)
            expr.addTerms(link.travel_time_mean,name)

        name=self.SP.addVar(vtype=GRB.CONTINUOUS,name="t")  #,lb=min_variance,ub=max_variance
        expr.addTerms(self.reliability_coefficient,name)

        self.SP.setObjective(expr, GRB.MINIMIZE)
        self.SP.update()

        #Flow balance
        for node in self.node_list:
            expr = LinExpr()
            #Flow out
            for outbound_link in node.outbound_links_list:
                name =self.SP.getVarByName("x_{}_{}".format(outbound_link.from_node_id, outbound_link.to_node_id))
                expr.addTerms(1,name)

            #Flow in
            for inbound_link in node.inbound_links_list:
                name = self.SP.getVarByName("x_{}_{}".format(inbound_link.from_node_id, inbound_link.to_node_id))
                expr.addTerms(-1, name)

            if node.node_id==self.origin:
                self.SP.addConstr(expr,GRB.EQUAL,1,name="Node_{}".format(self.origin))

            if node.node_id==self.destination:
                self.SP.addConstr(expr, GRB.EQUAL, -1, name="Node_{}".format(self.destination))


            if node.node_id!=self.origin and node.node_id!=self.destination:
                self.SP.addConstr(expr, GRB.EQUAL, 0, name="Node_{}".format(node.node_id))

        self.SP.update()
        self.SP.write("SP.lp")


    def g_reduce_the_searching_region_of_RMP(self): ###bug
        #least expected path
        EP= Model("EP")
        EP.setParam('OutputFlag', 0)
        expr = LinExpr()
        for link in self.link_list:
            name = "x_{}_{}".format(link.from_node_id, link.to_node_id)
            name = EP.addVar(vtype=GRB.CONTINUOUS, name=name, lb=0, ub=1)
            expr.addTerms(link.travel_time_mean, name)

        EP.setObjective(expr, GRB.MINIMIZE)
        EP.update()

        # Flow balance
        for node in self.node_list:
            expr = LinExpr()
            # Flow out
            for outbound_link in node.outbound_links_list:
                name = EP.getVarByName("x_{}_{}".format(outbound_link.from_node_id, outbound_link.to_node_id))
                expr.addTerms(1, name)

            # Flow in
            for inbound_link in node.inbound_links_list:
                name = EP.getVarByName("x_{}_{}".format(inbound_link.from_node_id, inbound_link.to_node_id))
                expr.addTerms(-1, name)

            if node.node_id == self.origin:
                EP.addConstr(expr, GRB.EQUAL, 1, name="Node_{}".format(self.origin))

            if node.node_id == self.destination:
                EP.addConstr(expr, GRB.EQUAL, -1, name="Node_{}".format(self.destination))

            if node.node_id != self.origin and node.node_id != self.destination:
                EP.addConstr(expr, GRB.EQUAL, 0, name="Node_{}".format(node.node_id))

        # EP.write("EP.lp")
        EP.optimize()
        values=EP.getVars()
        min_mean=EP.objVal
        max_variance=0
        for link in self.link_list:
            variance=link.travel_time_variance
            index=link.link_id
            if round(values[index].x)==1:
                print(values[index])
                max_variance+=variance

        #least variance path
        EP1 = Model("EP1")
        EP1.setParam('OutputFlag', 0)
        expr = LinExpr()
        for link in self.link_list:
            name = "x_{}_{}".format(link.from_node_id, link.to_node_id)
            name = EP1.addVar(vtype=GRB.CONTINUOUS, name=name, lb=0, ub=1)
            expr.addTerms(link.travel_time_variance, name)

        EP1.setObjective(expr, GRB.MINIMIZE)
        EP1.update()

        # Flow balance
        for node in self.node_list:
            expr = LinExpr()
            # Flow out
            for outbound_link in node.outbound_links_list:
                name = EP1.getVarByName("x_{}_{}".format(outbound_link.from_node_id, outbound_link.to_node_id))
                expr.addTerms(1, name)

            # Flow in
            for inbound_link in node.inbound_links_list:
                name = EP1.getVarByName("x_{}_{}".format(inbound_link.from_node_id, inbound_link.to_node_id))
                expr.addTerms(-1, name)

            if node.node_id == self.origin:
                EP1.addConstr(expr, GRB.EQUAL, 1, name="Node_{}".format(self.origin))

            if node.node_id == self.destination:
                EP1.addConstr(expr, GRB.EQUAL, -1, name="Node_{}".format(self.destination))

            if node.node_id != self.origin and node.node_id != self.destination:
                EP1.addConstr(expr, GRB.EQUAL, 0, name="Node_{}".format(node.node_id))
        EP1.write("SP.lp")

        EP1.update()
        EP1.optimize()
        values = EP1.getVars()
        min_variance = EP1.objVal
        max_mean = 0
        for link in self.link_list:
            mean = link.travel_time_mean
            index = link.link_id
            if round(values[index].x) == 1:
                print(values[index])
                max_mean += mean
        print(min_mean,max_mean,min_variance, max_variance)
        return min_mean,max_mean,min_variance, max_variance








    def g_find_the_path_of_SP_solution(self,values):
        path_links = {}
        for link in self.link_list:
            link_index=link.link_id
            from_node=link.from_node_id
            to_node=link.to_node_id
            if values[link_index].x==1:
                path_links[from_node]=to_node
        node_seq=[self.origin]
        current_node=self.origin
        while current_node!=self.destination:
            current_node=path_links[current_node]
            node_seq.append(current_node)
        self.SP_solution.append(node_seq)

    def g_output_results(self,time):
        #gaps and time
        with open("gap.csv","w") as fl:
            fl.write("iteration,local_LB,local_UB,LB,UB,gap\n")
            for i in range(len(self.global_lower_bound)):
                local_LB=round(self.local_lower_bound[i],2)
                local_UB=round(self.local_upper_bound[i],2)
                LB=round(self.global_lower_bound[i],2)
                UB=round(self.global_upper_bound[i],2)
                gap=(UB-LB)/UB
                fl.write(str(i+1)+","+str(local_LB)+","+str(local_UB)+","+str(LB)+","+str(UB)+","+str(gap)+"\n")
            fl.write("CPU time {} second".format(time))


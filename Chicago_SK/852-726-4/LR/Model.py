from gurobipy import *
from Read_data import Input
class LR:
    def __init__(self):
        data=Input()
        self.node_list, self.link_list, self.number_of_nodes, self.number_of_links=data.read_links()
        self.origin = 852
        self.destination = 726
        self.reliability_coefficient=4
        self.global_lower_bound=[-10000]
        self.global_upper_bound=[10000]
        self.local_lower_bound=[]
        self.local_upper_bound=[]
        self.multiplier=0.01
        self.maximum_iterations=100
        self.acceptable_gap=0.005
        # self.g_solve_the_primal_problem()

    def g_solve_RSP_LR(self):
        #step 1: Initilize
        min_mean,max_mean,min_variance, max_variance=self.g_reduce_the_searching_region_of_RMP()
        #step 2: solve the decomposed subproblems
        for i in range(self.maximum_iterations):
            local_lower_bound=0
            print("iteration:{}".format(i+1))
            #subproblem I
            self.g_construct_subproblem()
            self.SP.optimize()
            variance=0
            mean=0
            values=self.SP.getVars()
            for link in self.link_list:
                index = link.link_id
                if round(values[index].x) == 1:
                    variance+=link.travel_time_variance
                    mean+=link.travel_time_mean
            local_lower_bound+=self.SP.objVal
            local_upper_bound=mean+self.reliability_coefficient*(variance)**0.5

            #subproblem II
            L1=0
            L2=self.reliability_coefficient*(max_variance)**0.5
            if L1<L2:
                y=0
                local_lower_bound+=L1
            else:
                y=max_variance
                local_lower_bound+=L2

            #step 3: update the multiplier
            if (variance-y)!=0:
                self.multiplier+=(local_upper_bound-local_lower_bound)/(variance-y)

            if local_lower_bound>self.global_lower_bound[-1]:
                self.global_lower_bound.append(local_lower_bound)
            else:
                self.global_lower_bound.append(self.global_lower_bound[-1])

            if local_upper_bound<self.global_upper_bound[-1]:
                self.global_upper_bound.append(local_upper_bound)
            else:
                self.global_upper_bound.append(self.global_upper_bound[-1])

            if self.global_upper_bound[-1]!=0:
                gap=(self.global_upper_bound[-1]-self.global_lower_bound[-1])/self.global_upper_bound[-1]
                if gap<self.acceptable_gap:
                    break


    def g_construct_subproblem(self):
        self.SP=Model("SP")
        self.SP.setParam('OutputFlag', 0)
        self.SP.setParam('MIPGap', 0)
        expr=LinExpr()
        for link in self.link_list:
            name="x_{}_{}".format(link.from_node_id,link.to_node_id)
            name=self.SP.addVar(vtype=GRB.BINARY,name=name)
            expr.addTerms(link.travel_time_mean+self.multiplier*link.travel_time_variance,name)

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
            fl.write("iteration,LB,UB,gap\n")
            for i in range(len(self.global_lower_bound)):
                LB=round(self.global_lower_bound[i],2)
                UB=round(self.global_upper_bound[i],2)
                gap=(UB-LB)/UB
                fl.write(str(i+1)+","+str(LB)+","+str(UB)+","+str(gap)+"\n")
            fl.write("CPU time {} second".format(time))


    def g_solve_the_primal_problem(self):
        primal_problem = Model("primal problem")
        expr = LinExpr()
        for link in self.link_list:
            name = "x_{}_{}".format(link.from_node_id, link.to_node_id)
            name = primal_problem.addVar(vtype=GRB.BINARY, name=name, lb=0, ub=1)
            expr.addTerms(link.travel_time_mean, name)
        y = primal_problem.addVar(vtype=GRB.CONTINUOUS, name="y", lb=0)
        expr.addTerms(self.reliability_coefficient, y)

        primal_problem.setObjective(expr, GRB.MINIMIZE)
        primal_problem.update()

        # Flow balance
        for node in self.node_list:
            expr = LinExpr()
            # Flow out
            for outbound_link in node.outbound_links_list:
                name = primal_problem.getVarByName(
                    "x_{}_{}".format(outbound_link.from_node_id, outbound_link.to_node_id))
                expr.addTerms(1, name)

            # Flow in
            for inbound_link in node.inbound_links_list:
                name = primal_problem.getVarByName("x_{}_{}".format(inbound_link.from_node_id, inbound_link.to_node_id))
                expr.addTerms(-1, name)

            if node.node_id == self.origin:
                primal_problem.addConstr(expr, GRB.EQUAL, 1, name="Node_{}".format(self.origin))

            if node.node_id == self.destination:
                primal_problem.addConstr(expr, GRB.EQUAL, -1, name="Node_{}".format(self.destination))

            if node.node_id != self.origin and node.node_id != self.destination:
                primal_problem.addConstr(expr, GRB.EQUAL, 0, name="Node_{}".format(node.node_id))

        # variance limit
        expr = LinExpr()
        for link in self.link_list:
            name = primal_problem.getVarByName("x_{}_{}".format(link.from_node_id, link.to_node_id))
            expr.addTerms(link.travel_time_variance, name)

        primal_problem.addConstr(expr, GRB.LESS_EQUAL, y ** 2, name="variance limit")

        primal_problem.update()
        primal_problem.write("primal_problem.lp")
        primal_problem.optimize()
        primal_problem.update()
        values=primal_problem.getVars()
        path_links = {}
        for link in self.link_list:
            link_index = link.link_id
            from_node = link.from_node_id
            to_node = link.to_node_id
            if values[link_index].x == 1:
                path_links[from_node] = to_node
        node_seq = [self.origin]
        current_node = self.origin
        while current_node != self.destination:
            current_node = path_links[current_node]
            node_seq.append(current_node)
        obj=primal_problem.Objval
        print(obj)
        return node_seq,obj

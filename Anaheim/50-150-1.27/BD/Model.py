from gurobipy import *
from Read_data import Input
class BD:
    def __init__(self):
        data=Input()
        self.node_list, self.link_list, self.number_of_nodes, self.number_of_links=data.read_links()
        self.O=50
        self.D=150
        self.reliability_coefficient=1.27
        self.origin =self.O-1
        self.destination =self.D-1
        self.global_lower_bound=[]
        self.global_upper_bound=[]
        self.local_lower_bound = []
        self.local_upper_bound = []
        self.SP_solution=[]
        self.RMP_solution=[]
        self.dual_price=[]
        self.maximum_iterations=10
        self.acceptable_gap=0.0001
        self.variance_limit=1000
        # self.g_solve_the_primal_problem()

    def g_solve_RSP_BD(self):
        #step 1: Initilize
        min_mean,max_mean,min_variance, max_variance=self.g_reduce_the_searching_region_of_RMP()
        self.variance_limit=(min_variance+max_variance)
        self.g_construct_Benders_main_problem(min_mean,max_mean,min_variance, max_variance)
        self.g_construct_subproblem()

        for i in range(self.maximum_iterations):
            print("iteration:{}".format(i+1))

            #1.solve the subproblem
            #1.1 obtain the best dual variable
            variables = self.SP.getVars()
            for variable in variables:
                variable.Vtype = GRB.CONTINUOUS
            self.SP.update()
            self.SP.write("SP.lp")
            self.SP.optimize()
            constraint = self.SP.getConstrByName("variance limit")
            pi = constraint.pi
            self.dual_price.append(pi)

            #1.2 obtain the best primal variable
            variables=self.SP.getVars()
            for variable in variables:
                variable.Vtype=GRB.BINARY
            self.SP.update()
            self.SP.optimize()
            #1.1 update the upper bound
            values = self.SP.getVars()
            mean_obj=0
            variance_obj = 0
            for link in self.link_list:
                index = link.link_id
                # if round(values[index].x) != 0:
                if round(values[index].x) == 1:
                    variance_obj += link.travel_time_variance
                    mean_obj+=link.travel_time_mean
            local_UB=mean_obj+self.reliability_coefficient*(variance_obj)**0.5
            self.g_find_the_path_of_SP_solution(values)

            # print(variance_obj)

            self.local_upper_bound.append(local_UB)
            if i==0 and self.global_upper_bound==[]:
                self.global_upper_bound.append(local_UB)
            if i!=0 and local_UB<=self.global_upper_bound[-1]:
                self.global_upper_bound.append(local_UB)
            if i!=0 and local_UB>self.global_upper_bound[-1]:
                self.global_upper_bound.append(self.global_upper_bound[-1])

            #1.2 provide a cut
            LR1=mean_obj-pi*variance_obj
            self.RMP.addConstr(self.z>=LR1+pi*(self.y)**2,"Cut_{}".format(i))
            print(pi)


            #2 solve the main problem
            self.RMP.setParam('QCPDual',1)
            self.RMP.update()
            self.RMP.optimize()
            self.RMP.write("RMP.lp")
            # 2.1 update the lower bound
            local_LB=self.RMP.objVal
            self.local_lower_bound.append(local_LB)
            if i==0 and self.global_lower_bound==[]:
                self.global_lower_bound.append(local_LB)
            if i!=0 and local_LB>=self.global_lower_bound[-1]:
                self.global_lower_bound.append(local_LB)
            if i!=0 and local_LB<self.global_lower_bound[-1]:
                self.global_lower_bound.append(self.global_lower_bound[-1])
            #2.2 provide a variance
            values=self.RMP.getVars()
            self.variance_limit=(values[-1].x)**2
            variance_limit=self.SP.getConstrByName("variance limit")
            variance_limit.rhs=self.variance_limit
            self.RMP.write("RMP.lp")
            self.RMP_solution.append([self.y.x,self.z.x])
            print(self.variance_limit)

            gap=(self.global_upper_bound[-1]-self.global_lower_bound[-1])/self.global_upper_bound[-1]
            print(gap)
            if gap<self.acceptable_gap:
                break
        print(self.local_lower_bound)
        print(self.local_upper_bound)



    def g_construct_Benders_main_problem(self,min_mean,max_mean,min_variance, max_variance):
        self.RMP=Model("QCP")
        self.RMP.setParam('NonConvex', 2)
        self.RMP.setParam('OutputFlag', 0)
        self.z=self.RMP.addVar(vtype=GRB.CONTINUOUS,name="z",lb=min_mean,ub=max_mean)
        self.y=self.RMP.addVar(vtype=GRB.CONTINUOUS, name="y",lb=(min_variance)**0.5,ub=(max_variance)**0.5)
        self.RMP.setObjective(self.z+self.reliability_coefficient*self.y,GRB.MINIMIZE)
        self.RMP.update()
        self.RMP.write("RMP.lp")


    def g_construct_subproblem(self):
        self.SP=Model("SP")
        self.SP.setParam('OutputFlag', 0)
        self.SP.setParam('MIPGap', 0)
        expr=LinExpr()
        for link in self.link_list:
            name="x_{}_{}".format(link.from_node_id,link.to_node_id)
            name=self.SP.addVar(vtype=GRB.CONTINUOUS,name=name,lb=0,ub=1)
            expr.addTerms(link.travel_time_mean,name)

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

        #variance limit
        expr = LinExpr()
        for link in self.link_list:
            name = self.SP.getVarByName("x_{}_{}".format(link.from_node_id,link.to_node_id))
            expr.addTerms(link.travel_time_variance,name)

        self.SP.addConstr(expr,GRB.LESS_EQUAL,self.variance_limit,name="variance limit")

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
        node_seq=[self.origin+1]
        current_node=self.origin
        while current_node!=self.destination:
            current_node=path_links[current_node]
            node_seq.append(current_node+1)
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

        #SP solution
        with open("SP_solution.csv", "w") as fl:
            fl.write("iteration,solution\n")
            for i in range(len(self.SP_solution)):
                solution=self.SP_solution[i]
                pi=self.dual_price[i]
                fl.write(str(i+1)+","+str(solution)+"\n")

        #dual solution
        with open("dual_solution.csv", "w") as fl:
            fl.write("iteration,pi\n")
            for i in range(len(self.SP_solution)):
                pi=self.dual_price[i]
                fl.write(str(i+1)+","+str(pi)+"\n")

        #RMP solution
        with open("RMP_solution.csv", "w") as fl:
            fl.write("iteration,y,z\n")
            for i in range(len(self.RMP_solution)):
                y=self.RMP_solution[i][0]
                z=self.RMP_solution[i][1]
                fl.write(str(i + 1) + "," + str(y) + "," + str(z)+ "\n")

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
        node_seq = [self.origin+1]
        current_node = self.origin
        while current_node != self.destination:
            current_node = path_links[current_node]
            node_seq.append(current_node+1)

        obj=primal_problem.Objval
        print(obj)
        return node_seq,obj

    def record_for_solver(self,node_seq,obj,time):
        with open("results_of_solver.txt","w") as fl:
            fl.write("Path:")
            fl.write(str(node_seq))
            fl.write("\n")
            fl.write("Obj:{}\n".format(obj))
            fl.write("Time:{} seconds".format(time))
"""
Solve the mean-standard deviation shortest path problem by Gurobi
Author: Maocan Song, Southeast University
Email: 1097133316@qq.com
Version: 1.0
"""
from Model import BD
import time
def main():
    start_time=time.time()
    mod=BD()
    node_seq,obj=mod.g_solve_the_primal_problem()
    # mod.g_solve_RSP_BD()
    end_time = time.time()
    CPU_time=round(end_time-start_time,1)
    mod.record_for_solver(node_seq,obj,CPU_time)
    print("CPU_time: {}".format(CPU_time))
    # mod.g_output_results(CPU_time)


if __name__ == '__main__':
    main()
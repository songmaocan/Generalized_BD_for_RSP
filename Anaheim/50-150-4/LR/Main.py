"""
Solve the mean-standard deviation shortest path problem by Lagrangian relaxation
Author: Maocan Song, Southeast University
Email: 1097133316@qq.com
Version: 1.0
"""
from Model import LR
import time
def main():
    start_time=time.time()
    mod=LR()
    mod.g_solve_RSP_LR()
    end_time = time.time()
    CPU_time=round(end_time-start_time,4)
    mod.g_output_results(CPU_time)


if __name__ == '__main__':
    main()
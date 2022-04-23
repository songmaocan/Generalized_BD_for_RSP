"""
Solve the mean-standard deviation shortest path problem by outer approximation
Author: Maocan Song, Southeast University
Email: 1097133316@qq.com
Version: 1.0
"""
from Model import OA
import time
def main():
    start_time=time.time()
    mod=OA()
    mod.g_solve_RSP_OA()
    end_time = time.time()
    CPU_time=round(end_time-start_time,4)
    mod.g_output_results(CPU_time)


if __name__ == '__main__':
    main()
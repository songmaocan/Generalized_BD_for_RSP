\ Model QCP
\ LP format - for model browsing. Use MPS format to capture full model detail.
Minimize
  z + y
Subject To
 Cut_0: z + [ ] >= 840
 Cut_1: z + [ 140 y ^2 ] >= 15480
 Cut_2: z + [ 5.084745762711864 y ^2 ] >= 1718.64406779661
 Cut_3: z + [ 2.4 y ^2 ] >= 1286.4
 Cut_4: z + [ ] >= 840
 Cut_5: z + [ ] >= 840
 Cut_6: z + [ ] >= 840
 Cut_7: z + [ ] >= 840
 Cut_8: z + [ ] >= 840
 Cut_9: z + [ ] >= 840
Bounds
 840 <= z <= 1200
 10.09950493836208 <= y <= 13.63818169698586
End

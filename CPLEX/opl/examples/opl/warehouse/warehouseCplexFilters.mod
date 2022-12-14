// --------------------------------------------------------------------------
// Licensed Materials - Property of IBM
//
// 5725-A06 5725-A29 5724-Y48 5724-Y49 5724-Y54 5724-Y55
// Copyright IBM Corporation 1998, 2020. All Rights Reserved.
//
// Note to U.S. Government Users Restricted Rights:
// Use, duplication or disclosure restricted by GSA ADP Schedule
// Contract with IBM Corp.
// --------------------------------------------------------------------------

// The scalable warehouse example has been artificially increased in size 
// so that the search is long enough for you to have time to interrupt it and look at feasible solutions. 
// The resulting size is greater than the size allowed in trial mode. 
// If you want to run this example, you need a commercial edition of CPLEX Studio to run this example. 
// If you are a student or teacher, you can also get a full version through the IBM Academic Initiative.
int Fixed        = 30;
int NbWarehouses = 50;
int NbStores     = 100;
assert( NbStores > NbWarehouses );

range Warehouses = 1..NbWarehouses;
range Stores     = 1..NbStores;
int Capacity[w in Warehouses] = 
  NbStores div NbWarehouses + 
  w % ( NbStores div NbWarehouses );
int SupplyCost[s in Stores][w in Warehouses] = 
  1 + ( ( s + 10 * w ) % 100 );

float Coefs[Warehouses];  
  
dvar boolean Open[Warehouses];
dvar float Supply[Stores][Warehouses] in 0..1;
dexpr int TotalFixedCost = sum( w in Warehouses ) Fixed * Open[w];
dexpr float TotalSupplyCost = sum( w in Warehouses, s in Stores )  SupplyCost[s][w] * Supply[s][w];
// define a range filter applied to solution pools
execute {
    for (var w in Warehouses) {
        Coefs[w] = 1;
    }
    cplex.addRangeFilter(30, 43, Open, Coefs);
}
minimize TotalFixedCost + TotalSupplyCost;
subject to {
  forall( s in Stores )
    ctStoreHasOneWarehouse: 
      sum( w in Warehouses ) 
        Supply[s][w] == 1;
  forall( w in Warehouses )
    ctOpen:
      sum( s in Stores ) 
        Supply[s][w] <= Open[w] * Capacity[w];
}


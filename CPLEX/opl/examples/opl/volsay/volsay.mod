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

dvar float+ Gas;
dvar float+ Chloride;


maximize
  40 * Gas + 50 * Chloride;
subject to {
  ctMaxTotal:     
    Gas + Chloride <= 50;
  ctMaxTotal2:    
    3 * Gas + 4 * Chloride <= 180;
  ctMaxChloride:  
    Chloride <= 40;
}

tuple SolutionT{ 
	float Gas; 
	float Chloride; 
};
{SolutionT} Solution = {<Gas,Chloride>};
execute{ 
	writeln(Solution);
}

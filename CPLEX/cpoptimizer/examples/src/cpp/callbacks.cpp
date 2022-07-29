// -------------------------------------------------------------- -*- C++ -*-
// File: ./examples/src/cpp/callbacks.cpp
// --------------------------------------------------------------------------
// Licensed Materials - Property of IBM
//
// 5724-Y48 5724-Y49 5724-Y54 5724-Y55 5725-A06 5725-A29
// Copyright IBM Corporation 1990, 2020. All Rights Reserved.
//
// Note to U.S. Government Users Restricted Rights:
// Use, duplication or disclosure restricted by GSA ADP Schedule
// Contract with IBM Corp.
// --------------------------------------------------------------------------

/* ------------------------------------------------------------

Problem Description
-------------------

This example demonstrates the use of a callback to deliver real-time
information on the lower and upper bounds of the objective function,
and the gap.

------------------------------------------------------------ */

#include <ilcp/cp.h>

ILOSTLBEGIN

class BoundsCallback : public IloCP::Callback {
private:
  ILOSTD(ostream&) _out;
  IloNum           _lb;
  IloNum           _ub;
  IloNum           _gap;

  // Helper class to restore stream flags cleanly
  class OstreamGuard {
  private: 
    ostream& _s;
    std::ios_base::fmtflags _f;
  public:
    OstreamGuard(ostream &s) : _s(s), _f(s.flags()) { }
    ~OstreamGuard() { _s.flags(_f); }
  };
public:
  BoundsCallback(ostream& out) : _out(out) { init(); }
  void init() {
    _lb  = -IloInfinity;
    _ub  = IloInfinity;
    _gap = IloInfinity;
  }
  void invoke(IloCP cp, IloCP::Callback::Reason reason) {
    OstreamGuard guard(_out);

    // Initialize the local fields at the beginning of search,
    // and print the banner
    if (reason == IloCP::Callback::StartSolve) {
      init();
      _out << "Time\tLB\tUB\tGap" << endl;
      _out << "=============================" << endl;
    }
    else if (reason == IloCP::Callback::EndSolve) {
      // Finish the line at the end of search
      _out << endl;
    }
    else {
      IloBool soln = (reason == IloCP::Callback::Solution);
      IloBool bnd = (reason == IloCP::Callback::ObjBound);
      if (soln || bnd) {
        // Write a newline if a line has already been written
        if (_lb > -IloInfinity && _ub < IloInfinity)
          _out << endl;
        if (soln) {
          // Update upper bound and gap (if a bound has been communicated)
          _ub = cp.getObjValue();
          if (_lb > -IloInfinity) 
            _gap = cp.getObjGap();
        }
        else if (bnd) {
          // Update lower bound and gap (if a solution has been found)
          _lb = cp.getObjBound();
          if (_ub < IloInfinity)
            _gap = cp.getObjGap();
        }
      }
      if (_lb > -IloInfinity && _ub < IloInfinity) {
        // Write a line when we have both a bound and a solution.
    int p = _out.precision();
        _out << "\r                                                  \r"
             << fixed << setprecision(1)
             << cp.getInfo(IloCP::SolveTime) << "\t"
             << setprecision(0)
             << _lb << "\t" << _ub << "\t"
             << setprecision(1)
             << 100 * _gap << "%\t" << flush;
    _out.precision(p);
      }
    }
  }
};

void SolveWithCallback(IloCP cp) {
  // Add callback, solve, then remove it.
  BoundsCallback cb(cp.out());
  cp.addCallback(&cb);
  cp.solve();
  cp.removeCallback(&cb);
}

class FileError : public IloException {
public:
  FileError() : IloException("Cannot open cpo file") {}
};

int main(int, const char * []) {
  IloEnv env;
  try { 
    // Load a model, and solve using a callback.
    IloCP cp(env);
    try {
      cp.importModel("../../../examples/data/linebal-BARTHOL2-142-30.cpo");
    } catch (IloException& e) {
      throw FileError();
    }
    cp.setParameter(IloCP::LogVerbosity, IloCP::Quiet);
    SolveWithCallback(cp);
    cp.end();
  } catch (IloException & ex) {
    env.out() << "Caught: " << ex << std::endl;
  }
  env.end();
  return 0;
}

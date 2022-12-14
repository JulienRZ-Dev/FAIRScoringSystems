// -------------------------------------------------------------- -*- C++ -*-
// File: ./include/ilopl/ilsched/ilosoplcpi.h
// --------------------------------------------------------------------------
// Licensed Materials - Property of IBM
//
// 5725-A06 5725-A29 5724-Y48 5724-Y49 5724-Y54 5724-Y55
// Copyright IBM Corp. 2000, 2020
//
// US Government Users Restricted Rights - Use, duplication or
// disclosure restricted by GSA ADP Schedule Contract with
// IBM Corp.
// ---------------------------------------------------------------------------

#ifndef __CONCERT_ilosoplcpiH
#define __CONCERT_ilosoplcpiH

#ifdef _WIN32
#pragma pack(push, 8)
#endif

#include <ilopl/ilosys.h>

# include <ilconcert/ilosmodel.h>
# include <ilconcert/ilsched/ilostimei.h>
# include <ilconcert/ilsched/ilossequencei.h>
#include <ilconcert/ilsched/ilosatomi.h>
# include <ilopl/ilomapextr.h>
# include <ilopl/ilooplcpi.h>

class IloIntervalVarSubMapExprI : public IloIntervalExprI {
  ILOEXTRDECL
protected:
  IloMapExtractIndexI* _index;
  IloInt _currentDim;
protected:
  virtual void atRemove(IloExtractableI* sub = 0, IloAny info = 0) ILO_OVERRIDE;
public:
  IloIntervalVarSubMapExprI(IloEnvI* env, IloMapExtractIndexI* index,
    IloInt dim);
  virtual ~IloIntervalVarSubMapExprI();
  virtual IloIntervalVarMap evalMap(const IloAlgorithm alg) const;
  virtual IloIntervalVarMap getMap() const = 0;
  virtual IloIntervalVarMap getEvaluatedMap(const IloAlgorithm alg) const = 0;
  IloIntervalVarSubMapExprI* makeSubMap(IloMapExtractIndexI* idx);
  DEFINE_MAP_UTILITIES()
  virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

template<class BaseClass, class FinalClass >
class IloConditionalFunctionExprI : public BaseClass {
  IloConstraintI* _cond;
  BaseClass* _then;
  BaseClass* _else;
public:
  IloConditionalFunctionExprI(IloEnvI* env,
    IloConstraintI* cond,
    BaseClass* left,
    BaseClass* right )
    : BaseClass(env),
    _cond((IloConstraintI*)cond->lockExpr()),
    _then(left),
    _else(right) {
  }

  virtual ~IloConditionalFunctionExprI() {}

  virtual void display( ILOSTD(ostream)& out) const ILO_OVERRIDE {
    _cond->display(out);
    out << " ? ";
    _then->display(out);
    out << " : ";
    _else->display(out);
  }

  virtual IloExtractableI* makeClone(IloEnvI* env) const ILO_OVERRIDE {
    IloConstraintI* cond = (IloConstraintI*)env->getClone(_cond);
    BaseClass* left = (BaseClass*)env->getClone(_then);
    BaseClass* right = (BaseClass*)env->getClone(_else);
    return new (env) FinalClass(env, cond, left, right);
  }

  virtual void visitSubExtractables(IloExtractableVisitor* v) ILO_OVERRIDE {
    v->beginVisit(this);
    v->visitChildren(this, _cond);
    v->visitChildren(this, _then);
    v->visitChildren(this, _else);
    v->endVisit(this);
  }

  IloConstraintI* getCond() const {return _cond;}
  BaseClass* getThen() const {return _then;}
  BaseClass* getElse() const {return _else;}
};

class IloConditionalPiecewiseFunctionExprI:
  public IloConditionalFunctionExprI<IloAdvPiecewiseFunctionExprI,
  IloConditionalPiecewiseFunctionExprI> {
    ILOEXTRDECL
public:
  IloConditionalPiecewiseFunctionExprI(IloEnvI* env,
    IloConstraintI* cond,
    IloAdvPiecewiseFunctionExprI* left,
    IloAdvPiecewiseFunctionExprI* right);
  virtual ~IloConditionalPiecewiseFunctionExprI(){}
  virtual IloBool isStepwise() const ILO_OVERRIDE { return getThen()->isStepwise(); }
};

class IloAdvPiecewiseFunctionExprSubMapExprI : public IloAdvPiecewiseFunctionExprI {
  ILOEXTRDECL
protected:
  IloMapExtractIndexI* _index;
  IloInt _currentDim;
public:
  IloAdvPiecewiseFunctionExprSubMapExprI(IloEnvI* env, IloMapExtractIndexI* index,
    IloInt dim);
  virtual ~IloAdvPiecewiseFunctionExprSubMapExprI();
  virtual IloPiecewiseFunctionExprMap evalMap(const IloAlgorithm alg) const;
  virtual IloPiecewiseFunctionExprMap getMap() const = 0;
  virtual IloPiecewiseFunctionExprMap getEvaluatedMap(const IloAlgorithm alg) const = 0;
  IloAdvPiecewiseFunctionExprSubMapExprI* makeSubMap(IloMapExtractIndexI* idx);
        virtual IloBool isStepwise() const ILO_OVERRIDE;
  DEFINE_MAP_UTILITIES()
};

class IloIntervalSequenceVarSubMapExprI : public IloIntervalSequenceExprI {
  ILOEXTRDECL
protected:
  IloMapExtractIndexI* _index;
  IloInt _currentDim;
public:
  IloIntervalSequenceVarSubMapExprI(IloEnvI* env, IloMapExtractIndexI* index,
    IloInt dim);
  virtual ~IloIntervalSequenceVarSubMapExprI();
  virtual IloIntervalSequenceVarMap evalMap(const IloAlgorithm alg) const;
  virtual IloIntervalSequenceVarMap getMap() const = 0;
  virtual IloIntervalSequenceVarMap getEvaluatedMap(const IloAlgorithm alg) const = 0;
  IloIntervalSequenceVarSubMapExprI* makeSubMap(IloMapExtractIndexI* idx);
  DEFINE_MAP_UTILITIES()
  virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloAdvCumulAtomI : public IloCumulFunctionExprI {
  ILOS_CPEXTR_DECL(IloAdvCumulAtomI, IloCumulFunctionExprI)
protected:
  IloIntExprI*  _levelMin; 
  
  IloAdvCumulAtomI(IloEnvI* env, IloIntExprI*  levelMin, const char* name=0);
public:
  virtual ~IloAdvCumulAtomI();
  virtual IloBool isPulse() const=0;
  virtual IloBool isStep() const=0;
  IloIntExprArg getLevelMin() const { return _levelMin; }
  virtual IloIntExprArg getValue() const=0;
  virtual IloBool isAtomic() const ILO_OVERRIDE { return IloTrue; }
protected:
  void visitAtoms(IloCumulFunctionExprI::AtomVisitor * visitor,
    IloCumulFunctionExprI::AtomVisitorContext * ctx) ILO_OVERRIDE;
  virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloStateFunctionExprSubMapExprI : public IloStateFunctionExprI {
  ILOEXTRDECL
protected:
  IloMapExtractIndexI* _index;
  IloInt _currentDim;
public:
  IloStateFunctionExprSubMapExprI(IloEnvI* env,
    IloMapExtractIndexI* index,
    IloInt dim);
  virtual ~IloStateFunctionExprSubMapExprI();
  IloStateFunctionExprSubMapExprI* makeSubMap(IloMapExtractIndexI* idx);
  virtual IloStateFunctionExprMap evalMap(const IloAlgorithm alg) const;
  virtual IloStateFunctionExprMap getMap() const = 0;
  virtual IloStateFunctionExprMap getEvaluatedMap(const IloAlgorithm alg) const = 0;
  DEFINE_MAP_UTILITIES()
    virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloAggregateCumulExprI : public IloCumulFunctionExprI {
  ILOS_CPEXTR_DECL(IloAggregateCumulExprI, IloCumulFunctionExprI)
    void visitAtoms(IloCumulFunctionExprI::AtomVisitor * visitor,
    IloCumulFunctionExprI::AtomVisitorContext * ctx) ILO_OVERRIDE;
private:
  IloComprehensionI* _comprehension;
  IloCumulFunctionExprI* _body;
  virtual IloExtractableI* makeClone(IloEnvI*) const ILO_OVERRIDE;
public:
  IloAggregateCumulExprI(IloEnvI* env, IloComprehensionI* comp,
    IloCumulFunctionExprI* expr, const char* name=0);
  virtual ~IloAggregateCumulExprI();
  IloComprehensionI* getComprehension() const { return _comprehension; }
  IloCumulFunctionExprI* getExpr() const { return _body; }
  virtual IloBool isAtomic() const ILO_OVERRIDE { return IloFalse; }
protected:
  virtual void atRemove(IloExtractableI* sub = 0, IloAny info = 0) ILO_OVERRIDE;
public:
  virtual void display(ILOSTD(ostream)& out) const ILO_OVERRIDE;
    virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloConditionalCumulFunctionExprI:
  public IloConditionalFunctionExprI<IloCumulFunctionExprI,
  IloConditionalCumulFunctionExprI> {
    ILOEXTRDECL
public:
  IloConditionalCumulFunctionExprI(IloEnvI* env,
    IloConstraintI* cond,
    IloCumulFunctionExprI* left,
    IloCumulFunctionExprI* right)
    : IloConditionalFunctionExprI<IloCumulFunctionExprI,
    IloConditionalCumulFunctionExprI>(env,
    cond,
    left,
    right) {}
  virtual ~IloConditionalCumulFunctionExprI(){}
  virtual IloBool isAtomic() const ILO_OVERRIDE;
  virtual void visitAtoms(AtomVisitor * visitor, AtomVisitorContext * ctx) ILO_OVERRIDE;
    virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloIntervalVarSubMapRootI : public IloIntervalVarSubMapExprI {
  ILOEXTRDECL
private:
  IloIntervalVarMap _map;
protected:
  virtual void visitSubExtractables(IloExtractableVisitor* v) ILO_OVERRIDE;
public:
  IloIntervalVarSubMapRootI(IloEnvI* env,
    IloMapExtractIndexI* index,
    IloIntervalVarMap m);
  virtual ~IloIntervalVarSubMapRootI();
  virtual IloExtractableI* makeClone(IloEnvI*) const ILO_OVERRIDE;
  virtual void display(ILOSTD(ostream)& out) const ILO_OVERRIDE;
  virtual IloIntervalVarMap getMap() const ILO_OVERRIDE { return _map; }
  virtual IloIntervalVarMap getEvaluatedMap(const IloAlgorithm alg) const ILO_OVERRIDE;
  virtual IloBool isRoot() const { return IloTrue; }
  virtual IloDiscreteDataCollectionI* getIndexer() const ILO_OVERRIDE {
    return _map.getImpl()->getIndexer();
  }
  virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloIntervalVarSubMapSubI : public IloIntervalVarSubMapExprI {
  ILOEXTRDECL
private:
  IloIntervalVarSubMapExprI* _owner;
protected:
  virtual void visitSubExtractables(IloExtractableVisitor* v) ILO_OVERRIDE;
public:
  IloIntervalVarSubMapSubI(IloEnvI* env, IloMapExtractIndexI* index,
    IloIntervalVarSubMapExprI* owner, IloInt dim);
  virtual ~IloIntervalVarSubMapSubI();
  virtual IloExtractableI* makeClone(IloEnvI*) const ILO_OVERRIDE;
  virtual void display(ILOSTD(ostream)& out) const ILO_OVERRIDE;
  IloIntervalVarSubMapExprI* getOwner() const { return _owner; }
  virtual IloIntervalVarMap getMap() const ILO_OVERRIDE { return _owner->getMap(); }
  virtual IloIntervalVarMap getEvaluatedMap(const IloAlgorithm alg) const ILO_OVERRIDE;
  virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloAdvPiecewiseFunctionSubMapRootI : public IloAdvPiecewiseFunctionExprSubMapExprI {
  ILOEXTRDECL
private:
  IloPiecewiseFunctionExprMap _map;
protected:
  virtual void visitSubExtractables(IloExtractableVisitor* v) ILO_OVERRIDE;
public:
  IloAdvPiecewiseFunctionSubMapRootI(IloEnvI* env,
    IloMapExtractIndexI* index,
    IloPiecewiseFunctionExprMap m);
  virtual ~IloAdvPiecewiseFunctionSubMapRootI();
  virtual IloExtractableI* makeClone(IloEnvI*) const ILO_OVERRIDE;
  virtual void display(ILOSTD(ostream)& out) const ILO_OVERRIDE;
  virtual IloPiecewiseFunctionExprMap getMap() const ILO_OVERRIDE { return _map; }
  virtual IloPiecewiseFunctionExprMap getEvaluatedMap(const IloAlgorithm alg) const ILO_OVERRIDE;
  virtual IloBool isRoot() const { return IloTrue; }
  virtual IloDiscreteDataCollectionI* getIndexer() const ILO_OVERRIDE {
    return _map.getImpl()->getIndexer();
  }
};

class IloAdvPiecewiseFunctionSubMapSubI : public IloAdvPiecewiseFunctionExprSubMapExprI {
  ILOEXTRDECL
private:
  IloAdvPiecewiseFunctionExprSubMapExprI* _owner;
protected:
  virtual void visitSubExtractables(IloExtractableVisitor* v) ILO_OVERRIDE;
public:
  IloAdvPiecewiseFunctionSubMapSubI(IloEnvI* env, IloMapExtractIndexI* index,
    IloAdvPiecewiseFunctionExprSubMapExprI* owner, IloInt dim);
  virtual ~IloAdvPiecewiseFunctionSubMapSubI();
  virtual IloExtractableI* makeClone(IloEnvI*) const ILO_OVERRIDE;
  virtual void display(ILOSTD(ostream)& out) const ILO_OVERRIDE;
  IloAdvPiecewiseFunctionExprSubMapExprI* getOwner() const { return _owner; }
  virtual IloPiecewiseFunctionExprMap getMap() const ILO_OVERRIDE { return _owner->getMap(); }
  virtual IloPiecewiseFunctionExprMap getEvaluatedMap(const IloAlgorithm alg) const ILO_OVERRIDE;
};

class IloIntervalSequenceVarSubMapRootI : public IloIntervalSequenceVarSubMapExprI {
  ILOEXTRDECL
private:
  IloIntervalSequenceVarMap _map;
protected:
  virtual void visitSubExtractables(IloExtractableVisitor* v) ILO_OVERRIDE;
public:
  IloIntervalSequenceVarSubMapRootI(IloEnvI* env,
    IloMapExtractIndexI* index,
    IloIntervalSequenceVarMap m);
  virtual ~IloIntervalSequenceVarSubMapRootI();
  virtual IloExtractableI* makeClone(IloEnvI*) const ILO_OVERRIDE;
  virtual void display(ILOSTD(ostream)& out) const ILO_OVERRIDE;
  virtual IloIntervalSequenceVarMap getMap() const ILO_OVERRIDE { return _map; }
  virtual IloIntervalSequenceVarMap getEvaluatedMap(const IloAlgorithm alg) const ILO_OVERRIDE;
  virtual IloBool isRoot() const { return IloTrue; }
  virtual IloDiscreteDataCollectionI* getIndexer() const ILO_OVERRIDE {
    return _map.getImpl()->getIndexer();
  }
  virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloIntervalSequenceVarSubMapSubI : public IloIntervalSequenceVarSubMapExprI {
  ILOEXTRDECL
private:
  IloIntervalSequenceVarSubMapExprI* _owner;
protected:
  virtual void visitSubExtractables(IloExtractableVisitor* v) ILO_OVERRIDE;
public:
  IloIntervalSequenceVarSubMapSubI(IloEnvI* env, IloMapExtractIndexI* index,
    IloIntervalSequenceVarSubMapExprI* owner,
    IloInt dim);
  virtual ~IloIntervalSequenceVarSubMapSubI();
  virtual IloExtractableI* makeClone(IloEnvI*) const ILO_OVERRIDE;
  virtual void display(ILOSTD(ostream)& out) const ILO_OVERRIDE;
  IloIntervalSequenceVarSubMapExprI* getOwner() const { return _owner; }
  virtual IloIntervalSequenceVarMap getMap() const ILO_OVERRIDE { return _owner->getMap(); }
  virtual IloIntervalSequenceVarMap getEvaluatedMap(const IloAlgorithm alg) const ILO_OVERRIDE;
  virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloCumulFunctionExprSubMapExprI : public IloCumulFunctionExprI {
  ILOEXTRDECL
protected:
  IloMapExtractIndexI* _index;
  IloInt _currentDim;
  void visitAtoms(IloCumulFunctionExprI::AtomVisitor * visitor,
    IloCumulFunctionExprI::AtomVisitorContext * ctx) ILO_OVERRIDE;
public:
  IloCumulFunctionExprSubMapExprI(IloEnvI* env, IloMapExtractIndexI* index,
    IloInt dim);
  virtual ~IloCumulFunctionExprSubMapExprI();
  virtual IloBool isAtomic() const ILO_OVERRIDE { return IloFalse; }
  virtual IloCumulFunctionExprMap evalMap(const IloAlgorithm alg) const;
  virtual IloCumulFunctionExprMap getMap() const = 0;
  virtual IloCumulFunctionExprMap getEvaluatedMap(const IloAlgorithm alg) const = 0;
  IloCumulFunctionExprSubMapExprI* makeSubMap(IloMapExtractIndexI* idx);
  DEFINE_MAP_UTILITIES()
  virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloCumulFunctionExprSubMapRootI : public IloCumulFunctionExprSubMapExprI {
  ILOEXTRDECL
private:
  IloCumulFunctionExprMap _map;
protected:
  virtual void visitSubExtractables(IloExtractableVisitor* v) ILO_OVERRIDE;
public:
  IloCumulFunctionExprSubMapRootI(IloEnvI* env,
    IloMapExtractIndexI* index,
    IloCumulFunctionExprMap m);
  virtual ~IloCumulFunctionExprSubMapRootI();
  virtual IloExtractableI* makeClone(IloEnvI*) const ILO_OVERRIDE;
  virtual void display(ILOSTD(ostream)& out) const ILO_OVERRIDE;
  virtual IloCumulFunctionExprMap getMap() const ILO_OVERRIDE { return _map; }
  virtual IloCumulFunctionExprMap getEvaluatedMap(const IloAlgorithm alg) const ILO_OVERRIDE;
  virtual IloBool isRoot() const { return IloTrue; }
  virtual IloDiscreteDataCollectionI* getIndexer() const ILO_OVERRIDE {
    return _map.getImpl()->getIndexer();
  }
  virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloCumulFunctionExprSubMapSubI : public IloCumulFunctionExprSubMapExprI {
  ILOEXTRDECL
private:
  IloCumulFunctionExprSubMapExprI* _owner;
protected:
  virtual void visitSubExtractables(IloExtractableVisitor* v) ILO_OVERRIDE;
public:
  IloCumulFunctionExprSubMapSubI(IloEnvI* env, IloMapExtractIndexI* index,
    IloCumulFunctionExprSubMapExprI* owner, IloInt dim);
  virtual ~IloCumulFunctionExprSubMapSubI();
  virtual IloExtractableI* makeClone(IloEnvI*) const ILO_OVERRIDE;
  virtual void display(ILOSTD(ostream)& out) const ILO_OVERRIDE;
  IloCumulFunctionExprSubMapExprI* getOwner() const { return _owner; }
  virtual IloCumulFunctionExprMap getMap() const ILO_OVERRIDE { return _owner->getMap(); }
  virtual IloCumulFunctionExprMap getEvaluatedMap(const IloAlgorithm alg) const ILO_OVERRIDE;
  virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloStateFunctionExprSubMapRootI :
  public IloStateFunctionExprSubMapExprI {
    ILOEXTRDECL
private:
  IloStateFunctionExprMap _map;
protected:
  virtual void visitSubExtractables(IloExtractableVisitor* v) ILO_OVERRIDE;
public:
  IloStateFunctionExprSubMapRootI(IloEnvI* env,
    IloMapExtractIndexI* index,
    IloStateFunctionExprMap m);
  virtual ~IloStateFunctionExprSubMapRootI();
  virtual IloExtractableI* makeClone(IloEnvI*) const ILO_OVERRIDE;
  virtual void display(ILOSTD(ostream)& out) const ILO_OVERRIDE;
  virtual IloStateFunctionExprMap getMap() const ILO_OVERRIDE { return _map; }
  virtual IloStateFunctionExprMap getEvaluatedMap(const IloAlgorithm alg) const ILO_OVERRIDE;
  virtual IloBool isRoot() const { return IloTrue; }
  virtual IloDiscreteDataCollectionI* getIndexer() const ILO_OVERRIDE {
    return _map.getImpl()->getIndexer();
  }
  virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

class IloStateFunctionExprSubMapSubI :
  public IloStateFunctionExprSubMapExprI {
    ILOEXTRDECL
protected:
  virtual void visitSubExtractables(IloExtractableVisitor* v) ILO_OVERRIDE;
private:
  IloStateFunctionExprSubMapExprI* _owner;
public:
  IloStateFunctionExprSubMapSubI(IloEnvI* env,
    IloMapExtractIndexI* index,
    IloStateFunctionExprSubMapExprI* owner,
    IloInt dim);
  virtual ~IloStateFunctionExprSubMapSubI();
  IloStateFunctionExprSubMapExprI* getOwner() const { return _owner; }
  virtual IloExtractableI* makeClone(IloEnvI*) const ILO_OVERRIDE;
  virtual void display(ILOSTD(ostream)& out) const ILO_OVERRIDE;
  virtual IloStateFunctionExprMap getMap() const ILO_OVERRIDE { return _owner->getMap(); }
  virtual IloStateFunctionExprMap getEvaluatedMap(const IloAlgorithm alg) const ILO_OVERRIDE;
  virtual IloBool isDecisionExpr() const ILO_OVERRIDE {return IloTrue;}
};

inline IloAdvPiecewiseFunctionI* MakeAdvStepFunction(IloEnvI* env, const IloNumArray x, const IloNumArray y, const char* name =0) {
  return new (env) IloAdvPiecewiseFunctionI(env, x, y, name);
}
inline IloAdvPiecewiseFunctionI* MakeAdvPiecewiseFunction(IloEnvI* env, const IloNumArray x, const IloNumArray s, IloNum x0, IloNum y0, const char* name=0) {
  return new (env) IloAdvPiecewiseFunctionI(env, x, s, x0, y0, name);
}

#ifdef _WIN32
#pragma pack(pop)
#endif

#endif

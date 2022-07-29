/* --------------------------------------------------------------------------
 * File: libopltabODBC.c
 * --------------------------------------------------------------------------
 * Licensed Materials - Property of IBM
 * 
 * 5725-A06 5725-A29 5724-Y48 5724-Y49 5724-Y54 5724-Y55 
 * Copyright IBM Corporation  2020. All Rights Reserved.
 *
 * Note to U.S. Government Users Restricted Rights:
 * Use, duplication or disclosure restricted by GSA ADP Schedule
 * Contract with IBM Corp.
 * --------------------------------------------------------------------------
 */

/* Table connection implementation based on sqlite.
 * This file defines classes that can be registered with an IloOplModel
 * instance as a custom data source so that in .dat files we can use
 * statements like
 *    ODBCConnection conn(...,...);  // connect to database
 *    data from ODBCRead(conn, "SELECT * FROM data");
 *    result to ODBCPublish(conn, "INSERT INTO results VALUES(?)");
 */

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#ifdef _WIN32
#include <windows.h>
#endif
#include <sql.h>
#include <sqlext.h>
#include <ilopl/data/iloopltabledatasource.h>

#define TUPLE_SEPARATOR '.' /** Separator in fully qualified names for
                             * fields in sub-tuples. */

#define MAX_STRING_LENGTH 4096 /** Maximum length of string values we can
                                * exchange with the database. Strings longer
                                * than this will result in errors.
                                */

#define MAX_NAME_LEN    1024   /** Maximum length of a column name.
                                * Columns with names longer than this
                                * will cause trouble.
                                */

/* ********************************************************************** *
 *                                                                        *
 *    Utility functions                                                   *
 *                                                                        *
 * ********************************************************************** */

#ifdef _WIN32
#  define STRDUP _strdup
#else
#  define STRDUP strdup
#endif

/** Cast a C-Style string to type SQLCHAR.
 * This may involve casting away 'const' and changing the signedness
 * of the type.
 */
static SQLCHAR *sqlchar(char const *text) { return (SQLCHAR *)text; }


/** Check the result of an ODBC function call.
 * If status indicates failure then error is set appropriately.
 * @return true on success, false otherwise.
 */
static int check(long status, IloOplTableError error) {
  if ( status != SQL_SUCCESS && status != SQL_SUCCESS_WITH_INFO ) {
    error->setBoth(error, (int)status, "SQL failed with %ld", status);
    return 0;
  }
  return 1;
}

/** More verbose check() function.
 * A potential exception message also contains the query that triggered
 * the error and a verbose error description obtained from the driver.
 * @return true on success, false otherwise.
 */
static int checkExt(SQLSMALLINT handleType, SQLHANDLE handle,
                    long status, char const *query, IloOplTableError error)
{
  if ( status != SQL_SUCCESS && status != SQL_SUCCESS_WITH_INFO ) {
    char buffer[1024];
    SQLCHAR state[6];
    SQLINTEGER nativeError = 0;
    SQLSMALLINT textlen = 0;
    if ( SQLGetDiagRec(handleType, handle, 1, state, &nativeError,
                       sqlchar(buffer), sizeof(buffer), &textlen)
        != SQL_SUCCESS )
    {
      sprintf(buffer, "unknown error %ld", status);
    }
    else {
      if ( textlen >= sizeof(buffer) )
        textlen = sizeof(buffer) - 1;
      buffer[textlen] = 0;
    }
    if ( query )
      error->setBoth(error, (int)status, "%s: %s (%ld, native %lld)", query,
                     buffer, status, (long long)nativeError);
    else
      error->setBoth(error, (int)status, "%s (%ld, native %lld)",
                     buffer, status, (long long)nativeError);
    return 0;
  }
  return 1;
}

#define checkENV(h,s,q,e) checkExt(SQL_HANDLE_ENV, (h), (s), (q), (e))
#define checkDBC(h,s,q,e) checkExt(SQL_HANDLE_DBC, (h), (s), (q), (e))
#define checkSTMT(h,s,q,e) checkExt(SQL_HANDLE_STMT, (h), (s), (q), (e))

static int exec(SQLHDBC dbc, char const *sql, IloOplTableError error)
{
  while (*sql && isspace(*sql)) ++sql;
  if ( *sql ) {
    SQLHSTMT stmt;
    int ok;

    if ( !check(SQLAllocHandle(SQL_HANDLE_STMT, dbc, &stmt), error) )
      return 0;
    ok = checkSTMT(stmt, SQLExecDirect(stmt, sqlchar(sql), SQL_NTS),
                   sql, error);
    SQLFreeHandle(SQL_HANDLE_STMT, stmt);
    return ok;
  }
  return 0;
}

/** Convenience function to set an error indicator to indicate out of memory.
 * @param error The error indicator to set.
 * @return always returns error.
 */
static IloOplTableError setOOM(IloOplTableError error) {
  error->setBoth(error, -1, "out of memory");
  return error;
}

/* ********************************************************************** *
 *                                                                        *
 *                                                                        *
 *                                                                        *
 * ********************************************************************** */

typedef struct {
  SQLHDBC *dbc;    /**< Connection for the transaction (SQL_HANDLE_DBC). */
  int     running; /**< Is a transaction running? */
} Transaction;

/** Complete a transaction.
 * If the transaction is still running then it will be rolled back.
 * In any case, the "auto commit" property of the respective connection
 * will be reset.
 * Any error in this method is ignored.
 */
static void transactionComplete(Transaction *trans)
{
  if ( trans->running ) {
    /* Not explicitly committed -> we must rollback. */
    SQLEndTran(SQL_HANDLE_DBC, trans->dbc, SQL_ROLLBACK);
    SQLSetConnectAttr(trans->dbc, SQL_ATTR_AUTOCOMMIT,
                      (SQLPOINTER)SQL_AUTOCOMMIT_ON, SQL_NTS);
  }
}

/** Start transaction.
 * The function starts a transaction which is finished either explicitly
 * by calling transactionCommit() (which commits the data to the database)
 * or by implicitly by the destructor (which rolls back the transaction).
 */
static IloOplTableError transactionStart(Transaction *trans,
                                         IloOplTableError error)
{
  assert(!trans->running);
  if ( !checkDBC(trans->dbc,
                 SQLSetConnectAttr(trans->dbc, SQL_ATTR_AUTOCOMMIT,
                                   (SQLPOINTER)SQL_AUTOCOMMIT_OFF,
                                   SQL_NTS), NULL, error) )
    return error;

  trans->running = 1;
  return NULL;
}

/** Commit a transaction that was previously started by start(). */
static IloOplTableError transactionCommit(Transaction *trans,
                                          IloOplTableError error)
{
  int ok;

  assert(trans->running);
  trans->running = 0;

  ok = checkDBC(trans->dbc, SQLEndTran(SQL_HANDLE_DBC, trans->dbc,
                                          SQL_COMMIT), NULL, error);
  (void)SQLSetConnectAttr(trans->dbc, SQL_ATTR_AUTOCOMMIT,
                          (SQLPOINTER)SQL_AUTOCOMMIT_ON, SQL_NTS);

  return ok ? NULL : error;
}

/* ********************************************************************** *
 *                                                                        *
 *                                                                        *
 *                                                                        *
 * ********************************************************************** */

typedef enum {
  T_NONE,   /**< Marks types that are not yet initialized. */
  T_INT8,   /**< 8bit signed integer, uses data.b as buffer. */
  T_INT16,  /**< 16bit signed integer, uses data.s as buffer. */
  T_INT32,  /**< 32bit signed integer, uses data.i as buffer. */
  T_INT64,  /**< 64bit signed integer, uses data.l as buffer. */
  T_FLOAT,  /**< Single precision float, uses data.f as buffer. */
  T_DOUBLE, /**< Double precision float, uses data.d as buffer. */
  T_TEXT    /**< NUL terminated string, uses data.s as buffer. */
} Type;     /**< Column types. */

/** Descriptor for a single column in a query or update.
 * This specifies the data type of the column as well as a buffer that
 * is used to exchange data for this column with ODBC.
 */
typedef struct {
  Type type;     /**< Type of column. */
  union {
    int8_t  b;
    int16_t s;
    int32_t i;
    int64_t l;
    float   f;
    double  d;
    char    *t;
  } data;        /**< Data that is bound to columns. */
  SQLLEN l;      /**< For the last argument to SQLBindCol(). */
} Column;

static IloOplTableError col2int(Column const *col, IloOplTableError error,
                                IloOplTableIntType *value_p) {
  SQLLEN r = 0;

  switch (col->type) {
  case T_INT8:
    r = 1;
    *value_p = (col->l == SQL_NULL_DATA) ? 0 : col->data.b;
    break;
  case T_INT16:
    r = 2;
    *value_p = (col->l == SQL_NULL_DATA) ? 0 : col->data.s;
    break;
  case T_INT32:
    r = 4;
    *value_p = (col->l == SQL_NULL_DATA) ? 0 : col->data.i;
    break;
  case T_INT64:
    r = 8;
    *value_p = (col->l == SQL_NULL_DATA) ? 0LL : col->data.l;
    break;
  default:
    error->setBoth(error, -1, "column is not integer");
    return error;
  }
  if ( col->l != SQL_NULL_DATA && col->l < r ) {
    error->setBoth(error, -1, "not enough data for int column %lld vs %lld",
                   (long long)col->l, (long long)r);
    return error;
  }
  return NULL;
}

static IloOplTableError col2num(Column const *col, IloOplTableError error,
                           double *value_p)
{
  SQLLEN r;

  switch (col->type) {
  case T_DOUBLE:
    r = 8;
    *value_p = (col->l == SQL_NULL_DATA) ? 0.0 : col->data.d;
    break;
  case T_FLOAT:
    r = 4;
    *value_p = (col->l == SQL_NULL_DATA) ? 0.0 : col->data.f;
    break;
  default:
    error->setBoth(error, -1, "column is not floating point");
    return error;
  }
  if ( col->l != SQL_NULL_DATA && col->l < r ) {
    error->setBoth(error, -1, "not enough data for double column %lld vs %lld",
                   (long long)col->l, (long long)r);
    return error;
  }
  return NULL;
}

static IloOplTableError col2str(Column const *col, IloOplTableError error,
                           char const **value_p)
{
  switch (col->type) {
  case T_TEXT:
    col->data.t[col->l] = '\0';
    *value_p = (col->l == SQL_NULL_DATA) ? "" : col->data.t;
    break;
  default:
    error->setBoth(error, -1, "column is not text");
    return error;
  }
  return NULL;
}

/* ********************************************************************** *
 *                                                                        *
 *                                                                        *
 *                                                                        *
 * ********************************************************************** */

/** Check that a column is within range.
 * @param col     The column index to test.
 * @param columns The number of columns available.
 * @param error   In case the index is out of range this indicator will set
 *                to contain an appropriate code/message.
 * @return true if the index is within range, false otherwise.
 */
static int checkColumn(IloOplTableColIndex col,
                       IloOplTableColIndex columns,
                       IloOplTableError error)
{
  if ( col < 0 || col >= columns ) {
    error->setBoth(error, -1, "index %lld out of range [0,%lld]",
                   col, columns);
    return 0;
  }
  return 1;
}

/* ********************************************************************** *
 *                                                                        *
 *    Data input                                                          *
 *                                                                        *
 * ********************************************************************** */

typedef struct {
  IloOplTableInputRowsC base;
  SQLHSTMT              stmt;         /**< ODBC handle (SQL_HANDLE_STMT). */
  Column                *result;      /**< Buffer to store query results. */
  SQLSMALLINT           cols;         /**< Number of columns in statement. */
  char const            **fieldNames; /**< Names for named fields. */
} ODBCInputRows;

static IloOplTableError inGetColumnCount(IloOplTableInputRows rows,
                                         IloOplTableError error,
                                         IloOplTableColIndex *cols_p)
{
  ODBCInputRows *r = (ODBCInputRows *)rows;

  (void)error;
  *cols_p = r->cols;

  return NULL;
}

static IloOplTableError inGetSelectedTupleFields(IloOplTableInputRows rows,
                                                 IloOplTableError error,
                                                 char *sep,
                                                 char const *const **fields_p)
{
  ODBCInputRows *r = (ODBCInputRows *)rows;
  
  (void)error;
  if ( sep )
    *sep = TUPLE_SEPARATOR;
  *fields_p = r->fieldNames;
  return NULL;
}

static IloOplTableError inReadInt(IloOplTableInputRows rows,
                                  IloOplTableError error,
                                  IloOplTableColIndex column,
                                  IloOplTableIntType *value_p)
{
  ODBCInputRows *r = (ODBCInputRows *)rows;

  if ( !checkColumn(column, r->cols, error) )
    return error;

  return col2int(&r->result[column], error, value_p);
}

static IloOplTableError inReadString(IloOplTableInputRows rows,
                                     IloOplTableError error,
                                     IloOplTableColIndex column,
                                     char const **value_p)
{
  ODBCInputRows *r = (ODBCInputRows *)rows;

  if ( !checkColumn(column, r->cols, error) )
    return error;

  return col2str(&r->result[column], error, value_p);
}

static IloOplTableError inReadNum(IloOplTableInputRows rows,
                                  IloOplTableError error,
                                  IloOplTableColIndex column,
                                  double *value_p)
{
  ODBCInputRows *r = (ODBCInputRows *)rows;

  if ( !checkColumn(column, r->cols, error) )
    return error;

  return col2num(&r->result[column], error, value_p);
}

static IloOplTableError inNext(IloOplTableInputRows rows,
                               IloOplTableError error, int *next_p)
{
  ODBCInputRows *r = (ODBCInputRows *)rows;
  long status = SQLFetch(r->stmt);
            
  if ( status == SQL_NO_DATA )
    *next_p = 0;
  else {
    if ( !checkSTMT(r->stmt, status, NULL, error) )
      return error;
    *next_p = 1;
  }
  return NULL;
}

static void inDestroy(ODBCInputRows *rows)
{
  if ( rows ) {
    SQLSMALLINT col;

    if ( rows->stmt )
      SQLFreeHandle(SQL_HANDLE_STMT, rows->stmt);

    if ( rows->result ) {
      for (col = 0; col < rows->cols; ++col)
        if ( rows->result[col].type == T_TEXT )
          free(rows->result[col].data.t);
      free(rows->result);
    }

    if ( rows->fieldNames ) {
      for (col = 0; col < rows->cols; ++col)
        free((char *)rows->fieldNames[col]);
      free((void *)rows->fieldNames);
    }

    free(rows);
  }
}

/* ********************************************************************** *
 *                                                                        *
 *    Data output                                                         *
 *                                                                        *
 * ********************************************************************** */

typedef struct {
  IloOplTableOutputRowsC base;
  SQLHSTMT               stmt;    /**< ODBC handle (SQL_HANDLE_STMT). */
  Column                 *params; /**< Data buffers for parameters. */
  SQLSMALLINT            cols;    /**< Number of parameters in statement. */
  Transaction            trans;   /**< Transaction for the update. */
} ODBCOutputRows;


static IloOplTableError outGetSelectedTupleFields(IloOplTableOutputRows rows,
                                                  IloOplTableError error,
                                                  char *sep,
                                                  IloOplTableColIndex *cols,
                                                  char const *const **fields_p)
{
  /* ODBC does not support named parameters. */
  (void)rows;
  (void)error;
  if ( sep )
    *sep = TUPLE_SEPARATOR;
  if ( cols )
    *cols = 0;
  *fields_p = NULL;
  return NULL;
}

static IloOplTableError outWriteInt(IloOplTableOutputRows rows,
                                    IloOplTableError error,
                                    IloOplTableColIndex column,
                                    IloOplTableIntType value)
{
  ODBCOutputRows *r = (ODBCOutputRows *)rows;

  if ( !checkColumn(column, r->cols, error) )
    return error;
  /* NOTE: The first parameter has index 1 */
  if ( r->params[column].type == T_NONE ) {
    if ( !checkSTMT(r->stmt, SQLBindParameter(r->stmt, column + 1,
                                              SQL_PARAM_INPUT,
                                              SQL_C_SBIGINT,
                                              SQL_BIGINT,
                                              0 /* ignored */, 0 /* ignored */,
                                              &r->params[column].data.l,
                                              sizeof(r->params[column].data.l),
                                              &r->params[column].l),
                    NULL, error) )
      return error;
    r->params[column].type = T_INT64;
  }
  r->params[column].data.l = value;
  return NULL;
}

static IloOplTableError outWriteString(IloOplTableOutputRows rows,
                                       IloOplTableError error,
                                       IloOplTableColIndex column,
                                       char const *value)
{
  ODBCOutputRows *r = (ODBCOutputRows *)rows;
  size_t len;

  if ( !checkColumn(column, r->cols, error) )
    return error;

  /* NOTE: The first parameter has index 1! */
  if ( r->params[column].type == T_NONE ) {
    r->params[column].type = T_TEXT;
    if ( (r->params[column].data.t = malloc(MAX_STRING_LENGTH)) == NULL )
      return setOOM(error);
    if ( !checkSTMT(r->stmt, SQLBindParameter(r->stmt, column + 1,
                                              SQL_PARAM_INPUT,
                                              SQL_C_CHAR, SQL_CHAR,
                                              MAX_STRING_LENGTH - 1, 0,
                                              r->params[column].data.t,
                                              MAX_STRING_LENGTH - 1,
                                              &r->params[column].l),
                    NULL, error) )
      return error;
    r->params[column].data.t[MAX_STRING_LENGTH - 1] = '\0';
    r->params[column].type = T_TEXT;
  }

  if ( !value ) /* NULL value is empty string */
    value = "";

  len = strlen(value);
  if ( len >= MAX_STRING_LENGTH ) {
    error->setBoth(error, -1, "output string too long");
    return error;
  }
  memcpy(r->params[column].data.t, value, len);
  r->params[column].data.t[len] = 0;
  r->params[column].l = len;
  return NULL;
}

static IloOplTableError outWriteNum(IloOplTableOutputRows rows,
                                    IloOplTableError error,
                                    IloOplTableColIndex column,
                                    double value)
{
  ODBCOutputRows *r = (ODBCOutputRows *)rows;

  if ( !checkColumn(column, r->cols, error) )
    return error;

  /* NOTE: The first parameter has index 1! */
  if ( r->params[column].type == T_NONE ) {
    if ( !checkSTMT(r->stmt, SQLBindParameter(r->stmt, column + 1,
                                              SQL_PARAM_INPUT,
                                              SQL_C_DOUBLE,
                                              SQL_REAL,
                                              0 /* ignored */, 0 /* ignored */,
                                              &r->params[column].data.d,
                                              sizeof(r->params[column].data.d),
                                              &r->params[column].l),
                    NULL, error) )
      return error;
    r->params[column].type = T_DOUBLE;
  }
  r->params[column].data.d = value;
  return NULL;
}

static IloOplTableError outEndRow(IloOplTableOutputRows rows,
                                  IloOplTableError error)
{
  ODBCOutputRows *r = (ODBCOutputRows *)rows;

  if ( !checkSTMT(r->stmt, SQLExecute(r->stmt), NULL, error) )
    return error;
  return NULL;
}

static IloOplTableError outCommit(IloOplTableOutputRows rows,
                                  IloOplTableError error)
{
  ODBCOutputRows *r = (ODBCOutputRows *)rows;

  return transactionCommit(&r->trans, error);
}

static void outDestroy(ODBCOutputRows *rows)
{
  if ( rows ) {
    SQLSMALLINT col;

    if ( rows->stmt )
      SQLFreeHandle(SQL_HANDLE_STMT, rows->stmt);

    if ( rows->params ) {
      for (col = 0; col < rows->cols; ++col)
        if ( rows->params[col].type == T_TEXT )
          free(rows->params[col].data.t);
      free(rows->params);
    }
    transactionComplete(&rows->trans);
    free(rows);
  }
}


/* ********************************************************************** *
 *                                                                        *
 *    Connection handling                                                 *
 *                                                                        *
 * ********************************************************************** */

typedef struct {
  IloOplTableConnectionC base;
  SQLHENV  env;   /**< ODBC environment handle (SQL_HANDLE_ENV). */
  SQLHDBC  dbc;   /**< Database connection (SQL_HANDLE_DBC). */
  int      named; /**< Are tuples assumed to be queried by fields? */
} ODBCConnection;

static void connDestroy(IloOplTableConnection conn)
{
  ODBCConnection *c = (ODBCConnection *)conn;

  if ( c ) {
    if ( c->dbc ) {
      SQLDisconnect(c->dbc);
      SQLFreeHandle(SQL_HANDLE_DBC, c->dbc);
    }
    if ( c->env )
      SQLFreeHandle(SQL_HANDLE_ENV, c->env);
    free(c);
  }
}

static IloOplTableError connOpenInputRows(IloOplTableConnection conn,
                                          IloOplTableError error,
                                          IloOplTableContext context,
                                          char const *query,
                                          IloOplTableInputRows *rows_p)
{
  ODBCConnection *c = (ODBCConnection *)conn;
  SQLHDBC dbc = c->dbc;
  IloOplTableError err = error;
  ODBCInputRows *rows = NULL;
  SQLSMALLINT col, cols;

  (void)context; /* unused in this example */

  if ( (rows = calloc(1, sizeof(*rows))) == NULL ) {
    setOOM(error);
    goto TERMINATE;
  }

  rows->base.getColumnCount = inGetColumnCount;
  rows->base.getSelectedTupleFields = inGetSelectedTupleFields;
  rows->base.readInt = inReadInt;
  rows->base.readString = inReadString;
  rows->base.readNum = inReadNum;
  rows->base.next = inNext;

  /* Prepare a statement with the SQL to be executed. Then query
   * the statements meta data to prepare fetching results.
   */
  if ( !checkDBC(dbc, SQLAllocHandle(SQL_HANDLE_STMT, dbc, &rows->stmt),
                 query, error) )
    goto TERMINATE;
  if ( !checkSTMT(rows->stmt, SQLPrepare(rows->stmt, sqlchar(query), SQL_NTS),
                  query, error) )
    goto TERMINATE;

  if ( !checkSTMT(rows->stmt, SQLNumResultCols(rows->stmt, &cols),
                  query, error) )
    goto TERMINATE;
  rows->cols = cols;

  if ( (rows->result = calloc(cols, sizeof(*rows->result))) == NULL ) {
    setOOM(error);
    goto TERMINATE;
  }

  if ( c->named ) {
    if ( (rows->fieldNames = calloc(cols, sizeof(*rows->fieldNames))) == NULL ) {
      setOOM(error);
      goto TERMINATE;
    }
  }

  /* Find the types of columns and bind fields to them. */
  for (col = 1; col <= cols; ++col) {
    SQLSMALLINT datatype;
    char name[MAX_NAME_LEN];
    SQLSMALLINT namelen;
    Column *r;

    if ( !checkSTMT(rows->stmt, SQLDescribeCol(rows->stmt, col, sqlchar(name),
                                               sizeof(name), &namelen,
                                               &datatype, 0, 0, 0), query,
                    error) )
      goto TERMINATE;
    if ( (size_t)namelen >= sizeof(name) ) {
      error->setBoth(error, -1, "name too long (max name is %lu)",
                       sizeof(name));
      goto TERMINATE;
    }

    r = &rows->result[col - 1];
    if ( c->named ) {
      if ( (rows->fieldNames[col - 1] = STRDUP(name)) == NULL ) {
        setOOM(error);
        goto TERMINATE;
      }
    }

    switch (datatype) {
    case SQL_TINYINT:
      r->type = T_INT8;
      if ( !checkSTMT(rows->stmt, SQLBindCol(rows->stmt, col, SQL_C_TINYINT,
                                             &r->data.b, sizeof (r->data.b),
                                             &r->l), query, error) )
        goto TERMINATE;
      break;
    case SQL_SMALLINT:
      r->type = T_INT16;
      if ( !checkSTMT(rows->stmt, SQLBindCol(rows->stmt, col, SQL_C_SHORT,
                                             &r->data.s, sizeof (r->data.s),
                                             &r->l), query, error) )
        goto TERMINATE;
      break;
    case SQL_INTEGER:
      r->type = T_INT32;
      if ( !checkSTMT(rows->stmt, SQLBindCol(rows->stmt, col, SQL_C_SLONG,
                                             &r->data.i, sizeof (r->data.i),
                                             &r->l), query, error) )
        goto TERMINATE;
      break;
    case SQL_BIGINT:
      r->type = T_INT64;
      if ( !checkSTMT(rows->stmt, SQLBindCol(rows->stmt, col, SQL_C_SBIGINT,
                                             &r->data.l, sizeof (r->data.l),
                                             &r->l), query, error) )
        goto TERMINATE;
      break;
	case SQL_FLOAT:
    case SQL_DOUBLE:
      r->type = T_DOUBLE;
      if ( !checkSTMT(rows->stmt, SQLBindCol(rows->stmt, col, SQL_C_DOUBLE,
                                             &r->data.d, sizeof (r->data.d),
                                             &r->l), query, error) )
        goto TERMINATE;
      break;
    case SQL_REAL:
      r->type = T_FLOAT;
      if ( !checkSTMT(rows->stmt, SQLBindCol(rows->stmt, col, SQL_C_FLOAT,
                                             &r->data.f, sizeof (r->data.f),
                                             &r->l), query, error) )
        goto TERMINATE;
      break;
    case SQL_CHAR:
    case SQL_VARCHAR:
    case SQL_LONGVARCHAR:
      r->type = T_TEXT;
      if ( (r->data.t = malloc(MAX_STRING_LENGTH)) == NULL ) {
        setOOM(error);
        goto TERMINATE;
      }
      if ( !checkSTMT(rows->stmt, SQLBindCol(rows->stmt, col, SQL_C_CHAR,
                                             r->data.t, MAX_STRING_LENGTH - 1,
                                             &r->l), query, error) )
        goto TERMINATE;
      r->data.t[MAX_STRING_LENGTH - 1] = '\0';
      break;
	case SQL_INVALID_HANDLE: // -2
	  error->setBoth(error, -1, "Column %d is invalid or does not exist",
                     (int)col);
	  goto TERMINATE;
    default:
      error->setBoth(error, -1, "Cannot handle column type %d",
                     (int)datatype);
      goto TERMINATE;
    }
  }

  /* Finally execute the statement. */
  if ( !checkSTMT(rows->stmt, SQLExecute(rows->stmt), query, error) )
    goto TERMINATE;

  *rows_p = &rows->base;
  rows = NULL;
  err = NULL;

 TERMINATE:
  inDestroy(rows);
  return err;
}

static void connCloseInputRows(IloOplTableConnection conn,
                               IloOplTableInputRows rows)
{
  (void)conn;
  inDestroy((ODBCInputRows *)rows);
}

static IloOplTableError connOpenOutputRows(IloOplTableConnection conn,
                                           IloOplTableError error,
                                           IloOplTableContext context,
                                           char const *query,
                                           IloOplTableOutputRows *rows_p)
{
  ODBCConnection *c = (ODBCConnection *)conn;
  SQLHDBC *dbc = c->dbc;
  IloOplTableError err = error;
  ODBCOutputRows *rows = NULL;
  SQLSMALLINT nParams;

  (void)context; /* unused in this example */

  if ( (rows = calloc(1, sizeof(*rows))) == NULL ) {
    setOOM(error);
    goto TERMINATE;
  }

  rows->base.getSelectedTupleFields = outGetSelectedTupleFields;
  rows->base.writeInt = outWriteInt;
  rows->base.writeString = outWriteString;
  rows->base.writeNum = outWriteNum;
  rows->base.endRow = outEndRow;
  rows->base.commit = outCommit;
  rows->trans.dbc = dbc;

  /* Wrap the execution of this statement into a transaction */
  if ( transactionStart(&rows->trans, error) )
    goto TERMINATE;

  if ( !checkDBC(dbc, SQLAllocHandle(SQL_HANDLE_STMT, dbc, &rows->stmt),
                 query, error) )
    goto TERMINATE;

  if ( !checkSTMT(rows->stmt, SQLPrepare(rows->stmt, sqlchar(query), SQL_NTS),
                  query, error) )
    goto TERMINATE;

  /* Query the number of parameters and size the parameter buffers
   * accordingly. Note that the individual elements in the array are
   * lazily initialized in the various writeXXX() functions. Binding
   * of the buffers to the statement happens in endRow().
   */
  if ( !checkSTMT(rows->stmt, SQLNumParams(rows->stmt, &nParams), query,
                  error) )
    goto TERMINATE;
  assert(nParams > 0);
  rows->cols = nParams;
  if ( (rows->params = calloc(rows->cols, sizeof(*rows->params))) == NULL ) {
    setOOM(error);
    goto TERMINATE;
  }

  *rows_p = &rows->base;
  rows = NULL;
  err = NULL;

 TERMINATE:

  outDestroy(rows);
  return err;
}

static void connCloseOutputRows(IloOplTableConnection conn,
                                IloOplTableOutputRows rows)
{
  (void)conn;
  outDestroy((ODBCOutputRows *)rows);
}

static IloOplTableError connCreate(char const *connstr,
                                   char const *sql,
                                   int load,
                                   IloOplTableContext context,
                                   IloOplTableError error,
                                   IloOplTableConnection *conn_p)
{
  IloOplTableError err = error;
  ODBCConnection *conn = NULL;
  IloOplTableArgs args = NULL;
  char *copy = NULL;

  if ( (conn = calloc(1, sizeof(*conn))) == NULL ) {
    setOOM(error);
    goto TERMINATE;
  }

  conn->base.destroy = connDestroy;
  conn->base.openInputRows = connOpenInputRows;
  conn->base.closeInputRows = connCloseInputRows;
  conn->base.openOutputRows = connOpenOutputRows;
  conn->base.closeOutputRows = connCloseOutputRows;

  /* Extract arguments from the connection string.
   * The connection string is assumed to be a semi-colon separated
   * list of name/value pairs. Characters can be escaped using the %-sign.
   */
  args = context->parseArgs(context, connstr, ';', '%');
  if ( args == NULL ) {
    error->setBoth(error, -1, "failed to parse connection string '%s'",
                   connstr);
    goto TERMINATE;
  }

# define K_NAMED     "named"
  if ( args->getBool(args, K_NAMED, &conn->named, &conn->named) != 0 ) {
    error->setBoth(error, -1, "failed to get 'named' from '%s'", connstr);
    goto TERMINATE;
  }
  connstr = args->original(args, K_NAMED, NULL);

  /* Allocate ODBC handle for the right version. */
  if ( !check(SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &conn->env),
              error) )
    goto TERMINATE;
  if ( !checkENV(conn->env, SQLSetEnvAttr(conn->env, SQL_ATTR_ODBC_VERSION,
                                          (SQLPOINTER)SQL_OV_ODBC3, 0),
                 NULL, error) )
    goto TERMINATE;

  /* Connect to dabase using connection string. */
  if ( !check(SQLAllocHandle(SQL_HANDLE_DBC, conn->env, &conn->dbc), error) )
    goto TERMINATE;
  if ( !checkDBC(conn->dbc, SQLDriverConnect(conn->dbc, 0,
                                             sqlchar(connstr), SQL_NTS,
                                             0, 0, 0,
                                             SQL_DRIVER_NOPROMPT),
                 connstr, error) )
    goto TERMINATE;

  /* If we open the connection for publishing and there is an initial
   * SQL statement to be executed then execute that now.
   */
  if ( !load && sql && *sql ) {
    /* Split sql command at semi-colons.
     * Note that we strip initial blanks since those may confuse some
     * drivers.
     */
    char *start, *semi;

    if ( (copy = STRDUP(sql)) == NULL ) {
      setOOM(error);
      goto TERMINATE;
    }

    start = copy;
    while ((semi = strchr(start, ';')) != NULL) {
      *semi = '\0';
      if ( !exec(conn->dbc, start, error) )
        goto TERMINATE;
      start = semi + 1;
    }

    if ( *start ) {
      if ( !exec(conn->dbc, start, error) )
        goto TERMINATE;
    }
  }

  *conn_p = &conn->base;
  conn = NULL;
  err = NULL;

 TERMINATE:
  free(copy);

  if ( conn )
    connDestroy(&conn->base);
  return err;
}

/* ********************************************************************** *
 *                                                                        *
 *    Factory and public constructor function                             *
 *                                                                        *
 * ********************************************************************** */

static int factoryRefCount = 0;

static IloOplTableError factoryConnect(char const *subId,
                                       char const *spec,
                                       int load,
                                       IloOplTableContext context,
                                       IloOplTableError error,
                                       IloOplTableConnection *conn_p)
{
  return connCreate(subId, spec, load, context, error, conn_p);
}

static void factoryIncRef(IloOplTableFactory fac)
{
  (void)fac;
  ++factoryRefCount;
}

static void factoryDecRef(IloOplTableFactory fac)
{
  (void)fac;
  assert(factoryRefCount > 0);
  --factoryRefCount;
}

static IloOplTableFactoryC const factory = {
  factoryConnect, factoryIncRef, factoryDecRef
};

/* This exports and defines the function that OPL will lookup in a
 * shared library when it encounters a "ODBCConnection" statement
 * in a .dat file.
 */
ILO_TABLE_EXPORT ILOOPLTABLEDATAHANDLER(ODBC, error, factory_p)
{
  (void)error;
  *factory_p = (IloOplTableFactory)&factory; /* cast away 'const' */
  factoryIncRef(*factory_p);
  return NULL;
}

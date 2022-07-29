# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

# gendoc: ignore
from docplex.mp.constants import ComparisonType
from docplex.mp.linear import LinearExpr, Var
from docplex.mp.mprinter import TextModelPrinter, _ExportWrapper
from docplex.mp.vartype import ContinuousVarType, IntegerVarType, BinaryVarType


class ModelPrettyPrinter(TextModelPrinter):
    vartype_map = {ContinuousVarType: "float", IntegerVarType: "int", BinaryVarType: "bool"}

    ct_symbol_map = {ComparisonType.EQ: "==",
                     ComparisonType.LE: "<=",
                     ComparisonType.GE: ">="}

    indented = ' ' * 2

    def __init__(self, nb_digits=6, sort_variable_names=False):
        # comment line is // as in OPL
        # do NOT forget about user names
        # no encoding is printed
        TextModelPrinter.__init__(self, indent=2, comment_start='//',
                                  nb_digits_for_floats=nb_digits,
                                  hide_user_names=False,
                                  encoding=None,
                                  sort_variable_names=sort_variable_names)

    def get_format(self):
        from docplex.mp.format import OPL_format

        return OPL_format

    def fix_name(self, mobj, prefix, local_index_map, hide_names):
        raw_name = mobj.name
        if raw_name and not hide_names and not mobj.is_generated():
            # there is a user name
            return self._translate_chars(raw_name)
        elif not isinstance(mobj, Var):
            # constraitn with no name -> no name
            return None
        elif mobj.is_generated():
            #mobj_origin = mobj.origin
            # if hasattr(mobj_origin, 'as_var') and mobj is mobj_origin.as_var:
            #     return str(mobj_origin)
            # else:
            return self._make_prefix_name(mobj, prefix, local_index_map, offset=1)
        else:
            # anonymous or anonymized variable. -> x<i>
            return self._make_prefix_name(mobj, prefix, local_index_map, offset=1)

    def _print_model_name(self, out, mdl):
        printed_name = mdl.name or "AnonymousModel"
        out.write("// model name is: {0:s}\n".format(printed_name))

    def _vartype_name(self, vartype):
        # INTERNA: returns a printable string for a vartype
        return self.vartype_map.get(type(vartype), "unknown")

    def _print_var_containers(self, out, mdl):
        gensym_count = 1
        printed_header = False
        for ctn in mdl.iter_var_containers():
            if not printed_header:
                self._print_line_comment(out, "var contrainer section")
                printed_header = True
            vartype_name = self._vartype_name(ctn.vartype)
            varctn_name = ctn.name
            if not varctn_name:
                varctn_name = 'x%d' % gensym_count
                gensym_count += 1
            out.write("dvar {0} {1}{2};\n".format(vartype_name, varctn_name, ctn.dimension_string))

        if printed_header:
            self._newline(out)

    def _print_single_vars(self, out, mdl):
        printed_header = False
        for v in mdl.iter_variables():
            var_ctn = v.container
            if var_ctn is not None:
                continue

            if not printed_header:
                self._print_line_comment(out, "single vars section")
                printed_header = True
            vartype_name = self._vartype_name(v.vartype)
            var_printname = self._var_name_map.get(v._index, "???")
            v_origin = v.origin
            s_generated = ' # -- generated by: {0!s}'.format(v_origin) if v_origin is not None else ''
            out.write("dvar {0} {1};{2}\n".format(vartype_name, var_printname, s_generated))

        if printed_header:
            self._newline(out)

    def _print_objective(self, wrapper, model):
        wrapper.write(model.objective_sense.verb)
        wrapper.flush(print_newline=True)
        objexpr = model.objective_expr
        objlin = objexpr.get_linear_part()
        printed = self._print_lexpr(wrapper, self._num_printer, self._var_name_map, objlin,
                                    allow_empty=True,
                                    print_constant=False)
        if objexpr.is_quad_expr() and objexpr.has_quadratic_term():
            self._print_qexpr_obj(wrapper, self._num_printer, self._var_name_map,
                                  quad_expr=objexpr,
                                  force_initial_plus=printed,
                                  use_double=False)
            printed = True
        obj_offset = objexpr.get_constant()
        if obj_offset:
            if printed and obj_offset > 0:
                wrapper.write(u'+')
            wrapper.write(self._num_to_string(obj_offset))
        wrapper.write(';', separator=False)
        wrapper.flush()

    def _pprint_expr(self, wrapper, expr):
        q = 0
        if expr.is_quad_expr() and expr.has_quadratic_term():
            q = self._print_qexpr_iter(wrapper, self._num_printer, self._var_name_map, expr.iter_sorted_quads(),
                                       use_double=False)
        self._print_expr_iter(wrapper, self._num_printer, self._var_name_map, expr.iter_terms(),
                              constant=expr.get_constant(),  # yes, print the constant
                              allow_empty=q > 0,
                              force_first_plus=q > 0  # force  a '+' if quadratic section is non-empty
                              )

    def _print_binary_constraint(self, wrapper, ct):
        left_expr = ct.left_expr
        right_expr = ct.right_expr
        self._pprint_expr(wrapper, left_expr)

        wrapper.write(self.ct_symbol_map[ct.sense])

        self._pprint_expr(wrapper, right_expr)

    def _print_range_constraint(self, wrapper, rng):
        expr = rng.expr
        lb = rng.lb
        ub = rng.ub
        wrapper.write(self._num_to_string(lb))
        wrapper.write("<=")
        self._print_lexpr(wrapper, self._num_printer, self._var_name_map, expr, print_constant=True)
        wrapper.write("<=")
        wrapper.write(self._num_to_string(ub))

    def _print_logical_constraint(self, wrapper, logi_ct, logical_symbol):
        active = logi_ct.active_value
        linear_ct = logi_ct.linear_constraint
        indicator_varname = self._var_print_name(logi_ct.binary_var)
        wrapper.write(indicator_varname)
        if 0 == active:
            wrapper.write("== 0")
        wrapper.write(logical_symbol)
        wrapper.write('(')
        self._print_binary_constraint(wrapper, linear_ct)
        wrapper.write(');', separator=False)

    def _print_linear_constraints(self, wrapper, model):
        wrapper.begin_line()
        for ct in model.iter_binary_constraints():

            wrapper.begin_line()
            ctname = self.linearct_print_name(ct)
            if ctname:
                wrapper.set_indent('  ')  # two spaces
                wrapper.write(" %s:" % ctname)
                wrapper.flush()
            else:
                wrapper.begin_line(indented=True)

            self._print_binary_constraint(wrapper, ct)
            wrapper.write(';', separator=False)
            wrapper.set_indent(' ')
            wrapper.flush(print_newline=True, restart_from_empty_line=False)

    def _print_ranges(self, wrapper, model):
        wrapper.begin_line()
        for ct in model.iter_range_constraints():

            wrapper.begin_line()
            ctname = self.linearct_print_name(ct)
            if ctname:
                wrapper.set_indent(2 * ' ')
                wrapper.write(' %s:' % ctname)
                wrapper.flush()

            else:
                wrapper.begin_line(indented=True)

            self._print_range_constraint(wrapper, ct)
            wrapper.write(';', separator=False)
            wrapper.flush()
        wrapper.set_indent(' ')

    def _print_logicals(self, wrapper, model):
        for ct in model.iter_logical_constraints():
            ctname = self.logicalct_print_name(ct)
            if ctname:
                wrapper.set_indent('  ')
                wrapper.write(" %s:" % ctname)
                wrapper.flush()
            else:
                wrapper.begin_line(indented=True)
            symb = '<=>' if ct.is_equivalence() else '<='
            self._print_logical_constraint(wrapper, ct, logical_symbol=symb)
            wrapper.set_indent(' ')
            wrapper.flush(restart_from_empty_line=True)

    def _print_quadratic_cts(self, wrapper, model):
        for qct in model.iter_quadratic_constraints():

            ctname = self.qc_print_name(qct)
            if ctname:
                wrapper.set_indent('  ')
                wrapper.write(" %s:" % ctname)
                wrapper.flush()
            else:
                wrapper.begin_line(indented=True)

            self._print_binary_constraint(wrapper, qct)
            wrapper.write(';', separator=False)
            wrapper.set_indent(' ')
            wrapper.flush(restart_from_empty_line=True)

    def _print_kpis(self, out, wrapper, model):
        printed_section_header = False
        for kpi in model.iter_kpis():
            if kpi.is_decision_expression():
                if not printed_section_header:
                    self._newline(out)
                    self._print_line_comment(out, " KPI section")
                    printed_section_header = True

                kpi_expr = kpi.to_expr()
                kpi_typename = 'int' if kpi_expr.is_discrete() else 'float'
                wrapper.write('dexpr {0} {1}'.format(kpi_typename, self._translate_chars(kpi.name)))
                wrapper.write('=')
                if isinstance(kpi_expr, LinearExpr):
                    self._print_lexpr(wrapper, self._num_printer, self._var_name_map, kpi_expr, print_constant=True)
                elif isinstance(kpi_expr, Var):
                    wrapper.write(kpi_expr.name)
                wrapper.write(';', separator=False)
                wrapper.flush(restart_from_empty_line=True)
                # ---
        if printed_section_header:
            wrapper.newline()

    def _print_sos(self, wrapper, model):
        varname_map = self._var_name_map
        for sos_varset in model.iter_sos():
            sos_varname_joined = ', '.join(varname_map[v._index] for v in sos_varset.iter_variables())
            wrapper.write('sos{0}: {1}'.format(sos_varset.sos_type.value, sos_varname_joined))
        wrapper.flush()

    def print_model_to_stream(self, out, model):
        wrapper = _ExportWrapper(oss=out, indent_str=' ', line_width=78)
        self.prepare(model)
        # header
        self._print_signature(out)
        self._print_encoding(out)
        self._print_model_name(out, model)

        # var containers
        self._print_var_containers(out, model)
        self._print_single_vars(out, model)
        # KPI section
        self._print_kpis(out, wrapper, model)

        self._print_objective(wrapper, model)
        wrapper.write("\nsubject to {")
        wrapper.flush()
        self._print_linear_constraints(wrapper, model)
        self._print_ranges(wrapper, model)
        self._print_logicals(wrapper, model)
        self._print_quadratic_cts(wrapper, model)
        self._print_sos(wrapper, model)
        out.write("}\n")

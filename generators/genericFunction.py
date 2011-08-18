#!/usr/bin/env python
from random import *

# Generation parameters
TIMEOUT = 2
MAX_PARAMETERS = 8
MAX_VARIABLES = 8
MAX_VALUE = 10000
MAX_STATEMENTS = 8
DEFINED_LIKELIHOOD = 8
EXPR_NEST_LIKELIHOOD = 3
STMT_NEST_LIKELIHOOD = 4
PARAMETER_LIKELIHOOD = 2
MAX_DEPTH = 8
INDENT = "    "

# Generation state
r = Random()
parameters = []
variables = []
functions = []
indentation = 0
loop_depth = 0

# Random utilities
def wchoice(l):
    tw = 0
    for (w,_) in l:
        tw += w
    v = r.randrange(0, tw)
    tw = 0
    for (w,e) in l:
        tw += w
        if v < tw:
            return e
    assert False

# Generation utilities
def emit(s):
    print "%s%s" % (INDENT * indentation, s)

def set_timeout(n):
    emit("timeout(%d);" % n)

def begin_block(s):
    global indentation
    emit(s)
    indentation += 1

def continue_block(s):
    global indentation
    assert not indentation == 0
    indentation -= 1
    emit(s)
    indentation += 1

def end_block(s):
    global indentation
    assert not indentation == 0
    indentation -= 1
    emit(s)

def new_variable():
    variables.append("v%d" % len(variables))
    if r.randrange(0, DEFINED_LIKELIHOOD) == 0:
        emit("var %s = %d;" % (variables[-1], r.randrange(0, MAX_VALUE)))
    else:
        emit("var %s;" % variables[-1])

def begin_new_function(nparams):
    global parameters
    functions.append("f%d" % len(functions))
    parameters = ["p%d" % x for x in range(0, nparams)]
    begin_block("function %s(%s) {" % (functions[-1], ','.join(parameters)))

def end_function():
    end_block("}")

# Generation routines
binary_bitops = ['&', '|', '^']
def binary_bitop_expr(d):
    bitop = r.choice(binary_bitops)
    return "(%s %s %s)" % (expr(d+1), bitop, expr(d+1))

binary_ariths = ['+']
def binary_arith_expr(d):
    arith = r.choice(binary_ariths)
    return "(%s %s %s)" % (expr(d+1), arith, expr(d+1))

unary_bitops = ['~']
def unary_bitop_expr(d):
    bitop = r.choice(unary_bitops)
    return "(%s %s)" % (bitop, expr(d+1))

incdecs = [(True,'++'), (True,'--'), (False,'++'), (False,'--')]
def var_incdec_expr(d):
    (prefix, arith) = r.choice(incdecs)
    if prefix:
        return "(%s%s)" % (arith, r.choice(variables))
    else:
        return "(%s%s)" % (r.choice(variables), arith)

def param_incdec_expr(d):
    if not len(parameters):
        return var_incdec_expr(d)
    (prefix, arith) = r.choice(incdecs)
    if prefix:
        return "(%s%s)" % (arith, r.choice(parameters))
    else:
        return "(%s%s)" % (r.choice(parameters), arith)

def call_expr(d):
    return "%s(%s)" % (r.choice(functions), ','.join([str(x) for x in parameter_list()]))

def param_expr(d):
    if len(parameters):
        return r.choice(parameters)
    return var_expr(d)

def var_expr(d):
    return r.choice(variables)

def one_point_seven_expr(d):
    return "1.7"

nest_exprs = [(100,binary_bitop_expr), (100,binary_arith_expr), (0,unary_bitop_expr)]
root_exprs = [(100,param_expr), (100,var_expr), (10,one_point_seven_expr), (0,var_incdec_expr), (0,param_incdec_expr)]
def expr(d):
    if d < MAX_DEPTH and r.randrange(0, EXPR_NEST_LIKELIHOOD) == 0:
        return wchoice(nest_exprs)(d)
    else:
        return wchoice(root_exprs)(d)

def var_assign_stmt(d):
    emit("%s = %s;" % (r.choice(variables), expr(d+1)))

def param_assign_stmt(d):
    emit("%s = %s;" % (r.choice(parameters), expr(d+1)))

def expr_stmt(d):
    emit("%s;" % expr(d+1))

def do_stmt(d):
    global loop_depth
    begin_block("loop%d: do {" % loop_depth)
    loop_depth += 1
    for i in range(0, r.randint(0, MAX_STATEMENTS)):
        stmt(d+1)
    loop_depth -= 1
    end_block("} while (%s);" % (expr(d+1)))

def while_stmt(d):
    global loop_depth
    begin_block("loop%d: while (%s) {" % (loop_depth, expr(d+1)))
    loop_depth += 1
    for i in range(0, r.randint(0, MAX_STATEMENTS)):
        stmt(d+1)
    loop_depth -= 1
    end_block("}")

def if_stmt(d):
    begin_block("if (%s) {" % expr(d+1))
    for i in range(0, r.randint(0, MAX_STATEMENTS)):
        stmt(d+1)
    end_block("}")

def ifelse_stmt(d):
    begin_block("if (%s) {" % expr(d+1))
    for i in range(0, r.randint(0, MAX_STATEMENTS / 2)):
        stmt(d+1)
    continue_block("} else {")
    for i in range(0, r.randint(0, MAX_STATEMENTS / 2)):
        stmt(d+1)
    end_block("}")

def call_stmt(d):
    emit("%s;" % call_expr(d+1))

def continue_stmt(d):
    emit("continue;")

def label_continue_stmt(d):
    emit("continue loop%d;" % r.randrange(0, loop_depth))

def break_stmt(d):
    emit("break;")

def label_break_stmt(d):
    emit("break loop%d;" % r.randrange(0, loop_depth))

def return_stmt(d):
    emit("return %s;" % r.choice(variables))

nest_stmts = [(100,do_stmt), (100,while_stmt), (100,if_stmt), (100,ifelse_stmt)]
root_stmts = [(50,var_assign_stmt), (0,param_assign_stmt), (100,expr_stmt), (10,return_stmt)]
root_loop_stmts = [(20,continue_stmt), (20,label_continue_stmt), (20,break_stmt), (20,label_break_stmt)]
def stmt(d):
    if d < MAX_DEPTH and r.randrange(0, STMT_NEST_LIKELIHOOD) == 0:
        wchoice(nest_stmts)(d)
    elif loop_depth >= 1:
        wchoice(root_stmts + root_loop_stmts)(d)
    else:
        wchoice(root_stmts)(d)

def function_decl():
    begin_new_function(r.randint(0, MAX_PARAMETERS))
    for i in range(0, r.randint(1, MAX_VARIABLES)):
        new_variable()
    for i in range(0, r.randint(1, MAX_STATEMENTS)):
        stmt(0)
    end_function()

def parameter_list():
    return r.sample(xrange(0, MAX_VALUE), len(parameters))

# Main routine
#set_timeout(TIMEOUT)
function_decl()
emit("print(%s);" % call_expr(0))

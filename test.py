import argparse
from test import extract_info
from test import database_speed
from test import parser as parse_module

import test

#from test import sim_module

parser = argparse.ArgumentParser(description='Parser input')
parser.add_argument(help="input test script module in [database-interactive, sim-interactive, speed_sql, extract_time, extract_sample, parse-log] to run", dest="script")
parser.add_argument("--args", nargs="+", help="function argument to pass to script", dest="func_args")
parser.add_argument("--func", help="function name to run script", dest="func_name")

args = parser.parse_args()
if args.script == "pretty-print":
    extract_info.pretty_print()

if args.script == "database-interactive":
    extract_info.interactive_print()

if args.script == "sim-interactive":
    sim_module.interactive_print()

if args.script == "speed_sql":
    database_speed.sql_test_speed()
    
if args.script == "extract_time":
    extract_info.camp_cell_extract_time()

if args.script == "extract_sample":
    extract_info.camp_cell_extract_sample()

if args.script == "parse-log":
    parse_module.parse_log()

if args.script == "unit-test":
    print("script run {} function argument {}".format(args.func_name ,args.func_args))
    if args.func_name == "ranking_module":
        from test.unit_tests.ranking_module import TestModule
        test_module = TestModule()
        test_module.run_test()
    if args.func_name == "module_test":
        from test.unit_tests.ranking_module import TestModule
        test_module = TestModule()
        test_module.module_test(attr=args.func_args[0], arfcns=args.func_args[1:-1], 
                index_round=args.func_args[-1])
    if args.func_name == "mobile_arfcn":
        from test.unit_tests.target_mobile import TargetMobile
        test_module = TargetMobile()
        test_module.plot_selected_arfcns(arfcns=[int(arfcn) for arfcn in args.func_args])
    if args.func_name == "mobile_data":
        from test.unit_tests.target_mobile import TargetMobile
        test_module = TargetMobile()
        test_module.plot_mobile_database()


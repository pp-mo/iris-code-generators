from gen_rules import write_rules_module

if __name__ == '__main__':
    write_rules_module('pp', ['../save_rules/pp_save_rules.txt'],
                       '../outputs/iris/fileformats/pp_save_rules.py',
                       save_style=True)

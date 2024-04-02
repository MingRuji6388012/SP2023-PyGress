import os
import shutil
from indra.reach import reach_api
from indra.databases import pmc_client
from indra.preassembler.hierarchy_manager import entity_hierarchy as eh
from indra.preassembler.hierarchy_manager import modification_hierarchy as mh
from indra.preassembler import Preassembler
from indra.pysb_assembler import PysbAssembler

def have_file(fname):
    return os.path.exists(fname)

if __name__ == '__main__':
    pmc_ids = ['PMC1234335', 'PMC3178447', 'PMC3690480',
               'PMC4345513', 'PMC534114']
    rerun = False
    
    pa = Preassembler(eh, mh)
    
    for pi in pmc_ids:
        print 'Reading %s...' % pi
        # If REACH already processed it then don't run it again
        if rerun or not have_file(pi + '.json'):
            if have_file(pi + '.txt'):
                txt = open(pi + '.txt').read()
                rp = reach_api.process_text(txt)
            elif have_file(pi + '.nxml'):
                rp = reach_api.process_nxml(pi + '.nxml')
            else:
                rp = reach_api.process_pmc(pi, save=True)
            shutil.move('reach_output.json', pi + '.json')
        else:
            rp = reach_api.process_json_file(pi + '.json')
        
        print '%s statements collected.' % len(rp.statements)
        pa.add_statements(rp.statements)
    
    print '%d statements collected in total.' % len(pa.stmts)
    duplicate_stmts = pa.combine_duplicates()
    print '%d statements after combining duplicates.' % len(duplicate_stmts)
    related_stmts = pa.combine_related()
    print '%d statements after combining related.' % len(related_stmts)

    pya = PysbAssembler()
    pya.add_statements(related_stmts)
    model = pya.make_model()

    print 'PySB model has %d monomers and %d rules' %\
        (len(model.monomers), len(model.rules))

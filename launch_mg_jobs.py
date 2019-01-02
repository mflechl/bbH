from jobs import Jobs
import argparse
import os
import ROOT
import json
import subprocess
from math import ceil
from math import sqrt
from array import array
from itertools import product

job_mgr = Jobs()
parser = argparse.ArgumentParser()

parser.add_argument('--mg-dir', default='./MG5_aMC_v2_6_1')
parser.add_argument('--base', default='./bbH_4FS_yb2')
parser.add_argument('-n', '--nevents', default=500000, type=int)
parser.add_argument('--mg-split', default=10000, type=int)
parser.add_argument('--cores', default=8, type=int)
parser.add_argument('--split', default=-1, type=int)
parser.add_argument('--qsh', default=0, type=int)
parser.add_argument('-m', '--mass', default='500')
parser.add_argument('--step', default='none', choices=['none', 'lhe', 'clean', 'upload', 'gen', 'ntuple', 'xsec', 'gridpack'])
parser.add_argument('--upload', default=None)
parser.add_argument('--gp-name', default='SUSYGluGluToBBHToTauTau_M-')
parser.add_argument('--download', default=None)
parser.add_argument('--usetmp', action='store_true')
parser.add_argument('--seed', default=0, type=int)
parser.add_argument('--postfix', default='')
parser.add_argument('--req-acc', default=-1.0, type=float)

job_mgr.attach_job_args(parser)
args = parser.parse_args()
job_mgr.set_args(args)

def run_cmd(arg):
    print arg
    os.system(arg)

if args.split == -1:
    args.split = args.nevents


for MASS in args.mass.split(','):
    base_name = os.path.basename(os.path.normpath(args.base))
    massdir = '%s_%s%s' % (base_name, MASS, args.postfix)
    if args.qsh == 1:
        massdir += '_qshDown'
    if args.qsh == 2:
        massdir += '_qshUp'
    workdir = os.path.join(args.mg_dir, massdir)

    if args.step in ['lhe']:
        if os.path.isdir(workdir):
            print 'Dir %s already exists, skipping' % workdir
            continue
        else:
            os.system('cp -r %s %s' % (args.base, workdir))

        with open('%s/Cards/param_card.dat' % (workdir)) as param_file:
            param_cfg = param_file.read()
        param_cfg = param_cfg.replace('{MASS}', '%.5e' % float(MASS))
        with open('%s/Cards/param_card.dat' % (workdir), "w") as outfile:
            outfile.write(param_cfg)
        
        with open('%s/Cards/run_card.dat' % (workdir)) as run_file:
            run_cfg = run_file.read()
        run_cfg = run_cfg.replace('{TOTAL_EVENTS}', '%i' % args.nevents)
        run_cfg = run_cfg.replace('{EVENTS_PER_JOB}', '%i' % args.mg_split)
        run_cfg = run_cfg.replace('{REQ_ACC}', '%g' % args.req_acc)
        run_cfg = run_cfg.replace('{SEED}', '%i' % args.seed)
        with open('%s/Cards/run_card.dat' % (workdir), "w") as outfile:
            outfile.write(run_cfg)

        with open('%s/Cards/amcatnlo_configuration.txt' % (workdir)) as amc_file:
            amc_cfg = amc_file.read()
        amc_cfg = amc_cfg.replace('{MG_PATH}', '%s' % os.path.abspath(args.mg_dir))
        amc_cfg = amc_cfg.replace('{LHAPDF_PATH}', '%s/bin/lhapdf-config' % subprocess.check_output(['scram', 'tool tag lhapdf LHAPDF_BASE']).strip())
#        amc_cfg = amc_cfg.replace('{FASTJET_PATH}', '%s/bin/fastjet-config' % subprocess.check_output(['scram', 'tool tag fastjet FASTJET_BASE']).strip())
        amc_cfg = amc_cfg.replace('{FASTJET_PATH}', '/cvmfs/cms.cern.ch/slc6_amd64_gcc481//external/fastjet/3.1.0/bin/fastjet-config')
        with open('%s/Cards/amcatnlo_configuration.txt' % (workdir), "w") as outfile:
            outfile.write(amc_cfg)
        
        with open('%s/SubProcesses/madfks_mcatnlo.inc' % (workdir)) as scale_file:
            scale_cfg = scale_file.read()
            frac_lo = 0.025
            frac_hi = 0.25
            if args.qsh == 1:
                frac_lo /= sqrt(2.)
                frac_hi /= sqrt(2.)
            if args.qsh == 2:
                frac_lo *= sqrt(2.)
                frac_hi *= sqrt(2.)
        scale_cfg = scale_cfg.replace('{FRAC_LO}', '%.3f' % frac_lo)
        scale_cfg = scale_cfg.replace('{FRAC_HI}', '%.3f' % frac_hi)
        with open('%s/SubProcesses/madfks_mcatnlo.inc' % (workdir), "w") as outfile:
            outfile.write(scale_cfg)
        
        base_cmd = 'cd %s' % workdir
        cmd = base_cmd
        cmd += '; echo -e "3\\n3" | ./bin/generate_events --nb_core=%i' % args.cores
#        cmd += '; echo "3" | ./bin/generate_events --nb_core=%i' % args.cores
#echo -e "3\n3"

        job_mgr.job_queue.append(cmd)
    
    if args.step in ['gridpack']:
        gp_name = '%s%s' % (args.gp_name, MASS) 
        run_cmd('mkdir gridpack_%s' % gp_name)
        run_cmd('cp -a  %s gridpack_%s/process' % (workdir, gp_name))
        run_cmd('echo "mg5_path = ../mgbasedir" >> gridpack_%s/process/Cards/amcatnlo_configuration.txt' % (gp_name))
        run_cmd('cp -a %s_ref gridpack_%s/mgbasedir' % (args.mg_dir, gp_name))
        run_cmd('cp runcmsgrid_NLO.sh gridpack_%s/runcmsgrid.sh' % (gp_name))
        run_cmd('cd gridpack_%s; ../cleangridmore.sh; cd ..' % (gp_name))
        run_cmd('cd gridpack_%s; XZ_OPT="--lzma2=preset=9,dict=512MiB" tar -cJpsf ../%s_tarball.tar.xz mgbasedir process runcmsgrid.sh; cd ..' % (gp_name, gp_name))

        

    if args.step in ['clean']:
        os.system('rm -r %s/SubProcesses %s/Events/run_01/alllogs_*' % (workdir, workdir))

    if args.step in ['upload'] and args.upload is not None:
        os.system('pushd %s/Events/run_01; gunzip -c events.lhe.gz > events.lhe; gfal-copy -f events.lhe %s/%s/events.lhe; rm events.lhe; popd' % (workdir, args.upload, massdir)) 
        #print 'pushd %s/Events/run_01; gunzip -c events.lhe.gz > events.lhe; gfal-copy -f events.lhe %s/%s/events.lhe; rm events.lhe; popd' % (workdir, args.upload, massdir) 
        
job_mgr.flush_queue()


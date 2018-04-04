cmsrel CMSSW_7_1_28; cd CMSSW_7_1_28/src; cmsenv; scram b -j 8

git clone git@github.com:mflechl/bbH.git
cd bbH

wget https://launchpad.net/mg5amcnlo/2.0/2.2.x/+download/MG5_aMC_v2.3.0.beta.tar.gz
tar -zxf MG5_aMC_v2.3.0.beta.tar.gz

# patches needed to fix this bug: https://bugs.launchpad.net/mg5amcnlo/+bug/1483772
patch MG5_aMC_v2_3_0_beta/vendor/CutTools/src/avh/avh_olo.f90 cuttools_avh_olo.f90.patch
patch MG5_aMC_v2_3_0_beta/vendor/IREGI/src/oneloop/src/avh_olo_units.f90 oneloop_avh_olo_units.f90.patch

# Generate dummy process directory interactively. I think this is mostly just to compile some of the common libraries we need.
cd MG5_aMC_v2_3_0_beta/
./bin/mg5
generate p p > h b b~ [QCD]
output bbH_test
exit
  
cd ..
tar -zxf bbH_4FS_yb2_modified.tar.gz

# Edit any of the cards, e.g. bbH_4FS_yb2/Cards/run_card.dat for sqrt(s)

# Setup directories and submit jobs
#   -m : comma separated list of mass points to produce
#   --cores X: tell mg to use X cores in parallel in each job.
#              Adjust -n option in --sub-opts if running on lxbatch
#              to request n-core machine.
#   --req-acc: sampling grid accuracy - leave as 0.001 (CMS default)
#   -n X: number of events to generate. Events aren't used for anything but has to be > 0
mkdir jobs
python launch_mg_jobs.py -m 200,250,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2300,2600,2900,3200,3500 --job-mode lxbatch --sub-opts '-q 2nd -n 4 -R "span[hosts=1]"' --task-name mgprod --step lhe --dir jobs/ --qsh 0 --cores 4 --req-acc 0.001 -n 100 #[--dry-run]




# Once jobs are done, convert output into an official-style gridpack:
cp -pr MG5_aMC_v2_3_0_beta MG5_aMC_v2_3_0_beta_ref
rm -rf MG5_aMC_v2_3_0_beta_ref/bbH_4FS_yb2*
python launch_mg_jobs.py -m 200,250,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2300,2600,2900,3200,3500 --step gridpack --dir jobs/ --qsh 0 --cores 4 -n 100 --req-acc 0.001 --gp-name SUSYGluGluToBBHToTauTau_M-



#to test: new area
cmsrel CMSSW_7_1_28; cd CMSSW_7_1_28/src; cmsenv
tar -xavf <name>.tar.xz
./runcmsgrid.sh 100 733 4  #<NEvents> <RandomSeed> <NumberOfCPUs>
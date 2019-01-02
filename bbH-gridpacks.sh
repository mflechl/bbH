#INSTRUCTIONS TO RUN WITH MG5_aMC_v2.6.1
#They need to be entered line-by-line (i.e. not executed as a script)

cmsrel CMSSW_7_1_30; cd CMSSW_7_1_30/src; cmsenv; scram b -j 8

git clone git@github.com:mflechl/bbH.git -b MG5_v2.6
cd bbH

#wget https://launchpad.net/mg5amcnlo/2.0/2.6.x/+download/MG5_aMC_v2.6.1.tar.gz
tar -zxf MG5_aMC_v2.6.1.tar.gz

# Generate dummy process directory interactively. I think this is mostly just to compile some of the common libraries we need.
cd MG5_aMC_v2_6_1
./bin/mg5
n
generate p p > h b b~ [QCD]
output bbH_test

exit
cat bbH_test/Source/PDF/pdfwrap_lhapdf.f | sed s#'      CALL SETPDFPATH(LHAPATH)'#'C      CALL SETPDFPATH(LHAPATH)'#g >bbH_test/Source/PDF/pdfwrap_lhapdf.f
  
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
python launch_mg_jobs.py -m 80,90,100,110,120,125,130,140,160,180,200,250,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2300,2600,2900,3200,3500 --job-mode lxbatch --sub-opts '-q 2nd -n 4 -R "span[hosts=1]"' --task-name mgprod --step lhe --dir jobs/ --qsh 0 --cores 4 --req-acc 0.001 -n 100 #[--dry-run]

#python launch_mg_jobs.py -m 200,500 --job-mode lxbatch --sub-opts '-q 2nd -n 4 -R "span[hosts=1]"' --task-name mgprod --step lhe --dir jobs/ --qsh 0 --cores 4 --req-acc 0.001 -n 100 --dry-run
#em MG5_aMC_v2_6_1/bbH_test/Cards/amcatnlo_configuration.txt -> fastjet = /cvmfs/cms.cern.ch/slc6_amd64_gcc481//external/fastjet/3.1.0/bin/fastjet-config
#em ./MG5_aMC_v2_6_1/bbH_test/Source/PDF/pdfwrap_lhapdf.f -> Comment out line 23, CALL SETPDFPATH(LHAPATH)


# Once jobs are done, convert output into an official-style gridpack:
cp -pr MG5_aMC_v2_6_1/ MG5_aMC_v2_6_1_ref
rm -rf MG5_aMC_v2_6_1_ref/bbH_4FS_yb2*
python launch_mg_jobs.py -m 80,90,100,110,120,125,130,140,160,180,200,250,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2300,2600,2900,3200,3500 --step gridpack --dir jobs/ --qsh 0 --cores 4 -n 100 --req-acc 0.001 --gp-name SUSYGluGluToBBH_M-



#to test: new area
cmsrel CMSSW_7_1_30; cd CMSSW_7_1_30/src; cmsenv
tar -axf <name>.tar.xz
./runcmsgrid.sh 100 733 4  #<NEvents> <RandomSeed> <NumberOfCPUs>

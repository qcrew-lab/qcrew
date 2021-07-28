@echo off
TITLE "QCREW'S REMOTE STAGE"
@echo on
call C:\Users\qcrew\Anaconda3\Scripts\activate.bat
call conda activate qcrew-run
cd ../qcrew/control/stage
python -m stage_setup

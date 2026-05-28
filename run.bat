@echo off
cd /d "%~dp0"
python main.py check_full_discount_games
echo %date% %time% - Script ran >> run_log.txt

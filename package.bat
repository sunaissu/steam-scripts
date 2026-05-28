@echo off
rd /s /q lambda_package 2>nul
mkdir lambda_package

pip install requests -t lambda_package --quiet

xcopy scripts lambda_package\scripts\ /E /I /Y /Q
copy lambda_function.py lambda_package\

cd lambda_package
powershell Compress-Archive -Path * -DestinationPath ..\lambda.zip -Force
cd ..

rd /s /q lambda_package

echo.
echo lambda.zip is ready. Upload it to AWS Lambda.

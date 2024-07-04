## Evaluation
Create conda environment
```
conda create --name evaluate python=3.11
conda activate evaluate
```

Install playwright
```
cd "Exercise3/data/"
npm init -y
npm install playwright
playwright install
```

Before running, make sure Cadenza Web App is running. In `C:\DisyCadenza_9.4.71\CadenzaWeb\bin` click on `setclasspath.bat` then `startup.bat`, then a Tomcat window should open. Don't close it while running evaluation.
Test with `http://localhost:8080/cadenza` in web browser if Cadenza Web Server has started succesfully.

Execute `evaluation.py` inside  "Exercise3/data/" directory with directory path of generated scripts `generated_scripts/<subfolder_name>` (no "/" at the end!)
```
python evaluate.py ./generated_scripts/few_shot/
```

Result .csv file is saved in  `evaluation_results/few_shot/`.

The number of workers and time out is set in `playwright.config.ts`. 
Timeout is reduced to 15s (default is 30s) to reduce evaluation time. 
The number of workers is set to 1 (sequential testing) due to the concurrent user problem.

***Note: Unfortunately, it still doesn't work properly due to the concurrent user problem of the CadenzaWebApp, so many tests might fail due to login problems....***
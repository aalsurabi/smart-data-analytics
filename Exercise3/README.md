## Evaluation
### Create conda environment and install packages
```
conda create --name evaluate python=3.11
conda activate evaluate
conda install pillow pandas numpy
pip install pixelmatch
```

Install playwright:
```
cd "Exercise3/data/"
npm init -y
npm install playwright
playwright install
```

The `workers` parameter in the `playwrigt.config.ts` is set to 1 for evaluation. Unfortunately, execution in parallel doesn't seem to work well. In general, often few tests seem to fail  but work when trying to execute them again. Sequentially, it seems to work better but still sometimes test fail randomly.
The `timeout` is changed from default 30s to 20s to reduce evaluation time. This value might some adjustment, depending how long running a script on average needs on your laptop. In my case, the test_script files took less than 10 seconds.

### 0. Run Cadenza Web App
Before running, make sure Cadenza Web App is running. In `C:\DisyCadenza_9.4.127\CadenzaWeb\bin` (make sure to take **version 9.4.127** not 9.4.71, since it allows for more than 10 concurrent users!) click on `setclasspath.bat` then `startup.bat`, then a Tomcat window should open. Wait until tomcat window prints "Server Startup" (takes about 30s-40s on my laptop) so that the server is ready. Don't close it while running evaluation.

(Test with `http://localhost:8080/cadenza` in web browser if Cadenza Web Server has started succesfully.)


### 1. Generate screenshots of test scripts
Execute `evaluation.py` inside  "Exercise3/data/" directory.

First generate the screenshots of test_script by executing the command:
```
python evaluate.py ./test_script --no-evaluate
```
This will generate the true screenshots of the test data which are used to compare to other generated screenshots. No evaluation csv file is generated. 
Sometimes, randomly tests fail, so in this case (because all test scrips should execute), the failing tests are executed again. Usually, a second run is succesful.


**Important: Before each new run of the script, restart the Cadenza Web App!** Otherwhise, it could lead to concorrent user problems again. (101 tests easily passed through but when repeated immediately again, there were some concurrent user problems..)


### 2. Evaluation
To evaluate the generated scripts from the LLM execute the script with the  directory path of the generated scripts `generated_scripts/<subfolder_name>` (**no "/" at the end!**), e.g.
```
python evaluate.py ./generated_scripts/few_shot
```

Result .csv file is saved in the directory  `evaluation_results/few_shot/`.

For next evaluation restart CadenzaWebServer.
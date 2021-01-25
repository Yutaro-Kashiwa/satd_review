# A replication package of "Empirical Study on Self-Admitted Technical Debt inModern Code Review"


## Procedure to run this program
1. Download datasets (http://)
2. Write the path of the downloaded dataset into data_dir of setting ini 
3. run shell script (run.sh)<br>
   sh run.sh [PROJECT_NAME] [START_REVIEW_NO] [STOP_REVIEW_NO] [THREAD_NUM]<br>
   * NOTE: We recommend to use Kubernetes because the program processes numerous reviews including many patches. We prepared Dockerfile on the top directory and sample setting file of Kubernetes under kube/created directory
4. run python script in src/_2_calculate/all.py which calculates the results of RQ1, RQ2, and RQ3 (only for the quantitative analysis). 
## NOTE
- The program often returns "Please Rerun" Error due to the busy state of pexpect.spawn. In this case, users just need to rerun the program specifying the number. 
- The program cannot process approximately 20 review records because they contain files written in the wrong formats. 
- Users can ignore "query file not found" and "detail file not found" errors because we removed irrelevant files from datasets. 
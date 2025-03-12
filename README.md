# buzzbot: Automated Solana Altcoin Trading.

Let's break down exactly which files you need to modify and what information to replace, step by step:

**1. `variables.tf` (Root Directory)**

* **`project_id`:**
    * Replace `"YOUR_PROJECT_ID"` with your actual Google Cloud Project ID.
* **`source_bucket`:**
    * Replace `"YOUR_SOURCE_BUCKET"` with the name of the Google Cloud Storage bucket where you'll store your Cloud Functions' source code (ZIP files).

    ```terraform
    variable "project_id" {
      type        = string
      description = "The GCP project ID"
    }

    variable "region" {
      type        = string
      description = "The GCP region"
      default     = "us-central1"
    }

    variable "source_bucket" {
      type        = string
      description = "The GCS bucket containing the function source code"
    }
    ```

**2. `main.tf` (Root Directory)**

* **`variable "users"`:**
    * Replace `"user1_private_key_value"` and `"user2_private_key_value"` with the actual, **encrypted** private keys for your users.
    * **Important:** Do not store plain-text private keys. Ideally, you should retrieve these keys from a secure source (like a database or an external API) and encrypt them before storing them in your Terraform state.
    * Add or remove users as needed.
* **Cloud Scheduler**
    * Verify the schedule is correct.

    ```terraform
    variable "users" {
      type = list(object({
        user_id     = string
        private_key = string
      }))
      default = [
        {
          user_id     = "user1",
          private_key = "user1_encrypted_private_key"
        },
        {
          user_id     = "user2",
          private_key = "user2_encrypted_private_key"
        },
      ]
    }
    ```

**3. `modules/cloud_run_service/main.tf` and `modules/cloud_function/main.tf`**

* These modules are designed to be reusable, so you shouldn't need to change anything directly within these files. All configuration will be passed through variables.

**4. `modules/user_service/main.tf`**

* No information needs to be changed here, the module recieves all needed information from the root module.

**5. `functions/trigger_function_1/main.py`, `functions/trigger_function_2/main.py`, `functions/trigger_function_3/main.py`**

* **Function Logic:**
    * Replace the placeholder logic (`# Your logic here. ...`) with the actual Python code for your Cloud Functions.
    * Modify the API calls, trigger conditions, and any data processing to match your specific requirements.
* **Error Handling:**
    * Add robust error handling using `try-except` blocks.
    * Add logging.
* **Dependencies:**
    * Make sure that the requirements.txt files in each functions directory contain all of the python packages that your functions need.
* **Environment Variables:**
    * Verify that the environment variables are being used correctly.
* **Secret Manager:**
    * If you are accessing secret manager from within your cloud functions, add the code to do so.

**6. `start_service/main.py`**

* **API Call:**
    * Replace `"https://api.example.com/data"` with the actual URL of the API you want to fetch data from.
* **Trigger Condition:**
    * Modify the trigger condition (`if api_data.get("value") > 10:`) to match your specific requirements.
* **Error Handling:**
    * Add comprehensive error handling.
* **Secret Manager:**
    * If you are accessing secret manager from within your cloud run instance, add the code to do so.
* **Time interval:**
    * Change the time.sleep(300) to the desired time interval.
* **Dependencies:**
    * Make sure that the requirements.txt file contains all of the python packages that your cloud run instance needs.

**7. `start_service/Dockerfile`**

* Verify that the Dockerfile correctly builds your cloud run image.

**8. Google Cloud Storage (GCS)**

* **Function Source Code:**
    * Zip the contents of each function directory (`trigger_function_1`, `trigger_function_2`, `trigger_function_3`) and upload the ZIP files to your GCS source bucket.
* **Container Registry:**
    * Build and push the docker image for the start\_service to the google container registry.

**Key Considerations**

* **Security:** Prioritize security. Encrypt sensitive data, use Secret Manager, and follow least privilege principles.
* **Testing:** Thoroughly test your code and infrastructure.
* **Monitoring:** Set up monitoring and alerting to ensure your service is running reliably.

By following these steps, you'll be able to customize the Terraform code and Python functions to meet your specific requirements.

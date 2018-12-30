
# How to start Naglite4 

Naglite4 requires 

## Enable Icinga2 API and setup API user

1. Make sure your Icinga2 can provide API.

      ```bash
    # check if Icinga 2  API is enabled     
    icinga2 feature enable api    
    # if not enabled, run API setup
    icinga2 api setup
   ```

2. Create API user by adding following to Icinga2 config 

    ```
    object ApiUser "naglite"{
      password = "enter-your-secret-password-here"
    
      permissions = [
                "objects/query/Host",
                "objects/query/Service",
                "events/*",    // not really needed
                "status/query" // not really needed
                ]
    }
    ```
    
3. Reload Icinga2 with updated config.

    ```bash
    # check your Icinga2 config is valid
    icinga2 daemon validate
 
    # reload Icinga 
    systemctl reload icinga2
    ```

## Start Naglite4

1. Setup Naglite together with its dependencies. (or use provided RPM).

2. Start the Flask application service - example systemd unit 
  starts appliction on `127.0.0.1:4080` 

## Connect web server with application   

2.  Forward requests from webserver to the started Flask application. 

    ```nginx
        location /naglite4/ {
                proxy_pass http://localhost:4080/;
        }
        location /naglite4/static/ {
                proxy_pass http://localhost:4080/naglite4/static/ ;
        }
     ```


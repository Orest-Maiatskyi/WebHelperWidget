# WebHelperWidget - API

## 🚧 Development Status

**The API is currently under development.**

## 🔧 Current Status

- [x] JWT authentication
- [x] Email verification
- [ ] Password recovery by email
- [x] Account info
- [ ] Optional 2FA
- [x] Widget API key management
- [x] Training file management 
- [ ] Fine-tuning management
- [ ] API tests
- [ ] Swagger docs

## 🚀 How To Run

1. Clone repo and navigate to the `api` directory:
   ```sh
   cd api
   ```
2. Create and activate a virtual environment:   
   ```sh
   python -m venv venv
   source venv/bin/activate   # For Linux/macOS
   venv\Scripts\activate      # For Windows
   ```
> [!IMPORTANT]
> Python ver. must be >= 3.10
3. Install dependencies:
   ```sh
   (venv) pip install -r requirements.txt
   ```
4. Install MySQL and Redis on your server
5. Create *config.py* file inside app folder, path should be: *../WebHelperWidget/api/app/config.py*
    ```python
    import os
    from datetime import timedelta
    
    class DevConfig:
        DEBUG = True
        TESTING = False
    
        SECRET_KEY = ''                                        # random long secret string, can be created by: secrets.token_hex(32)
        SECURITY_PASSWORD_SALT = ''                            # salt to hash passwords in DB
    
        JWT_SECRET_KEY = ''                                    # can be created by: secrets.token_hex(64)
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)       # jwt access token lifetime
        JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=24)        # jwt refresh token lifetime
        JWT_BLACKLIST_ENABLED = True                           # If True - check redis for blacklisted tokens
        JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']     # Which token types should be checked in redis
    
        SQLALCHEMY_DATABASE_USERNAME = ''                      
        SQLALCHEMY_DATABASE_PASSWORD = ''                      
        SQLALCHEMY_DATABASE_HOST = ''                          
        SQLALCHEMY_DATABASE_PORT = ''                          
        SQLALCHEMY_DATABASE_NAME = ''                          
        SQLALCHEMY_DATABASE_URI = f'mysql+mysqlconnector://{SQLALCHEMY_DATABASE_USERNAME}:{SQLALCHEMY_DATABASE_PASSWORD}' \
                                  f'@{SQLALCHEMY_DATABASE_HOST}:{SQLALCHEMY_DATABASE_PORT}/{SQLALCHEMY_DATABASE_NAME}'
        SQLALCHEMY_TRACK_MODIFICATIONS = True                  
    
        REDIS_PASSWORD = ''                                    
        REDIS_HOST = ''                                        
        REDIS_PORT = ''
        REDIS_NAME = ''                                        
        REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_NAME}'
    
        MAIL_SERVER = ''                                       
        MAIL_PORT = ''                                         
        MAIL_USE_TLS = ''                                      
        MAIL_USERNAME = ''                                     
        MAIL_PASSWORD = ''                                     
        MAIL_DEFAULT_SENDER = ''                               
    
        MAIL_TOKEN_SECRET_KEY = ''                             
        MAIL_TOKEN_SECRET_SALT = ''                            
        MAIL_TOKEN_EXP = 250                                   # Lifetime value of email verification link or password recovery link
    
        OPENAI_API_KEY = ''                                    
     
        MATH_CAPTCHA_DURATION = 60                             # The time in which the user must solve the captcha (value in seconds) 
   
    current_config = DevConfig
    ```
6. Run the API:
   ```sh
   (venv) python entry.py
   ```

email_regexp = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
"""
This regular expression validates email addresses.

### Example Valid Matches:
- `user@example.com`
- `user.name+tag@sub-domain.example.org`
- `john.doe@company.co.uk`

### Example Invalid Matches:
- `user@com` (missing a proper TLD)
- `user@.com` (domain starts with a dot)
- `user@domain..com` (consecutive dots are invalid)
"""

password_regexp = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
"""
This regex validates a password with specific complexity requirements.

### Summary of Password Requirements:
- **Minimum Length**: 8 characters.
- **Must Contain**:
  - At least one uppercase letter.
  - At least one lowercase letter.
  - At least one digit.
  - At least one special character (`@$!%*?&`).
- **Allowed Characters**: Uppercase and lowercase letters, digits, and the special characters in `@$!%*?&`.

### Examples of Valid Passwords:
- `Abcdef1@`
- `P@ssw0rd123`
- `Strong!Pass2023`

### Examples of Invalid Passwords:
- `abcdef1@` (missing uppercase letter)
- `ABCDEF1@` (missing lowercase letter)
- `Abcdefgh` (missing digit and special character)
- `Ab1@` (less than 8 characters)
"""

name_regexp = r'^[a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ]{3,50}$'
"""
This regular expression matches a string that consists of between 3 and 50 characters, which can be English or 
Cyrillic letters (including Russian and Ukrainian), and the Russian "ё" in both cases. The string cannot contain 
spaces, punctuation, or other symbols.
"""

math_captcha_answer_regexp = r'^(?:[1-9][0-9]{0,2}|1000)$'
"""
This regular expression for matching numbers that are greater than 0 but less than or equal to 1000:
"""

removal_reason_regexp = r'^.{10,255}$'
"""
This regular expression for a string to be at least 10 characters and at most 255 characters.
"""

uuid4_regexp = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'
"""
This regular expression for a uuid4 string verification.
"""

api_key_name_regexp = r'^.{1, 100}$'
"""
This regular expression for api key optional description, min 1 symbol, max 100.
"""

api_key_domains_regexp = r'^(?:[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:,\s*[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})*$'
"""
This regular expression that matches a string containing domains separated by commas.

### Examples:
    example.com,example.org 	       ✅ Yes
    example.com, example.org,sub.net   ✅ Yes
    example.com,"	                   ❌ No
    example,com,example.org            ❌ No
    example.com,,example.org           ❌ No
"""

openai_file_id_regexp = r'^file-[a-zA-Z0-9]{22}$'
"""
This regular expression that matches a openai file id.
"""

mail_token_regexp = r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$'
"""
This regular expression for email tokens.
"""
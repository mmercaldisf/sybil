import os
import time
import requests
import tempfile

from dotenv import load_dotenv

SALESFORCE_ROOT_CA = """-----BEGIN CERTIFICATE-----
MIIF0DCCA7igAwIBAgIIW6vDkGPKX68wDQYJKoZIhvcNAQENBQAwgYUxCzAJBgNV
BAYTAlVTMRMwEQYDVQQIDApDYWxpZm9ybmlhMRYwFAYDVQQHDA1TYW4gRnJhbmNp
c2NvMR0wGwYDVQQKDBRzYWxlc2ZvcmNlLmNvbSwgaW5jLjEqMCgGA1UEAwwhc2Fs
ZXNmb3JjZS5jb20gSW50ZXJuYWwgUm9vdCBDQSAzMB4XDTE4MDkyNjE3MzYxNloX
DTI4MDkyMzE3MzYxNlowgYUxCzAJBgNVBAYTAlVTMRMwEQYDVQQIDApDYWxpZm9y
bmlhMRYwFAYDVQQHDA1TYW4gRnJhbmNpc2NvMR0wGwYDVQQKDBRzYWxlc2ZvcmNl
LmNvbSwgaW5jLjEqMCgGA1UEAwwhc2FsZXNmb3JjZS5jb20gSW50ZXJuYWwgUm9v
dCBDQSAzMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAgtwwTEHIl/Ok
v9hVHlJCGqxIxrzc6IokzThQSqo/ec21Q7C+dCnvX7d/iyQgviP5S256Jwx06WFT
4IZH9CYyiLpE+/3NHc7ni//bQGCpt0+o+PHPyXwtEpnp+NZZnR1iHlVRoNYrJqoq
r8ZPgbdC8m4e4xnrhleyAk3aTgzg88tcVKEmFi38rd3/5vMiZL6O/98HENwfrgIg
pAwdEhdjxuzEMITPUrk0Lo/3SeCK249dv6EWM7RQfdnzy2zlMcROONXn1NMZ35hK
SJ9DXc2M+hF5wNypGF3dyghQTdq/nxJkxFZIUkUcd0NzMpqjMoMrmsqv8qn4ZOWA
EyfPckNHv27R+tSSo+ctTAulL1xrQn/M2CFlBfQmZkSFToEPoLOzABnBwkJpwFm9
awPyaolf5l4Y/N9cZTcaG71SBf/yGcqzycgnujjBjJhRz0i2JE9s1a/NA0ALEe0m
6JIfpu1eL0+qOMajeiHebs9hjCdFzWuX4LFO4k76U3d1WTtlnFtg/7FUFkHzMv46
X6p9syjWfD7snU5hCD0N4037IeXzAV1zVnazbzzEP7dJDlJPivFw0DtCoQAsdK2V
XWA3Q2daUYiS8zyFagzIbk7+TzqcGWGvZq4DfEmAISRrOQKbU27VybV8Qwf2xTLh
CYHexYtC3XpO7lhdbjcBEQYNB47GtmcCAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB
/zAdBgNVHQ4EFgQUHdspGyq4y/PRIWJxYHVOMAoktwEwDgYDVR0PAQH/BAQDAgEG
MA0GCSqGSIb3DQEBDQUAA4ICAQALlaByN29bU8w9ZbPsmQ8ow6ElybyU8sPNs1o7
X2bxZRqHEWIbtirwYDFLaF93+qPdUrZ8F4Eckp6bHEmi7WF81xEHyL6rJ9SmTepm
syEn2pbi/PV66JMlzReaAl2+n1Avy7G6Zvn7Mm7IgCQKqfwaiSYFmBK7vRskaK1N
+nZfs5z83K7FBur1SCkUcPaYz3UA/rtqBiG5g9q16jFp0LyWfbK5Vo1EwX0knb/3
G7w0MDqrWehPIfrm2Jr+Sb4BOg7kItErVzu0D1EIiRJejvbYraeNKVQPXLHOqm5z
9dGAmUk7434AXrJvD8edR8fBA12rzSm8X/Zj51qSYybvdRUXNUONxLW0v1flLoUh
dUFXjcHVbcuDXWD1KYlf7u5AFUlN72jlk5RlJX5U71p+j/+1Wm/tHTG7sH7BmJlK
VNuUSYMRZp5lq6KXG2Ifs9fulWLAIhhW8kgi0QGmMD0dsYZ1JG+bY2tj+Zr3YtvH
GEBKux6nFFzq9IFsvwGrhI76Sx5hOiiRTXNxHxPB/oviZF4+GLS2IETjeQTQOU9D
eDocv81UUn0C9ZEnHXYHr9UcGWDY0Iv4PJDRxm9h1DjK8kH9r7BFx40ZV1m/cy0P
8hyDMT3LeuaTmBPf4uEqsXsk3c9Kjxn8KfrrTyzt+wYr2fVf613P+9SgVqglvN+G
U7OoSA==
-----END CERTIFICATE-----
"""

# Create a tempfile for our RootCA 
root_ca_file = tempfile.NamedTemporaryFile()
root_ca_file.write(SALESFORCE_ROOT_CA.encode())
root_ca_file.flush()

# Run the battery of envar loads
load_dotenv(os.path.expanduser("~/.llm_gateway"))
load_dotenv(".llm_gateway")
load_dotenv("env.conf")

# Load Custom Envars - Useful when an application already has its own.
def load_custom_environment(env_path):
    load_dotenv(env_path)

API_BASE_URL = "https://bot-svc-llm.sfproxy.einstein.dev1-uswest2.aws.sfdc.cl"
API_BASE_URL_BACKUP = "https://bot-svc-llm.sfproxy.einstein.aws-dev4-uswest2.aws.sfdc.cl"
DEFAULT_MODEL = "gpt-4-32k"
DEFAULT_TURBO_MODEL="gpt-4-1106-preview"
ORG62_ORG_ID = "00DSG00000061ur2AA"
MAX_BATCH_WORKERS=10

def generate(prompt, model=DEFAULT_TURBO_MODEL, temperature=0):
    
    base_url = API_BASE_URL
    
    headers = {
    'X-LLM-Provider': os.environ.get('LLM_GATEWAY_PROVIDER',"OpenAI"),
    'X-Org-Id':os.environ.get('LLM_ORG_ID',ORG62_ORG_ID),
    'Authorization': 'API_KEY %s' % os.environ.get("LLM_API_KEY","")
    }


    headers['x-client-feature-id'] = "SABotTest"

    data = {
    'prompt':prompt,
    "temperature":temperature,
    "model":model
    }


    response = requests.post("%s/v1.0/generations" % base_url,headers=headers,json=data, verify=root_ca_file.name)
    if response.status_code == 200:
        return True, response.json()['generations'][0]['text']
    # Rate Limited - We'll wait a bit and try again.
    elif response.status_code == 429: 
        time.sleep(10)
        response = requests.post("%s/v1.0/generations" % base_url,headers=headers,json=data, verify=SALESFORCE_ROOT_CA)
        if response.status_code == 200:
            return True, response.json()['generations'][0]['text']
    return False, response.content


if __name__ == "__main__":
   # Test Single Request 
   response = generate("Tell me a joke about penguins")
   print(response)

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



def process_gateway_request(endpoint, data, max_attempts=0):
    org_id = os.environ.get('LLM_ORG_ID',"00DSG00000061ur2AA")
    tenant_id = os.environ.get("LLM_ORG_TENANT_ID",f"core/{org_id}/{org_id}")
    base_url = os.environ.get("LLM_API_BASEURL", "https://bot-svc-llm.sfproxy.einstein.dev1-uswest2.aws.sfdc.cl")
    url = f"{base_url}{endpoint}"
    headers = {
    'X-LLM-Provider': os.environ.get('LLM_GATEWAY_PROVIDER',"OpenAI"),
    'X-Org-Id':org_id,
    'Authorization': 'API_KEY %s' % os.environ.get("LLM_API_KEY","651192c5-37ff-440a-b930-7444c69f4422"),
    'x-client-feature-id': os.environ.get("LLM_FEATURE_ID","Exploratory_Trial"),
    'x-sfdc-core-tenant-id': tenant_id
    }
 
    sleep_time = 1
    response_status = 0
    request_attempt = 0
    response = None
    while response_status != 200:
        r = requests.post(url, headers=headers, json=data, verify=root_ca_file.name)
        response_status = r.status_code
        if response_status == 429:
            time.sleep(sleep_time)
            sleep_time *=2
            if max_attempts > 0:
                request_attempt +=1
                if request_attempt >= max_attempts:
                    print("[LLM Gateway Request] Max Attempts Exceeded - Failing")
                    return False, response
            continue

        # Fix the race condition with the gateway...
        elif response_status == 400:
            if "It must follow the correct tenantKey format" in r.text:
                print("[LLM Gateway] Tenant ID Race Condition Hit, Retrying...")
                continue


        # TODO: Handle Other Edge Cases for Retry
        if response_status == 200:
            response = r.json()
            return True, response
        else:
            print(f"[LLM Gateway] Request Failed: {response_status}")
            print(r.text)
        break
    return False, response


def generate(prompt, model="gpt-4-0125-preview", temperature=0.7, max_attempts=0):
    data = {
        "prompt":prompt,
        "temperature":temperature,
        "model":model
    }
    status, response = process_gateway_request("/v1.0/generations",data,max_attempts=max_attempts)
    if status is False:
        print("Generate Failed")
        return None
    response_text = response['generations'][0]['text']
    return response_text


if __name__ == "__main__":
   # Test Single Request 
   response = generate("Tell me a joke about penguins")
   print(response)

# NGINX Plus API Gateway / AuthN / AuthZ with external backend DB

## Description

This is a sample NGINX Plus API Gateway configuration to publish REST APIs enforcing authentication and authorization.

NGINX Plus authenticates client requests by validating the JWT token. The backend DB provides a REST API used by NGINX Plus.
NGINX Plus authorizes the client request by fetching an authorization JSON from the external backend DB and matching it against:

- Request HTTP Method
- "X-AuthZ" HTTP header
- User role (from JWT claim "roles")

The authorization json is defined as:

```
    {
      'ruleid': 1,
      'enabled': 'true',
      'uri': 'v1.0/getRandomFact',
      'matchRules': {
        'method': 'GET',
        'roles': 'guest',
        'xauthz': 'api-v1.0'
      },
      'operation': {
        'url': 'http://numbersapi.com/random/year'
      }
    }
```

uri is the lookup key. If authentication and authorization succeed  NGINX Plus reverse-proxies the client request to the operation.url field.

The backend DB provides an endpoint (at /jwks.json) used by NGINX Plus to fetch the JWT secret.

## Prerequisites

- Kubernetes or Openshift cluster
- Linux VM with Docker to build all images
- Private registry to push the NGINX Plus and backend DB images
- The NGINX Plus image must include javascript (nginx-plus-module-njs) support

## Building the NGINX Plus image

Refer to the official documentation at

```
https://docs.nginx.com/nginx/admin-guide/installing-nginx/installing-nginx-docker/#docker_plus
```

## Deploying this repository

Build the backend DB:

```
cd backend-db
docker build --no-cache -t YOUR_PRIVATE_REGISTRY/nginx-authn-authz-backend-db:1.0 .
docker push YOUR_PRIVATE_REGISTRY/nginx-authn-authz-backend-db:1.0
```

Spin up NGINX Plus:

1. Update the backend DB "image" line referenced in 1.backend-db.yaml
2. Update the NGINX Plus "image" line referenced in 5.nginx-apigw.yaml
3. Run the following commands

```
cd apigw
kubectl apply -f 0.apigw.ns.yaml
cd certs
./cert-install.sh install
cd ..
kubectl apply -f 1.backend-db.yaml
kubectl apply -f 2.nginx.conf.yaml
kubectl apply -f 3.nginx.js.yaml
kubectl apply -f 4.nginx-authn-authz.conf.yaml
kubectl apply -f 5.nginx-apigw.yaml
```

## Cleaning up this repository

```
cd apigw
kubectl delete -f 0.apigw.ns.yaml
```

## Namespace check

```
$ kubectl get all -n nginx-authn-authz
NAME                               READY   STATUS    RESTARTS   AGE
pod/backend-db-5449cd986d-t4wg4    1/1     Running   0          4m26s
pod/nginx-apigw-5b567bd46d-mngmv   1/1     Running   0          22s

NAME                  TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)           AGE
service/backend-db    ClusterIP   10.102.99.56     <none>        5000/TCP          4m25s
service/nginx-apigw   ClusterIP   10.104.215.242   <none>        80/TCP,8080/TCP   21s

NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/backend-db    1/1     1            1           4m26s
deployment.apps/nginx-apigw   1/1     1            1           22s

NAME                                     DESIRED   CURRENT   READY   AGE
replicaset.apps/backend-db-5449cd986d    1         1         1       4m26s
replicaset.apps/nginx-apigw-5b567bd46d   1         1         1       22s

$ kubectl get ingress -n nginx-authn-authz
NAME          CLASS   HOSTS                                                   ADDRESS   PORTS     AGE
backend-db    nginx   db.nginx-authn-authz.ff.lan                                       80        25s
nginx-apigw   nginx   nginx-authn-authz.ff.lan,api.nginx-authn-authz.ff.lan             80, 443   15s
```

## NGINX Plus dashboard

Using your favourite browser open:

```
https://api.nginx-authn-authz.ff.lan/dashboard.html
```

## Creating JWT tokens

(see also https://www.nginx.com/blog/authenticating-api-clients-jwt-nginx-plus/)

This repository's backend DB uses a JWT secret defined as

```
$ cd jwt
$ cat jwks.json
{
  "keys": [
    {
      "k":"ZmFudGFzdGljand0",
      "kty":"oct",
      "kid":"0001"
    }
  ]
}
```
the k field is the generated symmetric key (base64url-encoded) basing on a secret (fantasticjwt in the example). The secret can be generated with the following command:

```
$ echo -n "fantasticjwt" | base64 | tr '+/' '-_' | tr -d '='
ZmFudGFzdGljand0
```

Create the JWT token using:

```
$ ./jwtEncoder.sh > jwt.token
$ cat jwt.token
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE2MjYyNTkxOTAsImV4cCI6MTYyNjI1OTE5MX0.eyJuYW1lIjoiSldUIG5hbWUgY2xhaW0iLCJzdWIiOiJKV1Qgc3ViIGNsYWltIiwiaXNzIjoiSldUIGlzcyBjbGFpbSIsInJvbGVzIjpbImd1ZXN0Il19.NbEhykETd6c2wHjU3HDOhypoOCpIGFxC1juZBWKUyO8
```

The decoded token is:

```
{
  "header": {
    "typ": "JWT",
    "alg": "HS256",
    "kid": "0001",
    "iss": "Bash JWT Generator",
    "iat": 1626259190,
    "exp": 1626259191
  },
  "payload": {
    "name": "JWT name claim",
    "sub": "JWT sub claim",
    "iss": "JWT iss claim",
    "roles": [
      "guest"
    ]
  }
}
```

## Backend DB test

Backend DB, fetching the JWT secret:

```
$ curl -s http://db.nginx-authn-authz.ff.lan/jwks.json | jq
{
  "keys": [
    {
      "k": "ZmFudGFzdGljand0",
      "kid": "0001",
      "kty": "oct"
    }
  ]
}
```

Backend DB, fetching all keys:

```
$ curl -s http://db.nginx-authn-authz.ff.lan/backend/fetchallkeys | jq
{
  "rules": [
    {
      "enabled": "true",
      "matchRules": {
        "method": "GET",
        "roles": "guest",
        "xauthz": "api-v1.0"
      },
      "operation": {
        "url": "http://numbersapi.com/random/year"
      },
      "ruleid": 1,
      "uri": "v1.0/getRandomFact"
    },
    {
      "enabled": "true",
      "matchRules": {
        "method": "GET",
        "roles": "guest netops",
        "xauthz": "api-v1.0"
      },
      "operation": {
        "url": "https://api.ipify.org/?format=json"
      },
      "ruleid": 2,
      "uri": "v1.0/getLocalIP"
    },
    {
      "enabled": "true",
      "matchRules": {
        "method": "POST",
        "roles": "devops",
        "xauthz": "api-v2.0"
      },
      "operation": {
        "url": "https://jsonplaceholder.typicode.com/posts"
      },
      "ruleid": 3,
      "uri": "v2.0/testPost"
    }
  ]
}
```

Backend DB, fetching a specific key:

```
$ curl -s http://db.nginx-authn-authz.ff.lan/backend/fetchkey/v1.0/getRandomFact | jq
{
  "rule": {
    "enabled": "true",
    "matchRules": {
      "method": "GET",
      "roles": "guest",
      "xauthz": "api-v1.0"
    },
    "operation": {
      "url": "http://numbersapi.com/random/year"
    },
    "ruleid": 1,
    "uri": "v1.0/getRandomFact"
  }
}
```

## REST API access test

Get NGINX Plus pod name:

```
$ kubectl get pods -n nginx-authn-authz
NAME                           READY   STATUS    RESTARTS   AGE
backend-db-5449cd986d-s6wjc    1/1     Running   0          2m35s
nginx-apigw-5b567bd46d-4dzlw   1/1     Running   0          30s
```

Display NGINX Plus logs:

```
$ kubectl logs nginx-apigw-5b567bd46d-4dzlw -n nginx-authn-authz -f
```

Open another terminal and use:

```
$ cd jwt
```

Test with valid HTTP method, no JWT token and no X-AuthZ header:

```
$ curl -X GET -ki https://nginx-authn-authz.ff.lan/v1.0/getRandomFact
HTTP/1.1 401 Unauthorized
Server: nginx/1.19.5
Date: Wed, 14 Jul 2021 00:05:58 GMT
Content-Type: text/html
Content-Length: 180
Connection: keep-alive
WWW-Authenticate: Bearer realm="authentication required"

<html>
<head><title>401 Authorization Required</title></head>
<body>
<center><h1>401 Authorization Required</h1></center>
<hr><center>nginx/1.19.10</center>
</body>
</html>
```

Test with valid JWT token, HTTP method and X-AuthZ header:

```
$ curl -X GET -ki -H "X-AuthZ: api-v1.0" -H "Authorization: Bearer `cat jwt.token`" https://nginx-authn-authz.ff.lan/v1.0/getRandomFact
HTTP/1.1 200 OK
Server: nginx/1.19.5
Date: Wed, 14 Jul 2021 10:46:42 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 134
Connection: keep-alive
X-Powered-By: Express
Access-Control-Allow-Origin: *
X-Numbers-API-Number: 1596
X-Numbers-API-Type: year
Pragma: no-cache
Cache-Control: no-cache,no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0
Expires: 0
ETag: W/"86-LOZwbw2FmGZayZAhgGE9bscPWIk"
Last-Modified: 1626259725

1596 is the year that Sir John Norreys and Sir Geoffrey Fenton travel to Connaught to parley with the local Irish lords on June NaNth.
```

Test with valid JWT token, HTTP method and invalid X-AuthZ header:

```
$ curl -X GET -ki -H "X-AuthZ: invalid" -H "Authorization: Bearer `cat jwt.token`" https://nginx-authn-authz.ff.lan/v1.0/getRandomFact
HTTP/1.1 403 Forbidden
Server: nginx/1.19.5
Date: Wed, 14 Jul 2021 10:48:26 GMT
Content-Type: text/html
Content-Length: 154
Connection: keep-alive

<html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
<hr><center>nginx/1.19.10</center>
</body>
</html>
```

Test with valid JWT token, X-AuthZ header and invalid HTTP method:

```
$ curl -X POST -ki -H "X-AuthZ: api-v1.0" -H "Authorization: Bearer `cat jwt.token`" https://nginx-authn-authz.ff.lan/v1.0/getRandomFact
HTTP/1.1 403 Forbidden
Server: nginx/1.19.5
Date: Wed, 14 Jul 2021 10:48:46 GMT
Content-Type: text/html
Content-Length: 154
Connection: keep-alive

<html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
<hr><center>nginx/1.19.10</center>
</body>
</html>
```

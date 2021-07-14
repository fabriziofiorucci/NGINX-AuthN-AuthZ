#!/bin/bash

case $1 in
	'clean')
		kubectl delete secret nginx-authn-authz.f5.ff.lan -n nginx-authn-authz
		rm nginx-authn-authz.f5.ff.lan.key nginx-authn-authz.f5.ff.lan.crt
	;;
	'install')
		openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout nginx-authn-authz.f5.ff.lan.key -out nginx-authn-authz.f5.ff.lan.crt -config nginx-authn-authz.f5.ff.lan.cnf
		kubectl create secret tls nginx-authn-authz.f5.ff.lan --key nginx-authn-authz.f5.ff.lan.key --cert nginx-authn-authz.f5.ff.lan.crt -n nginx-authn-authz
	;;
	*)
		echo "$0 [clean|install]"
		exit
	;;
esac

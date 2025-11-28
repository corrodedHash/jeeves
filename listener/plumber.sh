#! /bin/sh
redis-cli -h redis LPUSH job_queue "{ \"project\": \"$1\"}"
